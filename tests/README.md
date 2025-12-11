# UDM (Unified Data Model) Test Suite

PRD-0008-UDM-FINAL-SCHEMA.md v3.0.0 기반 pytest 단위 테스트

## 테스트 구조

```
tests/
├── __init__.py          # 테스트 패키지 초기화
├── conftest.py          # 공통 픽스처 (30개)
├── test_udm.py          # 메인 테스트 파일 (84개 테스트)
└── README.md            # 본 문서
```

---

## 실행 방법

### 기본 실행

```bash
cd D:\AI\claude01\Archive_Converter
pytest tests/test_udm.py -v
```

### 커버리지 리포트

```bash
pytest tests/test_udm.py --cov=src.models.udm --cov-report=term-missing
```

### 특정 테스트 클래스만 실행

```bash
pytest tests/test_udm.py::TestEnums -v
pytest tests/test_udm.py::TestSegmentValidation -v
```

### 특정 테스트 함수만 실행

```bash
pytest tests/test_udm.py::TestEnums::test_brand_enum_values -v
```

---

## 테스트 범위 (84개 테스트)

### 1. Enum 테스트 (8개)

모든 Enum 값 존재 확인 및 개수 검증

- `Brand` (12개 값)
- `EventType` (6개 값)
- `AssetType` (10개 값)
- `Location` (7개 값)
- `GameVariant` (9개 값)
- `GameType` (2개 값)
- `AllInStage` (5개 값)
- `SegmentType` (5개 값)

### 2. Model 생성 테스트 (25개)

AAA 패턴 (Arrange-Act-Assert) 적용

#### EventContext (4개)
- 최소/전체 필드 생성
- 연도 범위 검증 (1970-2100)

#### TechSpec (4개)
- 최소/전체 필드 생성
- 해상도 패턴 검증

#### PlayerInHand (5개)
- 최소/전체 필드 생성
- 홀카드 형식 검증 (AA, KK, AKs 등)
- 포지션 검증 (BTN, BB, UTG 등)

#### SituationFlags (3개)
- 기본값 생성
- `to_tags()` 변환 테스트

#### Segment (4개)
- 최소/전체 필드 생성
- UUID 자동 생성 확인
- `duration_sec` computed field 검증

#### Asset (3개)
- 최소/전체 필드 생성
- UUID 자동 생성 확인

#### UDMDocument (3개)
- 최소 필드 생성
- `from_asset()` 팩토리 메서드
- `to_json_dict()` 직렬화

### 3. 유효성 검증 테스트 (8개)

비즈니스 규칙 검증

#### Segment 검증 (6개)
- **BR-001**: `time_out_sec > time_in_sec` 검증
- `time_out_sec == time_in_sec` 허용 (duration=0)
- **rating 범위 (0-5)** 검증
- **BR-003**: 핸드 길이 경고 (10초-3600초)

#### Asset 검증 (2개)
- Segment `parent_asset_uuid` 일치 검증
- 파일명 확장자 검증

### 4. 유틸리티 함수 테스트 (19개)

#### parse_filename() (7개)

NAS 파일명 패턴별 파싱 테스트

- `WCLA24-15.mp4` → Circuit Subclip
- `WP23-PE-01.mp4` → Paradise Player Emotion
- `WP23-03.mp4` → Paradise Subclip
- `PAD_S13_EP01_GGPoker-001.mp4` → PAD Episode
- `10-wsop-2024-be-ev-21-25k-nlh-hr-ft-description.mp4` → WSOP Mastered
- `250507_Super High Roller Poker FINAL TABLE with Player.mp4` → GGMillions
- Unknown 패턴 → 빈 메타데이터

#### infer_brand_from_path() (7개)

경로 기반 브랜드/이벤트 유형 추론

- `/ARCHIVE/WSOP/WSOP Bracelet Event/` → WSOP Bracelet
- `/ARCHIVE/WSOP/WSOP Circuit Event/` → WSOPC Circuit
- `/ARCHIVE/HCL/` → HCL Cash Game Show
- `/ARCHIVE/PAD/` → PAD Cash Game Show
- `/ARCHIVE/GGMillions/` → GGMillions
- Unknown 경로 → OTHER 브랜드
- Windows 경로 정규화 (`\` → `/`)

#### infer_asset_type_from_path() (6개)

폴더 기반 AssetType 추론

- `STREAM` → AssetType.STREAM
- `SUBCLIP` → AssetType.SUBCLIP
- `Mastered` → AssetType.MASTER
- `Hand Clip` → AssetType.HAND_CLIP
- `Clean` → AssetType.CLEAN
- Unknown → AssetType.SUBCLIP (기본값)

#### generate_json_schema() (2개)
- JSON Schema 생성 확인
- Schema 구조 검증

#### generate_minimal_asset() (1개)
- 최소 Asset 생성 함수 테스트

### 5. 관계 테스트 (19개)

#### Asset-Segment 관계 (3개)
- `add_segment()` → parent_uuid 자동 설정
- `get_segments_by_type()` → 유형별 필터링
- `get_total_duration()` → 전체 길이 계산

#### Segment-PlayerInHand 관계 (5개)
- `get_player_names()` → 플레이어 이름 목록
- `add_tag()` → 태그 추가 (action, emotion, content)
- 중복 태그 방지

#### UDMDocument 변환 (3개)
- `from_asset()` → 기본/커스텀 source
- `to_json_dict()` → None 값 제외

#### Edge Cases (5개)
- 빈 segments 리스트 처리
- 플레이어 정보 없는 Segment
- 유니코드 문자 지원 (한글, 특수문자, 이모지)
- 매우 긴 설명 문자열 (10,000자)
- 같은 시간 범위의 여러 Segment

#### Integration Tests (3개)
- 전체 워크플로우: Asset 생성 → Segment 추가 → UDMDocument 변환 → JSON 직렬화
- 파일명 파싱 → Asset 생성
- 경로 추론 → Asset 생성

---

## 커버리지 결과

```
Name                Stmts   Miss  Cover   Missing
-------------------------------------------------
src\models\udm.py     297      8    97%   350, 354, 356, 358, 395, 571, 683, 790
-------------------------------------------------
TOTAL                 297      8    97%
```

**97% 코드 커버리지 달성**

### 미커버 라인 분석

- **350, 354, 356, 358**: `SituationFlags.to_tags()` 일부 분기 (hero-fold, hero-call, river-killer)
- **395, 571, 683**: Pydantic validator 내부 경고/통과 분기
- **790**: `model_json_schema_static()` 미사용 메서드

---

## 공통 픽스처 (conftest.py)

### 기본 픽스처 (3개)
- `sample_uuid`: 테스트용 고정 UUID
- `sample_year`: 2024
- `sample_brand`: Brand.WSOP

### EventContext 픽스처 (2개)
- `minimal_event_context`: 최소 필수 필드
- `full_event_context`: 모든 필드 포함

### TechSpec 픽스처 (2개)
- `minimal_tech_spec`: 기본값
- `full_tech_spec`: 모든 필드 포함

### PlayerInHand 픽스처 (2개)
- `sample_player`: 단일 플레이어
- `sample_players`: 2명 플레이어 리스트

### SituationFlags 픽스처 (1개)
- `sample_situation_flags`: 쿨러 상황

### Segment 픽스처 (2개)
- `minimal_segment`: 최소 필드
- `full_segment`: 모든 필드 포함

### Asset 픽스처 (2개)
- `minimal_asset`: 최소 필드
- `full_asset`: 모든 필드 포함

### UDMDocument 픽스처 (2개)
- `minimal_udm_document`: 최소 필드
- `full_udm_document`: 모든 필드 포함

### 팩토리 함수 (2개)
- `make_segment`: Segment 생성 팩토리
- `make_asset`: Asset 생성 팩토리

---

## TDD 모범 사례 적용

### AAA 패턴 (Arrange-Act-Assert)

모든 테스트는 3단계 구조를 따릅니다:

```python
def test_example(self):
    # Arrange - 테스트 데이터 준비
    segment = Segment(
        parent_asset_uuid=sample_uuid,
        time_in_sec=0.0,
        time_out_sec=60.0
    )

    # Act - 동작 실행
    duration = segment.duration_sec

    # Assert - 결과 검증
    assert duration == 60.0
```

### 테스트 독립성

- 각 테스트는 독립적으로 실행 가능
- 픽스처를 통한 데이터 격리
- 실행 순서 무관

### 의미 있는 테스트 이름

- `test_create_minimal_event_context`: 최소 필드 생성 테스트
- `test_time_out_greater_than_time_in`: 비즈니스 규칙 검증
- `test_infer_wsop_bracelet`: 경로 추론 테스트

### 엣지 케이스 커버리지

- 빈 리스트 처리
- 유니코드/특수문자
- 매우 긴 문자열
- 경계값 검증 (0, 5, 1970, 2100)

### 통합 테스트

- 실제 워크플로우 시뮬레이션
- 여러 모델 간 상호작용 검증
- JSON 직렬화/역직렬화

---

## 테스트 실행 시간

```
84 passed in 0.20s
```

**평균 2.4ms/test** - 매우 빠른 단위 테스트

---

## 향후 개선 사항

### 1. Property-Based Testing

Hypothesis를 사용한 랜덤 데이터 생성 테스트

```python
from hypothesis import given
import hypothesis.strategies as st

@given(st.integers(min_value=1970, max_value=2100))
def test_event_context_year_property(year):
    ctx = EventContext(year=year, brand=Brand.WSOP)
    assert ctx.year == year
```

### 2. Mutation Testing

mutmut을 사용한 테스트 품질 검증

```bash
mutmut run --paths-to-mutate=src/models/udm.py
```

### 3. Parametrize 확장

더 많은 데이터 조합 테스트

```python
@pytest.mark.parametrize("brand,event_type", [
    (Brand.WSOP, EventType.BRACELET),
    (Brand.WSOPC, EventType.CIRCUIT),
    (Brand.HCL, EventType.CASH_GAME_SHOW),
])
def test_brand_event_type_mapping(brand, event_type):
    # ...
```

### 4. 성능 벤치마크

pytest-benchmark를 사용한 성능 측정

```python
def test_parse_filename_benchmark(benchmark):
    result = benchmark(parse_filename, "WCLA24-15.mp4")
    assert result.code_prefix == "WCLA"
```

---

## 참조

- **PRD**: `docs/PRD-0008-UDM-FINAL-SCHEMA.md` v3.0.0
- **소스 코드**: `D:\AI\claude01\Archive_Converter\src\models\udm.py`
- **테스트 파일**: `D:\AI\claude01\Archive_Converter\tests\test_udm.py`
- **픽스처**: `D:\AI\claude01\Archive_Converter\tests\conftest.py`

---

## 작성자

- **작성일**: 2025-12-11
- **Test Engineer Agent**: Claude Code
- **테스트 프레임워크**: pytest 9.0.1
- **커버리지**: 97% (297 statements, 8 missing)
