"""
Job API routes for handling job creation, status, and management.
"""

from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from sqlmodel import select
from datetime import datetime
import logging

from app.db.database import get_session
from app.models.job_models import Job, JobStatus
from app.schemas.job_schemas import (
    JobSubmission, 
    JobStatusResponse, 
    JobCancelRequest,
    JobRetryRequest,
    JobListResponse,
    ErrorResponse,
    QueueStatusResponse
)
from app.services.queue import job_queue

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/", response_model=JobStatusResponse, status_code=status.HTTP_201_CREATED)
async def create_job(job_data: JobSubmission):
    """Create a new video processing job"""
    try:
        # Create job in database using simple service
        from app.services.simple_db import create_job
        job = create_job(
            youtube_url=str(job_data.youtube_url),
            job_type=job_data.job_type.value,
            priority=job_data.priority,
            options=job_data.options or {}
        )
        
        # Enqueue job for processing
        await job_queue.enqueue_job(job.id)
        
        logger.info(f"Created job {job.id} for URL: {job_data.youtube_url}")
        
        return JobStatusResponse.model_validate(job)
        
    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}"
        )


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get the status and details of a specific job"""
    from app.services.simple_db import get_job
    
    job = get_job(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return JobStatusResponse.model_validate(job)


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    status_filter: Optional[JobStatus] = Query(None, description="Filter by job status"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
):
    """List jobs with optional filtering and pagination"""
    from app.services.simple_db import list_jobs
    
    try:
        # Get jobs from database
        jobs = list_jobs(limit=limit + offset)  # Get extra for filtering
        
        # Apply filters (basic implementation)
        if status_filter:
            jobs = [job for job in jobs if job.status == status_filter]
        
        if job_type:
            jobs = [job for job in jobs if job.job_type == job_type]
        
        # Apply pagination
        total = len(jobs)
        jobs = jobs[offset:offset + limit]
        
        return JobListResponse(
            jobs=[JobStatusResponse.model_validate(job) for job in jobs],
            total=total,
            page=offset // limit + 1,
            per_page=limit,
            pages=(total + limit - 1) // limit
        )
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list jobs: {str(e)}"
        )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    session: Session = Depends(get_session)
):
    """Delete a completed, failed, or cancelled job"""
    job = session.get(Job, job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Only allow deletion of completed, failed, or cancelled jobs
    if job.status not in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete job that is currently processing"
        )
    
    try:
        session.delete(job)
        session.commit()
        logger.info(f"Deleted job {job_id}")
        
    except Exception as e:
        logger.error(f"Failed to delete job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete job: {str(e)}"
        )


@router.post("/{job_id}/cancel", response_model=dict)
async def cancel_job(
    job_id: str,
    cancel_request: JobCancelRequest = None,
    session: Session = Depends(get_session)
):
    """Cancel a pending or queued job"""
    job = session.get(Job, job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.status not in [JobStatus.PENDING, JobStatus.QUEUED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only cancel jobs that are pending or queued"
        )
    
    try:
        reason = cancel_request.reason if cancel_request else "Cancelled by user"
        success = await job_queue.cancel_job(job_id, reason)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel job"
            )
        
        return {"message": f"Job {job_id} has been cancelled", "reason": reason}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel job: {str(e)}"
        )


@router.post("/{job_id}/retry", response_model=JobStatusResponse)
async def retry_job(
    job_id: str,
    retry_request: JobRetryRequest = None,
    session: Session = Depends(get_session)
):
    """Retry a failed job"""
    job = session.get(Job, job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.status != JobStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only retry failed jobs"
        )
    
    # Check retry limits
    if job.retry_count >= job.max_retries and not (retry_request and retry_request.force):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job has exceeded maximum retry count ({job.max_retries})"
        )
    
    try:
        # Reset job status
        job.status = JobStatus.PENDING
        job.error_message = None
        job.retry_count += 1
        job.progress = 0.0
        job.started_at = None
        job.completed_at = None
        
        session.add(job)
        session.commit()
        session.refresh(job)
        
        # Enqueue for retry
        await job_queue.enqueue_job(job_id)
        
        logger.info(f"Retrying job {job_id} (attempt {job.retry_count})")
        
        return JobStatusResponse.model_validate(job)
        
    except Exception as e:
        logger.error(f"Failed to retry job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry job: {str(e)}"
        )


@router.get("/queue/status", response_model=QueueStatusResponse)
async def get_queue_status():
    """Get current queue status"""
    try:
        status = await job_queue.get_queue_status()
        return QueueStatusResponse(**status)
    except Exception as e:
        logger.error(f"Failed to get queue status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue status: {str(e)}"
        )


@router.delete("/queue/clear", status_code=status.HTTP_204_NO_CONTENT)
async def clear_queue(
    session: Session = Depends(get_session)
):
    """Clear all pending and queued jobs (admin only - add auth in production)"""
    try:
        # Get all pending and queued jobs
        statement = select(Job).where(Job.status.in_([JobStatus.PENDING, JobStatus.QUEUED]))
        jobs = session.exec(statement).all()
        
        # Mark as cancelled
        for job in jobs:
            job.status = JobStatus.CANCELLED
            job.error_message = "Cleared by administrator"
            job.completed_at = datetime.utcnow()
            session.add(job)
        
        session.commit()
        
        logger.info(f"Cleared {len(jobs)} jobs from queue")
        
    except Exception as e:
        logger.error(f"Failed to clear queue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear queue: {str(e)}"
        )


@router.get("/statistics", response_model=dict)
async def get_job_statistics(session: Session = Depends(get_session)):
    """Get job statistics"""
    try:
        # Get counts by status
        status_counts = {}
        for status in JobStatus:
            count = len(session.exec(select(Job).where(Job.status == status)).all())
            status_counts[status] = count
        
        # Get counts by type
        job_type_counts = {}
        # This would need to be implemented based on actual job types
        # For now, return basic stats
        total_jobs = sum(status_counts.values())
        
        return {
            "total_jobs": total_jobs,
            "by_status": status_counts,
            "queue_running": job_queue.is_running,
            "active_workers": len([w for w in job_queue.workers.values() if not w.done()])
        }
        
    except Exception as e:
        logger.error(f"Failed to get job statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job statistics: {str(e)}"
        )