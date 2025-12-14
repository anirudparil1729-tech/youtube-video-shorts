"""Audio extraction from video files using FFmpeg."""

import logging
import subprocess
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class AudioExtractor:
    """Extracts audio from video files using FFmpeg."""

    @staticmethod
    async def extract_audio(
        video_path: str,
        output_path: str,
        audio_format: str = "wav",
        sample_rate: int = 16000,
    ) -> str:
        """Extract audio from video file.
        
        Args:
            video_path: Path to video file
            output_path: Directory to save audio
            audio_format: Output format (wav, mp3, flac)
            sample_rate: Sample rate in Hz
            
        Returns:
            Path to extracted audio file
        """
        Path(output_path).mkdir(parents=True, exist_ok=True)

        audio_file = Path(output_path) / f"audio.{audio_format}"

        cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-acodec",
            "pcm_s16le" if audio_format == "wav" else "libmp3lame",
            "-ar",
            str(sample_rate),
            "-ac",
            "1",
            "-y",
            str(audio_file),
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Extracted audio to {audio_file}")
            return str(audio_file)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to extract audio: {e.stderr.decode()}")
            raise

    @staticmethod
    async def get_audio_duration(audio_path: str) -> float:
        """Get duration of audio file.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Duration in seconds
        """
        import json

        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_format",
                    "-of",
                    "json",
                    audio_path,
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(result.stdout)
            duration = float(data.get("format", {}).get("duration", 0))
            return duration
        except Exception as e:
            logger.error(f"Failed to get audio duration: {e}")
            raise
