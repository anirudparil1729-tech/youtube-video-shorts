"""YouTube video download and metadata extraction using yt-dlp."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class VideoDownloader:
    """Handles video downloads and metadata extraction from YouTube."""

    def __init__(self, output_dir: str):
        """Initialize the downloader.
        
        Args:
            output_dir: Directory to store downloaded files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def validate_and_get_metadata(self, url: str) -> Dict[str, Any]:
        """Validate YouTube URL and extract metadata.
        
        Args:
            url: YouTube URL to validate
            
        Returns:
            Dictionary with video metadata
            
        Raises:
            ValueError: If URL is invalid or inaccessible
        """
        import yt_dlp

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            logger.error(f"Failed to extract metadata from {url}: {e}")
            raise ValueError(f"Invalid or inaccessible YouTube URL: {e}")

        metadata = {
            "video_id": info.get("id"),
            "title": info.get("title"),
            "duration": info.get("duration"),  # in seconds
            "uploader": info.get("uploader"),
            "description": info.get("description"),
            "view_count": info.get("view_count"),
            "upload_date": info.get("upload_date"),
            "thumbnail": info.get("thumbnail"),
            "formats": info.get("formats", []),
        }

        if metadata["duration"] and metadata["duration"] > 7200:  # 2 hours
            raise ValueError(f"Video duration {metadata['duration']}s exceeds 2-hour limit")

        return metadata

    async def download_video(self, url: str, job_id: str) -> str:
        """Download video from YouTube.
        
        Args:
            url: YouTube URL
            job_id: Job ID for naming
            
        Returns:
            Path to downloaded video file
        """
        import yt_dlp

        job_dir = self.output_dir / job_id / "source"
        job_dir.mkdir(parents=True, exist_ok=True)

        ydl_opts = {
            "format": "best[ext=mp4]/best",
            "outtmpl": str(job_dir / "%(id)s.%(ext)s"),
            "quiet": False,
            "no_warnings": True,
            "progress_hooks": [],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_file = Path(ydl.prepare_filename(info))
                logger.info(f"Downloaded video to {video_file}")
                return str(video_file)
        except Exception as e:
            logger.error(f"Failed to download video from {url}: {e}")
            raise

    async def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get video information using ffprobe.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video info
        """
        import subprocess

        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_format",
                    "-show_streams",
                    "-of",
                    "json",
                    video_path,
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return json.loads(result.stdout)
        except Exception as e:
            logger.error(f"Failed to get video info for {video_path}: {e}")
            raise
