"""
Pydantic schemas for API request/response models.
"""

from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
from app.models.job_models import JobStatus, JobType, ProcessingStage, ClipMetadata


class JobSubmission(BaseModel):
    """Schema for job submission requests"""
    youtube_url: HttpUrl = Field(..., description="YouTube video URL to process")
    job_type: JobType = Field(..., description="Type of processing job")
    priority: int = Field(default=0, ge=0, le=10, description="Job priority (0-10)")
    options: Optional[Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Job-specific options"
    )
    
    @validator("youtube_url")
    def validate_youtube_url(cls, v):
        """Validate that the URL is a YouTube URL"""
        url_str = str(v).lower()
        youtube_domains = ["youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com"]
        if not any(domain in url_str for domain in youtube_domains):
            raise ValueError("URL must be a valid YouTube URL")
        return v


class JobStatusResponse(BaseModel):
    """Schema for job status responses"""
    id: str
    youtube_url: str
    job_type: JobType
    status: JobStatus
    progress: float = Field(ge=0.0, le=100.0)
    priority: int
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    worker_id: Optional[str] = None
    
    # Video information
    video_title: Optional[str] = None
    video_duration: Optional[float] = None
    video_description: Optional[str] = None
    video_uploader: Optional[str] = None
    video_view_count: Optional[int] = None
    video_thumbnail: Optional[str] = None
    
    # Processing results
    audio_file_path: Optional[str] = None
    transcript: Optional[str] = None
    transcript_segments: Optional[List[Dict[str, Any]]] = None
    analysis_results: Optional[Dict[str, Any]] = None
    generated_clips: Optional[List[Dict[str, Any]]] = None
    output_files: Optional[List[str]] = None
    total_file_size: Optional[int] = None
    processing_time: Optional[float] = None
    retry_count: int = 0
    
    class Config:
        from_attributes = True


class JobEventResponse(BaseModel):
    """Schema for job event responses"""
    id: str
    job_id: str
    event_type: str
    stage: Optional[ProcessingStage] = None
    message: str
    progress: Optional[float] = Field(None, ge=0.0, le=100.0)
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True


class WorkerStatusResponse(BaseModel):
    """Schema for worker status responses"""
    worker_id: str
    status: str
    current_job_id: Optional[str] = None
    last_heartbeat: datetime
    jobs_processed: int
    average_processing_time: Optional[float] = None
    
    class Config:
        from_attributes = True


class JobCancelRequest(BaseModel):
    """Schema for job cancellation requests"""
    reason: Optional[str] = Field(None, description="Reason for cancellation")


class JobRetryRequest(BaseModel):
    """Schema for job retry requests"""
    force: bool = Field(default=False, description="Force retry even if max retries reached")


class BulkJobAction(BaseModel):
    """Schema for bulk job actions"""
    job_ids: List[str] = Field(..., min_items=1, description="List of job IDs")
    action: str = Field(..., description="Action to perform: cancel, retry, delete")


class QueueStatusResponse(BaseModel):
    """Schema for queue status responses"""
    is_running: bool
    total_jobs: int
    pending_jobs: int
    processing_jobs: int
    completed_jobs: int
    failed_jobs: int
    cancelled_jobs: int
    active_workers: int
    queue_size: int
    estimated_wait_time: Optional[float] = None


class SystemStatusResponse(BaseModel):
    """Schema for system status responses"""
    status: str
    version: str
    uptime: float
    database_connected: bool
    queue_running: bool
    active_workers: int
    total_jobs: int
    memory_usage: Optional[Dict[str, Any]] = None
    disk_usage: Optional[Dict[str, Any]] = None


class JobListResponse(BaseModel):
    """Schema for job list responses"""
    jobs: List[JobStatusResponse]
    total: int
    page: int
    per_page: int
    pages: int


class JobEventListResponse(BaseModel):
    """Schema for job event list responses"""
    events: List[JobEventResponse]
    total: int


class ErrorResponse(BaseModel):
    """Schema for error responses"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ProcessingOptions(BaseModel):
    """Schema for processing options"""
    # Audio extraction options
    audio_format: str = Field(default="wav", description="Audio format: wav, mp3, flac")
    audio_quality: str = Field(default="high", description="Audio quality: low, medium, high")
    
    # Transcription options
    language: Optional[str] = Field(default=None, description="Language code for transcription")
    model_size: str = Field(default="base", description="Whisper model size: tiny, base, small, medium, large")
    
    # Clip generation options
    clip_duration: float = Field(default=30.0, description="Clip duration in seconds")
    overlap_duration: float = Field(default=2.0, description="Overlap between clips in seconds")
    max_clips: Optional[int] = Field(default=None, description="Maximum number of clips to generate")
    
    # Analysis options
    sentiment_analysis: bool = Field(default=True, description="Enable sentiment analysis")
    topic_modeling: bool = Field(default=True, description="Enable topic modeling")
    keyword_extraction: bool = Field(default=True, description="Enable keyword extraction")
    
    # Output options
    output_format: str = Field(default="mp4", description="Output video format")
    resolution: Optional[str] = Field(default=None, description="Output resolution (e.g., 1080p)")
    fps: Optional[int] = Field(default=None, description="Output framerate")
    
    # Filter options
    min_confidence: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum confidence threshold")
    max_duration: Optional[float] = Field(default=None, description="Maximum clip duration in seconds")