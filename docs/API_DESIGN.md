# Archive Converter API Design

**Version**: 1.0.0
**Date**: 2025-12-11
**Status**: Implementation Ready

---

## 1. 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer                            │
│  (Web Dashboard, CLI Tools, External Services)              │
└────────────────┬────────────────────────────────────────────┘
                 │ HTTP/REST
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Layer                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Routers (routes/)                                   │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │   │
│  │  │ Assets │ │Segments│ │ Search │ │ Export │ ...   │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘       │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Middleware (CORS, Auth, Rate Limit, Logging)       │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Schemas (schemas/)                                  │   │
│  │  Request DTOs ←→ UDM Models ←→ Response DTOs        │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer                             │
│  (Business Logic - 향후 구현)                                │
│  - AssetService                                             │
│  - SegmentService                                           │
│  - SearchService                                            │
│  - ExportService                                            │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                  Repository Layer                           │
│  (Data Access - 향후 구현)                                   │
│  - AssetRepository                                          │
│  - SegmentRepository                                        │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  PostgreSQL  │  │   MongoDB    │  │Elasticsearch │      │
│  │  (관계형)     │  │   (문서)      │  │  (검색)       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. API 엔드포인트

### 2.1 Asset CRUD

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET | `/api/v1/assets` | Asset 목록 조회 (페이징/필터) | ✅ Designed |
| GET | `/api/v1/assets/{uuid}` | Asset 상세 조회 | ✅ Designed |
| POST | `/api/v1/assets` | Asset 생성 | ✅ Designed |
| PUT | `/api/v1/assets/{uuid}` | Asset 수정 | ✅ Designed |
| DELETE | `/api/v1/assets/{uuid}` | Asset 삭제 (CASCADE) | ✅ Designed |
| GET | `/api/v1/assets/{uuid}/segments` | Asset의 Segment 목록 | ✅ Designed |

**필터링 옵션**:
- `brand`: 브랜드 필터 (WSOP, HCL, PAD 등)
- `year`: 연도 필터 (1970-2100)
- `asset_type`: Asset 유형 (STREAM, SUBCLIP 등)

**정렬**:
- `sort_by`: created_at (기본), file_name, event_year
- `sort_order`: desc (기본), asc

**페이징**:
- `page`: 페이지 번호 (1부터 시작)
- `page_size`: 페이지당 항목 수 (기본: 50, 최대: 1000)

---

### 2.2 Segment CRUD

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET | `/api/v1/segments` | Segment 목록 조회 | ✅ Designed |
| GET | `/api/v1/segments/{uuid}` | Segment 상세 조회 | ✅ Designed |
| POST | `/api/v1/assets/{asset_uuid}/segments` | Segment 생성 | ✅ Designed |
| PUT | `/api/v1/segments/{uuid}` | Segment 수정 | ✅ Designed |
| DELETE | `/api/v1/segments/{uuid}` | Segment 삭제 | ✅ Designed |

**검증 규칙**:
- BR-001: `time_out_sec > time_in_sec`
- BR-003: 권장 핸드 길이 10-3600초 (경고만)
- BR-002: `winner`가 `players`에 포함 (경고만)

---

### 2.3 검색/필터

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET | `/api/v1/search` | 통합 검색 (Asset + Segment) | ✅ Designed |

**검색 파라미터**:
- `q`: 전문 검색 (파일명, 플레이어명, 설명)
- `brand`, `year`, `location`: 이벤트 필터
- `rating_min`, `rating_max`: 별점 범위
- `player_name`: 특정 플레이어 포함
- `tags`: 태그 필터 (OR 조건)

**Segment 전용 필터**:
- `has_cooler`: 쿨러 핸드
- `has_badbeat`: 배드비트
- `has_allin_preflop`: 프리플랍 올인
- `duration_min_sec`, `duration_max_sec`: 핸드 길이 범위

**응답**:
- `results`: Asset + Segment 통합 결과
- `relevance_score`: 검색 관련도 (0.0-1.0)
- `match_reason`: 매칭 이유 (디버깅용)

---

### 2.4 Export

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| POST | `/api/v1/export/json` | JSON 내보내기 | ✅ Designed |
| POST | `/api/v1/export/json/stream` | JSON 스트리밍 다운로드 | ✅ Designed |
| POST | `/api/v1/export/csv` | CSV 내보내기 | ✅ Designed |
| POST | `/api/v1/export/csv/stream` | CSV 스트리밍 다운로드 | ✅ Designed |

**JSON Export 옵션**:
- `pretty_print`: JSON 포맷팅 (indent=2)
- `include_metadata`: 메타데이터 포함
- `include_segments`: Segment 데이터 포함

**CSV Export 옵션**:
- `delimiter`: 필드 구분자 (`,` | `\t` | `|` | `;`)
- `array_delimiter`: 배열 요소 구분자 (기본: `|`)
- `encoding`: 파일 인코딩 (기본: `utf-8-sig` - Excel BOM)
- `columns`: 출력할 컬럼 목록 (지정하지 않으면 전체)

**출력 형식**:

**JSON**:
```json
{
  "_metadata": {
    "exported_at": "2025-12-11T14:30:00Z",
    "schema_version": "3.0.0"
  },
  "assets": [...]
}
```

**CSV** (평면화):
```csv
asset_uuid,file_name,event_year,event_brand,segment_uuid,time_in_sec,rating,winner,players,tags_action
550e8400-...,2024 WSOPC.mp4,2024,WSOPC,a1b2c3d4-...,425.5,5,Negreanu,"Negreanu|Hellmuth","preflop-allin|cooler"
```

---

### 2.5 통계

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET | `/api/v1/stats` | 전체 통계 | ✅ Designed |
| GET | `/api/v1/stats/brand/{brand}` | 브랜드별 통계 | ✅ Designed |
| GET | `/api/v1/stats/year/{year}` | 연도별 통계 | ✅ Designed |

**통계 정보**:
- Asset 총 수, 파일 크기 합계, 총 영상 길이
- Segment 총 수, 평균 길이, 별점 분포
- 브랜드별/연도별 분포
- 상위 플레이어 (등장 횟수)

---

## 3. 데이터 모델 레이어 분리

### 3.1 3-Layer 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│  UDM Models (src/models/udm.py)                         │
│  - Domain Models (Asset, Segment)                       │
│  - Business Validation                                  │
│  - UUID, computed fields                                │
└────────────────┬────────────────────────────────────────┘
                 │ Conversion
                 ▼
┌─────────────────────────────────────────────────────────┐
│  API Schemas (src/api/schemas/)                         │
│  - Request DTOs (create, update)                        │
│  - Response DTOs (경량화, 페이징)                         │
│  - UDM과 독립적 (API 변경 시 UDM 영향 없음)                │
└────────────────┬────────────────────────────────────────┘
                 │ Serialization
                 ▼
┌─────────────────────────────────────────────────────────┐
│  JSON/CSV (API Response)                                │
│  - Client-friendly format                               │
│  - Camel case 또는 snake_case 선택 가능                  │
└─────────────────────────────────────────────────────────┘
```

### 3.2 레이어별 책임

| Layer | 파일 위치 | 책임 |
|-------|---------|------|
| **Domain** | `src/models/udm.py` | 비즈니스 로직, 검증, 불변성 |
| **API** | `src/api/schemas/` | HTTP 요청/응답, 페이징, 필터 |
| **Persistence** | (향후) `src/repositories/` | DB 저장/조회, 쿼리 |

---

## 4. 스케일링 전략

### 4.1 Horizontal Scaling

```
                    ┌──────────────┐
                    │ Load Balancer│
                    │   (Nginx)    │
                    └──────┬───────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
     ┌──────────┐   ┌──────────┐   ┌──────────┐
     │ FastAPI  │   │ FastAPI  │   │ FastAPI  │
     │ Instance │   │ Instance │   │ Instance │
     └────┬─────┘   └────┬─────┘   └────┬─────┘
          │              │              │
          └──────────────┼──────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  Shared Data Layer  │
              │  (PostgreSQL/Redis) │
              └─────────────────────┘
```

**스케일링 포인트**:
1. **Stateless API**: FastAPI 인스턴스 무상태 설계
2. **Session Store**: Redis 기반 세션 공유
3. **DB Connection Pool**: 연결 풀 관리
4. **Read Replicas**: 읽기 전용 복제본 (검색/통계)

---

### 4.2 성능 최적화

| 항목 | 전략 | 예상 효과 |
|------|------|----------|
| **Pagination** | Cursor-based (향후) | O(1) 다음 페이지 |
| **Caching** | Redis (메타데이터, 통계) | 90% 응답 시간 감소 |
| **Indexing** | DB 인덱스 (UUID, year, brand) | 쿼리 100x 빠름 |
| **Lazy Loading** | Segment 별도 조회 | N+1 문제 방지 |
| **Streaming** | Export 대용량 처리 | 메모리 효율 |

---

### 4.3 Bottleneck 예상

| 구간 | 병목 요인 | 해결책 |
|------|----------|--------|
| **검색** | Full-text scan | Elasticsearch 도입 |
| **Export** | 대용량 메모리 | 스트리밍 처리 |
| **통계** | 집계 쿼리 | Materialized View |
| **Asset 생성** | 파일 메타 추출 | 비동기 작업 큐 |

---

## 5. 보안

### 5.1 인증/인가 (Phase 2)

```python
# JWT 기반 인증
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# 권한 레벨
- READ: 조회만 가능
- WRITE: CRUD 가능
- ADMIN: Export, 통계, 관리
```

### 5.2 Rate Limiting (Phase 2)

```python
# Redis 기반 Rate Limiter
- 100 requests/min (일반 사용자)
- 1000 requests/min (인증 사용자)
- Export: 10 requests/hour
```

### 5.3 입력 검증

- **Pydantic**: 자동 타입 검증
- **Field Validators**: 커스텀 비즈니스 규칙
- **SQL Injection 방지**: Parameterized Queries
- **XSS 방지**: Response sanitization

---

## 6. 기술 스택

| Layer | Technology | Version | Rationale |
|-------|-----------|---------|-----------|
| **Framework** | FastAPI | 0.104+ | 비동기, 자동 문서화, Pydantic 통합 |
| **Validation** | Pydantic | 2.5+ | 타입 안전, 자동 검증 |
| **Server** | Uvicorn | 0.24+ | ASGI, 고성능 |
| **Database** | PostgreSQL | 15+ | 관계형, JSONB 지원 |
| **Search** | Elasticsearch | 8.0+ | Full-text search |
| **Cache** | Redis | 7.0+ | 세션, 통계 캐싱 |
| **Migration** | Alembic | 1.12+ | DB 스키마 관리 |
| **ORM** | SQLAlchemy | 2.0+ | Async ORM |

---

## 7. 파일 구조

```
src/api/
├── __init__.py
├── main.py                 # FastAPI app factory
├── dependencies.py         # 공통 의존성 (페이징, DB 세션)
├── exceptions.py           # 커스텀 예외
├── schemas/                # Pydantic DTOs
│   ├── __init__.py
│   ├── common.py           # Pagination, Error
│   ├── asset.py            # Asset DTOs
│   ├── segment.py          # Segment DTOs
│   ├── search.py           # Search DTOs
│   └── export.py           # Export DTOs
└── routes/                 # 엔드포인트
    ├── __init__.py
    ├── assets.py           # Asset CRUD
    ├── segments.py         # Segment CRUD
    ├── search.py           # 검색
    ├── export.py           # Export
    └── stats.py            # 통계
```

---

## 8. 향후 확장

### Phase 2 (Enhancement)

- [ ] **DB 연동**: PostgreSQL + SQLAlchemy
- [ ] **인증**: JWT 기반 Auth
- [ ] **Rate Limiting**: Redis 기반
- [ ] **Caching**: 통계 캐싱
- [ ] **Background Jobs**: Celery + Redis
- [ ] **File Upload**: Asset 파일 업로드

### Phase 3 (Advanced)

- [ ] **Elasticsearch**: Full-text search
- [ ] **WebSocket**: 실시간 알림
- [ ] **GraphQL**: 복잡한 쿼리 지원
- [ ] **Multi-tenancy**: 조직별 격리
- [ ] **Audit Log**: 변경 이력 추적

---

## 9. 실행 방법

```bash
# 개발 서버 실행
cd src/api
uvicorn main:app --reload --port 8000

# API 문서 확인
open http://localhost:8000/docs

# 헬스 체크
curl http://localhost:8000/health
```

---

## 10. 예제 요청/응답

### Asset 생성

**Request**:
```bash
POST /api/v1/assets
Content-Type: application/json

{
  "file_name": "2024 WSOPC LA - Main Event Day2.mp4",
  "asset_type": "STREAM",
  "event_context": {
    "year": 2024,
    "brand": "WSOPC",
    "location": "Las Vegas"
  },
  "source_origin": "NAS_WSOP_2024"
}
```

**Response**:
```json
{
  "asset_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "file_name": "2024 WSOPC LA - Main Event Day2.mp4",
  "asset_type": "STREAM",
  "event_context": {
    "year": 2024,
    "brand": "WSOPC",
    "location": "Las Vegas"
  },
  "source_origin": "NAS_WSOP_2024",
  "created_at": "2025-12-11T14:30:00Z",
  "segment_count": 0
}
```

---

### Segment 생성

**Request**:
```bash
POST /api/v1/assets/550e8400-e29b-41d4-a716-446655440000/segments
Content-Type: application/json

{
  "time_in_sec": 425.5,
  "time_out_sec": 510.2,
  "rating": 5,
  "winner": "Daniel Negreanu",
  "players": [
    {"name": "Daniel Negreanu", "hand": "AA", "is_winner": true},
    {"name": "Phil Hellmuth", "hand": "KK", "is_winner": false}
  ],
  "tags_action": ["preflop-allin", "cooler"]
}
```

**Response**:
```json
{
  "segment_uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "parent_asset_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "time_in_sec": 425.5,
  "time_out_sec": 510.2,
  "duration_sec": 84.7,
  "rating": 5,
  "winner": "Daniel Negreanu",
  "players": [...],
  "tags_action": ["preflop-allin", "cooler"]
}
```

---

## 11. 관련 문서

- **UDM Schema**: `D:\AI\claude01\Archive_Converter\src\models\udm.py`
- **Export PRD**: `D:\AI\claude01\Archive_Converter\prds\PRD-0005-EXPORT-AGENT.md`
- **API Main**: `D:\AI\claude01\Archive_Converter\src\api\main.py`
