"""Speech-to-text transcription using OpenAI Whisper with model caching."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """Handles speech-to-text transcription using Whisper with caching."""

    def __init__(self, model_name: str = "base", cache_dir: Optional[str] = None):
        """Initialize transcriber.
        
        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
            cache_dir: Directory to cache models
        """
        self.model_name = model_name
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".cache" / "whisper"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.model = None

    async def load_model(self) -> Any:
        """Load Whisper model with caching.
        
        Returns:
            Loaded Whisper model
        """
        import whisper

        if self.model is not None:
            return self.model

        # Set cache directory for Whisper
        import os

        os.environ["WHISPER_CACHE"] = str(self.cache_dir)

        logger.info(f"Loading Whisper model: {self.model_name}")
        self.model = whisper.load_model(self.model_name)
        logger.info(f"Whisper model loaded: {self.model_name}")

        return self.model

    async def transcribe(
        self,
        audio_path: str,
        language: str = "en",
    ) -> Dict[str, Any]:
        """Transcribe audio file.
        
        Args:
            audio_path: Path to audio file
            language: Language code
            
        Returns:
            Dictionary with transcript and segments
        """
        model = await self.load_model()

        logger.info(f"Transcribing audio: {audio_path}")

        result = model.transcribe(
            audio_path,
            language=language,
            verbose=False,
        )

        # Format segments with timing information
        segments = []
        for seg in result.get("segments", []):
            segments.append({
                "id": seg.get("id"),
                "start": seg.get("start"),
                "end": seg.get("end"),
                "text": seg.get("text", "").strip(),
                "confidence": seg.get("confidence", 1.0),
            })

        transcription = {
            "full_text": result.get("text", ""),
            "language": result.get("language"),
            "segments": segments,
        }

        logger.info(f"Transcription complete: {len(segments)} segments")

        return transcription
