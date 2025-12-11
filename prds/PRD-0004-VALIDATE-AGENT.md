# PRD-0004: Validate Agent (Block 3)

**Version**: 1.0.0
**Status**: Draft
**Created**: 2025-12-11
**Parent**: PRD-0001-MASTER-ORCHESTRATOR

---

## 1. Overview

### 1.1 Purpose

Validate Agent는 Transform Agent가 생성한 **UDM 데이터**를 검증하여 **스키마 준수**와 **비즈니스 규칙 충족**을 확인하는 Block입니다.

### 1.2 Scope

- **IN**: UDM Asset/Segment 리스트
- **OUT**: 검증된 UDM 리스트 + Validation Report

### 1.3 Non-Goals

- 데이터 변환/수정 (Transform Block 담당)
- 출력 포맷팅 (Export Block 담당)
- 자동 수정 (사용자 승인 후 별도 처리)

---

## 2. Validation Types

### 2.1 Schema Validation

| Check Type | Description | Example |
|------------|-------------|---------|
| **Required Fields** | 필수 필드 존재 확인 | `asset_uuid`, `file_name` |
| **Type Check** | 데이터 타입 검증 | `time_in_sec: float` |
| **Format Check** | 포맷 검증 | UUID 형식, 날짜 형식 |
| **Range Check** | 값 범위 검증 | `rating: 0-5` |
| **Enum Check** | 허용 값 검증 | `game_type: TOURNAMENT|CASH_GAME` |

### 2.2 Business Rule Validation

| Rule Type | Description | Example |
|-----------|-------------|---------|
| **Time Consistency** | 시간 순서 검증 | `time_in_sec < time_out_sec` |
| **Reference Integrity** | 참조 무결성 | `parent_asset_uuid` 존재 |
| **Uniqueness** | 중복 검사 | `segment_uuid` 유일성 |
| **Semantic Check** | 의미적 검증 | winner가 players에 포함 |
| **Cross-field** | 필드 간 검증 | Tournament면 pot_size 필수 아님 |

### 2.3 Quality Checks

| Check Type | Description | Severity |
|------------|-------------|----------|
| **Completeness** | 선택 필드 채움률 | WARNING |
| **Consistency** | 값 일관성 | WARNING |
| **Outlier** | 이상값 감지 | INFO |
| **Duplicate** | 중복 레코드 | WARNING |

---

## 3. Interface

### 3.1 Input Contract

```python
@dataclass
class ValidateInput:
    """Validate Agent 입력"""
    assets: list[Asset]
    segments: list[Segment]
    options: ValidateOptions

@dataclass
class ValidateOptions:
    """검증 옵션"""
    strict_mode: bool = False       # 엄격 모드 (WARNING도 실패)
    skip_rules: list[str] = None    # 스킵할 규칙 ID
    custom_rules: list[Rule] = None # 커스텀 규칙
    report_level: str = "ERROR"     # 리포트 최소 레벨
```

### 3.2 Output Contract

```python
@dataclass
class ValidateOutput:
    """Validate Agent 출력"""
    valid_assets: list[Asset]       # 검증 통과 Asset
    valid_segments: list[Segment]   # 검증 통과 Segment
    report: ValidationReport        # 검증 리포트
    is_valid: bool                  # 전체 검증 결과

@dataclass
class ValidationReport:
    """검증 리포트"""
    total_checks: int
    passed_checks: int
    failed_checks: int
    errors: list[ValidationError]
    warnings: list[ValidationWarning]
    info: list[ValidationInfo]
    summary: ValidationSummary

@dataclass
class ValidationError:
    """검증 에러"""
    rule_id: str
    severity: Severity              # ERROR, WARNING, INFO
    entity_type: str                # "asset" | "segment"
    entity_id: str                  # UUID
    field_name: str | None
    message: str
    actual_value: Any
    expected: str
    suggestion: str | None          # 수정 제안
```

---

## 4. Validation Rules

### 4.1 Schema Rules (Pydantic)

```python
from pydantic import BaseModel, Field, validator
from typing import Literal
import uuid

class AssetSchema(BaseModel):
    """Asset 스키마 정의"""
    asset_uuid: str = Field(..., pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
    file_name: str = Field(..., min_length=1, max_length=500)
    file_path_rel: str | None = None
    event_context: EventContext
    tech_spec: TechSpec | None = None
    source_origin: str = Field(..., min_length=1)

class SegmentSchema(BaseModel):
    """Segment 스키마 정의"""
    segment_uuid: str
    parent_asset_uuid: str
    time_in_sec: float = Field(..., ge=0)
    time_out_sec: float = Field(..., ge=0)
    game_type: Literal["TOURNAMENT", "CASH_GAME"]
    rating: int | None = Field(None, ge=0, le=5)
    winner: str | None = None
    hand_matchup: str | None = None
    players: list[str] | None = None
    tags_action: list[str] | None = None
    tags_emotion: list[str] | None = None
    description: str | None = None

    @validator("time_out_sec")
    def time_out_after_time_in(cls, v, values):
        if "time_in_sec" in values and v <= values["time_in_sec"]:
            raise ValueError("time_out_sec must be greater than time_in_sec")
        return v
```

### 4.2 Business Rules (Custom)

```python
class BusinessRules:
    """비즈니스 규칙 정의"""

    @staticmethod
    def winner_in_players(segment: Segment) -> ValidationResult:
        """승자가 플레이어 목록에 포함되어야 함"""
        if segment.winner and segment.players:
            if segment.winner not in segment.players:
                return ValidationResult(
                    valid=False,
                    rule_id="BR-001",
                    message=f"Winner '{segment.winner}' not in players list",
                    suggestion=f"Add '{segment.winner}' to players or correct winner name"
                )
        return ValidationResult(valid=True)

    @staticmethod
    def reasonable_duration(segment: Segment) -> ValidationResult:
        """핸드 시간이 합리적인 범위인지"""
        duration = segment.time_out_sec - segment.time_in_sec
        if duration > 3600:  # 1시간 초과
            return ValidationResult(
                valid=False,
                rule_id="BR-002",
                severity=Severity.WARNING,
                message=f"Segment duration ({duration}s) exceeds 1 hour",
                suggestion="Verify time_in and time_out values"
            )
        if duration < 10:  # 10초 미만
            return ValidationResult(
                valid=False,
                rule_id="BR-003",
                severity=Severity.WARNING,
                message=f"Segment duration ({duration}s) is very short",
                suggestion="Verify time_in and time_out values"
            )
        return ValidationResult(valid=True)

    @staticmethod
    def unique_segment_uuids(segments: list[Segment]) -> ValidationResult:
        """Segment UUID 유일성"""
        uuids = [s.segment_uuid for s in segments]
        duplicates = [u for u in uuids if uuids.count(u) > 1]
        if duplicates:
            return ValidationResult(
                valid=False,
                rule_id="BR-004",
                message=f"Duplicate segment UUIDs: {set(duplicates)}",
                suggestion="Regenerate UUIDs for duplicates"
            )
        return ValidationResult(valid=True)
```

### 4.3 Rule Configuration

```yaml
# config/validation_rules.yaml
rules:
  schema:
    enabled: true
    strict: true

  business:
    - id: "BR-001"
      name: "winner_in_players"
      enabled: true
      severity: "ERROR"

    - id: "BR-002"
      name: "reasonable_duration"
      enabled: true
      severity: "WARNING"
      max_duration_sec: 3600
      min_duration_sec: 10

    - id: "BR-003"
      name: "unique_segment_uuids"
      enabled: true
      severity: "ERROR"

  quality:
    - id: "QC-001"
      name: "completeness_check"
      enabled: true
      severity: "INFO"
      target_fields:
        - "rating"
        - "hand_matchup"
        - "players"
      min_fill_rate: 0.7
```

---

## 5. Core Components

### 5.1 Architecture

```
┌────────────────────────────────────────────────────────┐
│                  Validate Agent                        │
├────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────┐  │
│  │              Rule Registry                        │  │
│  │     모든 검증 규칙 등록 및 관리                   │  │
│  └────────────────────┬─────────────────────────────┘  │
│                       │                                │
│    ┌──────────────────┼──────────────────┐            │
│    │                  │                  │            │
│    ▼                  ▼                  ▼            │
│ ┌────────┐    ┌────────────┐    ┌────────────┐       │
│ │Schema  │    │Business    │    │Quality     │       │
│ │Validator│   │Rule Engine │    │Checker     │       │
│ └────────┘    └────────────┘    └────────────┘       │
│                                                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │           Report Generator                        │  │
│  │      검증 결과 집계 및 리포트 생성               │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

### 5.2 Validation Engine

```python
class ValidationEngine:
    """검증 엔진 코어"""

    def __init__(self, config: ValidationConfig):
        self.schema_validator = SchemaValidator()
        self.rule_engine = BusinessRuleEngine(config.business_rules)
        self.quality_checker = QualityChecker(config.quality_rules)

    async def validate(
        self,
        assets: list[Asset],
        segments: list[Segment],
        options: ValidateOptions
    ) -> ValidateOutput:
        errors = []
        warnings = []
        infos = []

        # 1. Schema Validation
        for asset in assets:
            result = self.schema_validator.validate_asset(asset)
            if not result.valid:
                errors.extend(result.errors)

        for segment in segments:
            result = self.schema_validator.validate_segment(segment)
            if not result.valid:
                errors.extend(result.errors)

        # 2. Business Rules
        for rule in self.rule_engine.rules:
            if rule.id in (options.skip_rules or []):
                continue
            result = await rule.execute(assets, segments)
            self._categorize_result(result, errors, warnings, infos)

        # 3. Quality Checks
        quality_results = self.quality_checker.check(assets, segments)
        infos.extend(quality_results)

        # 4. Filter valid entities
        valid_assets = [a for a in assets if not self._has_errors(a, errors)]
        valid_segments = [s for s in segments if not self._has_errors(s, errors)]

        # 5. Generate Report
        report = self._generate_report(errors, warnings, infos)

        return ValidateOutput(
            valid_assets=valid_assets,
            valid_segments=valid_segments,
            report=report,
            is_valid=len(errors) == 0
        )
```

---

## 6. Agent Definition

### 6.1 Claude Agent Spec

```yaml
name: validate-agent
description: UDM 데이터의 스키마 및 비즈니스 규칙 검증 전문 에이전트
category: data-pipeline
tier: domain

tools:
  - Read
  - Grep
  - Write

triggers:
  - "validate data"
  - "check UDM"
  - "verify schema"
  - "데이터 검증"

capabilities:
  - Pydantic 스키마 검증
  - 커스텀 비즈니스 규칙 적용
  - 데이터 품질 분석
  - 상세 검증 리포트 생성
```

### 6.2 Agent Prompt Template

```markdown
## Validate Agent

당신은 Archive Converter의 Validate 전문가입니다.

### 역할
- UDM 데이터의 스키마 준수 여부 검증
- 비즈니스 규칙 충족 확인
- 데이터 품질 분석 및 리포팅

### 원칙
1. 데이터 수정하지 않음 (검증만)
2. 모든 에러/경고 상세 기록
3. 수정 제안 제공
4. ERROR → WARNING → INFO 단계별 분류

### 출력 형식
ValidAssets + ValidSegments + ValidationReport
```

---

## 7. Validation Report Format

### 7.1 Summary Report

```json
{
  "summary": {
    "total_assets": 100,
    "valid_assets": 98,
    "total_segments": 450,
    "valid_segments": 445,
    "validation_time_ms": 1250,
    "pass_rate": 0.978
  },
  "by_severity": {
    "ERROR": 7,
    "WARNING": 15,
    "INFO": 23
  },
  "by_rule": {
    "SCHEMA": 3,
    "BR-001": 2,
    "BR-002": 5,
    "QC-001": 15
  }
}
```

### 7.2 Detailed Error Report

```json
{
  "errors": [
    {
      "rule_id": "SCHEMA",
      "severity": "ERROR",
      "entity_type": "segment",
      "entity_id": "a1b2c3d4-0001",
      "field_name": "time_out_sec",
      "message": "time_out_sec must be greater than time_in_sec",
      "actual_value": 100.0,
      "context": {
        "time_in_sec": 200.0
      },
      "suggestion": "Swap time_in_sec and time_out_sec values"
    },
    {
      "rule_id": "BR-001",
      "severity": "ERROR",
      "entity_type": "segment",
      "entity_id": "a1b2c3d4-0002",
      "field_name": "winner",
      "message": "Winner 'D. Negreanu' not in players list",
      "actual_value": "D. Negreanu",
      "context": {
        "players": ["Phil Hellmuth", "Phil Ivey"]
      },
      "suggestion": "Add 'D. Negreanu' to players or correct winner name"
    }
  ]
}
```

---

## 8. Testing

### 8.1 Test Cases

| Test ID | Description | Input | Expected |
|---------|-------------|-------|----------|
| VAL-001 | 유효한 Asset | valid_asset | PASS |
| VAL-002 | 누락 필수 필드 | missing_uuid | ERROR |
| VAL-003 | 잘못된 UUID 형식 | invalid_uuid | ERROR |
| VAL-004 | time_in > time_out | time_reversed | ERROR |
| VAL-005 | winner not in players | bad_winner | ERROR |
| VAL-006 | 중복 segment_uuid | duplicate_uuids | ERROR |
| VAL-007 | 비정상 duration | long_duration | WARNING |
| VAL-008 | 낮은 필드 채움률 | sparse_data | INFO |

### 8.2 Test Fixtures

```
tests/fixtures/validate/
├── valid/
│   ├── complete_asset.json
│   └── complete_segment.json
├── invalid/
│   ├── missing_required.json
│   ├── bad_uuid_format.json
│   ├── time_reversed.json
│   ├── winner_not_in_players.json
│   └── duplicate_uuids.json
└── edge_cases/
    ├── minimal_valid.json
    └── all_optional_null.json
```

---

## 9. Dependencies

### 9.1 Required

| Package | Version | Purpose |
|---------|---------|---------|
| pydantic | 2.0+ | 스키마 검증 |

### 9.2 Optional

| Package | Version | Purpose |
|---------|---------|---------|
| jsonschema | 4.0+ | JSON Schema 검증 |
| cerberus | 1.3+ | 유연한 검증 규칙 |

---

## 10. Success Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| 검증 정확도 | 100% | 모든 에러 탐지 |
| 처리 속도 | 50,000 records/sec | 검증 처리량 |
| False Positive | < 0.1% | 오탐률 |
| 리포트 완성도 | 100% | 모든 이슈 상세 기록 |

---

## 11. Related PRDs

- **PRD-0001**: Master Orchestrator (Parent)
- **PRD-0003**: Transform Agent (Input 제공)
- **PRD-0005**: Export Agent (Output 전달)
