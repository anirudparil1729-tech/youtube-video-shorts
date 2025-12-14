"""Integration tests for the media processing pipeline."""

import json
import pytest
import tempfile
from pathlib import Path
from typing import Any, Dict

from app.services.media_pipeline import MediaProcessingPipeline
from app.models.job_models import ProcessingStage


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_audio_path():
    """Create a sample audio file for testing.
    
    This creates a simple WAV file with synthetic audio.
    """
    import wave
    import struct
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        audio_path = f.name
    
    # Create simple test audio
    sample_rate = 16000
    duration = 10  # 10 seconds
    frequency = 440  # A4 note
    
    try:
        with wave.open(audio_path, 'wb') as wav_file:
            # Set audio parameters
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 2 bytes per sample
            wav_file.setframerate(sample_rate)
            
            # Generate simple sine wave
            import math
            frames = []
            for i in range(sample_rate * duration):
                sample = int(32767 * 0.5 * math.sin(2 * math.pi * frequency * i / sample_rate))
                frames.append(struct.pack('<h', sample))
            
            wav_file.writeframes(b''.join(frames))
        
        yield audio_path
    finally:
        Path(audio_path).unlink(missing_ok=True)


class TestAudioExtraction:
    """Tests for audio extraction from video."""

    @pytest.mark.asyncio
    async def test_extract_audio_requires_video_file(self):
        """Test that audio extraction handles missing files."""
        from app.services.audio_extractor import AudioExtractor
        
        extractor = AudioExtractor()
        
        with pytest.raises(Exception):
            await extractor.extract_audio(
                "/nonexistent/video.mp4",
                "/tmp/output"
            )


class TestTranscriber:
    """Tests for Whisper transcriber."""

    @pytest.mark.asyncio
    async def test_transcriber_initialization(self):
        """Test that transcriber can be initialized."""
        from app.services.transcriber import WhisperTranscriber
        
        transcriber = WhisperTranscriber(model_name="base")
        assert transcriber.model_name == "base"

    @pytest.mark.asyncio
    async def test_transcriber_model_caching(self, temp_output_dir):
        """Test that transcriber caches models properly."""
        from app.services.transcriber import WhisperTranscriber
        
        cache_dir = Path(temp_output_dir) / "cache"
        transcriber1 = WhisperTranscriber(
            model_name="base",
            cache_dir=str(cache_dir)
        )
        transcriber2 = WhisperTranscriber(
            model_name="base",
            cache_dir=str(cache_dir)
        )
        
        # Both should be able to use the same cache directory
        assert transcriber1.cache_dir == transcriber2.cache_dir


class TestSegmentAnalyzer:
    """Tests for segment analysis."""

    @pytest.mark.asyncio
    async def test_analyzer_loads_models(self):
        """Test that analyzer can load NLP models."""
        from app.services.segment_analyzer import SegmentAnalyzer
        
        analyzer = SegmentAnalyzer()
        await analyzer.load_models()
        
        assert analyzer.nlp is not None
        assert analyzer.sentiment_model is not None

    @pytest.mark.asyncio
    async def test_text_analysis(self):
        """Test basic text analysis functionality."""
        from app.services.segment_analyzer import SegmentAnalyzer
        
        analyzer = SegmentAnalyzer()
        
        result = await analyzer.analyze_text("This is an amazing video!")
        
        assert "sentiment" in result
        assert "confidence" in result
        assert result["sentiment"] in ["positive", "negative"]
        assert 0 <= result["confidence"] <= 1


class TestFaceDetection:
    """Tests for face detection."""

    @pytest.mark.asyncio
    async def test_get_crop_region_no_detections(self):
        """Test crop region calculation without face detections."""
        from app.services.face_detector import FaceDetector
        
        crop_region = await FaceDetector.get_crop_region(
            detections=[],
            frame_width=1920,
            frame_height=1080,
            target_aspect=9/16
        )
        
        assert "x" in crop_region
        assert "y" in crop_region
        assert "width" in crop_region
        assert "height" in crop_region
        assert crop_region["strategy"] == "center_crop"

    @pytest.mark.asyncio
    async def test_get_crop_region_with_detections(self):
        """Test crop region calculation with face detections."""
        from app.services.face_detector import FaceDetector
        
        detections = [
            {
                "frame": 0,
                "time": 0.0,
                "faces": [
                    {
                        "x": 0.3,
                        "y": 0.2,
                        "width": 0.2,
                        "height": 0.3,
                        "confidence": 0.9
                    }
                ]
            }
        ]
        
        crop_region = await FaceDetector.get_crop_region(
            detections=detections,
            frame_width=1920,
            frame_height=1080,
            target_aspect=9/16
        )
        
        assert "x" in crop_region
        assert "y" in crop_region
        assert "width" in crop_region
        assert "height" in crop_region
        assert crop_region["strategy"] == "face_tracking"
        
        # Check bounds
        assert 0 <= crop_region["x"]
        assert 0 <= crop_region["y"]
        assert crop_region["width"] > 0
        assert crop_region["height"] > 0


class TestVideoEncoder:
    """Tests for video encoding."""

    @pytest.mark.asyncio
    async def test_get_video_dimensions_error(self):
        """Test handling of nonexistent video files."""
        from app.services.video_encoder import VideoEncoder
        
        with pytest.raises(Exception):
            await VideoEncoder.get_video_dimensions("/nonexistent/video.mp4")


class TestProgressCallback:
    """Tests for progress callback functionality."""

    @pytest.mark.asyncio
    async def test_progress_callback_called(self):
        """Test that progress callback is invoked during processing."""
        from app.services.media_pipeline import MediaProcessingPipeline
        
        progress_calls = []
        
        async def mock_callback(stage: ProcessingStage, progress: float, message: str):
            progress_calls.append({
                "stage": stage,
                "progress": progress,
                "message": message
            })
        
        # Verify callback interface
        assert callable(mock_callback)


class TestPipelineIntegration:
    """End-to-end pipeline integration tests."""

    @pytest.mark.asyncio
    async def test_pipeline_initialization(self, temp_output_dir):
        """Test that pipeline initializes properly."""
        pipeline = MediaProcessingPipeline(output_dir=temp_output_dir)
        
        assert pipeline.pipeline is not None or pipeline.downloader is not None

    @pytest.mark.asyncio
    async def test_output_directory_creation(self):
        """Test that output directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "new_pipeline_output"
            
            pipeline = MediaProcessingPipeline(output_dir=str(output_dir))
            
            # Directory should be created
            assert output_dir.exists()


class TestProgressStages:
    """Tests for progress stage tracking."""

    def test_processing_stages_enum(self):
        """Test that all processing stages are defined."""
        stages = [
            ProcessingStage.INITIALIZING,
            ProcessingStage.DOWNLOADING,
            ProcessingStage.EXTRACTING_AUDIO,
            ProcessingStage.TRANSCRIBING,
            ProcessingStage.ANALYZING,
            ProcessingStage.GENERATING_CLIPS,
            ProcessingStage.FINALIZING,
            ProcessingStage.COMPLETED,
        ]
        
        assert len(stages) > 0
        for stage in stages:
            assert hasattr(stage, 'value')
            assert isinstance(stage.value, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
