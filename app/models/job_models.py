"""
Database models for the video processing application.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlmodel import Column, DateTime, Field, Float, Integer, JSON, SQLModel, String, Text


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Job type enumeration"""
    AUDIO_EXTRACTION = "audio_extraction"
    TRANSCRIPTION = "transcription"
    CLIP_GENERATION = "clip_generation"
    FULL_PROCESSING = "full_processing"
    ANALYSIS = "analysis"


class ProcessingStage(str, Enum):
    """Processing stage enumeration"""
    INITIALIZING = "initializing"
    DOWNLOADING = "downloading"
    EXTRACTING_AUDIO = "extracting_audio"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    GENERATING_CLIPS = "generating_clips"
    FINALIZING = "finalizing"
    COMPLETED = "completed"


class JobBase(SQLModel):
    """Base job model with common fields"""
    youtube_url: str = Field(sa_column=Column(String, nullable=False))
    job_type: JobType = Field(sa_column=Column(String, nullable=False))
    status: JobStatus = Field(
        default=JobStatus.PENDING,
        sa_column=Column(String, default=JobStatus.PENDING.value)
    )
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    priority: int = Field(default=0, ge=0, le=10)
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSON))
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text))
    worker_id: Optional[str] = Field(default=None, sa_column=Column(String))


class Job(JobBase, table=True):
    """Job database model"""
    __tablename__ = "jobs"
    
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        sa_column=Column(String, primary_key=True, index=True)
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=datetime.utcnow)
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    )
    started_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime)
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime)
    )
    timeout_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime)
    )
    
    # YouTube video information
    video_title: Optional[str] = Field(default=None, sa_column=Column(String))
    video_duration: Optional[float] = Field(default=None, sa_column=Column(Float))
    video_description: Optional[str] = Field(default=None, sa_column=Column(Text))
    video_uploader: Optional[str] = Field(default=None, sa_column=Column(String))
    video_view_count: Optional[int] = Field(default=None, sa_column=Column(Integer))
    video_thumbnail: Optional[str] = Field(default=None, sa_column=Column(String))
    
    # Processing results
    audio_file_path: Optional[str] = Field(default=None, sa_column=Column(String))
    transcript: Optional[str] = Field(default=None, sa_column=Column(Text))
    transcript_segments: Optional[List[Dict[str, Any]]] = Field(
        default=None, 
        sa_column=Column(JSON)
    )
    analysis_results: Optional[Dict[str, Any]] = Field(
        default=None, 
        sa_column=Column(JSON)
    )
    generated_clips: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        sa_column=Column(JSON)
    )
    output_files: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSON)
    )
    
    # Metadata
    total_file_size: Optional[int] = Field(default=None, sa_column=Column(Integer))
    processing_time: Optional[float] = Field(default=None, sa_column=Column(Float))
    retry_count: int = Field(default=0, ge=0)
    max_retries: int = Field(default=3, ge=0)


class JobEvent(SQLModel, table=True):
    """Job event log model for tracking progress"""
    __tablename__ = "job_events"
    
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        sa_column=Column(String, primary_key=True)
    )
    job_id: str = Field(sa_column=Column(String, index=True))
    event_type: str = Field(sa_column=Column(String))
    stage: Optional[ProcessingStage] = Field(
        default=None,
        sa_column=Column(String)
    )
    message: str = Field(sa_column=Column(Text))
    progress: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON)
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=datetime.utcnow)
    )


class WorkerStatus(SQLModel, table=True):
    """Worker status tracking model"""
    __tablename__ = "worker_status"
    
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        sa_column=Column(String, primary_key=True)
    )
    worker_id: str = Field(sa_column=Column(String, unique=True, index=True))
    status: str = Field(sa_column=Column(String))
    current_job_id: Optional[str] = Field(
        default=None,
        sa_column=Column(String)
    )
    last_heartbeat: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=datetime.utcnow)
    )
    jobs_processed: int = Field(default=0)
    average_processing_time: Optional[float] = Field(default=None, sa_column=Column(Float))
    system_info: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON)
    )


class ClipMetadata(SQLModel):
    """Clip metadata model"""
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: float
    end_time: float
    duration: float
    file_size: Optional[int] = None
    resolution: Optional[str] = None
    fps: Optional[float] = None
    codec: Optional[str] = None
    audio_codec: Optional[str] = None
    thumbnail_path: Optional[str] = None
    transcript_segment: Optional[str] = None
    tags: Optional[List[str]] = None