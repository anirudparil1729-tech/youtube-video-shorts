#!/usr/bin/env python3
"""Example: Complete clip pipeline usage.

This example demonstrates how to use the clip pipeline to process
a YouTube video and generate short clips.

Usage:
    python example_pipeline_usage.py "https://www.youtube.com/watch?v=VIDEO_ID"
"""

import asyncio
import json
import sys
from pathlib import Path

# Assuming this is run from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.services.media_pipeline import MediaProcessingPipeline
from app.models.job_models import ProcessingStage


async def main():
    """Run the complete pipeline example."""
    
    if len(sys.argv) < 2:
        print("Usage: python example_pipeline_usage.py <youtube_url>")
        print("Example: python example_pipeline_usage.py 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'")
        sys.exit(1)
    
    youtube_url = sys.argv[1]
    job_id = "example_job_123"
    
    print(f"\n{'='*60}")
    print("Clip Pipeline Example")
    print(f"{'='*60}")
    print(f"URL: {youtube_url}")
    print(f"Job ID: {job_id}")
    print(f"Output Directory: {settings.output_dir}")
    print()
    
    # Initialize pipeline
    pipeline = MediaProcessingPipeline(output_dir=settings.output_dir)
    
    # Define progress callback
    async def progress_callback(stage: ProcessingStage, progress: float, message: str):
        """Progress callback that prints updates."""
        print(f"[{stage.value.upper():15}] {progress:5.1f}% - {message}")
    
    try:
        print("Starting pipeline...\n")
        
        # Process the job
        result = await pipeline.process_job(
            job_id=job_id,
            youtube_url=youtube_url,
            job_type="full_processing",
            options={
                "language": "en",
                "quality": "high",
                "audio_format": "wav",
                "sample_rate": 16000,
            },
            progress_callback=progress_callback,
        )
        
        print("\n" + "="*60)
        print("Processing Complete!")
        print("="*60)
        
        # Display results
        print(f"\nVideo Title: {result['video_title']}")
        print(f"Duration: {result['video_duration']:.1f}s")
        print(f"Uploader: {result['uploader']}")
        print(f"\nTranscript Preview:")
        print(f"  {result['transcript'][:200]}...")
        
        print(f"\nGenerated {result['clips_generated']} Clips:")
        print("-" * 60)
        
        for clip in result['generated_clips']:
            print(f"\nClip {clip['id'] + 1}:")
            print(f"  Title: {clip['title']}")
            print(f"  Time: {clip['start']:.1f}s → {clip['end']:.1f}s ({clip['duration']:.1f}s)")
            print(f"  Interest Score: {clip['interest_score']:.2f}")
            print(f"  Description: {clip['description']}")
            print(f"  Output: {clip['file']}")
        
        # Save results to JSON
        results_file = Path(settings.output_dir) / job_id / "example_results.json"
        with open(results_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\nFull results saved to: {results_file}")
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
