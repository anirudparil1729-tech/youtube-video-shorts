"""
Application configuration management.
"""

from pathlib import Path
from typing import List, Optional

from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    app_name: str = "Video Processing API"
    debug: bool = False
    environment: str = "development"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str = "sqlite:///./video_processing.db"
    
    # Redis (for future queue implementation)
    redis_url: Optional[str] = None
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Job Queue
    max_concurrent_jobs: int = 3
    job_timeout: int = 3600  # 1 hour in seconds
    queue_poll_interval: float = 0.1  # seconds
    
    # File Storage
    upload_dir: str = "./uploads"
    output_dir: str = "./outputs"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    
    # YouTube/Video Processing
    max_video_duration: int = 7200  # 2 hours in seconds
    allowed_video_formats: List[str] = [
        "mp4", "avi", "mov", "wmv", "flv", "webm", "mkv"
    ]
    
    # AI/ML Models
    whisper_model: str = "base"  # tiny, base, small, medium, large
    enable_gpu: bool = False
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = None
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    app_password: str = "dev-password"
    
    # Rate Limiting
    requests_per_minute: int = 60
    
    @validator("database_url")
    def validate_database_url(cls, v):
        if v.startswith("sqlite") and "///" in v:
            # Ensure sqlite database directory exists
            db_path = v.replace("sqlite:///", "")
            if db_path != ":memory:":
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        return v
    
    @validator("upload_dir", "output_dir")
    def create_directories(cls, v):
        Path(v).mkdir(parents=True, exist_ok=True)
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()