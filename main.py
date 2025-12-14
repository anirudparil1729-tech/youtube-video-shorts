"""Minimal working FastAPI backend for video processing.

This module provides a lightweight, in-memory implementation used by tests and
local development. The longer-term architecture is described in
`docs/architecture.md`.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from typing import Any

import uvicorn
from fastapi import (
    Body,
    FastAPI,
    HTTPException,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl, field_validator


# Simple in-memory job storage for demonstration
jobs_db: dict[str, dict[str, Any]] = {}
job_queue: list[str] = []
processing_jobs: dict[str, dict[str, Any]] = {}
job_subscribers: dict[str, list[WebSocket]] = {}


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


class JobSubmission(BaseModel):
    youtube_url: HttpUrl = Field(..., description="YouTube video URL to process")
    job_type: JobType = Field(default=JobType.TRANSCRIPTION)
    priority: int = Field(default=0, ge=0, le=10)
    options: dict[str, Any] = Field(default_factory=dict)

    @field_validator("youtube_url")
    @classmethod
    def validate_youtube_url(cls, v: HttpUrl) -> HttpUrl:
        url_str = str(v).lower()
        youtube_domains = ("youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com")
        if not any(domain in url_str for domain in youtube_domains):
            raise ValueError("URL must be a valid YouTube URL")
        return v


class JobCancelRequest(BaseModel):
    reason: str | None = None


class JobRetryRequest(BaseModel):
    force: bool = False


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat() + "Z"


async def notify_subscribers(job_id: str, message: dict[str, Any]) -> None:
    """Notify all subscribers of job updates."""

    subscribers = job_subscribers.get(job_id)
    if not subscribers:
        return

    for websocket in subscribers.copy():
        try:
            await websocket.send_text(json.dumps(message))
        except Exception:
            # Ignore disconnected websockets
            pass


async def process_job(job_id: str) -> None:
    """Simulate job processing with progress updates."""

    job = jobs_db.get(job_id)
    if not job:
        return

    job["status"] = JobStatus.PROCESSING
    job["progress"] = 0
    job["started_at"] = datetime.utcnow()

    stages: list[tuple[int, str]] = [
        (10, "Initializing job..."),
        (30, "Downloading video..."),
        (50, "Extracting audio..."),
        (70, "Transcribing audio..."),
        (85, "Analyzing content..."),
        (95, "Finalizing results..."),
        (100, "Job completed successfully!"),
    ]

    for progress, message in stages:
        if job["status"] == JobStatus.CANCELLED:
            break

        job["progress"] = progress
        job["updated_at"] = datetime.utcnow()

        await notify_subscribers(
            job_id,
            {
                "type": "progress_update",
                "data": {
                    "job_id": job_id,
                    "status": job["status"],
                    "progress": progress,
                    "message": message,
                    "timestamp": _iso(datetime.utcnow()),
                },
            },
        )

        await asyncio.sleep(0.05)

    if job["status"] != JobStatus.CANCELLED:
        job["status"] = JobStatus.COMPLETED
        job["progress"] = 100
        job["completed_at"] = datetime.utcnow()
        job["updated_at"] = datetime.utcnow()

        job["video_title"] = f"Sample Video - {job_id[:8]}"
        job["transcript"] = "This is a sample transcript from the video."
        job["analysis_results"] = {
            "sentiment": "positive",
            "topics": ["technology", "tutorial"],
            "confidence": 0.95,
        }
        job["generated_clips"] = [
            {"start": 0, "end": 30, "title": "Introduction"},
            {"start": 30, "end": 60, "title": "Main Content"},
        ]

        await notify_subscribers(
            job_id,
            {
                "type": "job_completed",
                "data": {
                    "job_id": job_id,
                    "status": job["status"],
                    "results": {
                        "video_title": job["video_title"],
                        "transcript": job["transcript"],
                        "analysis_results": job["analysis_results"],
                        "generated_clips": job["generated_clips"],
                    },
                },
            },
        )

    processing_jobs.pop(job_id, None)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Application lifespan management."""

    logging.info("Starting Video Processing API...")

    for i in range(3):
        asyncio.create_task(worker_loop(f"worker-{i}"))

    yield

    logging.info("Shutting down Video Processing API...")


async def worker_loop(worker_id: str) -> None:
    """Simple worker loop."""

    logging.info("Worker %s started", worker_id)

    while True:
        if job_queue:
            job_id = job_queue.pop(0)
            if job_id in jobs_db:
                processing_jobs[job_id] = {"worker_id": worker_id}
                await process_job(job_id)
        else:
            await asyncio.sleep(0.05)


app = FastAPI(
    title="Video Processing API",
    description="API for processing YouTube videos with AI models",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "Video Processing API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
    }


@app.get("/health")
async def health_check() -> dict[str, Any]:
    return {
        "status": "healthy",
        "queue_size": len(job_queue),
        "processing_jobs": len(processing_jobs),
        "total_jobs": len(jobs_db),
    }


@app.post("/api/v1/jobs/", status_code=status.HTTP_201_CREATED)
async def create_job(job_data: JobSubmission) -> dict[str, Any]:
    job_id = str(uuid.uuid4())

    now = datetime.utcnow()

    job: dict[str, Any] = {
        "id": job_id,
        "youtube_url": str(job_data.youtube_url),
        "job_type": job_data.job_type,
        "status": JobStatus.QUEUED,
        "progress": 0,
        "priority": job_data.priority,
        "created_at": now,
        "updated_at": now,
        "options": job_data.options,
    }

    jobs_db[job_id] = job
    job_queue.append(job_id)

    logging.info("Created job %s for URL: %s", job_id, job_data.youtube_url)

    return {
        "id": job_id,
        "youtube_url": job["youtube_url"],
        "job_type": job["job_type"],
        "status": job["status"],
        "progress": job["progress"],
        "priority": job["priority"],
        "created_at": _iso(job["created_at"]),
        "updated_at": _iso(job["updated_at"]),
    }


@app.get("/api/v1/jobs/{job_id}")
async def get_job_status(job_id: str) -> dict[str, Any]:
    job = jobs_db.get(job_id)

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    return {
        "id": job["id"],
        "youtube_url": job["youtube_url"],
        "job_type": job["job_type"],
        "status": job["status"],
        "progress": job["progress"],
        "priority": job["priority"],
        "created_at": _iso(job["created_at"]),
        "updated_at": _iso(job["updated_at"]),
        "video_title": job.get("video_title"),
        "transcript": job.get("transcript"),
        "analysis_results": job.get("analysis_results"),
        "generated_clips": job.get("generated_clips"),
    }


def _enum_value(value: Any) -> str:
    if isinstance(value, Enum):
        return value.value
    return str(value)


@app.get("/api/v1/jobs/")
async def list_jobs(
    status_filter: str | None = None,
    job_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    jobs = list(jobs_db.values())

    if status_filter:
        jobs = [job for job in jobs if _enum_value(job.get("status")) == status_filter]

    if job_type:
        jobs = [job for job in jobs if _enum_value(job.get("job_type")) == job_type]

    jobs.sort(key=lambda j: j["created_at"], reverse=True)

    total = len(jobs)
    jobs_page = jobs[offset : offset + limit]

    return {
        "jobs": [
            {
                "id": job["id"],
                "youtube_url": job["youtube_url"],
                "job_type": job["job_type"],
                "status": job["status"],
                "progress": job["progress"],
                "priority": job["priority"],
                "created_at": _iso(job["created_at"]),
                "updated_at": _iso(job["updated_at"]),
            }
            for job in jobs_page
        ],
        "total": total,
        "page": offset // limit + 1,
        "per_page": limit,
        "pages": (total + limit - 1) // limit,
    }


@app.delete("/api/v1/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: str) -> Response:
    job = jobs_db.get(job_id)

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job["status"] not in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete job that is currently processing",
        )

    jobs_db.pop(job_id, None)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/api/v1/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    cancel_request: JobCancelRequest | None = Body(default=None),
) -> dict[str, Any]:
    job = jobs_db.get(job_id)

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job["status"] not in {JobStatus.PENDING, JobStatus.QUEUED}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only cancel jobs that are pending or queued",
        )

    job["status"] = JobStatus.CANCELLED
    job["updated_at"] = datetime.utcnow()

    if job_id in job_queue:
        job_queue.remove(job_id)

    reason = cancel_request.reason if cancel_request else None
    return {"message": f"Job {job_id} has been cancelled", "reason": reason}


@app.post("/api/v1/jobs/{job_id}/retry")
async def retry_job(
    job_id: str,
    retry_request: JobRetryRequest | None = Body(default=None),
) -> dict[str, Any]:
    job = jobs_db.get(job_id)

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job["status"] != JobStatus.FAILED and not (retry_request and retry_request.force):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only retry failed jobs",
        )

    job["status"] = JobStatus.QUEUED
    job["progress"] = 0
    job["updated_at"] = datetime.utcnow()
    job_queue.append(job_id)

    return {
        "id": job["id"],
        "youtube_url": job["youtube_url"],
        "job_type": job["job_type"],
        "status": job["status"],
        "progress": job["progress"],
        "priority": job["priority"],
        "created_at": _iso(job["created_at"]),
        "updated_at": _iso(job["updated_at"]),
    }


@app.get("/api/v1/jobs/queue/status")
async def get_queue_status() -> dict[str, Any]:
    return {
        "is_running": True,
        "total_jobs": len(jobs_db),
        "pending_jobs": len(
            [j for j in jobs_db.values() if j["status"] == JobStatus.PENDING]
        ),
        "queued_jobs": len(
            [j for j in jobs_db.values() if j["status"] == JobStatus.QUEUED]
        ),
        "processing_jobs": len(
            [j for j in jobs_db.values() if j["status"] == JobStatus.PROCESSING]
        ),
        "completed_jobs": len(
            [j for j in jobs_db.values() if j["status"] == JobStatus.COMPLETED]
        ),
        "failed_jobs": len(
            [j for j in jobs_db.values() if j["status"] == JobStatus.FAILED]
        ),
        "cancelled_jobs": len(
            [j for j in jobs_db.values() if j["status"] == JobStatus.CANCELLED]
        ),
        "active_workers": 3,
        "queue_size": len(job_queue),
    }


@app.get("/api/v1/jobs/statistics")
async def get_job_statistics() -> dict[str, Any]:
    by_status: dict[str, int] = {status.value: 0 for status in JobStatus}
    for job in jobs_db.values():
        by_status[_enum_value(job["status"])] += 1

    return {
        "total_jobs": len(jobs_db),
        "by_status": by_status,
        "queue_running": True,
        "active_workers": 3,
    }


@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    if job_id not in jobs_db:
        await websocket.close(code=1008, reason="Job not found")
        return

    await websocket.accept()

    job_subscribers.setdefault(job_id, []).append(websocket)

    try:
        job = jobs_db[job_id]
        initial_data = {
            "type": "initial_status",
            "data": {
                "job_id": job_id,
                "status": job["status"],
                "progress": job["progress"],
                "timestamp": _iso(datetime.utcnow()),
            },
        }
        await websocket.send_text(json.dumps(initial_data))

        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        pass
    finally:
        if job_id in job_subscribers:
            job_subscribers[job_id] = [ws for ws in job_subscribers[job_id] if ws != websocket]
            if not job_subscribers[job_id]:
                del job_subscribers[job_id]


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
