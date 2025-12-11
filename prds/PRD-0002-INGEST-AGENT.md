# PRD-0002: Ingest Agent (Block 1)

**Version**: 1.0.0
**Status**: Draft
**Created**: 2025-12-11
**Parent**: PRD-0001-MASTER-ORCHESTRATOR

---

## 1. Overview

### 1.1 Purpose

Ingest Agent는 다양한 소스 포맷(CSV, Excel, JSON, API)에서 원본 데이터를 읽어 **Raw Record** 형태로 추출하는 Block입니다.

### 1.2 Scope

- **IN**: 소스 파일/API endpoint, 소스 타입 정보
- **OUT**: Raw Record 리스트 (원본 데이터 그대로)

### 1.3 Non-Goals

- 데이터 변환/정규화 (Transform Block 담당)
- 스키마 검증 (Validate Block 담당)
- 프로파일 관리 (Profile Manager 담당)

---

## 2. Supported Sources

### 2.1 Phase 1 (MVP)

| Source Type | Extension | Library |
|-------------|-----------|---------|
| CSV | `.csv` | pandas / csv |
| Excel | `.xlsx`, `.xls` | openpyxl / pandas |
| JSON | `.json` | json |
| JSONL | `.jsonl` | json (streaming) |

### 2.2 Phase 2 (Enhancement)

| Source Type | Description | Library |
|-------------|-------------|---------|
| Google Sheets | API 연동 | google-api-client |
| Iconik API | MAM Export | httpx |
| CatDV XML | Legacy MAM | lxml |
| SQLite DB | Embedded DB | sqlite3 |

---

## 3. Interface

### 3.1 Input Contract

```python
@dataclass
class IngestInput:
    """Ingest Agent 입력"""
    source_type: SourceType        # CSV, EXCEL, JSON, API
    source_path: str | None        # 파일 경로 (file-based)
    source_config: dict | None     # API 설정 (api-based)
    encoding: str = "utf-8"        # 문자 인코딩
    sheet_name: str | None = None  # Excel 시트명
    skip_rows: int = 0             # 건너뛸 행 수
    max_rows: int | None = None    # 최대 행 수 (테스트용)
```

### 3.2 Output Contract

```python
@dataclass
class IngestOutput:
    """Ingest Agent 출력"""
    records: list[RawRecord]       # 원본 레코드 리스트
    source_info: SourceInfo        # 소스 메타데이터
    stats: IngestStats             # 처리 통계

@dataclass
class RawRecord:
    """원본 레코드 (변환 전)"""
    row_index: int                 # 원본 행 번호
    raw_data: dict[str, Any]       # 컬럼명: 값 매핑
    source_hash: str               # 레코드 해시 (중복 검출용)

@dataclass
class SourceInfo:
    """소스 메타데이터"""
    source_type: SourceType
    source_path: str
    column_names: list[str]
    total_rows: int
    detected_encoding: str
    file_hash: str | None          # 파일 전체 해시

@dataclass
class IngestStats:
    """처리 통계"""
    total_rows: int
    processed_rows: int
    skipped_rows: int
    error_rows: int
    duration_ms: int
```

---

## 4. Core Components

### 4.1 Architecture

```
┌────────────────────────────────────────────────┐
│               Ingest Agent                     │
├────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────┐  │
│  │           Source Router                   │  │
│  │    source_type → Reader 선택             │  │
│  └────────────────┬─────────────────────────┘  │
│                   │                            │
│    ┌──────────────┼──────────────┐            │
│    │              │              │            │
│    ▼              ▼              ▼            │
│ ┌──────┐    ┌──────┐    ┌──────┐            │
│ │ CSV  │    │Excel │    │ JSON │   ...       │
│ │Reader│    │Reader│    │Reader│            │
│ └──┬───┘    └──┬───┘    └──┬───┘            │
│    │           │           │                 │
│    └───────────┼───────────┘                 │
│                │                             │
│                ▼                             │
│  ┌──────────────────────────────────────────┐  │
│  │         Record Normalizer                 │  │
│  │    Column Names, Data Types 정리         │  │
│  └──────────────────────────────────────────┘  │
└────────────────────────────────────────────────┘
```

### 4.2 Reader Interface

```python
from abc import ABC, abstractmethod

class BaseReader(ABC):
    """소스 Reader 베이스 클래스"""

    @abstractmethod
    async def read(self, config: IngestInput) -> AsyncIterator[RawRecord]:
        """원본 데이터 스트리밍 읽기"""
        pass

    @abstractmethod
    async def get_source_info(self, config: IngestInput) -> SourceInfo:
        """소스 메타데이터 추출"""
        pass

    @abstractmethod
    def supports(self, source_type: SourceType) -> bool:
        """지원 여부 확인"""
        pass
```

### 4.3 Concrete Readers

```python
class CSVReader(BaseReader):
    """CSV 파일 Reader"""

    async def read(self, config: IngestInput) -> AsyncIterator[RawRecord]:
        # pandas or csv module
        pass

class ExcelReader(BaseReader):
    """Excel 파일 Reader"""

    async def read(self, config: IngestInput) -> AsyncIterator[RawRecord]:
        # openpyxl for streaming
        pass

class JSONReader(BaseReader):
    """JSON/JSONL 파일 Reader"""

    async def read(self, config: IngestInput) -> AsyncIterator[RawRecord]:
        # json module, JSONL은 line-by-line
        pass
```

---

## 5. Processing Logic

### 5.1 Flow

```
1. Source Validation
   └─ 파일 존재 확인, 접근 권한 체크

2. Encoding Detection
   └─ chardet로 자동 감지 또는 config 사용

3. Header Extraction
   └─ 컬럼명 추출, 정규화 (trim, lowercase)

4. Row Iteration
   └─ 스트리밍 방식으로 행 단위 처리

5. Record Creation
   └─ RawRecord 생성, 해시 계산

6. Stats Collection
   └─ 처리 통계 집계
```

### 5.2 Error Handling

| Error Type | Handling | Recovery |
|------------|----------|----------|
| FileNotFound | 즉시 실패 | 재시도 불가 |
| EncodingError | 대체 인코딩 시도 | utf-8 → cp949 → latin-1 |
| MalformedRow | 스킵 + 로깅 | 계속 처리 |
| MemoryError | 청크 사이즈 축소 | 재시도 |

### 5.3 Large File Handling

```python
# Streaming 처리 (메모리 효율)
CHUNK_SIZE = 10000  # rows per chunk

async def read_large_file(path: str) -> AsyncIterator[list[RawRecord]]:
    chunk = []
    async for record in reader.read(config):
        chunk.append(record)
        if len(chunk) >= CHUNK_SIZE:
            yield chunk
            chunk = []
    if chunk:
        yield chunk
```

---

## 6. Agent Definition

### 6.1 Claude Agent Spec

```yaml
name: ingest-agent
description: 다양한 소스에서 원본 데이터를 추출하는 전문 에이전트
category: data-pipeline
tier: domain

tools:
  - Read
  - Grep
  - Bash
  - Write

triggers:
  - "ingest data from"
  - "read CSV"
  - "import Excel"
  - "데이터 수집"

capabilities:
  - CSV/Excel/JSON 파일 파싱
  - 인코딩 자동 감지
  - 스트리밍 대용량 처리
  - 소스 메타데이터 추출
```

### 6.2 Agent Prompt Template

```markdown
## Ingest Agent

당신은 Archive Converter의 Ingest 전문가입니다.

### 역할
- 다양한 소스(CSV, Excel, JSON)에서 원본 데이터 추출
- 인코딩 문제 해결
- 소스 메타데이터 분석

### 원칙
1. 데이터 변환하지 않음 (Transform Block 담당)
2. 원본 값 그대로 유지
3. 스트리밍 방식으로 메모리 효율적 처리

### 출력 형식
RawRecord 리스트 + SourceInfo + IngestStats
```

---

## 7. Configuration

### 7.1 Source Config Schema

```yaml
# profiles/sources/excel_legacy.yaml
source:
  type: excel
  options:
    sheet_name: "Hand Data"
    skip_rows: 2
    header_row: 3
    encoding: utf-8
    date_columns:
      - "Date"
      - "Tournament Date"
    numeric_columns:
      - "Rating"
      - "Pot Size"
```

### 7.2 Default Settings

```python
DEFAULT_CONFIG = {
    "encoding": "utf-8",
    "chunk_size": 10000,
    "max_errors": 100,
    "retry_count": 3,
    "timeout_seconds": 300,
}
```

---

## 8. Testing

### 8.1 Test Cases

| Test ID | Description | Input | Expected |
|---------|-------------|-------|----------|
| ING-001 | 기본 CSV 읽기 | valid.csv | RawRecords 반환 |
| ING-002 | Excel 멀티시트 | multi.xlsx | 지정 시트만 |
| ING-003 | 인코딩 감지 | cp949.csv | 자동 감지 |
| ING-004 | 대용량 파일 | 100MB.csv | 스트리밍 처리 |
| ING-005 | 잘못된 행 | malformed.csv | 스킵 + 로깅 |

### 8.2 Test Fixtures

```
tests/fixtures/ingest/
├── valid_simple.csv
├── valid_unicode.csv
├── valid_large.csv
├── excel_single_sheet.xlsx
├── excel_multi_sheet.xlsx
├── json_array.json
├── jsonl_stream.jsonl
├── malformed_rows.csv
└── encoding_cp949.csv
```

---

## 9. Dependencies

### 9.1 Required

| Package | Version | Purpose |
|---------|---------|---------|
| pandas | 2.0+ | CSV/Excel 처리 |
| openpyxl | 3.1+ | Excel 스트리밍 |
| chardet | 5.0+ | 인코딩 감지 |
| aiofiles | 23.0+ | 비동기 파일 I/O |

### 9.2 Optional

| Package | Version | Purpose |
|---------|---------|---------|
| google-api-python-client | 2.0+ | Google Sheets |
| httpx | 0.25+ | API 호출 |
| lxml | 5.0+ | XML 파싱 |

---

## 10. Success Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| 처리 속도 | 50,000 rows/sec | CSV 기준 |
| 메모리 사용 | < 500MB | 100MB 파일 처리 시 |
| 에러율 | < 0.1% | 정상 파일 기준 |
| 인코딩 감지율 | 99%+ | 자동 감지 정확도 |

---

## 11. Related PRDs

- **PRD-0001**: Master Orchestrator (Parent)
- **PRD-0003**: Transform Agent (Output 전달)
- **PRD-0006**: Profile Manager (Source Config 참조)
