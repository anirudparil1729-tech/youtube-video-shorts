# Clip Pipeline Usage Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Download Required Models (First Time)

Models are automatically downloaded on first use, but you can pre-download them:

```bash
# Download Whisper base model (~140MB)
python -c "import whisper; whisper.load_model('base')"

# Download spaCy model (~40MB)
python -m spacy download en_core_web_sm

# Download Transformers model (happens on first use, ~268MB)
# No action needed - will download automatically
```

### 3. Start the Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### 4. Submit a Processing Job

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/" \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "job_type": "full_processing",
    "priority": 5,
    "options": {
      "language": "en",
      "quality": "high"
    }
  }'
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "job_type": "full_processing",
  "status": "queued",
  "progress": 0.0,
  "created_at": "2024-01-01T12:00:00Z"
}
```

### 5. Monitor Progress

#### Via REST API
```bash
curl "http://localhost:8000/api/v1/jobs/{job_id}"
```

#### Via WebSocket (Real-time)
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/{job_id}');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log(`Progress: ${data.data.progress}%`);
    console.log(`Status: ${data.data.status}`);
};
```

### 6. Retrieve Results

```bash
curl "http://localhost:8000/api/v1/jobs/{job_id}" | jq '.generated_clips'
```

Response:
```json
[
  {
    "id": 0,
    "start": 10.0,
    "end": 45.0,
    "duration": 35.0,
    "title": "Video Introduction",
    "description": "Introduction to the video content...",
    "interest_score": 0.85,
    "file": "outputs/{job_id}/clips/clip_0_final/with_metadata.mp4"
  },
  {
    "id": 1,
    "start": 50.0,
    "end": 85.0,
    "duration": 35.0,
    "title": "Main Content",
    "description": "Main content segment...",
    "interest_score": 0.78,
    "file": "outputs/{job_id}/clips/clip_1_final/with_metadata.mp4"
  }
]
```

## Usage Examples

### Example 1: Basic Transcription Job

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/" \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://www.youtube.com/watch?v=example",
    "job_type": "transcription",
    "options": {
      "language": "en"
    }
  }'
```

### Example 2: Clip Generation with Custom Options

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/" \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://www.youtube.com/watch?v=example",
    "job_type": "clip_generation",
    "priority": 8,
    "options": {
      "language": "en",
      "quality": "high",
      "min_clip_duration": 30,
      "max_clip_duration": 40,
      "min_clips": 5,
      "audio_format": "wav",
      "sample_rate": 16000
    }
  }'
```

### Example 3: Python API Usage

```python
import httpx
import json
import asyncio

async def process_video():
    async with httpx.AsyncClient() as client:
        # Create job
        response = await client.post(
            "http://localhost:8000/api/v1/jobs/",
            json={
                "youtube_url": "https://www.youtube.com/watch?v=example",
                "job_type": "full_processing",
                "options": {
                    "language": "en",
                    "quality": "high"
                }
            }
        )
        
        job = response.json()
        job_id = job["id"]
        
        # Poll for completion
        while True:
            response = await client.get(f"http://localhost:8000/api/v1/jobs/{job_id}")
            job = response.json()
            
            print(f"Status: {job['status']}")
            print(f"Progress: {job['progress']}%")
            
            if job["status"] in ["completed", "failed"]:
                break
            
            await asyncio.sleep(5)
        
        if job["status"] == "completed":
            print(f"Generated {len(job['generated_clips'])} clips")
            for clip in job["generated_clips"]:
                print(f"  - {clip['title']}: {clip['file']}")
        else:
            print(f"Job failed: {job['error_message']}")

asyncio.run(process_video())
```

### Example 4: WebSocket Real-time Monitoring

```python
import asyncio
import json
import websockets

async def monitor_job(job_id):
    uri = f"ws://localhost:8000/ws/{job_id}"
    
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            
            if data["type"] == "initial_status":
                print(f"Initial status: {data['data']['status']}")
            
            elif data["type"] == "job_update":
                print(f"Progress: {data['data']['progress']}%")
                print(f"Status: {data['data']['status']}")
            
            elif data["type"] == "job_completed":
                print("Job completed!")
                results = data['data']['results']
                print(f"Generated {results['clips_generated']} clips")
                break

# Usage
asyncio.run(monitor_job("your-job-id"))
```

## Pipeline Configuration

### Whisper Model Selection

Choose the appropriate model size based on your hardware:

```bash
# Fastest (lowest quality)
WHISPER_MODEL=tiny

# Balanced (recommended)
WHISPER_MODEL=base

# High quality (slower)
WHISPER_MODEL=small
```

### Queue Configuration

```bash
# Maximum concurrent jobs
MAX_CONCURRENT_JOBS=3

# Job timeout (seconds)
JOB_TIMEOUT=3600

# Queue poll interval
QUEUE_POLL_INTERVAL=0.1
```

### Storage Configuration

```bash
# Output directory
OUTPUT_DIR=./outputs

# Upload directory
UPLOAD_DIR=./uploads
```

## File Structure

After processing, the output structure will be:

```
outputs/{job_id}/
├── source/
│   └── {video_id}.mp4              # Original downloaded video
├── audio/
│   └── audio.wav                   # Extracted audio (16kHz mono)
├── clips/
│   ├── clip_0.mp4                  # Raw clip segment
│   ├── clip_0/
│   │   └── cropped.mp4             # Cropped to 9:16
│   │   └── with_metadata.mp4       # Final output with metadata
│   ├── clip_1/
│   │   └── with_metadata.mp4
│   └── ...
├── transcript.json                 # Full transcript with segments
├── candidates.json                 # Analyzed candidate segments
└── results.json                    # Final results and metadata
```

## Accessing Generated Clips

### Download Clips

```bash
# Get job results
curl "http://localhost:8000/api/v1/jobs/{job_id}" -o job.json

# Extract clip paths
jq '.generated_clips[].file' job.json

# Download a clip
curl "file://{absolute_path}/outputs/{job_id}/clips/clip_0_final/with_metadata.mp4" -o clip.mp4
```

### Stream Clips

```python
from fastapi.responses import FileResponse

@app.get("/clips/{job_id}/{clip_id}")
async def get_clip(job_id: str, clip_id: int):
    clip_path = f"outputs/{job_id}/clips/clip_{clip_id}_final/with_metadata.mp4"
    return FileResponse(clip_path, media_type="video/mp4")
```

## Testing

### Run Tests

```bash
# All tests
pytest

# Specific test file
pytest app/tests/test_segment_generation.py -v

# With coverage
pytest --cov=app --cov-report=html
```

### Test with Sample Data

The test suite includes fixtures for sample audio and transcripts:

```python
from app.tests.test_segment_generation import sample_transcript_segments

# Use in your tests
segments = sample_transcript_segments()
```

## Troubleshooting

### Job Status: FAILED

Check the `error_message` field:

```bash
curl "http://localhost:8000/api/v1/jobs/{job_id}" | jq '.error_message'
```

### Common Errors

**"ffmpeg: command not found"**
```bash
# Install FFmpeg
sudo apt-get install ffmpeg  # Linux
brew install ffmpeg          # macOS
```

**"Module not found: whisper"**
```bash
pip install openai-whisper
```

**"Timeout after 3600 seconds"**
- Increase `JOB_TIMEOUT` for long videos
- Use smaller Whisper model
- Reduce `MAX_CONCURRENT_JOBS`

### Debug Mode

Enable debug logging:

```bash
DEBUG=true LOG_LEVEL=DEBUG python main.py
```

## Performance Tips

### For Large Videos (>30 minutes)

1. Use `WHISPER_MODEL=tiny` for speed
2. Set `MAX_CONCURRENT_JOBS=1` to reduce memory
3. Increase `JOB_TIMEOUT=7200` for 2+ hour videos

### For Better Quality

1. Use `WHISPER_MODEL=small` or `base`
2. Set `quality=high` in processing options
3. Enable GPU with `ENABLE_GPU=true`

### For Production

1. Use database-backed queue (Redis/PostgreSQL)
2. Run workers separately
3. Use CDN for clip delivery
4. Implement clip caching
5. Monitor resource usage

## API Reference

### Create Job

```
POST /api/v1/jobs/
Content-Type: application/json

{
  "youtube_url": "string (required)",
  "job_type": "full_processing|clip_generation|transcription|audio_extraction|analysis",
  "priority": 0-10 (default: 0),
  "options": {
    "language": "en",
    "quality": "fast|medium|high",
    "audio_format": "wav|mp3",
    "sample_rate": 16000
  }
}
```

### Get Job

```
GET /api/v1/jobs/{job_id}

Returns: Job object with all details and results
```

### List Jobs

```
GET /api/v1/jobs/?status_filter=pending|queued|processing|completed|failed&limit=10&offset=0
```

### Cancel Job

```
POST /api/v1/jobs/{job_id}/cancel
Content-Type: application/json

{
  "reason": "optional"
}
```

### WebSocket

```
WS /ws/{job_id}

Events:
- initial_status: Initial job status
- job_update: Progress update
- job_completed: Job finished successfully
```

## Examples Repository

Check the `docs/examples/` directory for complete working examples:

- `python_client.py` - Full pipeline usage example
- `webhook_integration.py` - Webhook handling
- `batch_processing.py` - Process multiple videos
