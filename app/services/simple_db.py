"""
Simple database service for job management.
"""

from sqlmodel import SQLModel, create_engine, Session, select
from typing import List, Optional
import uuid
from datetime import datetime
from app.models.job_models import Job


def get_db_engine():
    """Get database engine"""
    return create_engine("sqlite:///./video_processing.db", echo=True)


def create_job(youtube_url: str, job_type: str, priority: int = 0, options: dict = None) -> Job:
    """Create a new job"""
    engine = get_db_engine()
    session = Session(engine)
    try:
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            youtube_url=youtube_url,
            job_type=job_type,
            priority=priority,
            options=options or {}
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        return job
    finally:
        session.close()


def get_job(job_id: str) -> Optional[Job]:
    """Get job by ID"""
    engine = get_db_engine()
    session = Session(engine)
    try:
        job = session.get(Job, job_id)
        return job
    finally:
        session.close()


def list_jobs(limit: int = 50) -> List[Job]:
    """List all jobs"""
    engine = get_db_engine()
    session = Session(engine)
    try:
        statement = select(Job).order_by(Job.created_at.desc()).limit(limit)
        jobs = session.exec(statement).all()
        return jobs
    finally:
        session.close()


def update_job_status(job_id: str, status: str, progress: float = None, 
                     video_title: str = None, transcript: str = None,
                     analysis_results: dict = None, generated_clips: list = None) -> bool:
    """Update job status and results"""
    engine = get_db_engine()
    session = Session(engine)
    try:
        job = session.get(Job, job_id)
        if job:
            job.status = status
            if progress is not None:
                job.progress = progress
            if video_title is not None:
                job.video_title = video_title
            if transcript is not None:
                job.transcript = transcript
            if analysis_results is not None:
                job.analysis_results = analysis_results
            if generated_clips is not None:
                job.generated_clips = generated_clips
            session.add(job)
            session.commit()
            return True
        return False
    finally:
        session.close()