"""
WebSocket routes for real-time job progress updates.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.db.database import get_session
from app.models.job_models import Job
from app.services.queue import job_queue

logger = logging.getLogger(__name__)
router = APIRouter()

# Store active WebSocket connections
active_connections: Dict[str, Set[WebSocket]] = {}


@router.websocket("/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str, session=Depends(get_session)):
    """WebSocket endpoint for real-time job progress updates"""
    
    # Verify job exists
    job = session.get(Job, job_id)
    if not job:
        await websocket.close(code=1008, reason="Job not found")
        return
    
    await websocket.accept()
    
    # Add to active connections
    if job_id not in active_connections:
        active_connections[job_id] = set()
    active_connections[job_id].add(websocket)
    
    # Subscribe to job updates
    update_queue = job_queue.subscribe_to_job(job_id)
    
    try:
        # Send initial job status
        initial_data = {
            "type": "initial_status",
            "data": {
                "job_id": job_id,
                "status": job.status,
                "progress": job.progress,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        await websocket.send_text(json.dumps(initial_data))
        
        # Handle incoming messages and send updates
        while True:
            try:
                # Wait for updates from the queue
                update = await update_queue.get()
                
                # Send update to this connection
                await websocket.send_text(json.dumps(update))
                
            except Exception as e:
                logger.error(f"Error sending WebSocket update: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for job {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
    finally:
        # Clean up
        active_connections[job_id].discard(websocket)
        if not active_connections[job_id]:
            del active_connections[job_id]
        
        job_queue.unsubscribe_from_job(job_id, update_queue)


@router.websocket("/jobs/broadcast")
async def broadcast_endpoint(websocket: WebSocket):
    """WebSocket endpoint for broadcasting system updates to all clients"""
    await websocket.accept()
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back or handle broadcast messages
            await websocket.send_text(f"Echo: {data}")
            
    except WebSocketDisconnect:
        logger.info("Broadcast WebSocket disconnected")
    except Exception as e:
        logger.error(f"Broadcast WebSocket error: {e}")


async def broadcast_to_job(job_id: str, message: dict):
    """Broadcast a message to all WebSocket connections for a specific job"""
    if job_id in active_connections:
        disconnected = set()
        
        for websocket in active_connections[job_id].copy():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception:
                disconnected.add(websocket)
        
        # Remove disconnected connections
        for websocket in disconnected:
            active_connections[job_id].discard(websocket)
            if not active_connections[job_id]:
                del active_connections[job_id]


async def broadcast_system_update(message: dict):
    """Broadcast a system-wide update to all connected clients"""
    message_json = json.dumps(message)
    
    for job_id, connections in active_connections.items():
        disconnected = set()
        
        for websocket in connections.copy():
            try:
                await websocket.send_text(message_json)
            except Exception:
                disconnected.add(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected:
            connections.discard(websocket)
            if not connections:
                del active_connections[job_id]


@router.websocket("/health")
async def health_endpoint(websocket: WebSocket):
    """WebSocket endpoint for connection health checks"""
    await websocket.accept()
    
    try:
        while True:
            # Send periodic health status
            health_data = {
                "type": "health",
                "data": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "active_connections": sum(len(conns) for conns in active_connections.values()),
                    "queue_running": job_queue.is_running
                }
            }
            
            await websocket.send_text(json.dumps(health_data))
            await asyncio.sleep(30)  # Send health update every 30 seconds
            
    except WebSocketDisconnect:
        logger.info("Health WebSocket disconnected")
    except Exception as e:
        logger.error(f"Health WebSocket error: {e}")


@router.get("/connections/status")
async def get_connections_status():
    """Get status of active WebSocket connections (for monitoring)"""
    return {
        "active_connections": len(active_connections),
        "jobs_with_connections": list(active_connections.keys()),
        "total_connections": sum(len(conns) for conns in active_connections.values()),
        "queue_running": job_queue.is_running
    }