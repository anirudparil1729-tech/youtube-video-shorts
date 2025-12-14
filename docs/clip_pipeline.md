# Clip Pipeline Documentation

## Overview

The clip pipeline is a comprehensive media processing system that converts YouTube videos into short, engaging clips (30-40 seconds) optimized for social media platforms. It uses a combination of open-source tools and local AI models to analyze content and automatically identify the most interesting segments.

## Architecture

### Pipeline Stages

1. **URL Validation & Metadata Extraction** (yt-dlp)
2. **Video Download** (yt-dlp)
3. **Audio Extraction** (FFmpeg)
4. **Transcription** (Whisper base model)
5. **Segment Analysis** (spaCy + Transformers)
6. **Segment Generation** (candidate clip selection)
7. **Face Detection** (MediaPipe/OpenCV)
8. **Video Encoding & Cropping** (FFmpeg)
9. **Metadata Attachment**

### Component Architecture

```
Input (YouTube URL)
    ↓
VideoDownloader (yt-dlp)
    ↓ [metadata, video file]
AudioExtractor (FFmpeg)
    ↓ [audio file]
WhisperTranscriber
    ↓ [transcript, segments]
SegmentAnalyzer (spaCy + Transformers)
    ↓ [interest scores]
SegmentGenerator
    ↓ [5+ candidate segments]
FaceDetector (MediaPipe)
    ↓ [crop region]
VideoEncoder (FFmpeg)
    ↓ [MP4 clips]
Output (Clips with metadata)
```

## Module Details

### VideoDownloader

Handles YouTube URL validation and video download.

**Key methods:**
- `validate_and_get_metadata(url)`: Validates URL and extracts metadata
- `download_video(url, job_id)`: Downloads video file
- `get_video_info(video_path)`: Gets FFprobe information

**Output:**
- Video file (MP4)
- Metadata (title, duration, uploader, thumbnail, etc.)

### AudioExtractor

Extracts audio from video files using FFmpeg.

**Key methods:**
- `extract_audio(video_path, output_path, audio_format, sample_rate)`: Extracts audio
- `get_audio_duration(audio_path)`: Gets audio duration

**Output:**
- Audio file (WAV, 16kHz mono by default)

### WhisperTranscriber

Performs speech-to-text transcription with model caching.

**Key features:**
- Model caching in `~/.cache/whisper/`
- Supports multiple model sizes (tiny, base, small, medium, large)
- Returns segments with timing information

**Key methods:**
- `load_model()`: Loads Whisper model (cached)
- `transcribe(audio_path, language)`: Transcribes audio

**Output:**
```json
{
  "full_text": "Complete transcript...",
  "language": "en",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 5.0,
      "text": "Hello world",
      "confidence": 0.95
    }
  ]
}
```

### SegmentAnalyzer

Analyzes transcript segments for interest/engagement using NLP.

**Key features:**
- Sentiment analysis (Transformers: distilbert-base-uncased-finetuned-sst-2-english)
- Entity recognition (spaCy)
- Question/exclamation detection
- Text length analysis

**Scoring factors:**
- Sentiment: +0.3 for positive, -0.1 for negative
- Questions: +0.2 boost
- Exclamations: +0.15 boost
- Entity presence: +0.05 per entity (max 0.2)
- Text length: +0.1 for 20-100 tokens
- Position: +0.1 for early segments (first 30%)

**Key methods:**
- `analyze_text(text)`: Analyzes text for sentiment and entities
- `score_segment(text, segment_index, total_segments)`: Scores segment 0-1

**Output:**
```json
{
  "sentiment": "positive|negative",
  "confidence": 0.95,
  "entities": [
    {"text": "Python", "label": "ORG"}
  ],
  "is_question": false,
  "has_exclamation": true,
  "text_length": 45
}
```

### SegmentGenerator

Generates candidate clips from transcript with interest ranking.

**Key features:**
- Sliding window approach (30-40s duration)
- Interest score averaging
- Automatic title/description generation
- Minimum 5 clips per video

**Key methods:**
- `generate_segments(segments, video_duration, segment_scores)`: Generates candidates

**Output:**
```json
[
  {
    "id": 0,
    "start": 10.0,
    "end": 45.0,
    "duration": 35.0,
    "title": "What is Python?",
    "description": "Python is a high-level programming...",
    "text": "Full segment text",
    "interest_score": 0.78
  }
]
```

### FaceDetector

Detects faces and calculates optimal crop region for 9:16 aspect ratio.

**Key features:**
- MediaPipe face detection
- Intelligent center-of-face tracking
- Falls back to center crop if no faces detected
- Respects frame boundaries

**Key methods:**
- `detect_faces_in_video(video_path, sample_rate)`: Detects faces frame-by-frame
- `get_crop_region(detections, frame_width, frame_height, target_aspect)`: Calculates crop region

**Output:**
```json
{
  "x": 640,
  "y": 120,
  "width": 320,
  "height": 570,
  "strategy": "face_tracking|center_crop"
}
```

### VideoEncoder

Encodes and crops video using FFmpeg.

**Key features:**
- Efficient clip extraction
- Aspect ratio cropping (maintains even dimensions)
- Metadata embedding
- Quality presets (fast, medium, high)

**Key methods:**
- `extract_clip(source_video, output_path, start_time, end_time, quality)`: Extracts clip
- `crop_and_encode(source_video, output_path, crop_region, quality)`: Crops video
- `add_metadata(video_path, output_path, metadata)`: Adds metadata
- `get_video_dimensions(video_path)`: Gets video dimensions

**Output:**
- MP4 file with metadata (title, description)

### MediaProcessingPipeline

Orchestrates the entire pipeline end-to-end.

**Key methods:**
- `process_job(job_id, youtube_url, job_type, options, progress_callback)`: Runs complete pipeline

**Progress stages:**
1. INITIALIZING (10%)
2. DOWNLOADING (25%)
3. EXTRACTING_AUDIO (40%)
4. TRANSCRIBING (55%)
5. ANALYZING (70%)
6. GENERATING_CLIPS (80%)
7. FINALIZING (95%)
8. COMPLETED (100%)

## Configuration

### Environment Variables

```bash
# Model configuration
WHISPER_MODEL=base  # Options: tiny, base, small, medium, large
ENABLE_GPU=false

# Storage
OUTPUT_DIR=./outputs
UPLOAD_DIR=./uploads

# Processing
MAX_VIDEO_DURATION=7200  # 2 hours in seconds
MAX_CONCURRENT_JOBS=3
```

### Processing Options

When creating a job, you can specify processing options:

```json
{
  "youtube_url": "https://www.youtube.com/watch?v=...",
  "job_type": "full_processing",
  "options": {
    "audio_format": "wav",
    "sample_rate": 16000,
    "language": "en",
    "quality": "high"
  }
}
```

## Model Requirements

### Memory and Storage

| Model | Size | Memory | Time (16s audio) |
|-------|------|--------|------------------|
| tiny | 39M | ~1GB | ~1s |
| base | 140M | ~1GB | ~2s |
| small | 244M | ~2GB | ~5s |
| medium | 769M | ~3GB | ~10s |
| large | 1550M | ~5GB | ~20s |

**Note:** First run downloads model to `~/.cache/whisper/`. Subsequent runs use cached version.

### Transformers Models

- `distilbert-base-uncased-finetuned-sst-2-english` (~268MB) - Sentiment analysis
- Downloaded to `~/.cache/huggingface/` on first use

### spaCy Models

- `en_core_web_sm` (~40MB) - English NLP
- Automatically downloaded if not present

## Pipeline Flow

### Step 1: URL Validation
```python
# Validates YouTube URL and extracts metadata
metadata = await downloader.validate_and_get_metadata(url)
# Returns: {title, duration, uploader, view_count, thumbnail, ...}
```

### Step 2: Download Video
```python
# Downloads video from YouTube
video_path = await downloader.download_video(url, job_id)
# Returns: path/to/video.mp4
```

### Step 3: Extract Audio
```python
# Extracts mono audio at 16kHz
audio_path = await extractor.extract_audio(
    video_path, 
    output_dir,
    audio_format="wav",
    sample_rate=16000
)
# Returns: path/to/audio.wav
```

### Step 4: Transcribe
```python
# Transcribes audio with timing info
transcription = await transcriber.transcribe(
    audio_path,
    language="en"
)
# Returns: {full_text, segments: [{start, end, text, confidence}]}
```

### Step 5: Analyze Segments
```python
# Scores each segment for interest
scores = []
for i, seg in enumerate(transcription['segments']):
    score = await analyzer.score_segment(
        seg['text'],
        segment_index=i,
        total_segments=len(transcription['segments'])
    )
    scores.append(score)
```

### Step 6: Generate Candidates
```python
# Generates 5+ candidate clips
candidates = await generator.generate_segments(
    transcription['segments'],
    video_duration=metadata['duration'],
    segment_scores=scores
)
# Returns: [{start, end, duration, title, description, interest_score}]
```

### Step 7: Detect Faces
```python
# Detects faces for intelligent cropping
detections = await face_detector.detect_faces_in_video(
    video_path,
    sample_rate=5  # Every 5th frame
)
crop_region = await face_detector.get_crop_region(
    detections,
    frame_width,
    frame_height,
    target_aspect=9/16
)
```

### Step 8: Render Clips
```python
# Creates 9:16 cropped MP4 clips
for candidate in candidates:
    # Extract clip
    clip_path = await encoder.extract_clip(
        video_path,
        start_time=candidate['start'],
        end_time=candidate['end']
    )
    
    # Crop to 9:16
    cropped_path = await encoder.crop_and_encode(
        clip_path,
        crop_region=crop_region
    )
    
    # Add metadata
    final_path = await encoder.add_metadata(
        cropped_path,
        metadata={
            'title': candidate['title'],
            'description': candidate['description']
        }
    )
```

## Output Structure

```
outputs/
├── {job_id}/
│   ├── source/
│   │   └── {video_id}.mp4
│   ├── audio/
│   │   └── audio.wav
│   ├── clips/
│   │   ├── clip_0/
│   │   │   └── cropped.mp4
│   │   │       └── with_metadata.mp4
│   │   └── clip_1/
│   │       └── ...
│   ├── transcript.json
│   ├── candidates.json
│   └── results.json
```

### results.json Structure

```json
{
  "status": "success",
  "video_title": "Tutorial Video",
  "video_duration": 300.0,
  "uploader": "John Doe",
  "transcript": "Full transcript text...",
  "transcript_segments": [...],
  "clips_generated": 5,
  "generated_clips": [
    {
      "id": 0,
      "start": 10.0,
      "end": 45.0,
      "duration": 35.0,
      "title": "Intro",
      "description": "Introduction to...",
      "interest_score": 0.78,
      "file": "path/to/clip_0_final/with_metadata.mp4"
    }
  ],
  "output_files": ["path/to/clip_0...", "path/to/clip_1...", ...],
  "files": {
    "source_video": "path/to/source",
    "extracted_audio": "path/to/audio",
    "transcript": "path/to/transcript.json",
    "candidates": "path/to/candidates.json"
  }
}
```

## Progress Tracking

The pipeline emits progress updates via callback:

```python
async def progress_callback(stage: ProcessingStage, progress: float, message: str):
    # stage: INITIALIZING, DOWNLOADING, EXTRACTING_AUDIO, etc.
    # progress: 0.0-100.0
    # message: Human-readable status message
    pass

await pipeline.process_job(
    job_id=job_id,
    youtube_url=url,
    job_type="full_processing",
    options={},
    progress_callback=progress_callback
)
```

These are automatically persisted to the database and streamed to WebSocket clients.

## Error Handling

The pipeline handles various error conditions:

- **Invalid URLs**: Raises `ValueError` during validation
- **Network errors**: Retries with exponential backoff
- **Transcription errors**: Falls back to silent segments
- **Face detection failures**: Falls back to center crop
- **Encoding errors**: Logs and continues with next clip

All errors are caught and stored in job `error_message` field.

## Performance Considerations

### Resource Usage

- **CPU**: Scales with model size and video resolution
- **Memory**: 1-5GB depending on Whisper model
- **Disk**: ~500MB per video (source + audio + clips)
- **Time**: 5-60 minutes depending on video length and model

### Optimization Tips

1. **Use smaller Whisper model for speed**: `WHISPER_MODEL=tiny` or `base`
2. **Set `MAX_CONCURRENT_JOBS=1`** to reduce memory pressure
3. **Enable GPU** with `ENABLE_GPU=true` (requires CUDA)
4. **Increase `sample_rate` in face detection** (e.g., `sample_rate=10`) for faster processing

### Bottlenecks

1. **Transcription**: Longest stage (10-30s per minute of audio)
2. **Face detection**: Proportional to video length
3. **Video encoding**: Depends on resolution and quality preset

## Testing

### Unit Tests

Test individual components:

```bash
pytest app/tests/test_segment_generation.py -v
pytest app/tests/test_media_pipeline.py -v
```

### Sample Data

Sample transcript segments are provided in test fixtures for testing segmentation logic without downloading real videos.

## Troubleshooting

### Common Issues

**FFmpeg not found**
```bash
# Install FFmpeg
sudo apt-get install ffmpeg ffprobe  # Linux
brew install ffmpeg                   # macOS
```

**Whisper model download fails**
```bash
# Pre-download model
python -c "import whisper; whisper.load_model('base')"
```

**Out of memory**
- Reduce `MAX_CONCURRENT_JOBS`
- Use smaller Whisper model
- Enable swap space

**Low segmentation quality**
- Check that transcript is accurate
- Verify models are loaded correctly
- Consider adjusting scoring weights

## Future Enhancements

1. **Speaker diarization**: Identify different speakers
2. **Highlight detection**: Automatic highlight moments
3. **Hook generation**: Detect attention-grabbing openings
4. **Title/hashtag suggestions**: Generate optimized titles
5. **Template overlays**: Add captions and graphics
6. **Multi-language support**: Improved language detection
7. **Custom scoring**: Allow user-defined scoring functions
8. **Distributed processing**: Scale with multiple workers

## Dependencies

### Core Dependencies
- `yt-dlp>=2023.12.30` - YouTube download
- `ffmpeg-python>=0.2.0` - Video processing
- `openai-whisper>=20231117` - Transcription
- `spacy>=3.7.2` - NLP
- `transformers>=4.36.0` - Sentiment analysis
- `opencv-python-headless>=4.8.1` - Computer vision

### Optional Dependencies
- `mediapipe` - Face detection (recommended)
- `torch>=2.0.0` - GPU acceleration
- `torchaudio>=2.0.0` - Audio processing

## References

- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
- [FFmpeg Documentation](https://ffmpeg.org/)
- [OpenAI Whisper](https://github.com/openai/whisper)
- [spaCy Documentation](https://spacy.io/)
- [Transformers Documentation](https://huggingface.co/docs/transformers)
- [MediaPipe Face Detection](https://google.github.io/mediapipe/)
