# PRD-0006: Profile Manager (Block 5)

**Version**: 1.0.0
**Status**: Draft
**Created**: 2025-12-11
**Parent**: PRD-0001-MASTER-ORCHESTRATOR

---

## 1. Overview

### 1.1 Purpose

Profile Manager는 **소스 데이터 → UDM 변환**을 위한 **매핑 프로파일**을 관리하는 Block입니다. 새로운 소스 포맷에 대한 프로파일 생성, 기존 프로파일 수정, 프로파일 검증 기능을 제공합니다.

### 1.2 Scope

- **IN**: 프로파일 요청 (생성/조회/수정/삭제)
- **OUT**: 프로파일 YAML/검증 결과

### 1.3 Non-Goals

- 실제 데이터 변환 (Transform Block 담당)
- 런타임 프로파일 로딩 (Orchestrator 담당)

---

## 2. Profile Types

### 2.1 Source Profiles

소스 데이터 읽기 설정:

| Profile Type | Description | Example |
|--------------|-------------|---------|
| **CSV Profile** | CSV 파일 읽기 설정 | delimiter, encoding, header_row |
| **Excel Profile** | Excel 파일 읽기 설정 | sheet_name, skip_rows |
| **API Profile** | API 연동 설정 | endpoint, auth, pagination |

### 2.2 Transform Profiles

UDM 매핑 설정:

| Profile Type | Description | Example |
|--------------|-------------|---------|
| **Field Mapping** | 컬럼→필드 매핑 | source_col → target_field |
| **Value Transform** | 값 변환 규칙 | timecode → seconds |
| **Normalization** | 정규화 딕셔너리 | name variants |

### 2.3 Export Profiles

출력 타겟 설정:

| Profile Type | Description | Example |
|--------------|-------------|---------|
| **File Export** | 파일 출력 설정 | path, format, options |
| **API Export** | API 업로드 설정 | endpoint, batch_size |

---

## 3. Interface

### 3.1 Profile CRUD

```python
class ProfileManager:
    """프로파일 관리자"""

    async def create_profile(
        self,
        profile_type: ProfileType,
        name: str,
        config: dict
    ) -> Profile:
        """새 프로파일 생성"""
        pass

    async def get_profile(
        self,
        name: str
    ) -> Profile | None:
        """프로파일 조회"""
        pass

    async def update_profile(
        self,
        name: str,
        config: dict
    ) -> Profile:
        """프로파일 수정"""
        pass

    async def delete_profile(
        self,
        name: str
    ) -> bool:
        """프로파일 삭제"""
        pass

    async def list_profiles(
        self,
        profile_type: ProfileType | None = None
    ) -> list[ProfileSummary]:
        """프로파일 목록 조회"""
        pass

    async def validate_profile(
        self,
        name: str
    ) -> ValidationResult:
        """프로파일 유효성 검증"""
        pass
```

### 3.2 Profile Generation

```python
class ProfileGenerator:
    """프로파일 자동 생성기"""

    async def analyze_source(
        self,
        source_path: str,
        source_type: SourceType
    ) -> SourceAnalysis:
        """소스 파일 분석"""
        pass

    async def suggest_mapping(
        self,
        analysis: SourceAnalysis,
        target_schema: dict
    ) -> SuggestedMapping:
        """매핑 제안 생성"""
        pass

    async def generate_profile(
        self,
        source_path: str,
        profile_name: str,
        user_hints: dict | None = None
    ) -> Profile:
        """프로파일 자동 생성"""
        pass
```

---

## 4. Profile Schema

### 4.1 Complete Profile Structure

```yaml
# profiles/complete/wsop_legacy_v1.yaml
profile:
  name: "wsop_legacy_v1"
  version: "1.0.0"
  description: "WSOP Legacy Excel 변환 프로파일"
  created_at: "2025-12-11T10:00:00Z"
  updated_at: "2025-12-11T14:30:00Z"
  author: "Archive Team"

source:
  type: "excel"
  options:
    sheet_name: "Hand Data"
    header_row: 2
    skip_rows: 0
    encoding: "utf-8"
  column_types:
    "Date": "date"
    "Rating": "int"
    "TC In": "timecode"
    "TC Out": "timecode"

transform:
  asset_mapping:
    asset_uuid:
      type: "generate"
      strategy: "file_hash"
    file_name:
      type: "direct"
      source_column: "File Name"
    event_context:
      type: "object"
      fields:
        year:
          type: "extract"
          source_column: "Event"
          pattern: "\\b(20\\d{2})\\b"
          transform: "to_int"
        series:
          type: "map"
          source_column: "Series"
          mapping:
            "WSOP": "WSOP"
            "World Series": "WSOP"
            "WSOPC": "WSOPC"
        location:
          type: "direct"
          source_column: "Location"
    source_origin:
      type: "constant"
      value: "Legacy_Excel_v1"

  segment_mapping:
    segment_uuid:
      type: "generate"
      strategy: "uuid4"
    time_in_sec:
      type: "timecode"
      source_column: "TC In"
      fps: 29.97
    time_out_sec:
      type: "timecode"
      source_column: "TC Out"
      fps: 29.97
    game_type:
      type: "enum"
      source_column: "Type"
      mapping:
        "T": "TOURNAMENT"
        "C": "CASH_GAME"
      default: "TOURNAMENT"
    rating:
      type: "direct"
      source_column: "Rating"
      transform: "to_int"
    winner:
      type: "direct"
      source_column: "Winner"
      normalize: true
    players:
      type: "array"
      source_columns:
        - "Player 1"
        - "Player 2"
        - "Player 3"
        - "Player 4"
      remove_empty: true
      normalize: true
    tags_action:
      type: "split"
      source_column: "Action Tags"
      delimiter: ","
    tags_emotion:
      type: "split"
      source_column: "Emotion Tags"
      delimiter: ","

normalization:
  dictionary: "player_names.yaml"
  fuzzy_threshold: 0.85
  fallback: "title_case"

export:
  default_targets:
    - name: "json_output"
      type: "json"
      path: "output/{profile}/{date}/export.json"
    - name: "csv_backup"
      type: "csv"
      path: "output/{profile}/{date}/export.csv"

validation:
  skip_rules: []
  custom_rules:
    - name: "wsop_specific_check"
      enabled: true
```

### 4.2 Minimal Profile

```yaml
# profiles/minimal_example.yaml
profile:
  name: "minimal_csv"
  version: "1.0.0"

source:
  type: "csv"

transform:
  segment_mapping:
    time_in_sec:
      type: "direct"
      source_column: "Start Time"
    time_out_sec:
      type: "direct"
      source_column: "End Time"
    game_type:
      type: "constant"
      value: "TOURNAMENT"
```

---

## 5. Core Components

### 5.1 Architecture

```
┌────────────────────────────────────────────────────────┐
│                  Profile Manager                       │
├────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────┐  │
│  │              Profile Repository                   │  │
│  │          YAML 파일 읽기/쓰기/관리                │  │
│  └────────────────────┬─────────────────────────────┘  │
│                       │                                │
│    ┌──────────────────┼──────────────────┐            │
│    │                  │                  │            │
│    ▼                  ▼                  ▼            │
│ ┌────────┐    ┌────────────┐    ┌────────────┐       │
│ │Profile │    │Profile     │    │Profile     │       │
│ │CRUD    │    │Validator   │    │Generator   │       │
│ └────────┘    └────────────┘    └────────────┘       │
│                                                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │           Dictionary Manager                      │  │
│  │      이름 정규화 딕셔너리 관리                   │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

### 5.2 Profile Repository

```python
class ProfileRepository:
    """프로파일 저장소"""

    def __init__(self, profiles_dir: str):
        self.profiles_dir = Path(profiles_dir)

    async def load(self, name: str) -> Profile:
        """YAML 파일에서 프로파일 로드"""
        path = self.profiles_dir / f"{name}.yaml"
        if not path.exists():
            raise ProfileNotFoundError(name)

        async with aiofiles.open(path) as f:
            content = await f.read()
            data = yaml.safe_load(content)
            return Profile.model_validate(data)

    async def save(self, profile: Profile) -> None:
        """프로파일을 YAML 파일로 저장"""
        path = self.profiles_dir / f"{profile.name}.yaml"
        data = profile.model_dump(exclude_none=True)

        async with aiofiles.open(path, "w") as f:
            await f.write(yaml.dump(data, allow_unicode=True, default_flow_style=False))

    async def list_all(self) -> list[ProfileSummary]:
        """모든 프로파일 목록"""
        profiles = []
        for path in self.profiles_dir.glob("*.yaml"):
            profile = await self.load(path.stem)
            profiles.append(ProfileSummary(
                name=profile.name,
                version=profile.version,
                description=profile.description,
                source_type=profile.source.type
            ))
        return profiles
```

### 5.3 Profile Validator

```python
class ProfileValidator:
    """프로파일 유효성 검증기"""

    async def validate(self, profile: Profile) -> ValidationResult:
        errors = []
        warnings = []

        # 1. Schema Validation (Pydantic)
        try:
            Profile.model_validate(profile.model_dump())
        except ValidationError as e:
            errors.extend(self._format_pydantic_errors(e))

        # 2. Reference Validation
        # - source_column이 실제 존재하는지
        # - dictionary 파일이 존재하는지
        ref_errors = await self._validate_references(profile)
        errors.extend(ref_errors)

        # 3. Logic Validation
        # - 순환 참조 검사
        # - 필수 필드 매핑 확인
        logic_errors = self._validate_logic(profile)
        errors.extend(logic_errors)

        # 4. Best Practice Warnings
        warnings.extend(self._check_best_practices(profile))

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
```

### 5.4 Profile Generator (AI-Assisted)

```python
class ProfileGenerator:
    """AI 지원 프로파일 자동 생성기"""

    async def analyze_source(self, source_path: str) -> SourceAnalysis:
        """소스 파일 분석"""
        # 1. 파일 타입 감지
        file_type = self._detect_file_type(source_path)

        # 2. 샘플 데이터 추출
        sample_rows = await self._extract_sample(source_path, limit=100)

        # 3. 컬럼 분석
        column_analysis = self._analyze_columns(sample_rows)

        return SourceAnalysis(
            file_type=file_type,
            columns=column_analysis,
            sample_rows=sample_rows[:5]
        )

    async def suggest_mapping(
        self,
        analysis: SourceAnalysis
    ) -> SuggestedMapping:
        """UDM 필드 매핑 제안"""
        suggestions = {}

        for col in analysis.columns:
            # 컬럼명 기반 매칭
            udm_field = self._match_column_name(col.name)

            # 값 패턴 기반 매칭
            if not udm_field:
                udm_field = self._match_by_pattern(col.sample_values)

            if udm_field:
                suggestions[col.name] = MappingSuggestion(
                    target_field=udm_field,
                    transform_type=self._suggest_transform(col),
                    confidence=self._calculate_confidence(col, udm_field)
                )

        return SuggestedMapping(suggestions=suggestions)

    # 컬럼명 → UDM 필드 매핑 패턴
    COLUMN_PATTERNS = {
        r"(?i)file.?name|filename": "file_name",
        r"(?i)tc.?in|time.?in|start": "time_in_sec",
        r"(?i)tc.?out|time.?out|end": "time_out_sec",
        r"(?i)player|participant": "players",
        r"(?i)winner": "winner",
        r"(?i)rating|score|stars": "rating",
        r"(?i)type|game.?type": "game_type",
        r"(?i)tag|label|keyword": "tags_action",
    }
```

---

## 6. Dictionary Management

### 6.1 Dictionary Structure

```yaml
# dictionaries/player_names.yaml
version: "1.0.0"
updated_at: "2025-12-11"

# 정규화된 이름 → 변형 리스트
normalizations:
  "Daniel Negreanu":
    aliases:
      - "D. Negreanu"
      - "Negreanu"
      - "Kid Poker"
      - "DNegs"
    metadata:
      country: "Canada"
      wsop_bracelets: 6

  "Phil Hellmuth":
    aliases:
      - "P. Hellmuth"
      - "Hellmuth"
      - "Poker Brat"
    metadata:
      country: "USA"
      wsop_bracelets: 17

# 자동 정규화 규칙
rules:
  - name: "expand_initial"
    pattern: "^(\\w)\\.\\s*(\\w+)$"
    description: "이니셜 확장 (D. Negreanu → lookup)"

  - name: "remove_nickname"
    pattern: "\"[^\"]+\""
    action: "remove"
    description: "닉네임 제거"
```

### 6.2 Dictionary Manager

```python
class DictionaryManager:
    """정규화 딕셔너리 관리자"""

    async def get_dictionary(self, name: str) -> NormalizationDict:
        """딕셔너리 로드"""
        pass

    async def add_entry(
        self,
        dict_name: str,
        canonical_name: str,
        aliases: list[str]
    ) -> None:
        """새 항목 추가"""
        pass

    async def search(
        self,
        dict_name: str,
        query: str,
        fuzzy: bool = True
    ) -> list[SearchResult]:
        """딕셔너리 검색"""
        pass

    async def export_csv(self, dict_name: str, output_path: str) -> None:
        """CSV로 내보내기 (편집용)"""
        pass

    async def import_csv(self, dict_name: str, csv_path: str) -> ImportResult:
        """CSV에서 가져오기"""
        pass
```

---

## 7. Agent Definition

### 7.1 Claude Agent Spec

```yaml
name: profile-manager
description: 매핑 프로파일 생성, 관리, 검증 전문 에이전트
category: data-pipeline
tier: support

tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep

triggers:
  - "create profile"
  - "edit mapping"
  - "add player name"
  - "프로파일 생성"
  - "매핑 설정"

capabilities:
  - 프로파일 CRUD
  - 소스 파일 분석
  - 매핑 제안 생성
  - 정규화 딕셔너리 관리
  - 프로파일 유효성 검증
```

### 7.2 Agent Prompt Template

```markdown
## Profile Manager Agent

당신은 Archive Converter의 Profile Manager 전문가입니다.

### 역할
- 새로운 소스 포맷에 대한 매핑 프로파일 생성
- 기존 프로파일 수정 및 관리
- 이름 정규화 딕셔너리 관리
- 프로파일 유효성 검증

### 원칙
1. YAML 형식 준수
2. 명확한 컬럼명→필드 매핑
3. 재사용 가능한 프로파일 설계
4. 딕셔너리 일관성 유지

### 출력 형식
Profile YAML 또는 ValidationResult
```

---

## 8. CLI Commands

### 8.1 Profile Commands

```bash
# 프로파일 목록
archive-converter profile list

# 프로파일 상세
archive-converter profile show wsop_legacy_v1

# 새 프로파일 생성 (대화형)
archive-converter profile create --interactive

# 소스 파일 분석 후 프로파일 제안
archive-converter profile suggest --source data.xlsx --name my_profile

# 프로파일 검증
archive-converter profile validate wsop_legacy_v1

# 프로파일 복사
archive-converter profile copy wsop_legacy_v1 wsop_legacy_v2
```

### 8.2 Dictionary Commands

```bash
# 딕셔너리 목록
archive-converter dict list

# 항목 추가
archive-converter dict add player_names "Phil Ivey" --alias "P. Ivey" --alias "Ivey"

# 검색
archive-converter dict search player_names "negreanu"

# CSV 내보내기/가져오기
archive-converter dict export player_names --output names.csv
archive-converter dict import player_names --input names_updated.csv
```

---

## 9. Testing

### 9.1 Test Cases

| Test ID | Description | Input | Expected |
|---------|-------------|-------|----------|
| PFM-001 | 프로파일 생성 | valid config | 저장 성공 |
| PFM-002 | 프로파일 검증 | valid profile | no errors |
| PFM-003 | 잘못된 프로파일 검증 | missing field | validation error |
| PFM-004 | 소스 분석 | excel file | column analysis |
| PFM-005 | 매핑 제안 | source analysis | suggested mapping |
| PFM-006 | 딕셔너리 검색 | "negreanu" | "Daniel Negreanu" |
| PFM-007 | 딕셔너리 추가 | new entry | 저장 성공 |

### 9.2 Test Fixtures

```
tests/fixtures/profiles/
├── valid/
│   ├── complete_profile.yaml
│   └── minimal_profile.yaml
├── invalid/
│   ├── missing_required.yaml
│   ├── bad_reference.yaml
│   └── circular_dependency.yaml
└── sources/
    ├── sample_excel.xlsx
    └── sample_csv.csv
```

---

## 10. Dependencies

### 10.1 Required

| Package | Version | Purpose |
|---------|---------|---------|
| pyyaml | 6.0+ | YAML 처리 |
| pydantic | 2.0+ | 스키마 검증 |
| aiofiles | 23.0+ | 비동기 파일 I/O |

### 10.2 Optional

| Package | Version | Purpose |
|---------|---------|---------|
| rapidfuzz | 3.0+ | Fuzzy 매칭 |
| rich | 13.0+ | CLI 출력 |

---

## 11. Success Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| 프로파일 생성 시간 | < 5분 | AI 지원 자동 생성 |
| 매핑 정확도 | 80%+ | 자동 제안 정확도 |
| 검증 완성도 | 100% | 모든 에러 탐지 |
| 딕셔너리 검색 | < 100ms | 검색 응답 시간 |

---

## 12. Related PRDs

- **PRD-0001**: Master Orchestrator (Parent)
- **PRD-0002**: Ingest Agent (Source Config 사용)
- **PRD-0003**: Transform Agent (Transform Profile 사용)
- **PRD-0005**: Export Agent (Export Config 사용)
