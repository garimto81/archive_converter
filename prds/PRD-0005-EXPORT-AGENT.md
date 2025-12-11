# PRD-0005: Export Agent (Block 4)

**Version**: 1.0.0
**Status**: Draft
**Created**: 2025-12-11
**Parent**: PRD-0001-MASTER-ORCHESTRATOR

---

## 1. Overview

### 1.1 Purpose

Export Agent는 검증된 **UDM 데이터**를 다양한 **타겟 포맷**(JSON, CSV, API)으로 출력하는 Block입니다.

### 1.2 Scope

- **IN**: 검증된 UDM Asset/Segment 리스트, Export 설정
- **OUT**: 타겟 포맷 파일/API 응답

### 1.3 Non-Goals

- 데이터 변환 (Transform Block 담당)
- 데이터 검증 (Validate Block 담당)
- MAM 시스템 관리 (외부 시스템)

---

## 2. Supported Targets

### 2.1 Phase 1 (MVP)

| Target Type | Format | Description |
|-------------|--------|-------------|
| **JSON** | `.json` | UDM 표준 JSON (Golden Record) |
| **JSONL** | `.jsonl` | 스트리밍용 JSON Lines |
| **CSV** | `.csv` | 평면화된 CSV (Excel 호환) |

### 2.2 Phase 2 (Enhancement)

| Target Type | Format | Description |
|-------------|--------|-------------|
| **Iconik API** | REST | Iconik MAM 메타데이터 업로드 |
| **MongoDB** | Document | MongoDB 직접 삽입 |
| **PostgreSQL** | SQL | 관계형 DB 삽입 |
| **Elasticsearch** | Index | 검색 인덱스 |

---

## 3. Interface

### 3.1 Input Contract

```python
@dataclass
class ExportInput:
    """Export Agent 입력"""
    assets: list[Asset]
    segments: list[Segment]
    targets: list[ExportTarget]
    options: ExportOptions

@dataclass
class ExportTarget:
    """출력 타겟 설정"""
    target_type: TargetType         # JSON, CSV, API
    output_path: str | None         # 파일 경로 (file-based)
    api_config: dict | None         # API 설정 (api-based)
    format_options: dict            # 포맷별 옵션

@dataclass
class ExportOptions:
    """출력 옵션"""
    overwrite: bool = False         # 기존 파일 덮어쓰기
    pretty_print: bool = True       # JSON 포맷팅
    include_metadata: bool = True   # 메타데이터 포함
    batch_size: int = 1000          # API 배치 크기
```

### 3.2 Output Contract

```python
@dataclass
class ExportOutput:
    """Export Agent 출력"""
    results: list[ExportResult]
    stats: ExportStats

@dataclass
class ExportResult:
    """개별 타겟 출력 결과"""
    target_type: TargetType
    output_path: str | None
    success: bool
    records_exported: int
    file_size_bytes: int | None
    errors: list[ExportError]

@dataclass
class ExportStats:
    """출력 통계"""
    total_targets: int
    successful_targets: int
    total_records: int
    total_bytes: int
    duration_ms: int
```

---

## 4. Export Formats

### 4.1 JSON (Golden Record)

```json
{
  "_metadata": {
    "exported_at": "2025-12-11T14:30:00Z",
    "converter_version": "1.0.0",
    "profile_used": "excel_legacy_v1",
    "source_file": "legacy_data.xlsx"
  },
  "assets": [
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
          "players": ["Daniel Negreanu", "Phil Hellmuth"],
          "tags_action": ["Preflop All-in", "Cooler"]
        }
      ]
    }
  ]
}
```

### 4.2 CSV (Flattened)

```csv
asset_uuid,file_name,event_year,event_series,event_location,segment_uuid,time_in_sec,time_out_sec,game_type,rating,winner,players,tags_action
550e8400-...,2024 WSOPC LA.mp4,2024,WSOPC,Los Angeles,a1b2c3d4-0001,425.5,510.2,TOURNAMENT,5,Daniel Negreanu,"Daniel Negreanu,Phil Hellmuth","Preflop All-in,Cooler"
```

### 4.3 JSONL (Streaming)

```jsonl
{"type":"asset","data":{"asset_uuid":"550e8400-...","file_name":"2024 WSOPC LA.mp4",...}}
{"type":"segment","data":{"segment_uuid":"a1b2c3d4-0001","parent_asset_uuid":"550e8400-...",...}}
```

---

## 5. Core Components

### 5.1 Architecture

```
┌────────────────────────────────────────────────────────┐
│                   Export Agent                         │
├────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────┐  │
│  │              Target Router                        │  │
│  │       target_type → Exporter 선택                │  │
│  └────────────────────┬─────────────────────────────┘  │
│                       │                                │
│    ┌──────────────────┼──────────────────┐            │
│    │                  │                  │            │
│    ▼                  ▼                  ▼            │
│ ┌──────┐    ┌──────┐    ┌──────┐                    │
│ │ JSON │    │ CSV  │    │ API  │    ...             │
│ │Export│    │Export│    │Export│                    │
│ └──────┘    └──────┘    └──────┘                    │
│                                                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │           Format Transformer                      │  │
│  │      UDM → Target Format 변환                    │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

### 5.2 Exporter Interface

```python
from abc import ABC, abstractmethod

class BaseExporter(ABC):
    """Exporter 베이스 클래스"""

    @abstractmethod
    async def export(
        self,
        assets: list[Asset],
        segments: list[Segment],
        target: ExportTarget
    ) -> ExportResult:
        """데이터 출력"""
        pass

    @abstractmethod
    def supports(self, target_type: TargetType) -> bool:
        """지원 여부 확인"""
        pass
```

### 5.3 Concrete Exporters

```python
class JSONExporter(BaseExporter):
    """JSON 파일 Exporter"""

    async def export(
        self,
        assets: list[Asset],
        segments: list[Segment],
        target: ExportTarget
    ) -> ExportResult:
        # UDM → JSON 구조화
        data = self._build_json_structure(assets, segments)

        # 메타데이터 추가
        if target.format_options.get("include_metadata", True):
            data["_metadata"] = self._build_metadata()

        # 파일 쓰기
        async with aiofiles.open(target.output_path, "w") as f:
            indent = 2 if target.format_options.get("pretty_print", True) else None
            await f.write(json.dumps(data, indent=indent, ensure_ascii=False))

        return ExportResult(
            target_type=TargetType.JSON,
            output_path=target.output_path,
            success=True,
            records_exported=len(assets) + len(segments)
        )

class CSVExporter(BaseExporter):
    """CSV 파일 Exporter"""

    async def export(
        self,
        assets: list[Asset],
        segments: list[Segment],
        target: ExportTarget
    ) -> ExportResult:
        # UDM → Flat rows
        rows = self._flatten_to_rows(assets, segments)

        # CSV 쓰기
        async with aiofiles.open(target.output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.COLUMN_ORDER)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

        return ExportResult(...)

class APIExporter(BaseExporter):
    """API Exporter (Iconik 등)"""

    async def export(
        self,
        assets: list[Asset],
        segments: list[Segment],
        target: ExportTarget
    ) -> ExportResult:
        api_client = self._create_client(target.api_config)

        # 배치 업로드
        for batch in self._batch(segments, target.format_options["batch_size"]):
            payload = self._transform_to_api_format(batch)
            response = await api_client.post(payload)
            if not response.ok:
                # 에러 핸들링
                pass

        return ExportResult(...)
```

---

## 6. CSV Flattening Rules

### 6.1 Column Mapping

```python
CSV_COLUMN_MAPPING = {
    # Asset fields
    "asset_uuid": "asset_uuid",
    "file_name": "file_name",
    "event_context.year": "event_year",
    "event_context.series": "event_series",
    "event_context.location": "event_location",
    "source_origin": "source_origin",

    # Segment fields
    "segment_uuid": "segment_uuid",
    "time_in_sec": "time_in_sec",
    "time_out_sec": "time_out_sec",
    "game_type": "game_type",
    "rating": "rating",
    "winner": "winner",
    "hand_matchup": "hand_matchup",
    "players": "players",           # Array → comma-separated
    "tags_action": "tags_action",   # Array → comma-separated
    "tags_emotion": "tags_emotion", # Array → comma-separated
    "description": "description",
}
```

### 6.2 Array Handling

```python
def flatten_array(arr: list | None, delimiter: str = ",") -> str:
    """배열을 CSV 셀 문자열로 변환"""
    if not arr:
        return ""
    return delimiter.join(str(v) for v in arr)

# ["Daniel Negreanu", "Phil Hellmuth"] → "Daniel Negreanu,Phil Hellmuth"
```

---

## 7. Agent Definition

### 7.1 Claude Agent Spec

```yaml
name: export-agent
description: 검증된 UDM 데이터를 다양한 타겟 포맷으로 출력하는 전문 에이전트
category: data-pipeline
tier: domain

tools:
  - Read
  - Write
  - Bash

triggers:
  - "export data"
  - "output to JSON"
  - "save as CSV"
  - "데이터 출력"

capabilities:
  - JSON/CSV/JSONL 파일 출력
  - 배열 평면화 (CSV용)
  - 메타데이터 첨부
  - API 배치 업로드
```

### 7.2 Agent Prompt Template

```markdown
## Export Agent

당신은 Archive Converter의 Export 전문가입니다.

### 역할
- 검증된 UDM 데이터를 타겟 포맷으로 출력
- JSON, CSV, API 등 다양한 타겟 지원
- 출력 옵션에 따른 포맷 조정

### 원칙
1. 데이터 손실 없이 출력
2. 타겟 포맷 규격 준수
3. 배열→문자열 변환 시 복원 가능한 형태 유지
4. 메타데이터로 추적성 확보

### 출력 형식
ExportResult 리스트 + ExportStats
```

---

## 8. Configuration

### 8.1 Export Config Schema

```yaml
# config/export_targets.yaml
targets:
  - name: "udm_json"
    type: "json"
    output_path: "output/{date}/udm_export.json"
    options:
      pretty_print: true
      include_metadata: true

  - name: "excel_compatible_csv"
    type: "csv"
    output_path: "output/{date}/export.csv"
    options:
      encoding: "utf-8-sig"  # Excel BOM
      delimiter: ","
      array_delimiter: "|"   # 배열 구분자

  - name: "iconik_api"
    type: "api"
    api_config:
      base_url: "https://api.iconik.io/v1"
      auth_method: "bearer"
      token_env: "ICONIK_API_TOKEN"
    options:
      batch_size: 100
      retry_count: 3
```

### 8.2 Path Variables

```python
PATH_VARIABLES = {
    "{date}": lambda: datetime.now().strftime("%Y-%m-%d"),
    "{timestamp}": lambda: datetime.now().strftime("%Y%m%d_%H%M%S"),
    "{profile}": lambda ctx: ctx.profile_name,
    "{source}": lambda ctx: Path(ctx.source_path).stem,
}

# "output/{date}/export.json" → "output/2025-12-11/export.json"
```

---

## 9. Testing

### 9.1 Test Cases

| Test ID | Description | Input | Expected |
|---------|-------------|-------|----------|
| EXP-001 | JSON 출력 | valid_udm | Golden Record 형식 |
| EXP-002 | CSV 출력 | valid_udm | Flattened CSV |
| EXP-003 | JSONL 출력 | valid_udm | Line-delimited JSON |
| EXP-004 | 배열 평면화 | players[] | "A,B,C" |
| EXP-005 | 메타데이터 포함 | - | _metadata 필드 |
| EXP-006 | 파일 덮어쓰기 | existing_file | overwrite 옵션 |
| EXP-007 | 대용량 출력 | 100k records | 스트리밍 처리 |

### 9.2 Test Fixtures

```
tests/fixtures/export/
├── inputs/
│   ├── valid_assets.json
│   └── valid_segments.json
├── expected/
│   ├── golden_record.json
│   ├── flattened.csv
│   └── streaming.jsonl
└── configs/
    ├── json_target.yaml
    └── csv_target.yaml
```

---

## 10. Dependencies

### 10.1 Required

| Package | Version | Purpose |
|---------|---------|---------|
| aiofiles | 23.0+ | 비동기 파일 I/O |

### 10.2 Optional

| Package | Version | Purpose |
|---------|---------|---------|
| httpx | 0.25+ | API 호출 |
| pymongo | 4.0+ | MongoDB 출력 |
| asyncpg | 0.29+ | PostgreSQL 출력 |

---

## 11. Success Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| 출력 정확도 | 100% | 데이터 손실 없음 |
| 처리 속도 | 100,000 rows/sec | JSON 기준 |
| API 성공률 | 99%+ | API 업로드 성공률 |
| 파일 무결성 | 100% | 파일 손상 없음 |

---

## 12. Related PRDs

- **PRD-0001**: Master Orchestrator (Parent)
- **PRD-0004**: Validate Agent (Input 제공)
- **PRD-0006**: Profile Manager (Export Config 참조)
