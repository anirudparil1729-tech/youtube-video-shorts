"""Simple database helpers.

The project intends to move toward a dedicated job manager / repository layer.
For now, these helpers keep database usage straightforward and testable.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from app.db.database import engine
from app.models.job_models import Job, JobStatus


def create_job(
    youtube_url: str,
    job_type: str,
    priority: int = 0,
    options: dict[str, Any] | None = None,
) -> Job:
    """Create a new job."""

    with Session(engine) as session:
        job = Job(
            youtube_url=youtube_url,
            job_type=job_type,
            priority=priority,
            options=options or {},
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        return job


def get_job(job_id: str) -> Job | None:
    """Get job by ID."""

    with Session(engine) as session:
        return session.get(Job, job_id)


def list_jobs(limit: int = 50) -> list[Job]:
    """List most recent jobs."""

    with Session(engine) as session:
        statement = select(Job).order_by(Job.created_at.desc()).limit(limit)
        return list(session.exec(statement).all())


def update_job(
    job_id: str,
    *,
    status: JobStatus | str | None = None,
    progress: float | None = None,
    error_message: str | None = None,
    worker_id: str | None = None,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
    video_title: str | None = None,
    transcript: str | None = None,
    analysis_results: dict[str, Any] | None = None,
    generated_clips: list[dict[str, Any]] | None = None,
    audio_file_path: str | None = None,
    output_files: list[str] | None = None,
    total_file_size: int | None = None,
    processing_time: float | None = None,
) -> bool:
    """Update job status and results."""

    with Session(engine) as session:
        job = session.get(Job, job_id)
        if not job:
            return False

        if status is not None:
            job.status = status  # type: ignore[assignment]
        if progress is not None:
            job.progress = progress
        if error_message is not None:
            job.error_message = error_message
        if worker_id is not None:
            job.worker_id = worker_id
        if started_at is not None:
            job.started_at = started_at
        if completed_at is not None:
            job.completed_at = completed_at

        if video_title is not None:
            job.video_title = video_title
        if transcript is not None:
            job.transcript = transcript
        if analysis_results is not None:
            job.analysis_results = analysis_results
        if generated_clips is not None:
            job.generated_clips = generated_clips

        if audio_file_path is not None:
            job.audio_file_path = audio_file_path
        if output_files is not None:
            job.output_files = output_files
        if total_file_size is not None:
            job.total_file_size = total_file_size
        if processing_time is not None:
            job.processing_time = processing_time

        session.add(job)
        session.commit()
        session.refresh(job)
        return True
