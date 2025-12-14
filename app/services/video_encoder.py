"""Video encoding and cropping using FFmpeg."""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class VideoEncoder:
    """Encodes and crops video using FFmpeg."""

    @staticmethod
    async def extract_clip(
        source_video: str,
        output_path: str,
        start_time: float,
        end_time: float,
        quality: str = "high",
    ) -> str:
        """Extract a clip from video.
        
        Args:
            source_video: Source video path
            output_path: Output directory
            start_time: Start time in seconds
            end_time: End time in seconds
            quality: Quality preset (fast, high, medium)
            
        Returns:
            Path to output clip
        """
        Path(output_path).mkdir(parents=True, exist_ok=True)

        clip_name = f"clip_{int(start_time)}_to_{int(end_time)}.mp4"
        output_file = Path(output_path) / clip_name

        preset = "ultrafast" if quality == "fast" else "medium" if quality == "high" else "fast"

        cmd = [
            "ffmpeg",
            "-ss",
            str(start_time),
            "-i",
            source_video,
            "-t",
            str(end_time - start_time),
            "-c:v",
            "libx264",
            "-preset",
            preset,
            "-crf",
            "28",  # Quality (lower = better, 28 is default)
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-y",
            str(output_file),
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Extracted clip to {output_file}")
            return str(output_file)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to extract clip: {e.stderr.decode()}")
            raise

    @staticmethod
    async def crop_and_encode(
        source_video: str,
        output_path: str,
        crop_region: Dict[str, int],
        quality: str = "high",
    ) -> str:
        """Crop video to specific region and encode.
        
        Args:
            source_video: Source video path
            output_path: Output directory
            crop_region: Dict with x, y, width, height
            quality: Quality preset
            
        Returns:
            Path to output video
        """
        Path(output_path).mkdir(parents=True, exist_ok=True)

        output_file = Path(output_path) / "cropped.mp4"

        x = crop_region["x"]
        y = crop_region["y"]
        w = crop_region["width"]
        h = crop_region["height"]

        # Ensure dimensions are even (required for h264)
        w = w - (w % 2)
        h = h - (h % 2)

        filter_str = f"crop={w}:{h}:{x}:{y}"

        preset = "ultrafast" if quality == "fast" else "medium" if quality == "high" else "fast"

        cmd = [
            "ffmpeg",
            "-i",
            source_video,
            "-vf",
            filter_str,
            "-c:v",
            "libx264",
            "-preset",
            preset,
            "-crf",
            "28",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-y",
            str(output_file),
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Cropped and encoded to {output_file}")
            return str(output_file)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to crop video: {e.stderr.decode()}")
            raise

    @staticmethod
    async def add_metadata(
        video_path: str,
        output_path: str,
        metadata: Dict[str, str],
    ) -> str:
        """Add metadata to video file.
        
        Args:
            video_path: Source video path
            output_path: Output directory
            metadata: Metadata dict (title, description, etc)
            
        Returns:
            Path to output video
        """
        Path(output_path).mkdir(parents=True, exist_ok=True)

        output_file = Path(output_path) / "with_metadata.mp4"

        # Build ffmpeg metadata args
        metadata_args = []
        if "title" in metadata:
            metadata_args.extend(["-metadata", f"title={metadata['title']}"])
        if "description" in metadata:
            metadata_args.extend(["-metadata", f"comment={metadata['description']}"])

        cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-c",
            "copy",
            *metadata_args,
            "-y",
            str(output_file),
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Added metadata to {output_file}")
            return str(output_file)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to add metadata: {e.stderr.decode()}")
            raise

    @staticmethod
    async def get_video_dimensions(video_path: str) -> Dict[str, int]:
        """Get video dimensions.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dict with width and height
        """
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-select_streams",
                    "v:0",
                    "-show_entries",
                    "stream=width,height",
                    "-of",
                    "json",
                    video_path,
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(result.stdout)
            stream = data["streams"][0]
            return {
                "width": stream["width"],
                "height": stream["height"],
            }
        except Exception as e:
            logger.error(f"Failed to get video dimensions: {e}")
            raise
