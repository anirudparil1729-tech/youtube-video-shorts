"""Job API routes.

These routes are part of the "full" backend (DB-backed + async queue).
The test suite in this repo currently targets the in-memory implementation in
`main.py`, but these routes remain as the intended production shape.
"""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.db.database import get_session
from app.models.job_models import Job, JobStatus
from app.schemas.job_schemas import (
    JobCancelRequest,
    JobListResponse,
    JobRetryRequest,
    JobStatusResponse,
    JobSubmission,
    QueueStatusResponse,
)
from app.services.queue import job_queue
from app.services.simple_db import create_job as db_create_job
from app.services.simple_db import get_job as db_get_job
from app.services.simple_db import list_jobs as db_list_jobs

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/", response_model=JobStatusResponse, status_code=status.HTTP_201_CREATED)
async def create_job_endpoint(job_data: JobSubmission) -> JobStatusResponse:
    try:
        job = db_create_job(
            youtube_url=str(job_data.youtube_url),
            job_type=job_data.job_type.value,
            priority=job_data.priority,
            options=job_data.options or {},
        )
        await job_queue.enqueue_job(job.id)
        return JobStatusResponse.model_validate(job)
    except Exception as e:
        logger.exception("Failed to create job")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {e}",
        ) from e


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    job = db_get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobStatusResponse.model_validate(job)


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    status_filter: JobStatus | None = Query(None, description="Filter by job status"),
    job_type: str | None = Query(None, description="Filter by job type"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
) -> JobListResponse:
    jobs = db_list_jobs(limit=limit + offset)

    if status_filter is not None:
        jobs = [job for job in jobs if job.status == status_filter]

    if job_type is not None:
        jobs = [job for job in jobs if job.job_type == job_type]

    total = len(jobs)
    jobs_page = jobs[offset : offset + limit]

    return JobListResponse(
        jobs=[JobStatusResponse.model_validate(job) for job in jobs_page],
        total=total,
        page=offset // limit + 1,
        per_page=limit,
        pages=(total + limit - 1) // limit,
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: str, session: Session = Depends(get_session)) -> None:
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.status not in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete job that is currently processing",
        )

    session.delete(job)
    session.commit()


@router.post("/{job_id}/cancel", response_model=dict)
async def cancel_job(
    job_id: str,
    cancel_request: JobCancelRequest | None = None,
) -> dict:
    reason = cancel_request.reason if cancel_request else "Cancelled by user"

    success = await job_queue.cancel_job(job_id, reason)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to cancel job (invalid state or not found)",
        )

    return {"message": f"Job {job_id} has been cancelled", "reason": reason}


@router.post("/{job_id}/retry", response_model=JobStatusResponse)
async def retry_job(
    job_id: str,
    retry_request: JobRetryRequest | None = None,
    session: Session = Depends(get_session),
) -> JobStatusResponse:
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.status != JobStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only retry failed jobs",
        )

    if job.retry_count >= job.max_retries and not (retry_request and retry_request.force):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job has exceeded maximum retry count ({job.max_retries})",
        )

    job.status = JobStatus.QUEUED
    job.error_message = None
    job.retry_count += 1
    job.progress = 0.0
    job.started_at = None
    job.completed_at = None
    job.updated_at = datetime.utcnow()

    session.add(job)
    session.commit()
    session.refresh(job)

    await job_queue.enqueue_job(job.id)
    return JobStatusResponse.model_validate(job)


@router.get("/queue/status", response_model=QueueStatusResponse)
async def get_queue_status() -> QueueStatusResponse:
    data = await job_queue.get_queue_status()
    return QueueStatusResponse(**data)


@router.delete("/queue/clear", status_code=status.HTTP_204_NO_CONTENT)
async def clear_queue(session: Session = Depends(get_session)) -> None:
    statement = select(Job).where(
        Job.status.in_([JobStatus.PENDING, JobStatus.QUEUED])
    )
    jobs = session.exec(statement).all()

    for job in jobs:
        job.status = JobStatus.CANCELLED
        job.error_message = "Cleared by administrator"
        job.completed_at = datetime.utcnow()
        job.updated_at = datetime.utcnow()
        session.add(job)

    session.commit()


@router.get("/statistics", response_model=dict)
async def get_job_statistics(session: Session = Depends(get_session)) -> dict:
    counts_by_status: dict[str, int] = {}
    for job_status in JobStatus:
        counts_by_status[job_status.value] = len(
            session.exec(select(Job).where(Job.status == job_status)).all()
        )

    return {
        "total_jobs": sum(counts_by_status.values()),
        "by_status": counts_by_status,
        "queue_running": job_queue.is_running,
        "active_workers": len([t for t in job_queue.workers.values() if not t.done()]),
    }
