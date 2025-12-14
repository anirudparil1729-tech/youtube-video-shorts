#!/usr/bin/env python3
"""Quick integration test to verify pipeline structure.

This test verifies that all pipeline components can be imported
and initialized correctly.
"""

import sys
import asyncio
from pathlib import Path


async def test_imports():
    """Test that all pipeline modules can be imported."""
    try:
        print("Testing imports...")
        
        from app.services.video_downloader import VideoDownloader
        print("✓ VideoDownloader imported")
        
        from app.services.audio_extractor import AudioExtractor
        print("✓ AudioExtractor imported")
        
        from app.services.transcriber import WhisperTranscriber
        print("✓ WhisperTranscriber imported")
        
        from app.services.segment_analyzer import SegmentAnalyzer
        print("✓ SegmentAnalyzer imported")
        
        from app.services.segment_generator import SegmentGenerator
        print("✓ SegmentGenerator imported")
        
        from app.services.face_detector import FaceDetector
        print("✓ FaceDetector imported")
        
        from app.services.video_encoder import VideoEncoder
        print("✓ VideoEncoder imported")
        
        from app.services.media_pipeline import MediaProcessingPipeline
        print("✓ MediaProcessingPipeline imported")
        
        from app.models.job_models import ProcessingStage
        print("✓ ProcessingStage imported")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


async def test_initialization():
    """Test that pipeline components can be initialized."""
    try:
        print("\nTesting initialization...")
        
        from app.services.media_pipeline import MediaProcessingPipeline
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = MediaProcessingPipeline(output_dir=tmpdir)
            print("✓ MediaProcessingPipeline initialized")
            
            assert pipeline.downloader is not None
            print("✓ VideoDownloader initialized")
            
            assert pipeline.extractor is not None
            print("✓ AudioExtractor initialized")
            
            assert pipeline.transcriber is not None
            print("✓ WhisperTranscriber initialized")
            
            assert pipeline.analyzer is not None
            print("✓ SegmentAnalyzer initialized")
            
            assert pipeline.generator is not None
            print("✓ SegmentGenerator initialized")
        
        return True
    except Exception as e:
        print(f"✗ Initialization failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


async def test_progress_stages():
    """Test that all progress stages are defined."""
    try:
        print("\nTesting progress stages...")
        
        from app.models.job_models import ProcessingStage
        
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
        
        for stage in stages:
            assert hasattr(stage, 'value')
            assert isinstance(stage.value, str)
            print(f"✓ {stage.name}: {stage.value}")
        
        return True
    except Exception as e:
        print(f"✗ Progress stages test failed: {e}", file=sys.stderr)
        return False


async def test_queue_integration():
    """Test that queue integrates with pipeline."""
    try:
        print("\nTesting queue integration...")
        
        from app.services.queue import job_queue
        from app.services.media_pipeline import MediaProcessingPipeline
        import tempfile
        
        # Queue should be able to initialize pipeline
        assert hasattr(job_queue, 'pipeline')
        print("✓ Queue has pipeline attribute")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = MediaProcessingPipeline(output_dir=tmpdir)
            assert pipeline is not None
            print("✓ Pipeline can be created")
        
        return True
    except Exception as e:
        print(f"✗ Queue integration test failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


async def test_configuration():
    """Test configuration is properly set."""
    try:
        print("\nTesting configuration...")
        
        from app.core.config import settings
        
        assert hasattr(settings, 'output_dir')
        print(f"✓ output_dir: {settings.output_dir}")
        
        assert hasattr(settings, 'whisper_model')
        print(f"✓ whisper_model: {settings.whisper_model}")
        
        assert hasattr(settings, 'max_concurrent_jobs')
        print(f"✓ max_concurrent_jobs: {settings.max_concurrent_jobs}")
        
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}", file=sys.stderr)
        return False


async def main():
    """Run all tests."""
    print("="*60)
    print("Clip Pipeline Integration Test")
    print("="*60)
    
    results = []
    
    results.append(("Imports", await test_imports()))
    results.append(("Initialization", await test_initialization()))
    results.append(("Progress Stages", await test_progress_stages()))
    results.append(("Queue Integration", await test_queue_integration()))
    results.append(("Configuration", await test_configuration()))
    
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name:30} {status}")
    
    all_passed = all(result for _, result in results)
    
    print("="*60)
    if all_passed:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
