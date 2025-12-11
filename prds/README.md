# Archive Converter PRD Index

**Version**: 1.0.0
**Last Updated**: 2025-12-11

---

## Overview

Archive Converter는 WSOP(World Series of Poker) 영상 메타데이터를 다양한 소스에서 수집하여 **UDM(Universal Data Model)** 형식으로 변환하는 데이터 파이프라인입니다.

---

## Architecture

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
│PRD-0002 │    │ PRD-0003 │    │ PRD-0004 │
└─────────┘    └──────────┘    └──────────┘
                                    │
    ┌───────────────────────────────┤
    │                               │
    ▼                               ▼
┌─────────┐                  ┌──────────┐
│ EXPORT  │                  │ PROFILE  │
│PRD-0005 │                  │ MANAGER  │
└─────────┘                  │ PRD-0006 │
                             └──────────┘
```

---

## PRD Documents

| PRD | Block | Agent | Description |
|-----|-------|-------|-------------|
| [PRD-0001](./PRD-0001-MASTER-ORCHESTRATOR.md) | Master | `orchestrator` | 전체 파이프라인 조율, UDM 정의 |
| [PRD-0002](./PRD-0002-INGEST-AGENT.md) | Block 1 | `ingest-agent` | CSV/Excel/JSON 데이터 수집 |
| [PRD-0003](./PRD-0003-TRANSFORM-AGENT.md) | Block 2 | `transform-agent` | Profile 기반 UDM 변환 |
| [PRD-0004](./PRD-0004-VALIDATE-AGENT.md) | Block 3 | `validate-agent` | 스키마/비즈니스 규칙 검증 |
| [PRD-0005](./PRD-0005-EXPORT-AGENT.md) | Block 4 | `export-agent` | JSON/CSV/API 출력 |
| [PRD-0006](./PRD-0006-PROFILE-MANAGER.md) | Block 5 | `profile-manager` | 매핑 프로파일 관리 |
| [PRD-0007](./PRD-0007-UDM-SCHEMA.md) | Schema | - | UDM 스키마 v1 (Deprecated) |
| [PRD-0008](./PRD-0008-UDM-FINAL-SCHEMA.md) | Schema | - | **UDM 최종 스키마** ✅ (gemini.md + 포커 확장) |
| [PRD-0009](./PRD-0009-SOURCE-DATA-SPEC.md) | Data Spec | - | **소스 데이터 명세** ✅ (Google Sheets, NAS, MAM) |

---

## Data Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   SOURCE     │     │   RAW        │     │   UDM        │
│   (CSV/Excel)│────▶│   RECORDS    │────▶│   (JSON)     │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │
       │                    │                    │
    INGEST              TRANSFORM            VALIDATE
    (Block 1)           (Block 2)            (Block 3)
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │   OUTPUT     │
                                          │   (JSON/CSV) │
                                          └──────────────┘
                                                 │
                                              EXPORT
                                              (Block 4)
```

---

## UDM (Universal Data Model)

### 설계 원칙

| 원칙 | 설명 |
|------|------|
| **Unique ID First** | UUID/Hash 기반 식별 |
| **Time as Float** | 타임코드 대신 초(Seconds) 단위 |
| **Tags as Arrays** | 복수 값은 Array로 저장 |

### 데이터 구조

**Level 1: Asset** (물리적 파일)
- `asset_uuid`, `file_name`, `event_context`, `tech_spec`, `source_origin`

**Level 2: Segment** (논리적 구간 - 핸드)
- `segment_uuid`, `parent_asset_uuid`, `time_in_sec`, `time_out_sec`
- `game_type`, `rating`, `winner`, `players[]`, `tags_action[]`, `tags_emotion[]`

---

## Block 독립성 원칙

각 Block은:

1. **자체 상태 관리**: 내부 상태는 Block 내에서만 관리
2. **인터페이스 계약**: 정의된 Input/Output 스키마만 준수
3. **무상태 처리**: 가능한 stateless하게 설계
4. **독립 배포 가능**: 다른 Block 변경 없이 업데이트 가능

### Block 간 통신

```python
@dataclass
class PipelineMessage:
    message_id: str          # 메시지 고유 ID
    source_block: str        # 발신 Block
    target_block: str        # 수신 Block
    payload: dict            # 데이터 페이로드
    correlation_id: str      # 파이프라인 추적 ID
```

---

## Agent Summary

| Agent | Tools | Triggers |
|-------|-------|----------|
| `ingest-agent` | Read, Grep, Bash | "ingest", "read CSV", "import Excel" |
| `transform-agent` | Read, Write, Edit | "transform", "convert to UDM", "apply profile" |
| `validate-agent` | Read, Grep, Write | "validate", "check UDM", "verify schema" |
| `export-agent` | Read, Write, Bash | "export", "output to JSON", "save as CSV" |
| `profile-manager` | Read, Write, Edit, Glob | "create profile", "edit mapping", "add player" |

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.12+ |
| **Async** | asyncio |
| **Validation** | Pydantic v2 |
| **Config** | YAML |
| **File I/O** | aiofiles, pandas, openpyxl |

---

## Implementation Phases

| Phase | Scope | PRDs |
|-------|-------|------|
| **Phase 1** | Core Infrastructure | PRD-0001 (Orchestrator, UDM Schema) |
| **Phase 2** | Ingest + Transform | PRD-0002, PRD-0003 |
| **Phase 3** | Validate + Export | PRD-0004, PRD-0005 |
| **Phase 4** | Profile Manager | PRD-0006 |
| **Phase 5** | Integration & API | All PRDs |

---

## Quick Start (향후)

```bash
# 설치
pip install archive-converter

# 기본 사용
archive-converter run --source data.xlsx --profile wsop_legacy_v1

# 프로파일 생성
archive-converter profile suggest --source new_data.csv --name my_profile

# 검증만 실행
archive-converter validate --input udm_data.json
```

---

## Related Documents

| Document | Location | Description |
|----------|----------|-------------|
| UDM 설계 문서 | `docs/gemini.md` | 원본 UDM 설계 사양 |
| 프로파일 예제 | `profiles/` | 매핑 프로파일 YAML |
| 테스트 데이터 | `tests/fixtures/` | 테스트용 샘플 데이터 |

---

## Source Data References

실제 분석에 사용된 Google Sheets:

| Sheet | ID | Records | Description |
|-------|-----|---------|-------------|
| WSOP Circuit 2024 | `1_RN_W_ZQclSZA0Iez6XniCXVtjkkd5HNZwiT6l-z6d4` | 38 | Circuit 시리즈 핸드 기록 |
| WSOP Database | `1pUMPKe-OsKc-Xd8lH1cP9ctJO4hj3keXY5RwNFp2Mtk` | 200+ | 메인 이벤트 상세 DB |

### 소스 간 차이점

| 항목 | Circuit Sheet | Database Sheet |
|------|---------------|----------------|
| **ID 방식** | 순번 (생성 필요) | UUID (그대로 사용) |
| **시간 형식** | 타임코드 (변환 필요) | 초/밀리초 (그대로 사용) |
| **이벤트 정보** | File Name에서 추출 | 별도 컬럼 (상세) |
| **태그 방식** | 다중 컬럼 | 쉼표 구분 문자열 |
| **상황 플래그** | 없음 | Boolean 컬럼 |
