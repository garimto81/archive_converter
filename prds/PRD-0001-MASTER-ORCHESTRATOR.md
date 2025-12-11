# PRD-0001: Archive Converter - Master Orchestrator

**Version**: 1.0.0
**Status**: Draft
**Created**: 2025-12-11
**Owner**: Archive Converter Team

---

## 1. Overview

### 1.1 Product Vision

Archive Converter는 다양한 소스(Excel, CSV, Legacy DB, MAM 시스템)에서 WSOP(World Series of Poker) 영상 메타데이터를 수집하여 **UDM(Universal Data Model)** 형식의 표준 JSON으로 변환하는 데이터 파이프라인입니다.

### 1.2 Problem Statement

- **데이터 파편화**: Excel, CatDV, Iconik 등 다양한 시스템에 메타데이터가 분산
- **포맷 비일관성**: 타임코드 형식, 플레이어 이름, 태그 체계가 소스마다 상이
- **MAM 종속성**: 특정 MAM 시스템에 종속되어 교체 시 데이터 이전 비용 발생
- **검색 불가**: 구조화되지 않은 데이터로 복잡한 쿼리 불가능

### 1.3 Solution

**5-Block Architecture** 기반의 모듈화된 데이터 파이프라인:

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR (This PRD)                      │
│         전체 파이프라인 조율, 상태 관리, 에러 핸들링              │
└─────────────────────┬───────────────────────────────────────────┘
                      │
    ┌─────────────────┼─────────────────┐
    │                 │                 │
    ▼                 ▼                 ▼
┌─────────┐    ┌──────────┐    ┌──────────┐
│ INGEST  │───▶│TRANSFORM │───▶│ VALIDATE │
│ Block 1 │    │ Block 2  │    │ Block 3  │
└─────────┘    └──────────┘    └──────────┘
                                    │
    ┌───────────────────────────────┤
    │                               │
    ▼                               ▼
┌─────────┐                  ┌──────────┐
│ EXPORT  │                  │ PROFILE  │
│ Block 4 │                  │ MANAGER  │
└─────────┘                  │ Block 5  │
                             └──────────┘
```

---

## 2. UDM (Universal Data Model)

### 2.1 설계 원칙

| 원칙 | 설명 |
|------|------|
| **Unique ID First** | 파일명/경로 대신 UUID/Hash 기반 식별 |
| **Time as Float** | 타임코드 대신 초(Seconds) 단위 저장 |
| **Tags as Arrays** | 복수 값은 컬럼 분리 대신 Array 사용 |

### 2.2 데이터 구조

#### Level 1: Asset Entity (물리적 파일)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `asset_uuid` | UUID | Yes | Primary Key (파일 Hash 기반) |
| `file_name` | String | Yes | 확장자 포함 파일명 |
| `file_path_rel` | String | No | NAS 루트 제외 상대 경로 |
| `event_context` | Object | Yes | `{ year, series, location }` |
| `tech_spec` | Object | No | `{ fps, resolution }` |
| `source_origin` | String | Yes | 데이터 출처 |

#### Level 2: Segment Entity (논리적 구간)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `segment_uuid` | UUID | Yes | Primary Key |
| `parent_asset_uuid` | UUID | Yes | Foreign Key → Asset |
| `time_in_sec` | Float | Yes | 시작 시간 (초, 소수점 3자리) |
| `time_out_sec` | Float | Yes | 종료 시간 |
| `game_type` | Enum | Yes | `TOURNAMENT` \| `CASH_GAME` |
| `rating` | Integer | No | 0-5 (별점) |
| `winner` | String | No | 승자 이름 (정규화됨) |
| `hand_matchup` | String | No | e.g., "AA vs KK" |
| `players` | Array | No | 참여 플레이어 리스트 |
| `tags_action` | Array | No | 액션 태그 |
| `tags_emotion` | Array | No | 감정/편집 태그 |
| `description` | String | No | 기타 메모 |

---

## 3. Block 구조

### 3.1 Block 목록

| Block | 담당 Agent | PRD | 역할 |
|-------|-----------|-----|------|
| Block 1 | `ingest-agent` | PRD-0002 | 다양한 소스에서 원본 데이터 수집 |
| Block 2 | `transform-agent` | PRD-0003 | Profile 기반 UDM 변환 |
| Block 3 | `validate-agent` | PRD-0004 | 스키마/비즈니스 규칙 검증 |
| Block 4 | `export-agent` | PRD-0005 | 타겟 시스템 포맷 출력 |
| Block 5 | `profile-manager` | PRD-0006 | 매핑 프로파일 관리 |

### 3.2 Block 간 통신

```python
# Message Contract
@dataclass
class PipelineMessage:
    message_id: str          # 메시지 고유 ID
    source_block: str        # 발신 Block
    target_block: str        # 수신 Block
    payload: dict            # 데이터 페이로드
    metadata: dict           # 처리 메타데이터
    timestamp: datetime      # 발신 시간
    correlation_id: str      # 파이프라인 추적 ID
```

### 3.3 독립성 원칙

각 Block은:
- **자체 상태 관리**: 내부 상태는 Block 내에서만 관리
- **인터페이스 계약**: 정의된 Input/Output 스키마만 준수
- **무상태 처리**: 가능한 stateless하게 설계
- **독립 배포 가능**: 다른 Block 변경 없이 업데이트 가능

---

## 4. Orchestrator 상세

### 4.1 책임

1. **파이프라인 초기화**: 설정 로드, Block 인스턴스 생성
2. **데이터 흐름 제어**: Block 간 메시지 라우팅
3. **상태 추적**: 각 Job의 진행 상황 모니터링
4. **에러 핸들링**: 실패 시 재시도, 롤백, 알림
5. **로깅/감사**: 모든 처리 과정 기록

### 4.2 핵심 인터페이스

```python
class Orchestrator:
    """파이프라인 오케스트레이터"""

    async def start_pipeline(
        self,
        source_config: SourceConfig,
        profile_name: str,
        export_targets: list[str]
    ) -> PipelineJob:
        """파이프라인 실행 시작"""
        pass

    async def get_job_status(self, job_id: str) -> JobStatus:
        """Job 상태 조회"""
        pass

    async def cancel_job(self, job_id: str) -> bool:
        """Job 취소"""
        pass

    async def retry_job(self, job_id: str, from_block: str) -> PipelineJob:
        """실패 지점부터 재시도"""
        pass
```

### 4.3 파이프라인 상태 머신

```
[INITIALIZED] → [INGESTING] → [TRANSFORMING] → [VALIDATING] → [EXPORTING] → [COMPLETED]
                    │              │               │              │
                    └──────────────┴───────────────┴──────────────┘
                                        │
                                        ▼
                                    [FAILED]
                                        │
                                        ▼
                                [RETRY_PENDING]
```

---

## 5. 기술 스택

### 5.1 Core

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Language | Python 3.12+ | 데이터 처리 생태계, 타입 힌트 |
| Async | asyncio | 비동기 파이프라인 처리 |
| Validation | Pydantic v2 | 스키마 검증, 직렬화 |
| Config | YAML/TOML | 프로파일 설정 |

### 5.2 Storage

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Intermediate | SQLite/JSON | 처리 중간 데이터 |
| Output | JSON | UDM 표준 포맷 |
| Profiles | YAML | 매핑 프로파일 |

### 5.3 Optional Integrations

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Queue | Redis/RabbitMQ | 대용량 처리 시 |
| Database | PostgreSQL/MongoDB | 영구 저장 시 |
| API | FastAPI | REST API 노출 시 |

---

## 6. 디렉토리 구조

```
Archive_Converter/
├── docs/
│   └── gemini.md              # UDM 설계 문서
├── prds/
│   ├── PRD-0001-MASTER-ORCHESTRATOR.md   # This file
│   ├── PRD-0002-INGEST-AGENT.md
│   ├── PRD-0003-TRANSFORM-AGENT.md
│   ├── PRD-0004-VALIDATE-AGENT.md
│   ├── PRD-0005-EXPORT-AGENT.md
│   └── PRD-0006-PROFILE-MANAGER.md
├── src/
│   ├── orchestrator/          # Orchestrator core
│   │   ├── __init__.py
│   │   ├── core.py            # Orchestrator class
│   │   ├── pipeline.py        # Pipeline management
│   │   └── models.py          # Shared models
│   ├── blocks/
│   │   ├── ingest/            # Block 1
│   │   ├── transform/         # Block 2
│   │   ├── validate/          # Block 3
│   │   ├── export/            # Block 4
│   │   └── profile/           # Block 5
│   └── common/
│       ├── schemas.py         # UDM schemas
│       ├── exceptions.py      # Custom exceptions
│       └── utils.py           # Utilities
├── profiles/                   # Mapping profiles
│   ├── excel_legacy_v1.yaml
│   ├── iconik_export.yaml
│   └── catdv_export.yaml
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── pyproject.toml
└── README.md
```

---

## 7. Success Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| **변환 정확도** | 99.5%+ | UDM 스키마 준수율 |
| **처리 속도** | 1000 rows/sec | 단일 스레드 기준 |
| **프로파일 재사용** | 90%+ | 신규 소스에 기존 프로파일 활용률 |
| **에러 복구율** | 95%+ | 자동 재시도 성공률 |

---

## 8. Milestones

| Phase | Scope | Deliverables |
|-------|-------|--------------|
| **Phase 1** | Core Infrastructure | Orchestrator, UDM Schema, Block Interface |
| **Phase 2** | Ingest + Transform | CSV/Excel Ingest, Profile-based Transform |
| **Phase 3** | Validate + Export | Schema Validation, JSON/CSV Export |
| **Phase 4** | Integration | Full Pipeline, Error Handling |
| **Phase 5** | Enhancement | API, Batch Processing, Monitoring |

---

## 9. Related PRDs

- **PRD-0002**: Ingest Agent (Block 1)
- **PRD-0003**: Transform Agent (Block 2)
- **PRD-0004**: Validate Agent (Block 3)
- **PRD-0005**: Export Agent (Block 4)
- **PRD-0006**: Profile Manager (Block 5)

---

## 10. Appendix

### A. UDM JSON Example (Golden Record)

```json
{
  "asset_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "file_name": "2024 WSOPC LA - Main Event Day2.mp4",
  "event_context": {
    "year": 2024,
    "series": "WSOPC",
    "location": "Los Angeles"
  },
  "segments": [
    {
      "segment_uuid": "a1b2c3d4-0001",
      "time_in_sec": 425.5,
      "time_out_sec": 510.2,
      "game_type": "TOURNAMENT",
      "rating": 5,
      "winner": "Daniel Negreanu",
      "hand_matchup": "AA vs KK",
      "players": ["Daniel Negreanu", "Phil Hellmuth", "Unknown Player"],
      "tags_action": ["Preflop All-in", "Cooler"],
      "tags_emotion": ["Excitement", "Suckout"]
    }
  ]
}
```

### B. Glossary

| Term | Definition |
|------|------------|
| **UDM** | Universal Data Model - 시스템 독립적 표준 데이터 모델 |
| **Asset** | 물리적 영상 파일 단위 |
| **Segment** | Asset 내 논리적 구간 (핸드) |
| **Profile** | 소스 포맷 → UDM 매핑 설정 |
| **MAM** | Media Asset Management 시스템 |
