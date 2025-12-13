"""
Minimal working FastAPI backend for video processing.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

# Simple in-memory job storage for demonstration
jobs_db: Dict[str, dict] = {}
job_queue: List[str] = []
processing_jobs: Dict[str, dict] = {}
job_subscribers: Dict[str, List] = {}


class JobStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    AUDIO_EXTRACTION = "audio_extraction"
    TRANSCRIPTION = "transcription"
    CLIP_GENERATION = "clip_generation"
    FULL_PROCESSING = "full_processing"
    ANALYSIS = "analysis"


# Simple processing simulation
async def process_job(job_id: str):
    """Simulate job processing with progress updates"""
    job = jobs_db.get(job_id)
    if not job:
        return
    
    job['status'] = JobStatus.PROCESSING
    job['progress'] = 0
    
    # Simulate processing stages
    stages = [
        (10, "Initializing job..."),
        (30, "Downloading video..."),
        (50, "Extracting audio..."),
        (70, "Transcribing audio..."),
        (85, "Analyzing content..."),
        (95, "Finalizing results..."),
        (100, "Job completed successfully!")
    ]
    
    for progress, message in stages:
        if job['status'] == JobStatus.CANCELLED:
            break
            
        job['progress'] = progress
        job['updated_at'] = datetime.utcnow()
        
        # Notify subscribers
        await notify_subscribers(job_id, {
            "type": "progress_update",
            "data": {
                "job_id": job_id,
                "status": job['status'],
                "progress": progress,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        await asyncio.sleep(2)
    
    # Complete the job
    if job['status'] != JobStatus.CANCELLED:
        job['status'] = JobStatus.COMPLETED
        job['progress'] = 100
        job['video_title'] = f"Sample Video - {job_id[:8]}"
        job['transcript'] = "This is a sample transcript from the video."
        job['analysis_results'] = {
            "sentiment": "positive",
            "topics": ["technology", "tutorial"],
            "confidence": 0.95
        }
        job['generated_clips'] = [
            {"start": 0, "end": 30, "title": "Introduction"},
            {"start": 30, "end": 60, "title": "Main Content"}
        ]
        
        await notify_subscribers(job_id, {
            "type": "job_completed",
            "data": {
                "job_id": job_id,
                "status": job['status'],
                "results": {
                    "video_title": job['video_title'],
                    "transcript": job['transcript'],
                    "analysis_results": job['analysis_results'],
                    "generated_clips": job['generated_clips']
                }
            }
        })
    
    processing_jobs.pop(job_id, None)


async def notify_subscribers(job_id: str, message: dict):
    """Notify all subscribers of job updates"""
    if job_id in job_subscribers:
        for websocket in job_subscribers[job_id]:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception:
                pass  # Ignore disconnected websockets


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logging.info("Starting Video Processing API...")
    
    # Start worker tasks
    for i in range(3):
        asyncio.create_task(worker_loop(f"worker-{i}"))
    
    yield
    
    logging.info("Shutting down Video Processing API...")


async def worker_loop(worker_id: str):
    """Simple worker loop"""
    logging.info(f"Worker {worker_id} started")
    
    while True:
        if job_queue:
            job_id = job_queue.pop(0)
            if job_id in jobs_db:
                processing_jobs[job_id] = {"worker_id": worker_id}
                await process_job(job_id)
        else:
            await asyncio.sleep(1)


# Create FastAPI application
app = FastAPI(
    title="Video Processing API",
    description="API for processing YouTube videos with AI models",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Video Processing API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "queue_size": len(job_queue),
        "processing_jobs": len(processing_jobs),
        "total_jobs": len(jobs_db)
    }


@app.post("/api/v1/jobs/")
async def create_job(job_data: dict):
    """Create a new video processing job"""
    try:
        job_id = str(uuid.uuid4())
        
        # Validate YouTube URL
        youtube_url = job_data.get("youtube_url")
        if not youtube_url or "youtube.com" not in youtube_url and "youtu.be" not in youtube_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid YouTube URL"
            )
        
        job_type = job_data.get("job_type", "transcription")
        priority = job_data.get("priority", 0)
        
        job = {
            "id": job_id,
            "youtube_url": youtube_url,
            "job_type": job_type,
            "status": JobStatus.PENDING,
            "progress": 0,
            "priority": priority,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "options": job_data.get("options", {})
        }
        
        jobs_db[job_id] = job
        job_queue.append(job_id)
        
        job['status'] = JobStatus.QUEUED
        
        logging.info(f"Created job {job_id} for URL: {youtube_url}")
        
        return {
            "id": job_id,
            "youtube_url": youtube_url,
            "job_type": job_type,
            "status": JobStatus.QUEUED,
            "progress": 0,
            "priority": priority,
            "created_at": job["created_at"].isoformat(),
            "updated_at": job["updated_at"].isoformat()
        }
        
    except Exception as e:
        logging.error(f"Failed to create job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}"
        )


@app.get("/api/v1/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get the status and details of a specific job"""
    job = jobs_db.get(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return {
        "id": job["id"],
        "youtube_url": job["youtube_url"],
        "job_type": job["job_type"],
        "status": job["status"],
        "progress": job["progress"],
        "priority": job["priority"],
        "created_at": job["created_at"].isoformat(),
        "updated_at": job["updated_at"].isoformat(),
        "video_title": job.get("video_title"),
        "transcript": job.get("transcript"),
        "analysis_results": job.get("analysis_results"),
        "generated_clips": job.get("generated_clips")
    }


@app.get("/api/v1/jobs/")
async def list_jobs(
    status_filter: Optional[str] = None,
    job_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List jobs with optional filtering and pagination"""
    jobs = list(jobs_db.values())
    
    # Apply filters
    if status_filter:
        jobs = [job for job in jobs if job["status"] == status_filter]
    
    if job_type:
        jobs = [job for job in jobs if job["job_type"] == job_type]
    
    # Sort by created_at desc
    jobs.sort(key=lambda j: j["created_at"], reverse=True)
    
    # Apply pagination
    total = len(jobs)
    jobs = jobs[offset:offset + limit]
    
    return {
        "jobs": [
            {
                "id": job["id"],
                "youtube_url": job["youtube_url"],
                "job_type": job["job_type"],
                "status": job["status"],
                "progress": job["progress"],
                "priority": job["priority"],
                "created_at": job["created_at"].isoformat(),
                "updated_at": job["updated_at"].isoformat()
            }
            for job in jobs
        ],
        "total": total,
        "page": offset // limit + 1,
        "per_page": limit,
        "pages": (total + limit - 1) // limit
    }


@app.delete("/api/v1/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a completed, failed, or cancelled job"""
    job = jobs_db.get(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job["status"] not in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete job that is currently processing"
        )
    
    jobs_db.pop(job_id, None)
    return {"message": f"Job {job_id} deleted successfully"}


@app.post("/api/v1/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a pending or queued job"""
    job = jobs_db.get(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job["status"] not in [JobStatus.PENDING, JobStatus.QUEUED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only cancel jobs that are pending or queued"
        )
    
    job["status"] = JobStatus.CANCELLED
    job["updated_at"] = datetime.utcnow()
    
    # Remove from queue if still there
    if job_id in job_queue:
        job_queue.remove(job_id)
    
    return {"message": f"Job {job_id} has been cancelled"}


@app.get("/api/v1/jobs/queue/status")
async def get_queue_status():
    """Get current queue status"""
    return {
        "is_running": True,
        "total_jobs": len(jobs_db),
        "pending_jobs": len([j for j in jobs_db.values() if j["status"] == JobStatus.PENDING]),
        "queued_jobs": len([j for j in jobs_db.values() if j["status"] == JobStatus.QUEUED]),
        "processing_jobs": len([j for j in jobs_db.values() if j["status"] == JobStatus.PROCESSING]),
        "completed_jobs": len([j for j in jobs_db.values() if j["status"] == JobStatus.COMPLETED]),
        "failed_jobs": len([j for j in jobs_db.values() if j["status"] == JobStatus.FAILED]),
        "cancelled_jobs": len([j for j in jobs_db.values() if j["status"] == JobStatus.CANCELLED]),
        "active_workers": 3,
        "queue_size": len(job_queue)
    }


# WebSocket endpoint for real-time updates
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time job progress updates"""
    
    # Verify job exists
    if job_id not in jobs_db:
        await websocket.close(code=1008, reason="Job not found")
        return
    
    await websocket.accept()
    
    # Add to subscribers
    if job_id not in job_subscribers:
        job_subscribers[job_id] = []
    job_subscribers[job_id].append(websocket)
    
    try:
        # Send initial job status
        job = jobs_db[job_id]
        initial_data = {
            "type": "initial_status",
            "data": {
                "job_id": job_id,
                "status": job["status"],
                "progress": job["progress"],
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        await websocket.send_text(json.dumps(initial_data))
        
        # Keep connection alive
        while True:
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        pass
    finally:
        # Remove from subscribers
        if job_id in job_subscribers:
            job_subscribers[job_id].remove(websocket)
            if not job_subscribers[job_id]:
                del job_subscribers[job_id]


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )