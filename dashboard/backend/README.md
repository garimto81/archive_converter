# Archive Dashboard Backend

FastAPI backend for the Archive Converter Dashboard. Supports 1:N relationship model (NAS File → Sheet Records → UDM Segments).

## Features

- **1:N Relationship Support**: One NAS file can have multiple sheet records and UDM segments
- **Mock Data**: Works without database or NAS connection for development
- **FastAPI**: Modern async Python web framework
- **Pydantic V2**: Strong typing and validation
- **OpenAPI Docs**: Auto-generated API documentation

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -e .

# Run server
python -m app.main

# Or with uvicorn directly
uvicorn app.main:app --reload --port 8000
```

### Docker

```bash
# Build image
docker build -t archive-dashboard-backend .

# Run container
docker run -p 8000:8000 archive-dashboard-backend
```

### With Docker Compose

```bash
cd ../
docker-compose up backend
```

## API Endpoints

### Matching Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/matching/matrix` | GET | Get matching matrix (1:N view) |
| `/api/matching/stats` | GET | Get matching statistics |
| `/api/matching/file/{file_name}/segments` | GET | Get all segments for a file |

### NAS Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/nas/folders` | GET | Get folder tree |
| `/api/nas/files?path={path}` | GET | Get files in folder |

### Example Requests

```bash
# Get matching matrix
curl http://localhost:8000/api/matching/matrix

# Filter by status
curl "http://localhost:8000/api/matching/matrix?status=partial"

# Search files
curl "http://localhost:8000/api/matching/matrix?search=STREAM"

# Get file segments
curl http://localhost:8000/api/matching/file/STREAM_01.mp4/segments

# Get stats
curl http://localhost:8000/api/matching/stats

# Get folder tree
curl http://localhost:8000/api/nas/folders

# Get files in folder
curl "http://localhost:8000/api/nas/files?path=/ARCHIVE/WSOP/STREAM"
```

## API Documentation

Once running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration (Pydantic Settings)
│   ├── routers/             # API endpoints
│   │   ├── matching.py      # Matching matrix endpoints
│   │   └── nas.py           # NAS browser endpoints
│   ├── schemas/             # Pydantic models
│   │   ├── matching.py      # Matching data models
│   │   └── nas.py           # NAS data models
│   └── services/            # Business logic
│       └── mock_data.py     # Mock data generator
├── pyproject.toml           # Dependencies
├── Dockerfile               # Container image
└── README.md                # This file
```

## Data Model (1:N Relationship)

```
NAS File (1)           Sheet Records (N)         UDM Segments (N)
═══════════           ═════════════════         ═══════════════
┌─────────────┐       ┌─────────────┐           ┌─────────┐
│ STREAM_01   │◄─────┤│ Segment 1   │──────────▶│ UDM #1  │
│             │       │ 00:00-02:30 │           └─────────┘
│             │◄─────┤│ Segment 2   │──────────▶│ UDM #2  │
│             │       │ 02:30-05:15 │           └─────────┘
│             │◄─────┤│ Segment 3   │──────────▶│ UDM #3  │
└─────────────┘       └─────────────┘           └─────────┘
```

### Example Response

```json
{
  "file_name": "STREAM_01.mp4",
  "nas": {
    "exists": true,
    "path": "/ARCHIVE/WSOP/STREAM_01.mp4",
    "size_mb": 2450.5,
    "duration_sec": 3600.0
  },
  "segment_count": 15,
  "udm_count": 15,
  "status": "complete",
  "status_detail": "15/15",
  "segments": [
    {
      "row_number": 1,
      "source": "archive_metadata",
      "time_in": "00:02:15",
      "time_out": "00:05:30",
      "time_in_sec": 135.0,
      "time_out_sec": 330.0,
      "rating": 4,
      "winner": "Phil Ivey",
      "hands": "AA vs KK",
      "udm": {
        "uuid": "uuid-STREAM_01.mp4-seg1",
        "status": "complete"
      }
    }
    // ... 14 more segments
  ]
}
```

## Mock Data

The mock data service generates realistic data:

- **20 NAS files** with varying segment counts (1-15 segments each)
- **Complete files**: All segments converted to UDM
- **Partial files**: Some segments not yet converted
- **Warning files**: Validation issues in some segments
- **No metadata files**: NAS files without sheet records

### Status Types

| Status | Description | Example |
|--------|-------------|---------|
| `complete` | All segments converted | STREAM_01.mp4 (15/15) |
| `partial` | Some segments converted | STREAM_02.mp4 (7/10) |
| `warning` | Validation issues | STREAM_03.mp4 (6/8) |
| `no_metadata` | No sheet records | UNKNOWN_FILE_01.mp4 (0) |
| `orphan` | Sheet records without NAS file | (rare) |

## Future Enhancements

- [ ] PostgreSQL database integration
- [ ] Real NAS scanner service
- [ ] Google Sheets API integration
- [ ] Redis caching
- [ ] Background task processing (Celery)
- [ ] WebSocket for real-time updates
- [ ] Authentication and authorization

## Development

### Run Tests

```bash
pip install -e ".[dev]"
pytest
```

### Code Quality

```bash
# Format code
black app/

# Type checking
mypy app/

# Linting
ruff check app/
```

## Environment Variables

See `.env.example` for all available configuration options.

## License

Internal use only.
