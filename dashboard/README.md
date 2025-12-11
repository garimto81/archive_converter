# Archive Converter Dashboard

NAS 저장소, Google Sheets 메타데이터, UDM 변환 결과를 한눈에 확인하는 통합 대시보드

## Quick Start

### Docker Compose (권장)

```bash
cd dashboard
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 개발 모드

**Backend:**
```bash
cd dashboard/backend
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd dashboard/frontend
npm install
npm run dev
```

## 아키텍처

```
┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│    Backend      │
│  React + Vite   │     │    FastAPI      │
│  localhost:3000 │     │  localhost:8000 │
└─────────────────┘     └─────────────────┘
```

## 데이터 관계 (1:N)

```
NAS File (1) ──▶ Sheet Records (N) ──▶ UDM Segments (N)
```

- 1개 영상 파일에 여러 핸드(세그먼트) 포함
- 각 핸드는 개별 UDM 문서로 변환

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/matching/matrix` | 매칭 매트릭스 |
| `GET /api/matching/stats` | 통계 |
| `GET /api/matching/file/{name}/segments` | 파일별 세그먼트 |
| `GET /api/nas/folders` | NAS 폴더 트리 |
| `GET /api/nas/files` | NAS 파일 목록 |

## 관련 문서

- [PRD-0010-DASHBOARD.md](../prds/PRD-0010-DASHBOARD.md)
- [PRD-0008-UDM-FINAL-SCHEMA.md](../prds/PRD-0008-UDM-FINAL-SCHEMA.md)
