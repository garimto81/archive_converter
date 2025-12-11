# Profiles

Archive Converter의 소스 데이터 → UDM 변환 프로파일 저장소입니다.

## 디렉토리 구조

```
profiles/
├── README.md                    # 이 파일
├── sources/                     # 소스 연결 설정
│   ├── google_sheets.yaml      # Google Sheets 소스 설정
│   └── excel_legacy.yaml       # Excel 파일 소스 설정
├── mappings/                    # UDM 매핑 프로파일
│   ├── wsop_circuit_2024.yaml  # WSOP Circuit Sheet 매핑
│   ├── wsop_database.yaml      # WSOP Database Sheet 매핑
│   ├── iconik_export.yaml      # Iconik MAM 시스템 매핑
│   ├── catdv_export.yaml       # CatDV MAM 시스템 매핑
│   └── nas_folder_scan.yaml    # NAS 폴더 스캔 매핑
└── dictionaries/                # 정규화 딕셔너리
    └── player_names.yaml       # 플레이어 이름 정규화

```

## 프로파일 유형

### 1. Source Profiles (`sources/`)

데이터 소스 연결 설정:
- Google Sheets 연결 정보 (Sheet ID, 인증)
- Excel 파일 읽기 설정 (Sheet 이름, 헤더 행)
- API 엔드포인트 설정

### 2. Mapping Profiles (`mappings/`)

소스 데이터 → UDM 필드 매핑:
- Asset 필드 매핑
- Segment 필드 매핑
- 값 변환 규칙 (타임코드, Enum, 배열 등)
- 이름 정규화 활성화

### 3. Dictionaries (`dictionaries/`)

정규화 딕셔너리:
- 플레이어 이름 변형 목록
- 자동 정규화 규칙

## 사용법

### CLI 명령어

```bash
# 프로파일 목록 보기
archive-converter profile list

# 프로파일 상세 정보
archive-converter profile show wsop_circuit_2024

# 프로파일 유효성 검증
archive-converter profile validate wsop_circuit_2024

# 프로파일로 변환 실행
archive-converter convert \
  --profile mappings/wsop_circuit_2024.yaml \
  --source sources/google_sheets.yaml \
  --output output/converted.json
```

### Python API

```python
from archive_converter.profile import ProfileManager
from archive_converter.orchestrator import Orchestrator

# Profile 로드
manager = ProfileManager(profiles_dir="profiles")
profile = await manager.load_profile("mappings/wsop_circuit_2024.yaml")

# 변환 실행
orchestrator = Orchestrator()
result = await orchestrator.run(
    ingest_profile=profile.source,
    transform_profile=profile.transform
)
```

## 프로파일 생성

### 자동 생성 (AI 지원)

```bash
# 소스 파일 분석 후 프로파일 제안
archive-converter profile suggest \
  --source data.xlsx \
  --name my_new_profile \
  --interactive
```

### 수동 작성

1. **템플릿 복사**: 기존 프로파일을 복사하여 시작

```bash
archive-converter profile copy wsop_circuit_2024 my_new_profile
```

2. **YAML 수정**: `mappings/my_new_profile.yaml` 편집

3. **검증**: 유효성 검증 후 사용

```bash
archive-converter profile validate my_new_profile
```

## 프로파일 구조

### 완전한 프로파일 예시

```yaml
profile:
  name: "wsop_circuit_2024"
  version: "1.0.0"
  description: "WSOP Circuit 2024 Google Sheet 변환 프로파일"

source:
  type: "google_sheets"
  sheet_id: "1_RN_W_ZQclSZA0Iez6XniCXVtjkkd5HNZwiT6l-z6d4"
  options:
    header_row: 1

transform:
  asset_mapping:
    asset_uuid:
      type: "generate"
      strategy: "content_hash"
    file_name:
      type: "direct"
      source_column: "File Name"
    event_context:
      type: "object"
      fields:
        year:
          type: "extract"
          source_column: "File Name"
          pattern: "\\b(20\\d{2})\\b"
          transform: "to_int"
        series:
          type: "extract"
          source_column: "File Name"
          pattern: "(WSOP[CEP]?|HCL|PAD)"

  segment_mapping:
    segment_uuid:
      type: "generate"
      strategy: "uuid4"
    time_in_sec:
      type: "timecode"
      source_column: "TC In"
      fps: 29.97
    game_type:
      type: "enum"
      source_column: "Type"
      mapping:
        "T": "TOURNAMENT"
        "C": "CASH_GAME"

normalization:
  dictionary: "player_names.yaml"
```

## Transform Types

### 필드 매핑 유형

| Type | Description | Example |
|------|-------------|---------|
| `direct` | 1:1 직접 매핑 | `source_column: "File Name"` |
| `generate` | UUID/Hash 생성 | `strategy: "uuid4"` |
| `extract` | 정규식 추출 | `pattern: "\\b(20\\d{2})\\b"` |
| `map` | 값 매핑 | `mapping: {"T": "TOURNAMENT"}` |
| `enum` | Enum 변환 | `mapping: + default` |
| `timecode` | 타임코드→초 | `fps: 29.97` |
| `array` | 배열 생성 | `source_columns: [...]` |
| `split` | 문자열 분리 | `delimiter: ","` |
| `object` | 중첩 객체 | `fields: {...}` |
| `constant` | 고정값 | `value: "Legacy_Excel_v1"` |

### 값 변환 (transform)

- `to_int`: 정수 변환
- `to_float`: 실수 변환
- `to_bool`: Boolean 변환
- `trim`: 공백 제거
- `upper`: 대문자 변환
- `lower`: 소문자 변환
- `title_case`: Title Case 변환

## 정규화 딕셔너리

### 플레이어 이름 정규화

`dictionaries/player_names.yaml`:

```yaml
version: "1.0.0"

normalizations:
  "Daniel Negreanu":
    - "D. Negreanu"
    - "Negreanu"
    - "Kid Poker"
    - "DNegs"

  "Phil Hellmuth":
    - "P. Hellmuth"
    - "Hellmuth"
    - "Poker Brat"

rules:
  - name: "expand_initial"
    pattern: "^(\\w)\\.\\s*(\\w+)$"
    action: "lookup"
```

### 딕셔너리 관리

```bash
# 항목 추가
archive-converter dict add player_names "Phil Ivey" \
  --alias "P. Ivey" \
  --alias "Ivey"

# 검색
archive-converter dict search player_names "negreanu"

# CSV 내보내기/가져오기
archive-converter dict export player_names --output names.csv
archive-converter dict import player_names --input names_updated.csv
```

## 관련 문서

- **PRD-0003-TRANSFORM-AGENT.md**: Transform 프로파일 스키마 상세
- **PRD-0006-PROFILE-MANAGER.md**: Profile Manager 설계
- **UDM.md**: Universal Data Model 스키마
- **src/models/udm.py**: UDM Pydantic 모델

## 버전 관리

프로파일은 버전 관리됩니다:

```yaml
profile:
  name: "wsop_circuit_2024"
  version: "1.2.0"  # 시맨틱 버저닝
  updated_at: "2025-12-11T10:00:00Z"
```

### 버전 규칙

- **MAJOR**: 호환성 깨지는 변경
- **MINOR**: 새 필드 추가
- **PATCH**: 버그 수정

## 테스트

프로파일 테스트:

```bash
# 단위 테스트
pytest tests/test_profiles.py -v

# 프로파일 검증 (Dry-run)
archive-converter convert \
  --profile mappings/wsop_circuit_2024.yaml \
  --source tests/fixtures/sample_data.xlsx \
  --dry-run
```

## 기여 가이드

새 프로파일 추가 시:

1. `mappings/` 에 YAML 파일 생성
2. 프로파일 유효성 검증 통과
3. 샘플 데이터로 테스트
4. PR 생성 (프로파일명, 용도 명시)

---

**Version**: 1.0.0
**Last Updated**: 2025-12-11
**Maintainer**: Archive Converter Team
