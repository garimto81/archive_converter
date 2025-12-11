# PRD-0003: Transform Agent (Block 2)

**Version**: 1.0.0
**Status**: Draft
**Created**: 2025-12-11
**Parent**: PRD-0001-MASTER-ORCHESTRATOR

---

## 1. Overview

### 1.1 Purpose

Transform Agent는 Ingest Agent로부터 받은 **Raw Record**를 **Profile 설정**에 따라 **UDM(Universal Data Model)** 형식으로 변환하는 Block입니다.

### 1.2 Scope

- **IN**: Raw Record 리스트, Profile 설정
- **OUT**: UDM Asset/Segment 리스트

### 1.3 Non-Goals

- 원본 데이터 읽기 (Ingest Block 담당)
- 최종 스키마 검증 (Validate Block 담당)
- 프로파일 생성/수정 (Profile Manager 담당)

---

## 2. Transformation Types

### 2.1 Field Mapping

| Transform Type | Description | Example |
|----------------|-------------|---------|
| **Direct** | 1:1 컬럼 매핑 | `file_name` → `file_name` |
| **Rename** | 컬럼명 변경 | `Video Title` → `file_name` |
| **Combine** | 다중 컬럼 병합 | `Year` + `Series` → `event_context` |
| **Split** | 단일 컬럼 분리 | `"AA vs KK"` → `players[]` |
| **Default** | 기본값 적용 | null → `"Unknown"` |
| **Constant** | 고정값 | - → `"Legacy_Excel_v1"` |

### 2.2 Value Transformation

| Transform Type | Description | Example |
|----------------|-------------|---------|
| **Timecode→Seconds** | TC를 초로 변환 | `"01:00:00:00"` → `3600.0` |
| **Name Normalize** | 이름 정규화 | `"D. Negreanu"` → `"Daniel Negreanu"` |
| **Array Parse** | 문자열→배열 | `"A, B, C"` → `["A", "B", "C"]` |
| **Enum Map** | 값 매핑 | `"T"` → `"TOURNAMENT"` |
| **Date Parse** | 날짜 파싱 | `"2024-01-15"` → `2024` |
| **Number Parse** | 숫자 파싱 | `"4.5"` → `4.5` |

---

## 3. Interface

### 3.1 Input Contract

```python
@dataclass
class TransformInput:
    """Transform Agent 입력"""
    raw_records: list[RawRecord]   # Ingest 출력
    profile: TransformProfile      # 매핑 프로파일
    options: TransformOptions      # 변환 옵션

@dataclass
class TransformOptions:
    """변환 옵션"""
    strict_mode: bool = False      # 엄격 모드 (실패 시 중단)
    generate_uuids: bool = True    # UUID 자동 생성
    normalize_names: bool = True   # 이름 정규화 활성화
    fallback_values: dict = None   # 필드별 기본값
```

### 3.2 Output Contract

```python
@dataclass
class TransformOutput:
    """Transform Agent 출력"""
    assets: list[Asset]            # UDM Asset 리스트
    segments: list[Segment]        # UDM Segment 리스트
    errors: list[TransformError]   # 변환 에러 리스트
    stats: TransformStats          # 처리 통계

@dataclass
class TransformError:
    """변환 에러"""
    row_index: int
    field_name: str
    error_type: str
    original_value: Any
    error_message: str

@dataclass
class TransformStats:
    """처리 통계"""
    total_records: int
    successful_assets: int
    successful_segments: int
    failed_records: int
    duration_ms: int
```

---

## 4. Profile Schema

### 4.1 Profile Structure

```yaml
# profiles/mappings/excel_legacy_v1.yaml
profile:
  name: "excel_legacy_v1"
  version: "1.0.0"
  source_type: "Legacy Excel"
  description: "기존 Excel 시트 매핑 프로파일"

asset_mapping:
  asset_uuid:
    type: "generate"
    strategy: "file_hash"           # file_hash | uuid4 | content_hash

  file_name:
    type: "direct"
    source_column: "File Name"

  event_context:
    type: "object"
    fields:
      year:
        type: "extract"
        source_column: "Event Name"
        pattern: "\\b(20\\d{2})\\b"
        transform: "to_int"
      series:
        type: "map"
        source_column: "Series"
        mapping:
          "WSOP": "WSOP"
          "World Series": "WSOP"
          "WSOPC": "WSOPC"
          "Circuit": "WSOPC"
      location:
        type: "direct"
        source_column: "Location"

segment_mapping:
  segment_uuid:
    type: "generate"
    strategy: "uuid4"

  time_in_sec:
    type: "timecode"
    source_column: "TC In"
    fps: 29.97
    fallback: 0.0

  time_out_sec:
    type: "timecode"
    source_column: "TC Out"
    fps: 29.97

  game_type:
    type: "enum"
    source_column: "Type"
    mapping:
      "T": "TOURNAMENT"
      "Tournament": "TOURNAMENT"
      "C": "CASH_GAME"
      "Cash": "CASH_GAME"
    default: "TOURNAMENT"

  players:
    type: "array"
    source_columns:
      - "Player 1"
      - "Player 2"
      - "Player 3"
    normalize: true
    remove_empty: true

  tags_action:
    type: "split"
    source_column: "Tags"
    delimiter: ","
    trim: true
```

### 4.2 Transform Types Detail

```python
class TransformType(Enum):
    DIRECT = "direct"           # 직접 매핑
    RENAME = "rename"           # 컬럼명 변경
    GENERATE = "generate"       # 값 생성 (UUID 등)
    MAP = "map"                 # 값 매핑
    ENUM = "enum"               # Enum 변환
    TIMECODE = "timecode"       # 타임코드 → 초
    ARRAY = "array"             # 배열 생성
    SPLIT = "split"             # 문자열 분리
    EXTRACT = "extract"         # 정규식 추출
    OBJECT = "object"           # 중첩 객체 생성
    CONSTANT = "constant"       # 고정값
    CONCAT = "concat"           # 문자열 연결
```

---

## 5. Core Components

### 5.1 Architecture

```
┌────────────────────────────────────────────────────────┐
│                  Transform Agent                       │
├────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────┐  │
│  │              Profile Loader                       │  │
│  │         YAML → TransformProfile                  │  │
│  └────────────────────┬─────────────────────────────┘  │
│                       │                                │
│                       ▼                                │
│  ┌──────────────────────────────────────────────────┐  │
│  │           Transform Engine                        │  │
│  │    RawRecord + Profile → UDM                     │  │
│  └────────────────────┬─────────────────────────────┘  │
│                       │                                │
│    ┌──────────────────┼──────────────────┐            │
│    │                  │                  │            │
│    ▼                  ▼                  ▼            │
│ ┌────────┐    ┌────────────┐    ┌────────────┐       │
│ │Field   │    │Value       │    │Name        │       │
│ │Mapper  │    │Transformer │    │Normalizer  │       │
│ └────────┘    └────────────┘    └────────────┘       │
│                                                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │           Asset/Segment Builder                   │  │
│  │       변환된 필드 → UDM 객체                      │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

### 5.2 Transform Engine

```python
class TransformEngine:
    """변환 엔진 코어"""

    def __init__(self, profile: TransformProfile):
        self.profile = profile
        self.field_mapper = FieldMapper()
        self.value_transformer = ValueTransformer()
        self.name_normalizer = NameNormalizer()

    async def transform_record(
        self,
        raw: RawRecord
    ) -> tuple[Asset | None, list[Segment], list[TransformError]]:
        """단일 레코드 변환"""
        errors = []

        # Asset 필드 변환
        asset_data = {}
        for field, config in self.profile.asset_mapping.items():
            try:
                value = self._transform_field(raw, config)
                asset_data[field] = value
            except TransformError as e:
                errors.append(e)

        # Segment 필드 변환
        segment_data = {}
        for field, config in self.profile.segment_mapping.items():
            try:
                value = self._transform_field(raw, config)
                segment_data[field] = value
            except TransformError as e:
                errors.append(e)

        # UDM 객체 생성
        asset = Asset(**asset_data) if asset_data else None
        segment = Segment(**segment_data, parent_asset_uuid=asset.asset_uuid)

        return asset, [segment], errors
```

### 5.3 Value Transformers

```python
class ValueTransformer:
    """값 변환기"""

    def timecode_to_seconds(
        self,
        timecode: str,
        fps: float = 29.97
    ) -> float:
        """타임코드를 초로 변환"""
        # "01:00:00:00" → 3600.0
        parts = timecode.split(":")
        h, m, s, f = map(int, parts)
        return h * 3600 + m * 60 + s + f / fps

    def parse_array(
        self,
        value: str,
        delimiter: str = ","
    ) -> list[str]:
        """문자열을 배열로 분리"""
        return [v.strip() for v in value.split(delimiter) if v.strip()]

    def normalize_name(self, name: str) -> str:
        """플레이어 이름 정규화"""
        # Name Normalization Dictionary 참조
        return self.name_dict.get(name.lower(), name)
```

---

## 6. Name Normalization

### 6.1 Dictionary Structure

```yaml
# profiles/dictionaries/player_names.yaml
normalizations:
  # Key: 정규화된 이름, Values: 알려진 변형
  "Daniel Negreanu":
    - "D. Negreanu"
    - "Negreanu"
    - "Kid Poker"
    - "DNegs"

  "Phil Hellmuth":
    - "P. Hellmuth"
    - "Hellmuth"
    - "Poker Brat"

  "Phil Ivey":
    - "P. Ivey"
    - "Ivey"
    - "Tiger Woods of Poker"

rules:
  # 자동 정규화 규칙
  - pattern: "^(\\w)\\.\\s*(\\w+)$"
    action: "expand_initial"
    lookup: true
```

### 6.2 Fuzzy Matching

```python
class NameNormalizer:
    """이름 정규화기"""

    def __init__(self, dictionary_path: str):
        self.dictionary = self._load_dictionary(dictionary_path)
        self.fuzzy_threshold = 0.85

    def normalize(self, name: str) -> str:
        # 1. Exact match
        if name in self.exact_lookup:
            return self.exact_lookup[name]

        # 2. Fuzzy match
        best_match, score = self._fuzzy_search(name)
        if score >= self.fuzzy_threshold:
            return best_match

        # 3. Return original (with title case)
        return name.title()
```

---

## 7. Agent Definition

### 7.1 Claude Agent Spec

```yaml
name: transform-agent
description: Profile 기반으로 원본 데이터를 UDM으로 변환하는 전문 에이전트
category: data-pipeline
tier: domain

tools:
  - Read
  - Write
  - Edit
  - Grep

triggers:
  - "transform data"
  - "convert to UDM"
  - "apply profile"
  - "데이터 변환"

capabilities:
  - Profile 기반 필드 매핑
  - 타임코드/날짜/숫자 파싱
  - 이름 정규화
  - 배열/객체 변환
```

### 7.2 Agent Prompt Template

```markdown
## Transform Agent

당신은 Archive Converter의 Transform 전문가입니다.

### 역할
- Profile 설정에 따라 Raw Record를 UDM으로 변환
- 타임코드, 이름, 배열 등 값 변환 처리
- 변환 에러 기록 및 리포팅

### 원칙
1. Profile 설정을 엄격히 준수
2. 원본 값 손실 최소화
3. 변환 실패 시 명확한 에러 메시지
4. 이름 정규화로 데이터 일관성 유지

### 출력 형식
Asset 리스트 + Segment 리스트 + TransformErrors + Stats
```

---

## 8. Testing

### 8.1 Test Cases

| Test ID | Description | Input | Expected |
|---------|-------------|-------|----------|
| TRF-001 | 기본 직접 매핑 | simple_profile | 1:1 매핑 |
| TRF-002 | 타임코드 변환 | "01:00:00:00" | 3600.0 |
| TRF-003 | 이름 정규화 | "D. Negreanu" | "Daniel Negreanu" |
| TRF-004 | 배열 파싱 | "A, B, C" | ["A", "B", "C"] |
| TRF-005 | Enum 매핑 | "T" | "TOURNAMENT" |
| TRF-006 | 객체 생성 | year+series+location | event_context |
| TRF-007 | 기본값 적용 | null | default value |
| TRF-008 | UUID 생성 | - | valid UUID |

### 8.2 Test Fixtures

```
tests/fixtures/transform/
├── profiles/
│   ├── simple_direct.yaml
│   ├── complex_mapping.yaml
│   └── with_normalization.yaml
├── inputs/
│   ├── raw_records_simple.json
│   ├── raw_records_timecode.json
│   └── raw_records_players.json
└── expected/
    ├── udm_simple.json
    ├── udm_timecode.json
    └── udm_players.json
```

---

## 9. Dependencies

### 9.1 Required

| Package | Version | Purpose |
|---------|---------|---------|
| pydantic | 2.0+ | 스키마 검증 |
| pyyaml | 6.0+ | YAML 파싱 |
| python-dateutil | 2.8+ | 날짜 파싱 |

### 9.2 Optional

| Package | Version | Purpose |
|---------|---------|---------|
| rapidfuzz | 3.0+ | Fuzzy 이름 매칭 |
| regex | 2023+ | 고급 정규식 |

---

## 10. Success Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| 변환 정확도 | 99.5%+ | Profile 대로 변환 |
| 이름 정규화율 | 95%+ | 알려진 이름 매칭 |
| 처리 속도 | 10,000 records/sec | 단순 매핑 기준 |
| 에러 리포팅 | 100% | 모든 실패 기록 |

---

## 11. Related PRDs

- **PRD-0001**: Master Orchestrator (Parent)
- **PRD-0002**: Ingest Agent (Input 제공)
- **PRD-0004**: Validate Agent (Output 전달)
- **PRD-0006**: Profile Manager (Profile 제공)
