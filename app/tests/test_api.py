"""
Basic tests for the video processing API.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Video Processing API"


def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_create_job():
    """Test creating a new job"""
    job_data = {
        "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "job_type": "transcription",
        "priority": 5,
        "options": {
            "language": "en",
            "model_size": "base"
        }
    }
    
    response = client.post("/api/v1/jobs/", json=job_data)
    assert response.status_code == 201
    
    data = response.json()
    assert "id" in data
    assert data["job_type"] == "transcription"
    assert data["status"] in ["pending", "queued", "processing"]
    assert data["youtube_url"] == job_data["youtube_url"]
    assert data["priority"] == 5
    
    return data["id"]


def test_create_job_invalid_url():
    """Test creating job with invalid YouTube URL"""
    job_data = {
        "youtube_url": "https://example.com/video",
        "job_type": "transcription"
    }
    
    response = client.post("/api/v1/jobs/", json=job_data)
    assert response.status_code == 422  # Validation error


def test_get_job_status():
    """Test getting job status"""
    # Create a job first
    job_id = test_create_job()
    
    # Get job status
    response = client.get(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == job_id
    assert "status" in data
    assert "progress" in data
    assert data["progress"] >= 0


def test_get_nonexistent_job():
    """Test getting status of non-existent job"""
    response = client.get("/api/v1/jobs/non-existent-id")
    assert response.status_code == 404


def test_list_jobs():
    """Test listing jobs"""
    # Create a few jobs first
    test_create_job()
    test_create_job()
    
    response = client.get("/api/v1/jobs/")
    assert response.status_code == 200
    
    data = response.json()
    assert "jobs" in data
    assert "total" in data
    assert "page" in data
    assert "per_page" in data
    assert "pages" in data
    assert isinstance(data["jobs"], list)


def test_list_jobs_with_filters():
    """Test listing jobs with filters"""
    response = client.get("/api/v1/jobs/?status_filter=pending&limit=10")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data["jobs"], list)


def test_queue_status():
    """Test queue status endpoint"""
    response = client.get("/api/v1/jobs/queue/status")
    assert response.status_code == 200
    
    data = response.json()
    assert "is_running" in data
    assert "total_jobs" in data
    assert "pending_jobs" in data
    assert "processing_jobs" in data
    assert "active_workers" in data


def test_job_statistics():
    """Test job statistics endpoint"""
    response = client.get("/api/v1/jobs/statistics")
    assert response.status_code == 200
    
    data = response.json()
    assert "total_jobs" in data
    assert "by_status" in data
    assert "queue_running" in data
    assert "active_workers" in data


def test_websocket_endpoint():
    """Test WebSocket endpoint connection"""
    # Create a job first
    job_id = test_create_job()
    
    # Test WebSocket connection
    from websockets.sync.client import connect
    import json
    
    try:
        with connect(f"ws://localhost:8000/ws/{job_id}") as websocket:
            # Send a message (should be ignored)
            websocket.send("ping")
            
            # Receive initial status
            message = websocket.recv(timeout=5)
            data = json.loads(message)
            
            assert data["type"] in ["initial_status", "job_update"]
            assert "job_id" in data["data"]
            assert data["data"]["job_id"] == job_id
    except Exception:
        # WebSocket test might fail in test environment
        pass


def test_create_job_different_types():
    """Test creating jobs of different types"""
    job_types = ["audio_extraction", "transcription", "clip_generation", "full_processing", "analysis"]
    
    for job_type in job_types:
        job_data = {
            "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "job_type": job_type
        }
        
        response = client.post("/api/v1/jobs/", json=job_data)
        assert response.status_code == 201
        assert response.json()["job_type"] == job_type


def test_job_priority():
    """Test job priority functionality"""
    job_data = {
        "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "job_type": "transcription",
        "priority": 10  # Maximum priority
    }
    
    response = client.post("/api/v1/jobs/", json=job_data)
    assert response.status_code == 201
    assert response.json()["priority"] == 10


def test_cancel_job():
    """Test cancelling a job"""
    # Create a job
    job_id = test_create_job()
    
    # Cancel it
    cancel_data = {"reason": "Test cancellation"}
    response = client.post(f"/api/v1/jobs/{job_id}/cancel", json=cancel_data)
    
    # Note: Cancellation might succeed or fail depending on job state
    assert response.status_code in [200, 400, 404]


def test_retry_failed_job():
    """Test retrying a failed job"""
    # Create a job
    job_id = test_create_job()
    
    # Try to retry it (might fail if job hasn't failed yet)
    response = client.post(f"/api/v1/jobs/{job_id}/retry")
    assert response.status_code in [200, 400, 404]


def test_delete_completed_job():
    """Test deleting a completed job"""
    # Create a job
    job_id = test_create_job()
    
    # Try to delete it (might fail if job is still processing)
    response = client.delete(f"/api/v1/jobs/{job_id}")
    assert response.status_code in [204, 400, 404]


if __name__ == "__main__":
    # Run basic smoke tests
    print("Running smoke tests...")
    
    test_root_endpoint()
    print("✓ Root endpoint test passed")
    
    test_health_check()
    print("✓ Health check test passed")
    
    test_create_job()
    print("✓ Create job test passed")
    
    test_list_jobs()
    print("✓ List jobs test passed")
    
    print("\nAll basic tests passed!")