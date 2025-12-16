# PokerGO Downloader Backend

FastAPI backend for PokerGO video downloading.

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Run development server
uvicorn app.main:app --reload --port 8080
```

### Docker

```bash
# Build and run
docker-compose up --build

# Access
# - API: http://localhost:8080
# - API Docs: http://localhost:8080/docs
# - Frontend: http://localhost:3000
```

## API Endpoints

### Videos

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/videos` | List videos with filters |
| GET | `/api/videos/{id}` | Get single video |
| POST | `/api/videos` | Create video |
| PATCH | `/api/videos/{id}` | Update video |
| POST | `/api/videos/import` | Import from JSON |
| GET | `/api/videos/export` | Export to JSON |
| GET | `/api/videos/stats` | Get statistics |

### Downloads

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/downloads` | Get queue status |
| POST | `/api/downloads` | Add to queue |
| DELETE | `/api/downloads/{id}` | Cancel download |
| PATCH | `/api/downloads/{id}/pause` | Pause download |
| PATCH | `/api/downloads/{id}/resume` | Resume download |

### HLS

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/hls/fetch` | Start HLS URL extraction |
| GET | `/api/hls/status` | Get fetch status |
| POST | `/api/hls/cancel` | Cancel fetch |
| GET | `/api/hls/missing` | Get videos without HLS |

### Settings

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/settings` | Get settings |
| PUT | `/api/settings` | Update settings |
| POST | `/api/settings/test-login` | Test login |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `/ws/downloads` | Real-time download progress |

## WebSocket Messages

```json
// Progress update
{
    "type": "progress",
    "video_id": "im_70009",
    "progress": 65.5,
    "speed": 19456000,
    "eta": 150,
    "status": "downloading"
}

// Completed
{
    "type": "completed",
    "video_id": "im_70009",
    "file_path": "/downloads/WSOP 2017 Episode 1.mp4",
    "file_size": 731185152
}

// Failed
{
    "type": "failed",
    "video_id": "im_70009",
    "error": "Network error"
}
```

## Configuration

Environment variables (prefix: `POKERGO_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8080` | Server port |
| `DEBUG` | `false` | Debug mode |
| `DATABASE_PATH` | `data/pokergo.db` | Database path |
| `DOWNLOAD_PATH` | `downloads` | Download directory |
| `DEFAULT_QUALITY` | `Best` | Default video quality |
| `MAX_CONCURRENT_DOWNLOADS` | `2` | Max parallel downloads |

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app
│   ├── config.py         # Settings
│   ├── models/           # Pydantic models
│   │   ├── video.py
│   │   ├── download.py
│   │   └── settings.py
│   ├── routers/          # API routes
│   │   ├── videos.py
│   │   ├── downloads.py
│   │   ├── hls.py
│   │   ├── settings.py
│   │   └── websocket.py
│   └── services/         # Business logic
│       ├── database.py
│       ├── download_manager.py
│       └── hls_fetcher.py
├── requirements.txt
├── Dockerfile
└── README.md
```
