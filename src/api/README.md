# Archive Converter REST API

**Version**: 1.0.0
**Status**: Implementation Ready (Mock Responses)

FastAPI 기반 비디오 아카이브 메타데이터 관리 REST API

---

## Quick Start

```bash
# 개발 서버 실행
cd D:\AI\claude01\Archive_Converter\src\api
python main.py

# 또는 uvicorn 직접 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# API 문서 확인
open http://localhost:8000/docs
```

---

## Features

- ✅ **Asset CRUD**: 비디오 파일 메타데이터 관리
- ✅ **Segment CRUD**: 포커 핸드 구간 관리
- ✅ **Search**: 복합 검색 및 필터링
- ✅ **Export**: JSON/CSV 데이터 내보내기
- ✅ **Stats**: 대시보드용 통계
- ✅ **OpenAPI**: 자동 문서화 (Swagger UI)
- ✅ **Pydantic V2**: 타입 안전 검증
- ✅ **Error Handling**: 표준화된 에러 응답

---

## API Endpoints

### Asset Management

```bash
# Asset 목록 조회
GET /api/v1/assets?page=1&page_size=50&brand=WSOP&year=2024

# Asset 상세 조회
GET /api/v1/assets/{uuid}

# Asset 생성
POST /api/v1/assets
{
  "file_name": "2024 WSOPC LA.mp4",
  "event_context": {"year": 2024, "brand": "WSOPC"},
  "source_origin": "NAS_WSOP_2024"
}

# Asset 수정
PUT /api/v1/assets/{uuid}

# Asset 삭제
DELETE /api/v1/assets/{uuid}

# Asset의 Segment 목록
GET /api/v1/assets/{uuid}/segments
```

### Segment Management

```bash
# Segment 생성
POST /api/v1/assets/{asset_uuid}/segments
{
  "time_in_sec": 425.5,
  "time_out_sec": 510.2,
  "rating": 5,
  "winner": "Daniel Negreanu"
}

# Segment 상세 조회
GET /api/v1/segments/{uuid}

# Segment 수정
PUT /api/v1/segments/{uuid}

# Segment 삭제
DELETE /api/v1/segments/{uuid}
```

### Search

```bash
# 통합 검색
GET /api/v1/search?q=negreanu&brand=WSOP&rating_min=4&has_cooler=true
```

### Export

```bash
# JSON 내보내기
POST /api/v1/export/json
{
  "pretty_print": true,
  "include_segments": true
}

# CSV 내보내기
POST /api/v1/export/csv
{
  "delimiter": ",",
  "array_delimiter": "|",
  "encoding": "utf-8-sig"
}

# 스트리밍 다운로드
POST /api/v1/export/json/stream
POST /api/v1/export/csv/stream
```

### Statistics

```bash
# 전체 통계
GET /api/v1/stats

# 브랜드별 통계
GET /api/v1/stats/brand/WSOP

# 연도별 통계
GET /api/v1/stats/year/2024
```

---

## Project Structure

```
src/api/
├── __init__.py
├── main.py                 # FastAPI app factory
├── dependencies.py         # 공통 의존성 (pagination, DB session)
├── exceptions.py           # 커스텀 예외 처리
├── schemas/                # Pydantic DTOs (Request/Response)
│   ├── __init__.py
│   ├── common.py           # Pagination, Error
│   ├── asset.py            # Asset DTOs
│   ├── segment.py          # Segment DTOs
│   ├── search.py           # Search DTOs
│   └── export.py           # Export DTOs
└── routes/                 # API 엔드포인트
    ├── __init__.py
    ├── assets.py           # Asset CRUD
    ├── segments.py         # Segment CRUD
    ├── search.py           # 검색/필터
    ├── export.py           # Export
    └── stats.py            # 통계
```

---

## Design Principles

### 1. Contract-First Design

```python
# API Schema와 UDM Model 분리
UDM Model (src/models/udm.py) → 비즈니스 로직
API Schema (src/api/schemas/) → HTTP 계약
```

### 2. Layered Architecture

```
Client → FastAPI → Service → Repository → Database
        (DTO)    (UDM)      (ORM)
```

### 3. RESTful Conventions

- **GET**: 조회 (Idempotent)
- **POST**: 생성 (Non-idempotent)
- **PUT**: 전체 수정 (Idempotent)
- **PATCH**: 부분 수정 (지원 안 함, PUT으로 통일)
- **DELETE**: 삭제 (Idempotent)

### 4. Response Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | 성공 (GET, PUT, DELETE) |
| 201 | Created | 생성 성공 (POST) |
| 400 | Bad Request | 잘못된 요청 |
| 404 | Not Found | 리소스 없음 |
| 409 | Conflict | 중복 등 충돌 |
| 422 | Unprocessable Entity | 검증 실패 |
| 500 | Internal Server Error | 서버 오류 |

### 5. Error Response Format

```json
{
  "error": "RESOURCE_NOT_FOUND",
  "message": "Asset not found: 550e8400-...",
  "details": {
    "resource_type": "Asset",
    "resource_id": "550e8400-..."
  },
  "path": "/api/v1/assets/550e8400-..."
}
```

---

## Validation Rules

### Asset

- `file_name`: 필수, 최소 1자
- `event_context.year`: 필수, 1970-2100
- `event_context.brand`: 필수, Enum (WSOP, HCL 등)

### Segment

- **BR-001**: `time_out_sec > time_in_sec` (필수)
- **BR-003**: 권장 핸드 길이 10-3600초 (경고만)
- **BR-002**: `winner`가 `players`에 포함 (경고만)

---

## Pagination

```bash
# 기본 페이징
GET /api/v1/assets?page=1&page_size=50

# 응답
{
  "items": [...],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_items": 1250,
    "total_pages": 25,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## Filtering & Sorting

### Asset 목록

```bash
# 필터링
?brand=WSOP&year=2024&asset_type=SUBCLIP

# 정렬
?sort_by=created_at&sort_order=desc
```

### Search

```bash
# 복합 필터
?q=negreanu
&brand=WSOP
&year=2024
&rating_min=4
&player_name=Daniel
&tags=cooler,badbeat
&has_cooler=true
&duration_min_sec=60
```

---

## Export Formats

### JSON (Golden Record)

```json
{
  "_metadata": {
    "exported_at": "2025-12-11T14:30:00Z",
    "schema_version": "3.0.0"
  },
  "assets": [
    {
      "asset_uuid": "550e8400-...",
      "file_name": "2024 WSOPC LA.mp4",
      "event_context": {...},
      "segments": [...]
    }
  ]
}
```

### CSV (Flattened)

```csv
asset_uuid,file_name,event_year,event_brand,segment_uuid,time_in_sec,rating,winner,players,tags_action
550e8400-...,2024 WSOPC LA.mp4,2024,WSOPC,a1b2c3d4-...,425.5,5,Negreanu,"Negreanu|Hellmuth","preflop-allin|cooler"
```

**평면화 규칙**:
- 배열 → `array_delimiter`로 구분 (기본: `|`)
- 중첩 객체 → Dot notation (`event_year`, `event_brand`)

---

## TODO (Phase 2)

- [ ] **Database**: PostgreSQL + SQLAlchemy 연동
- [ ] **Authentication**: JWT 기반 인증
- [ ] **Authorization**: RBAC (READ/WRITE/ADMIN)
- [ ] **Rate Limiting**: Redis 기반
- [ ] **Caching**: 통계/검색 결과 캐싱
- [ ] **Background Jobs**: Export 비동기 처리
- [ ] **Search Engine**: Elasticsearch 연동
- [ ] **File Upload**: Asset 파일 업로드
- [ ] **Audit Log**: 변경 이력 추적
- [ ] **Monitoring**: Prometheus + Grafana

---

## Testing

```bash
# pytest 설치
pip install pytest pytest-asyncio httpx

# 테스트 실행 (향후)
pytest tests/api/ -v
```

---

## Dependencies

```bash
# 필수
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0

# 향후 추가
sqlalchemy>=2.0.0          # ORM
alembic>=1.12.0            # Migration
redis>=5.0.0               # Cache
elasticsearch>=8.0.0       # Search
python-jose[cryptography]  # JWT
passlib[bcrypt]            # Password hashing
python-multipart           # File upload
```

---

## Related Documents

- **API Design**: `D:\AI\claude01\Archive_Converter\docs\API_DESIGN.md`
- **Architecture**: `D:\AI\claude01\Archive_Converter\docs\API_ARCHITECTURE.md`
- **UDM Schema**: `D:\AI\claude01\Archive_Converter\src\models\udm.py`
- **Export PRD**: `D:\AI\claude01\Archive_Converter\prds\PRD-0005-EXPORT-AGENT.md`

---

## Example Requests

### Asset 생성

```bash
curl -X POST http://localhost:8000/api/v1/assets \
  -H "Content-Type: application/json" \
  -d '{
    "file_name": "2024 WSOPC LA - Main Event Day2.mp4",
    "asset_type": "STREAM",
    "event_context": {
      "year": 2024,
      "brand": "WSOPC",
      "location": "Las Vegas"
    },
    "source_origin": "NAS_WSOP_2024"
  }'
```

### Segment 생성

```bash
curl -X POST http://localhost:8000/api/v1/assets/{asset_uuid}/segments \
  -H "Content-Type: application/json" \
  -d '{
    "time_in_sec": 425.5,
    "time_out_sec": 510.2,
    "rating": 5,
    "winner": "Daniel Negreanu",
    "players": [
      {"name": "Daniel Negreanu", "hand": "AA", "is_winner": true},
      {"name": "Phil Hellmuth", "hand": "KK", "is_winner": false}
    ],
    "tags_action": ["preflop-allin", "cooler"]
  }'
```

### 검색

```bash
curl "http://localhost:8000/api/v1/search?q=negreanu&brand=WSOP&rating_min=4"
```

### CSV Export

```bash
curl -X POST http://localhost:8000/api/v1/export/csv \
  -H "Content-Type: application/json" \
  -d '{
    "delimiter": ",",
    "array_delimiter": "|",
    "encoding": "utf-8-sig",
    "rating_min": 4
  }'
```

---

## License

Archive Converter Team
