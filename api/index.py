"""Vercel/Netlify serverless function adapter for FastAPI backend.

This module serves as a lightweight adapter that initializes the FastAPI app
for serverless environments, handling large binary dependencies (FFmpeg, Whisper)
via on-demand downloads.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Any, Dict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for binary paths
FFMPEG_PATH = None
WHISPER_MODEL_PATH = None

def ensure_binaries() -> None:
    """Download and setup required binaries on-demand."""
    global FFMPEG_PATH, WHISPER_MODEL_PATH
    
    # Create temp directory for binaries
    temp_dir = Path(tempfile.gettempdir()) / "video_processing"
    temp_dir.mkdir(exist_ok=True)
    
    # Setup FFmpeg
    if not FFMPEG_PATH:
        FFMPEG_PATH = setup_ffmpeg(temp_dir)
        logger.info(f"FFmpeg available at: {FFMPEG_PATH}")
    
    # Setup Whisper models (use smaller model for serverless)
    if not WHISPER_MODEL_PATH:
        WHISPER_MODEL_PATH = temp_dir / "whisper_models"
        WHISPER_MODEL_PATH.mkdir(exist_ok=True)
        logger.info(f"Whisper models directory: {WHISPER_MODEL_PATH}")

def setup_ffmpeg(temp_dir: Path) -> str:
    """Download and setup FFmpeg binary."""
    ffmpeg_dir = temp_dir / "ffmpeg"
    ffmpeg_dir.mkdir(exist_ok=True)
    
    ffmpeg_path = ffmpeg_dir / "ffmpeg"
    
    # Check if FFmpeg already exists
    if ffmpeg_path.exists():
        return str(ffmpeg_path)
    
    # Download FFmpeg binary
    if sys.platform.startswith('linux'):
        # Linux x64
        url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
        archive_path = ffmpeg_dir / "ffmpeg.tar.xz"
        
        logger.info("Downloading FFmpeg...")
        urllib.request.urlretrieve(url, archive_path)
        
        # Extract
        subprocess.run([
            "tar", "-xf", str(archive_path), "-C", str(ffmpeg_dir)
        ], check=True)
        
        # Find and move binary
        extracted_dir = next(ffmpeg_dir.glob("ffmpeg-*"))
        bin_dir = extracted_dir / "bin"
        binary = bin_dir / "ffmpeg"
        binary.rename(ffmpeg_path)
        
        # Cleanup
        archive_path.unlink()
        extracted_dir.rmdir()
        ffmpeg_dir.rmdir()
        
    else:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")
    
    # Make executable
    ffmpeg_path.chmod(0o755)
    return str(ffmpeg_path)

def setup_environment() -> None:
    """Setup environment variables for serverless execution."""
    # Add temp directory to PATH
    temp_dir = Path(tempfile.gettempdir()) / "video_processing"
    temp_dir.mkdir(exist_ok=True)
    
    os.environ["PATH"] = f"{temp_dir}/bin:{temp_dir}/ffmpeg:{os.environ.get('PATH', '')}"
    os.environ["TMPDIR"] = str(temp_dir)
    os.environ["HOME"] = str(temp_dir)
    os.environ["PYTHONPATH"] = "/opt/python" if Path("/opt/python").exists() else ""

def create_serverless_app():
    """Create and configure FastAPI app for serverless execution."""
    setup_environment()
    ensure_binaries()
    
    # Import main app
    from main import app
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from sqlmodel import Session

    from app.db.database import engine, init_db
    from app.services.tasks import seed_default_categories

    init_db()
    with Session(engine) as session:
        seed_default_categories(session)
    
    # Create serverless-specific app
    serverless_app = FastAPI(
        title="Video Processing API (Serverless)",
        description="Serverless version of the Video Processing API",
        version="1.0.0-serverless",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add CORS middleware
    serverless_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Copy routes from main app
    for route in app.routes:
        serverless_app.routes.append(route)
    
    # Add serverless-specific routes
    @serverless_app.get("/health/serverless")
    async def serverless_health():
        return {
            "status": "healthy",
            "platform": "serverless",
            "binaries_ready": bool(FFMPEG_PATH),
            "ffmpeg_path": FFMPEG_PATH,
            "temp_dir": str(Path(tempfile.gettempdir()) / "video_processing")
        }
    
    @serverless_app.get("/binaries/status")
    async def binaries_status():
        """Check status of binary dependencies."""
        temp_dir = Path(tempfile.gettempdir()) / "video_processing"
        ffmpeg_ready = bool(FFMPEG_PATH)
        
        return {
            "ffmpeg": {
                "available": ffmpeg_ready,
                "path": FFMPEG_PATH,
                "version": None if not ffmpeg_ready else get_binary_version("ffmpeg")
            },
            "whisper": {
                "available": WHISPER_MODEL_PATH.exists() if WHISPER_MODEL_PATH else False,
                "path": str(WHISPER_MODEL_PATH),
                "models_dir": str(WHISPER_MODEL_PATH)
            },
            "temp_dir": str(temp_dir),
            "disk_usage": get_directory_size(temp_dir)
        }
    
    return serverless_app

def get_binary_version(binary_name: str) -> str:
    """Get version of installed binary."""
    try:
        result = subprocess.run(
            [binary_name, "-version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.split('\n')[0]
    except Exception as e:
        logger.warning(f"Could not get version for {binary_name}: {e}")
    return None

def get_directory_size(path: Path) -> Dict[str, Any]:
    """Get size information for directory."""
    if not path.exists():
        return {"total": 0, "available": "unknown"}
    
    total_size = 0
    try:
        for file_path in path.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
    except Exception as e:
        logger.warning(f"Could not calculate directory size: {e}")
    
    return {
        "total": total_size,
        "total_mb": round(total_size / (1024 * 1024), 2)
    }

# Create the serverless app
app = create_serverless_app()

# Export for serverless platforms
handler = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))