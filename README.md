# Video Processing API - Backend

A comprehensive FastAPI-based backend service for processing YouTube videos with AI models including transcription, analysis, and clip generation.

## Features

### Core Functionality
- **Job Management**: Create, track, and manage video processing jobs
- **Real-time Progress**: WebSocket-based live progress updates
- **Multiple Job Types**:
  - Audio extraction from YouTube videos
  - Video transcription using OpenAI Whisper
  - Video analysis with spaCy and transformers
  - Clip generation with customizable segments
  - Full processing pipeline
- **Async Queue System**: In-process async worker queue with configurable concurrency
- **Database Persistence**: SQLite with SQLModel ORM for reliable data storage

### Advanced Features
- **Priority Queuing**: Jobs can be prioritized (0-10)
- **Retry Logic**: Automatic retry with configurable limits
- **Event Tracking**: Detailed job event logging
- **Worker Monitoring**: Real-time worker status and health checks
- **WebSocket Streaming**: Live progress updates for multiple clients per job
- **Comprehensive API**: RESTful API with filtering, pagination, and bulk operations

## Quick Start

### Prerequisites
- Python 3.11+
- Virtual environment (recommended)

### Installation

1. **Clone and setup environment:**
```bash
git clone <repository-url>
cd video-processing-api
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Setup environment:**
```bash
cp .env.example .env
# Edit .env with your preferences
```

4. **Run the application:**
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Jobs API (`/api/v1/jobs`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/jobs/` | Create a new processing job |
| `GET` | `/jobs/{job_id}` | Get job status and details |
| `GET` | `/jobs/` | List jobs with filtering and pagination |
| `DELETE` | `/jobs/{job_id}` | Delete a completed/failed job |
| `POST` | `/jobs/{job_id}/cancel` | Cancel a pending/queued job |
| `POST` | `/jobs/{job_id}/retry` | Retry a failed job |
| `GET` | `/queue/status` | Get queue status |
| `DELETE` | `/queue/clear` | Clear all pending jobs |
| `GET` | `/statistics` | Get job statistics |

### WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `/ws/{job_id}` | Real-time job progress updates |
| `/ws/jobs/broadcast` | System-wide broadcast channel |
| `/ws/health` | Connection health monitoring |
| `/connections/status` | Active connection status |

## API Usage Examples

### Create a Job

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/" \\
  -H "Content-Type: application/json" \\
  -d '{
    "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "job_type": "full_processing",
    "priority": 5,
    "options": {
      "audio_format": "wav",
      "language": "en",
      "max_clips": 10
    }
  }'
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "job_type": "full_processing",
  "status": "pending",
  "progress": 0.0,
  "created_at": "2024-01-01T12:00:00Z",
  "priority": 5
}
```

### Get Job Status

```bash
curl "http://localhost:8000/api/v1/jobs/{job_id}"
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "job_type": "full_processing",
  "status": "processing",
  "progress": 45.0,
  "video_title": "Example Video",
  "transcript": "Hello world...",
  "analysis_results": {
    "sentiment": "positive",
    "topics": ["technology", "tutorial"]
  },
  "generated_clips": [
    {
      "start": 0.0,
      "end": 30.0,
      "title": "Introduction"
    }
  ]
}
```

### List Jobs with Filtering

```bash
curl "http://localhost:8000/api/v1/jobs/?status_filter=processing&limit=10&offset=0"
```

### WebSocket Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/550e8400-e29b-41d4-a716-446655440000');

ws.onopen = function(event) {
    console.log('WebSocket connected');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'initial_status':
            console.log('Initial status:', data.data);
            break;
        case 'job_update':
            console.log(`Progress: ${data.data.progress}%`);
            console.log(`Status: ${data.data.status}`);
            break;
    }
};

ws.onclose = function(event) {
    console.log('WebSocket disconnected');
};
```

## Job Types

| Type | Description | Output |
|------|-------------|---------|
| `audio_extraction` | Extract audio from YouTube video | Audio file (wav/mp3/flac) |
| `transcription` | Generate transcript using Whisper | Text transcript with timestamps |
| `analysis` | Analyze content with AI models | Sentiment, topics, keywords |
| `clip_generation` | Generate video clips | Video clips with metadata |
| `full_processing` | Complete pipeline | All outputs combined |

## Configuration

### Environment Variables

All configuration is managed through environment variables (see `.env.example`):

```bash
# Application
APP_NAME="Video Processing API"
DEBUG=true
ENVIRONMENT=development

# Database
DATABASE_URL="sqlite:///./video_processing.db"

# Queue
MAX_CONCURRENT_JOBS=3
JOB_TIMEOUT=3600

# AI Models
WHISPER_MODEL=base
ENABLE_GPU=false
```

### Processing Options

Each job can include processing options:

```json
{
  "options": {
    "audio_format": "wav",
    "audio_quality": "high",
    "language": "en",
    "model_size": "base",
    "clip_duration": 30.0,
    "overlap_duration": 2.0,
    "max_clips": 10,
    "sentiment_analysis": true,
    "topic_modeling": true,
    "keyword_extraction": true,
    "output_format": "mp4",
    "resolution": "1080p",
    "min_confidence": 0.7
  }
}
```

## Architecture

### Project Structure

```
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── README.md              # This file
└── app/
    ├── __init__.py
    ├── core/              # Core functionality
    │   ├── config.py      # Settings management
    │   └── logging.py     # Logging configuration
    ├── db/                # Database
    │   └── database.py    # DB connection and session
    ├── models/            # Database models
    │   └── job_models.py  # Job and related models
    ├── schemas/           # Pydantic schemas
    │   └── job_schemas.py # API request/response models
    ├── services/          # Business logic
    │   └── queue.py       # Job queue service
    ├── api/               # API routes
    │   └── v1/
    │       └── routes/    # Route handlers
    └── utils/             # Utility functions
```

### Key Components

1. **FastAPI Application**: Main application with lifespan management
2. **SQLModel Database**: SQLite database with auto-migration
3. **Async Job Queue**: Worker-based queue with progress tracking
4. **WebSocket Manager**: Real-time communication layer
5. **Configuration Management**: Pydantic-based settings with validation

### Data Flow

1. **Job Creation**: Client submits job via REST API
2. **Validation**: Job data validated and persisted to database
3. **Queue Assignment**: Job added to async queue based on priority
4. **Worker Processing**: Available worker picks up job and processes
5. **Progress Updates**: Worker sends progress events via WebSocket
6. **Completion**: Results saved to database and notifications sent

## Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

### Test Examples

```python
# Create test job
response = client.post("/api/v1/jobs/", json={
    "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "job_type": "transcription",
    "options": {"language": "en"}
})

job_id = response.json()["id"]
assert response.status_code == 201

# Get job status
response = client.get(f"/api/v1/jobs/{job_id}")
assert response.status_code == 200
assert response.json()["status"] in ["pending", "queued", "processing"]
```

## Development

### Code Quality

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint code
ruff check app/ tests/

# Type checking
mypy app/
```

### Database Management

The application automatically creates database tables on startup. For development:

```bash
# Reset database
rm video_processing.db

# Database will be recreated automatically on next run
```

### Adding New Features

1. **New Job Type**: Add to `JobType` enum in `models/job_models.py`
2. **Processing Logic**: Extend `_process_job` method in `services/queue.py`
3. **API Endpoints**: Add to appropriate route file in `api/v1/routes/`
4. **Schema Updates**: Add Pydantic models in `schemas/job_schemas.py`

## Production Deployment

### Environment Setup

```bash
# Production environment variables
export DEBUG=false
export DATABASE_URL="postgresql://user:pass@localhost/dbname"
export REDIS_URL="redis://localhost:6379"
export SECRET_KEY="your-production-secret-key"
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Health Checks

Monitor application health:

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "queue_running": true,
  "debug": false
}
```

## Performance Considerations

### Queue Configuration

- **Worker Count**: Adjust `MAX_CONCURRENT_JOBS` based on CPU cores
- **Job Timeout**: Set `JOB_TIMEOUT` to prevent stuck jobs
- **Poll Interval**: Adjust `QUEUE_POLL_INTERVAL` for responsiveness vs. CPU usage

### Database Optimization

- **Connection Pooling**: SQLite has limited concurrent access
- **Indexing**: Automatic indexes on frequently queried fields
- **Pagination**: All list endpoints support pagination

### Memory Management

- **Job Results**: Large transcripts and analysis results are stored efficiently
- **WebSocket Connections**: Automatic cleanup of disconnected clients
- **Worker Processes**: Non-blocking async implementation

## Troubleshooting

### Common Issues

1. **Database Locked**: SQLite doesn't support concurrent writes
2. **WebSocket Connection Failed**: Check firewall and proxy settings
3. **Job Stuck in Queue**: Check worker processes and timeout settings
4. **Import Errors**: Ensure virtual environment is activated

### Logs

Enable detailed logging:

```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
```

Check logs:
```bash
tail -f application.log
```

### Monitoring

Use health endpoints:
- `/health` - Application health
- `/api/v1/jobs/queue/status` - Queue status
- `/api/v1/jobs/statistics` - Job statistics
- `/ws/connections/status` - WebSocket connections

## Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation
4. Run linting and type checking
5. Test with different scenarios

## License

This project is licensed under the MIT License.