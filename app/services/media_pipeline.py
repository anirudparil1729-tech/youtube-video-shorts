"""Main media processing pipeline orchestrator."""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from app.core.config import settings
from app.models.job_models import ProcessingStage
from app.services.audio_extractor import AudioExtractor
from app.services.face_detector import FaceDetector
from app.services.segment_analyzer import SegmentAnalyzer
from app.services.segment_generator import SegmentGenerator
from app.services.transcriber import WhisperTranscriber
from app.services.video_downloader import VideoDownloader
from app.services.video_encoder import VideoEncoder

logger = logging.getLogger(__name__)


class MediaProcessingPipeline:
    """Orchestrates the complete media processing pipeline."""

    def __init__(self, output_dir: str = settings.output_dir):
        """Initialize pipeline.
        
        Args:
            output_dir: Base output directory
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.downloader = VideoDownloader(str(self.output_dir))
        self.extractor = AudioExtractor()
        self.transcriber = WhisperTranscriber(
            model_name=settings.whisper_model,
            cache_dir=str(self.output_dir / ".cache"),
        )
        self.analyzer = SegmentAnalyzer()
        self.generator = SegmentGenerator()

    async def process_job(
        self,
        job_id: str,
        youtube_url: str,
        job_type: str,
        options: Dict[str, Any],
        progress_callback: Optional[Callable[[ProcessingStage, float, str], Any]] = None,
    ) -> Dict[str, Any]:
        """Process a video job end-to-end.
        
        Args:
            job_id: Job ID
            youtube_url: YouTube URL to process
            job_type: Type of job (full_processing, clip_generation, etc)
            options: Processing options
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with processing results
        """
        job_dir = self.output_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Stage 1: Validate and get metadata
            await self._progress(
                progress_callback,
                ProcessingStage.INITIALIZING,
                10.0,
                "Validating YouTube URL and fetching metadata...",
            )

            metadata = await self.downloader.validate_and_get_metadata(youtube_url)
            logger.info(f"Video metadata: {metadata['title']}")

            # Stage 2: Download video
            await self._progress(
                progress_callback,
                ProcessingStage.DOWNLOADING,
                25.0,
                f"Downloading video: {metadata['title']}",
            )

            video_path = await self.downloader.download_video(youtube_url, job_id)
            logger.info(f"Downloaded video to {video_path}")

            # Stage 3: Extract audio
            await self._progress(
                progress_callback,
                ProcessingStage.EXTRACTING_AUDIO,
                40.0,
                "Extracting audio from video...",
            )

            audio_format = options.get("audio_format", "wav")
            sample_rate = options.get("sample_rate", 16000)
            audio_dir = job_dir / "audio"
            audio_path = await self.extractor.extract_audio(
                video_path,
                str(audio_dir),
                audio_format=audio_format,
                sample_rate=sample_rate,
            )
            logger.info(f"Extracted audio to {audio_path}")

            # Stage 4: Transcribe audio
            await self._progress(
                progress_callback,
                ProcessingStage.TRANSCRIBING,
                55.0,
                "Transcribing audio with Whisper...",
            )

            language = options.get("language", "en")
            transcription = await self.transcriber.transcribe(audio_path, language=language)
            logger.info(f"Transcription complete: {len(transcription['segments'])} segments")

            # Save transcript
            transcript_path = job_dir / "transcript.json"
            with open(transcript_path, "w") as f:
                json.dump(transcription, f, indent=2)

            # Stage 5: Analyze segments
            await self._progress(
                progress_callback,
                ProcessingStage.ANALYZING,
                70.0,
                "Analyzing transcript for highlights...",
            )

            segment_scores = []
            for i, seg in enumerate(transcription["segments"]):
                score = await self.analyzer.score_segment(
                    seg["text"],
                    i,
                    len(transcription["segments"]),
                )
                segment_scores.append(score)

            logger.info(f"Computed interest scores for {len(segment_scores)} segments")

            # Stage 6: Generate candidates
            await self._progress(
                progress_callback,
                ProcessingStage.GENERATING_CLIPS,
                80.0,
                "Generating candidate clips...",
            )

            video_duration = metadata.get("duration", 0)
            candidate_segments = await self.generator.generate_segments(
                transcription["segments"],
                video_duration,
                segment_scores,
            )

            # Save candidates
            candidates_path = job_dir / "candidates.json"
            with open(candidates_path, "w") as f:
                json.dump(candidate_segments, f, indent=2)

            logger.info(f"Generated {len(candidate_segments)} candidate clips")

            # Stage 7: Render clips
            await self._progress(
                progress_callback,
                ProcessingStage.GENERATING_CLIPS,
                85.0,
                "Rendering video clips...",
            )

            clips = await self._render_clips(
                video_path,
                candidate_segments,
                metadata,
                job_dir,
            )

            logger.info(f"Rendered {len(clips)} clips")

            # Stage 8: Finalize
            await self._progress(
                progress_callback,
                ProcessingStage.FINALIZING,
                95.0,
                "Finalizing results...",
            )

            # Prepare output
            output_files = [clip["output_file"] for clip in clips]
            clips_metadata = [
                {
                    "id": clip["id"],
                    "start": clip["start"],
                    "end": clip["end"],
                    "duration": clip["duration"],
                    "title": clip["title"],
                    "description": clip["description"],
                    "interest_score": clip["interest_score"],
                    "file": clip["output_file"],
                }
                for clip in clips
            ]

            result = {
                "status": "success",
                "video_title": metadata.get("title"),
                "video_duration": video_duration,
                "uploader": metadata.get("uploader"),
                "transcript": transcription["full_text"],
                "transcript_segments": transcription["segments"],
                "clips_generated": len(clips),
                "generated_clips": clips_metadata,
                "output_files": output_files,
                "files": {
                    "source_video": video_path,
                    "extracted_audio": audio_path,
                    "transcript": str(transcript_path),
                    "candidates": str(candidates_path),
                },
            }

            # Save final results
            results_path = job_dir / "results.json"
            with open(results_path, "w") as f:
                json.dump(result, f, indent=2)

            await self._progress(
                progress_callback,
                ProcessingStage.COMPLETED,
                100.0,
                "Processing complete!",
            )

            return result

        except Exception as e:
            logger.exception(f"Pipeline failed: {e}")
            raise

    async def _render_clips(
        self,
        source_video: str,
        segments: List[Dict[str, Any]],
        metadata: Dict[str, Any],
        job_dir: Path,
    ) -> List[Dict[str, Any]]:
        """Render video clips for each segment.
        
        Args:
            source_video: Path to source video
            segments: List of segment definitions
            metadata: Video metadata
            job_dir: Job directory
            
        Returns:
            List of rendered clip metadata
        """
        clips = []
        clips_dir = job_dir / "clips"
        clips_dir.mkdir(parents=True, exist_ok=True)

        # Get video dimensions for cropping
        dimensions = await VideoEncoder.get_video_dimensions(source_video)

        # Detect faces for intelligent cropping
        detections = await FaceDetector.detect_faces_in_video(source_video, sample_rate=5)
        crop_region = await FaceDetector.get_crop_region(
            detections,
            dimensions["width"],
            dimensions["height"],
            target_aspect=9 / 16,
        )

        logger.info(f"Using crop region: {crop_region}")

        for i, segment in enumerate(segments):
            # Extract clip
            clip_path = await VideoEncoder.extract_clip(
                source_video,
                str(clips_dir),
                segment["start"],
                segment["end"],
            )

            # Crop to 9:16
            cropped_path = await VideoEncoder.crop_and_encode(
                clip_path,
                str(clips_dir / f"clip_{i}"),
                crop_region,
            )

            # Add metadata
            clip_metadata = {
                "title": segment.get("title", f"Clip {i+1}"),
                "description": segment.get("description", ""),
            }

            final_path = await VideoEncoder.add_metadata(
                cropped_path,
                str(clips_dir / f"clip_{i}_final"),
                clip_metadata,
            )

            clip_info = {
                "id": i,
                "start": segment["start"],
                "end": segment["end"],
                "duration": segment["duration"],
                "title": segment.get("title", f"Clip {i+1}"),
                "description": segment.get("description", ""),
                "interest_score": segment.get("interest_score", 0.0),
                "output_file": final_path,
                "crop_strategy": crop_region.get("strategy", "unknown"),
            }

            clips.append(clip_info)

        return clips

    @staticmethod
    async def _progress(
        callback: Optional[Callable],
        stage: ProcessingStage,
        progress: float,
        message: str,
    ) -> None:
        """Emit progress update.
        
        Args:
            callback: Optional progress callback
            stage: Processing stage
            progress: Progress percentage
            message: Status message
        """
        if callback:
            try:
                result = callback(stage, progress, message)
                if hasattr(result, "__await__"):
                    await result
            except Exception as e:
                logger.exception(f"Progress callback failed: {e}")
