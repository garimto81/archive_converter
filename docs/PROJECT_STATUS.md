# Archive Converter - 프로젝트 현황 문서

**Version**: 1.0.0
**Last Updated**: 2025-12-11
**Status**: Phase 2 완료, Phase 3 준비 중

---

## 1. 프로젝트 개요

### 1.1 목적

Archive Converter는 **다양한 MAM(Media Asset Management) 솔루션과 Google Sheets 데이터**를 하나의 일관된 **UDM(Universal Data Model)** 스키마로 변환하는 데이터 파이프라인입니다.

### 1.2 핵심 문제

| 문제 | 설명 |
|------|------|
| **데이터 파편화** | Excel, CatDV, Iconik, Google Sheets 등 다양한 시스템에 메타데이터 분산 |
| **포맷 비일관성** | 타임코드 형식, 플레이어 이름, 태그 체계가 소스마다 상이 |
| **MAM 종속성** | 특정 MAM 시스템에 종속되어 교체 시 데이터 이전 비용 발생 |
| **검색 불가** | 구조화되지 않은 데이터로 복잡한 쿼리 불가능 |

### 1.3 해결책

**Profile 기반 변환 파이프라인**:
- 각 소스별 YAML 프로파일 정의
- 프로파일에 따라 자동으로 UDM 변환
- MAM 독립적인 표준 데이터 모델

---

## 2. 시스템 아키텍처

### 2.1 5-Block Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR (PRD-0001)                      │
│         전체 파이프라인 조율, 상태 관리, 에러 핸들링              │
└─────────────────────┬───────────────────────────────────────────┘
                      │
    ┌─────────────────┼─────────────────┐
    │                 │                 │
    ▼                 ▼                 ▼
┌─────────┐    ┌──────────┐    ┌──────────┐
│ INGEST  │───▶│TRANSFORM │───▶│ VALIDATE │
│ Block 1 │    │ Block 2  │    │ Block 3  │
│PRD-0002 │    │ PRD-0003 │    │ PRD-0004 │
└─────────┘    └──────────┘    └──────────┘
                                    │
    ┌───────────────────────────────┤
    │                               │
    ▼                               ▼
┌─────────┐                  ┌──────────┐
│ EXPORT  │                  │ PROFILE  │
│ Block 4 │                  │ MANAGER  │
│PRD-0005 │                  │ PRD-0006 │
└─────────┘                  └──────────┘
```

### 2.2 데이터 흐름

```
┌──────────────────┐     ┌──────────────┐     ┌──────────────┐
│   SOURCE         │     │   RAW        │     │   UDM        │
│ (CSV/Excel/MAM)  │────▶│   RECORDS    │────▶│   (JSON)     │
└──────────────────┘     └──────────────┘     └──────────────┘
       │                        │                    │
       │                        │                    │
    INGEST                  TRANSFORM            VALIDATE
    (Block 1)               (Block 2)            (Block 3)
                                                     │
                                                     ▼
                                              ┌──────────────┐
                                              │   OUTPUT     │
                                              │   (JSON/CSV) │
                                              └──────────────┘
```

---

## 3. UDM (Universal Data Model)

### 3.1 설계 원칙

| 원칙 | 설명 |
|------|------|
| **Unique ID First** | UUID/Hash 기반 식별 |
| **Time as Float** | 타임코드 대신 초(Seconds) 단위 |
| **Tags as Arrays** | 복수 값은 Array로 저장 |

### 3.2 2-Level 구조

**Level 1: Asset** (물리적 파일)

| Field | Type | Description |
|-------|------|-------------|
| `asset_uuid` | UUID | Primary Key |
| `file_name` | String | 확장자 포함 파일명 |
| `event_context` | Object | year, series, event_type, location |
| `tech_spec` | Object | fps, resolution, codec |
| `source_origin` | Object | nas_path, mam_system |

**Level 2: Segment** (논리적 구간 - 핸드)

| Field | Type | Description |
|-------|------|-------------|
| `segment_uuid` | UUID | Primary Key |
| `parent_asset_uuid` | UUID | Foreign Key → Asset |
| `time_in_sec` | Float | 시작 시간 (초) |
| `time_out_sec` | Float | 종료 시간 (초) |
| `game_type` | Enum | TOURNAMENT, CASH_GAME |
| `players` | List[PlayerInHand] | 플레이어별 핸드 정보 |
| `tags_action` | List[str] | 액션 태그 |
| `tags_emotion` | List[str] | 감정/편집 태그 |

### 3.3 PlayerInHand 구조 (v3.0 신규)

기존 `hand_matchup: "AA vs KK"` 방식에서 구조화된 형태로 개선:

```python
class PlayerInHand(BaseModel):
    """핸드 참여 플레이어 정보"""
    name: str                           # "Daniel Negreanu"
    hand: Optional[str] = None          # "AA", "KK" (홀카드)
    position: Optional[str] = None      # "BTN", "BB", "UTG"
    is_winner: bool = False             # 승자 여부
    chips_won: Optional[int] = None     # 획득 칩
```

---

## 4. 데이터 소스

### 4.1 지원 소스 타입

| Phase | Source Type | Library | Status |
|-------|-------------|---------|--------|
| **Phase 1** | CSV | pandas/csv | 설계 완료 |
| **Phase 1** | Excel (.xlsx/.xls) | openpyxl/pandas | 설계 완료 |
| **Phase 1** | JSON/JSONL | json | 설계 완료 |
| **Phase 2** | Google Sheets | google-api-client | 계획 |
| **Phase 2** | Iconik API | httpx | 계획 |
| **Phase 2** | CatDV XML | lxml | 계획 |

### 4.2 실제 소스 데이터

#### Google Sheets (분석 완료)

| Sheet | ID | Records | Description |
|-------|-----|---------|-------------|
| Archive Metadata | `1_RN_W_ZQclSZA0Iez6XniCXVtjkkd5HNZwiT6l-z6d4` | 38 | Circuit 시리즈 핸드 기록 |
| Iconik Metadata | `1pUMPKe-OsKc-Xd8lH1cP9ctJO4hj3keXY5RwNFp2Mtk` | 200+ | 메인 이벤트 상세 DB |

**소스 간 차이점**:

| 항목 | Archive Metadata | Iconik Metadata |
|------|---------------|----------------|
| **ID 방식** | 순번 (생성 필요) | UUID (그대로 사용) |
| **시간 형식** | 타임코드 (변환 필요) | 초/밀리초 (그대로 사용) |
| **이벤트 정보** | File Name에서 추출 | 별도 컬럼 (상세) |
| **태그 방식** | 다중 컬럼 | 쉼표 구분 문자열 |
| **상황 플래그** | 없음 | Boolean 컬럼 |

#### NAS 저장소 (2025-12-12 스캔 완료)

- **마운트**: `Z:\` / `\\10.10.100.122\docker\GGPNAs\`
- **총 파일 수**: 1,381개
- **파일 형식**: MP4(990) + MOV(269) + MXF(114) + 기타(8)

| 브랜드 | 파일 수 | 설명 |
|--------|---------|------|
| WSOP | 1,286 | Archive(545) + Bracelet(693) + Circuit(48) |
| PAD | 44 | S12(21) + S13(23) |
| GOG | 27 | E01~E12 에피소드 |
| GGMillions | 13 | Super High Roller FT |
| MPP | 11 | 2025 Cyprus |
| HCL | 0 | 폴더만 존재 (파일 없음) |

---

## 5. 완료된 작업

### 5.1 문서 작성

| 문서 | 위치 | 설명 |
|------|------|------|
| PRD-0001 | `prds/PRD-0001-MASTER-ORCHESTRATOR.md` | Master Orchestrator |
| PRD-0002 | `prds/PRD-0002-INGEST-AGENT.md` | Ingest Agent |
| PRD-0003 | `prds/PRD-0003-TRANSFORM-AGENT.md` | Transform Agent |
| PRD-0004 | `prds/PRD-0004-VALIDATE-AGENT.md` | Validate Agent |
| PRD-0005 | `prds/PRD-0005-EXPORT-AGENT.md` | Export Agent |
| PRD-0006 | `prds/PRD-0006-PROFILE-MANAGER.md` | Profile Manager |
| PRD-0007 | `prds/PRD-0007-UDM-SCHEMA.md` | UDM v1 (Deprecated) |
| PRD-0008 | `prds/PRD-0008-UDM-FINAL-SCHEMA.md` | **UDM v3.0 (현재)** |

### 5.2 코드 구현

#### UDM Schema (Pydantic V2)

| 파일 | 라인 수 | 내용 |
|------|---------|------|
| `src/models/udm.py` | 1,017 | 8 Enums, 10 Models |
| `src/models/__init__.py` | 76 | 모듈 익스포트 |

**Enums**:
- `Brand`, `EventType`, `AssetType`, `Location`
- `GameVariant`, `GameType`, `AllInStage`, `SegmentType`

**Models**:
- `EventContext`, `TechSpec`, `FileNameMeta`, `SourceOrigin`
- `SituationFlags`, `PlayerInHand`, `Segment`, `Asset`
- `UDMMetadata`, `UDMDocument`

**Utility Functions**:
- `parse_filename()` - 파일명에서 메타데이터 추출
- `generate_json_schema()` - JSON Schema 생성
- `infer_brand_from_path()` - 경로에서 브랜드 추론
- `infer_asset_type_from_path()` - 경로에서 에셋 타입 추론

#### Unit Tests

| 파일 | 내용 |
|------|------|
| `tests/test_udm.py` | 84개 테스트 케이스, 97% 커버리지 |
| `tests/conftest.py` | 30개 pytest 픽스처 |
| `tests/README.md` | 테스트 가이드 |

#### FastAPI Endpoints

| 디렉토리 | 파일 | 내용 |
|---------|------|------|
| `src/api/` | `main.py` | FastAPI 앱 진입점 |
| | `dependencies.py` | 페이지네이션, 정렬, DB 세션 |
| | `exceptions.py` | 커스텀 예외 |
| `src/api/routes/` | `assets.py` | Asset CRUD (5 endpoints) |
| | `segments.py` | Segment CRUD (5 endpoints) |
| | `search.py` | 검색 (3 endpoints) |
| | `export.py` | 내보내기 (3 endpoints) |
| | `stats.py` | 통계 (3 endpoints) |
| `src/api/schemas/` | 5개 파일 | Pydantic DTOs |

**총 19개 API 엔드포인트**

#### Dashboard UI Mockup

| 파일 | 내용 |
|------|------|
| `docs/UI_MOCKUP.md` | 1,078 라인, 4개 화면 설계 |
| `docs/API_DESIGN.md` | API 문서 |
| `docs/API_ARCHITECTURE.md` | 아키텍처 다이어그램 |

### 5.3 통계

| 항목 | 수치 |
|------|------|
| **총 파일 수** | 27개 |
| **총 라인 수** | 7,544 라인 |
| **테스트 커버리지** | 97% |
| **API 엔드포인트** | 19개 |

---

## 6. 발견된 이슈 및 수정사항

### 6.1 PRD-0008 수정

| 이슈 | 수정 내용 |
|------|----------|
| NAS 구조 오류 | 루트 레벨 + ARCHIVE 분리 → ARCHIVE만 (194폴더) |
| "핸드별 PK" 용어 | → "Segment 고유 식별자 (Primary Key)" |
| `hand_matchup` 문제 | "AA vs KK" → `PlayerInHand` 구조화 |

### 6.2 PRD 검토 결과 - 개선 필요 사항

| 영역 | 문제점 | 제안 |
|------|--------|------|
| 소스 명세 부재 | 각 소스별 컬럼 구조 미정의 | PRD-0009 작성 |
| 프로파일 예제 부재 | 실제 사용할 YAML 없음 | `profiles/` 디렉토리 구성 |
| MAM 스키마 부재 | Iconik/CatDV 출력 형식 미정의 | 상세 분석 필요 |

---

## 7. 기술 스택

| Layer | Technology |
|-------|------------|
| **Language** | Python 3.12+ |
| **Async** | asyncio |
| **Validation** | Pydantic V2 |
| **API** | FastAPI |
| **Testing** | pytest |
| **Config** | YAML |
| **File I/O** | aiofiles, pandas, openpyxl |

---

## 8. 다음 단계

### 8.1 즉시 필요

| 우선순위 | 작업 | 설명 |
|---------|------|------|
| 1 | **PRD-0009** | 소스 데이터 명세서 작성 |
| 2 | **profiles/** | 실제 프로파일 YAML 작성 |
| 3 | **DB 통합** | PostgreSQL + SQLAlchemy ORM |

### 8.2 Phase 3 계획

| 작업 | 설명 |
|------|------|
| Repository 패턴 | 데이터 액세스 추상화 |
| Service Layer | 비즈니스 로직 분리 |
| Alembic | 스키마 마이그레이션 |
| JWT 인증 | API 보안 |

---

## 9. 디렉토리 구조 (현재)

```
Archive_Converter/
├── docs/
│   ├── UI_MOCKUP.md
│   ├── API_DESIGN.md
│   ├── API_ARCHITECTURE.md
│   └── PROJECT_STATUS.md      # 현재 문서
├── prds/
│   ├── README.md
│   ├── PRD-0001 ~ PRD-0008
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   └── udm.py             # UDM 스키마 (1,017줄)
│   └── api/
│       ├── main.py
│       ├── dependencies.py
│       ├── exceptions.py
│       ├── routes/            # 5개 라우트 파일
│       └── schemas/           # 5개 스키마 파일
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # 30 픽스처
│   ├── test_udm.py            # 84 테스트
│   └── README.md
└── profiles/                   # (TODO: 생성 필요)
```

---

## 10. 참조 링크

| 리소스 | 위치 |
|--------|------|
| NAS 저장소 | `\\10.10.100.122\docker\GGPNAs\ARCHIVE\` |
| Archive Metadata | Google Sheets ID: `1_RN_W_ZQclSZA0Iez6XniCXVtjkkd5HNZwiT6l-z6d4` |
| Iconik Metadata | Google Sheets ID: `1pUMPKe-OsKc-Xd8lH1cP9ctJO4hj3keXY5RwNFp2Mtk` |
