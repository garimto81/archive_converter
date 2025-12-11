# PRD-0007: UDM Schema Specification

**Version**: 1.0.0
**Status**: Draft
**Created**: 2025-12-11
**Parent**: PRD-0001-MASTER-ORCHESTRATOR

---

## 1. Overview

### 1.1 Purpose

본 문서는 Archive Converter의 핵심인 **UDM(Universal Data Model)** 스키마를 정의합니다. 두 개의 실제 소스 데이터(WSOP Circuit 2024, WSOP Database)를 분석하여 모든 소스를 통합할 수 있는 표준 스키마를 설계합니다.

### 1.2 Source Data Analysis

#### Source 1: WSOP Circuit 2024 Sheet
- **ID**: `1_RN_W_ZQclSZA0Iez6XniCXVtjkkd5HNZwiT6l-z6d4`
- **Records**: 38개 핸드
- **특징**: 간단한 구조, 타임코드 기반, 다중 플레이어 컬럼

#### Source 2: WSOP Database Sheet
- **ID**: `1pUMPKe-OsKc-Xd8lH1cP9ctJO4hj3keXY5RwNFp2Mtk`
- **Records**: 200+ 핸드
- **특징**: UUID 기반, 밀리초/초 단위 시간, 상세 태깅 시스템

### 1.3 Design Goals

1. **통합성**: 두 소스 데이터를 손실 없이 수용
2. **확장성**: 향후 새로운 소스/필드 추가 가능
3. **호환성**: JSON, CSV, DB 등 다양한 출력 지원
4. **검색성**: 복잡한 쿼리 지원 (플레이어, 태그, 시간 범위)

---

## 2. Source Data Mapping Analysis

### 2.1 Field Comparison

| UDM Field | Source 1 (Circuit) | Source 2 (Database) | 통합 방안 |
|-----------|-------------------|---------------------|-----------|
| `segment_uuid` | - (없음, 생성 필요) | `id` | UUID 사용/생성 |
| `title` | - | `title` | 새 필드 추가 |
| `time_in_sec` | `In` (타임코드) | `time_start_S` | 초 단위 통일 |
| `time_out_sec` | `Out` (타임코드) | `time_end_S` | 초 단위 통일 |
| `event_context.year` | File Name에서 추출 | `Year_` | 연도 추출 |
| `event_context.series` | File Name에서 추출 | `ProjectName` | 시리즈명 |
| `event_context.location` | - | `Location` | 장소 |
| `event_context.venue` | - | `Venue` | 카지노/시설명 |
| `event_context.episode` | - | `EpisodeEvent` | 에피소드/이벤트명 |
| `rating` | `Hand Grade` (★) | `HandGrade` (★) | 별점 → 숫자 |
| `winner` | `Winner` | - (title에서 추출) | 승자명 |
| `hand_matchup` | `Hands` | `HANDTag` | 핸드 대결 |
| `players` | Player 1/2/3 컬럼 | `PlayersTags` (쉼표) | Array 통일 |
| `tags_action` | 플레이 태그 컬럼들 | `PokerPlayTags` | Array 통일 |
| `tags_emotion` | 감정 태그 컬럼들 | `Emotion` | Array 통일 |
| `tags_situation` | - | Badbeat/Bluff/Suckout/Cooler | 새 카테고리 |
| `adjective` | - | `Adjective` | 새 필드 |
| `all_in_stage` | - | `All-in` | 새 필드 |
| `runout_type` | - | `RUNOUTTag` | 새 필드 |
| `post_flop` | - | `PostFlop` | 새 필드 |
| `file_path` | `Nas Folder Link` | - | 파일 경로 |

### 2.2 Gap Analysis

| 항목 | Source 1 부족 | Source 2 부족 |
|------|--------------|--------------|
| **ID** | UUID 없음 | ✓ |
| **시간** | 타임코드 (변환 필요) | ✓ (초 단위) |
| **이벤트 정보** | 제한적 | ✓ (상세) |
| **파일 경로** | ✓ | 없음 |
| **승자** | ✓ | 없음 (추론 필요) |
| **상황 플래그** | 없음 | ✓ (Badbeat 등) |

---

## 3. UDM Schema Definition

### 3.1 Level 1: Asset Entity

물리적 파일(영상) 단위의 정보입니다.

```python
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class TechSpec(BaseModel):
    """기술 사양"""
    fps: float = Field(default=29.97, description="프레임레이트")
    resolution: Optional[str] = Field(None, description="해상도 (예: 1080p)")
    codec: Optional[str] = Field(None, description="코덱 (예: H.264)")
    duration_sec: Optional[float] = Field(None, description="전체 길이 (초)")

class EventContext(BaseModel):
    """이벤트 컨텍스트"""
    year: int = Field(..., ge=2000, le=2100, description="개최 연도")
    series: str = Field(..., description="시리즈명 (WSOP, WSOPC, WPT 등)")
    location: Optional[str] = Field(None, description="도시/지역")
    venue: Optional[str] = Field(None, description="카지노/시설명")
    episode: Optional[str] = Field(None, description="에피소드/이벤트명")
    game_variant: Optional[str] = Field(None, description="게임 종류 (NLH, PLO 등)")
    buy_in: Optional[str] = Field(None, description="바이인 금액")

class Asset(BaseModel):
    """물리적 파일 엔티티"""
    asset_uuid: UUID = Field(..., description="Asset 고유 ID (파일 해시 기반)")
    file_name: str = Field(..., min_length=1, description="파일명 (확장자 포함)")
    file_path_rel: Optional[str] = Field(None, description="NAS 상대 경로")
    file_path_abs: Optional[str] = Field(None, description="절대 경로")
    event_context: EventContext = Field(..., description="이벤트 정보")
    tech_spec: Optional[TechSpec] = Field(None, description="기술 사양")
    source_origin: str = Field(..., description="데이터 출처")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### 3.2 Level 2: Segment Entity

논리적 구간(핸드) 단위의 정보입니다.

```python
from enum import Enum
from typing import Literal

class GameType(str, Enum):
    TOURNAMENT = "TOURNAMENT"
    CASH_GAME = "CASH_GAME"
    SIT_N_GO = "SIT_N_GO"

class AllInStage(str, Enum):
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    NONE = "none"

class SituationType(str, Enum):
    COOLER = "cooler"
    BADBEAT = "badbeat"
    BLUFF = "bluff"
    SUCKOUT = "suckout"
    HERO_CALL = "hero_call"
    FOLD = "fold"

class Segment(BaseModel):
    """논리적 구간 엔티티 (핸드)"""

    # === 식별 정보 ===
    segment_uuid: UUID = Field(..., description="Segment 고유 ID")
    parent_asset_uuid: UUID = Field(..., description="부모 Asset UUID (FK)")

    # === 시간 정보 (초 단위, 소수점 3자리) ===
    time_in_sec: float = Field(..., ge=0, description="시작 시간 (초)")
    time_out_sec: float = Field(..., ge=0, description="종료 시간 (초)")
    time_in_ms: Optional[int] = Field(None, description="시작 시간 (밀리초)")
    time_out_ms: Optional[int] = Field(None, description="종료 시간 (밀리초)")

    # === 기본 정보 ===
    title: Optional[str] = Field(None, description="핸드 제목/설명")
    game_type: GameType = Field(default=GameType.TOURNAMENT, description="게임 타입")
    rating: Optional[int] = Field(None, ge=0, le=5, description="평점 (0-5)")

    # === 핸드 결과 ===
    winner: Optional[str] = Field(None, description="승자 이름 (정규화)")
    hand_matchup: Optional[str] = Field(None, description="핸드 대결 (예: AA vs KK)")
    pot_size: Optional[float] = Field(None, description="팟 크기")

    # === 참여자 ===
    players: Optional[list[str]] = Field(None, description="참여 플레이어 리스트")
    player_count: Optional[int] = Field(None, ge=2, description="참여자 수")

    # === 태그 시스템 ===
    tags_action: Optional[list[str]] = Field(None, description="액션 태그")
    tags_emotion: Optional[list[str]] = Field(None, description="감정 태그")
    tags_situation: Optional[list[SituationType]] = Field(None, description="상황 태그")
    tags_custom: Optional[list[str]] = Field(None, description="커스텀 태그")

    # === 상세 분석 (Source 2 확장) ===
    adjective: Optional[str] = Field(None, description="형용사 (brutal, insane 등)")
    all_in_stage: Optional[AllInStage] = Field(None, description="올인 시점")
    runout_type: Optional[str] = Field(None, description="런아웃 타입 (runner runner 등)")
    post_flop: Optional[bool] = Field(None, description="플롭 이후 진행 여부")

    # === 상황 플래그 (Boolean) ===
    is_cooler: bool = Field(default=False, description="쿨러 여부")
    is_badbeat: bool = Field(default=False, description="배드비트 여부")
    is_bluff: bool = Field(default=False, description="블러프 여부")
    is_suckout: bool = Field(default=False, description="석아웃 여부")

    # === 메모 ===
    description: Optional[str] = Field(None, description="기타 메모")
    notes: Optional[str] = Field(None, description="편집자 노트")

    # === 메타데이터 ===
    source_row_index: Optional[int] = Field(None, description="원본 행 번호")
    source_origin: Optional[str] = Field(None, description="데이터 출처")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # === Validators ===
    @validator("time_out_sec")
    def time_out_after_time_in(cls, v, values):
        if "time_in_sec" in values and v <= values["time_in_sec"]:
            raise ValueError("time_out_sec must be greater than time_in_sec")
        return v

    @validator("players")
    def normalize_players(cls, v):
        if v:
            return [p.strip() for p in v if p and p.strip()]
        return v

    @computed_field
    @property
    def duration_sec(self) -> float:
        """구간 길이 (초)"""
        return self.time_out_sec - self.time_in_sec
```

### 3.3 Complete UDM Document

Asset과 Segment를 포함한 완전한 UDM 문서입니다.

```python
class UDMDocument(BaseModel):
    """완전한 UDM 문서"""

    # === 메타데이터 ===
    schema_version: str = Field(default="1.0.0", description="스키마 버전")
    exported_at: datetime = Field(default_factory=datetime.utcnow)
    converter_version: str = Field(default="1.0.0", description="변환기 버전")
    profile_used: Optional[str] = Field(None, description="사용된 프로파일")
    source_file: Optional[str] = Field(None, description="원본 파일")

    # === 데이터 ===
    assets: list[Asset] = Field(default_factory=list, description="Asset 리스트")

    # === 통계 ===
    @computed_field
    @property
    def total_assets(self) -> int:
        return len(self.assets)

    @computed_field
    @property
    def total_segments(self) -> int:
        return sum(len(a.segments) for a in self.assets if hasattr(a, 'segments'))
```

---

## 4. Enum & Type Definitions

### 4.1 Series Types

```python
class SeriesType(str, Enum):
    """포커 시리즈 타입"""
    WSOP = "WSOP"                    # World Series of Poker
    WSOPC = "WSOPC"                  # WSOP Circuit
    WSOP_EUROPE = "WSOP_EUROPE"     # WSOP Europe
    WSOP_PARADISE = "WSOP_PARADISE" # WSOP Paradise
    WSOP_ASIA = "WSOP_ASIA"         # WSOP Asia
    WPT = "WPT"                      # World Poker Tour
    EPT = "EPT"                      # European Poker Tour
    OTHER = "OTHER"
```

### 4.2 Game Variants

```python
class GameVariant(str, Enum):
    """게임 종류"""
    NLH = "NLH"           # No Limit Hold'em
    PLO = "PLO"           # Pot Limit Omaha
    PLO8 = "PLO8"         # PLO Hi-Lo
    HORSE = "HORSE"       # Mixed Game
    RAZZ = "RAZZ"
    STUD = "STUD"
    MIXED = "MIXED"
    OTHER = "OTHER"
```

### 4.3 Action Tags (Predefined)

```python
ACTION_TAGS = [
    # 프리플롭
    "3bet", "4bet", "5bet", "squeeze", "limp", "iso-raise",
    # 포스트플롭
    "c-bet", "check-raise", "float", "probe", "donk-bet",
    # 올인
    "preflop-allin", "flop-allin", "turn-allin", "river-allin",
    # 플레이 스타일
    "bluff", "semi-bluff", "value-bet", "thin-value",
    "hero-call", "hero-fold", "snap-call", "tank-fold",
    # 결과
    "cooler", "set-over-set", "flush-over-flush",
    "runner-runner", "one-outer", "bad-beat", "suckout"
]
```

### 4.4 Emotion Tags (Predefined)

```python
EMOTION_TAGS = [
    # 긍정
    "excitement", "joy", "relief", "celebration",
    # 부정
    "frustration", "disappointment", "tilt", "regret",
    # 중립
    "intense", "dramatic", "suspense", "shock",
    # 형용사
    "brutal", "insane", "incredible", "amazing", "sick"
]
```

---

## 5. JSON Schema (Golden Record)

### 5.1 완전한 JSON 예시

```json
{
  "_metadata": {
    "schema_version": "1.0.0",
    "exported_at": "2025-12-11T15:30:00Z",
    "converter_version": "1.0.0",
    "profile_used": "wsop_database_v1",
    "source_file": "WSOP_Database.csv"
  },
  "assets": [
    {
      "asset_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "file_name": "2024 WSOP ME Day7 Final Table.mp4",
      "file_path_rel": "/WSOP/2024/Main_Event/Day7/",
      "event_context": {
        "year": 2024,
        "series": "WSOP",
        "location": "Las Vegas",
        "venue": "Horseshoe Casino",
        "episode": "Main Event Final Table",
        "game_variant": "NLH",
        "buy_in": "$10,000"
      },
      "tech_spec": {
        "fps": 29.97,
        "resolution": "1080p",
        "duration_sec": 14400.0
      },
      "source_origin": "WSOP_Database_v1",
      "segments": [
        {
          "segment_uuid": "4fcb98f2-ee5b-11ef-9be4-faa8f6b7d111",
          "parent_asset_uuid": "550e8400-e29b-41d4-a716-446655440000",
          "time_in_sec": 425.5,
          "time_out_sec": 510.2,
          "time_in_ms": 425500,
          "time_out_ms": 510200,
          "title": "Fan doubles KK vs Yea QQs",
          "game_type": "TOURNAMENT",
          "rating": 4,
          "winner": "Chih Fan",
          "hand_matchup": "KK vs QQ",
          "players": ["Steve Yea", "Chih Fan"],
          "player_count": 2,
          "tags_action": ["preflop-allin", "cooler"],
          "tags_emotion": ["intense", "dramatic"],
          "tags_situation": ["cooler"],
          "adjective": "brutal",
          "all_in_stage": "preflop",
          "runout_type": null,
          "post_flop": false,
          "is_cooler": true,
          "is_badbeat": false,
          "is_bluff": false,
          "is_suckout": false,
          "description": "Classic cooler situation at final table",
          "source_row_index": 1
        },
        {
          "segment_uuid": "5abc12d3-ff6c-22fg-0cf5-gbb9g7c8e222",
          "parent_asset_uuid": "550e8400-e29b-41d4-a716-446655440000",
          "time_in_sec": 1200.0,
          "time_out_sec": 1350.5,
          "title": "Epic bluff by Negreanu",
          "game_type": "TOURNAMENT",
          "rating": 5,
          "winner": "Daniel Negreanu",
          "hand_matchup": "72o vs AK",
          "players": ["Daniel Negreanu", "Phil Hellmuth"],
          "player_count": 2,
          "tags_action": ["bluff", "river-allin", "hero-fold"],
          "tags_emotion": ["excitement", "incredible"],
          "tags_situation": ["bluff"],
          "adjective": "insane",
          "all_in_stage": "river",
          "post_flop": true,
          "is_bluff": true,
          "description": "Negreanu's legendary 72 bluff",
          "source_row_index": 2
        }
      ]
    }
  ],
  "_stats": {
    "total_assets": 1,
    "total_segments": 2,
    "total_duration_sec": 235.2
  }
}
```

---

## 6. Profile Mapping Templates

### 6.1 Source 1 (Circuit Sheet) Profile

```yaml
# profiles/wsop_circuit_2024.yaml
profile:
  name: "wsop_circuit_2024"
  version: "1.0.0"
  source_id: "1_RN_W_ZQclSZA0Iez6XniCXVtjkkd5HNZwiT6l-z6d4"

source:
  type: "google_sheet"
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
    file_path_rel:
      type: "direct"
      source_column: "Nas Folder Link"
    event_context:
      type: "object"
      fields:
        year:
          type: "extract"
          source_column: "File Name"
          pattern: "\\b(20\\d{2})\\b"
          transform: "to_int"
        series:
          type: "constant"
          value: "WSOPC"
        location:
          type: "extract"
          source_column: "File Name"
          pattern: "WSOPC\\s+(\\w+)"
    source_origin:
      type: "constant"
      value: "Circuit_Sheet_2024"

  segment_mapping:
    segment_uuid:
      type: "generate"
      strategy: "uuid4"
    time_in_sec:
      type: "timecode"
      source_column: "In"
      fps: 29.97
    time_out_sec:
      type: "timecode"
      source_column: "Out"
      fps: 29.97
    rating:
      type: "star_to_int"
      source_column: "Hand Grade"
      mapping:
        "★": 1
        "★★": 2
        "★★★": 3
        "★★★★": 4
        "★★★★★": 5
    winner:
      type: "direct"
      source_column: "Winner"
      normalize: true
    hand_matchup:
      type: "direct"
      source_column: "Hands"
    players:
      type: "array"
      source_columns:
        - "Player 1"
        - "Player 2"
        - "Player 3"
      remove_empty: true
      normalize: true
    tags_action:
      type: "collect"
      source_columns:
        - "Play Tag 1"
        - "Play Tag 2"
        - "Play Tag 3"
      remove_empty: true
    tags_emotion:
      type: "collect"
      source_columns:
        - "Emotion Tag 1"
        - "Emotion Tag 2"
      remove_empty: true
```

### 6.2 Source 2 (Database Sheet) Profile

```yaml
# profiles/wsop_database_v1.yaml
profile:
  name: "wsop_database_v1"
  version: "1.0.0"
  source_id: "1pUMPKe-OsKc-Xd8lH1cP9ctJO4hj3keXY5RwNFp2Mtk"

source:
  type: "google_sheet"
  options:
    header_row: 1

transform:
  asset_mapping:
    asset_uuid:
      type: "generate"
      strategy: "content_hash"
      source_columns: ["ProjectName", "Year_", "EpisodeEvent"]
    event_context:
      type: "object"
      fields:
        year:
          type: "direct"
          source_column: "Year_"
          transform: "to_int"
        series:
          type: "map"
          source_column: "ProjectName"
          mapping:
            "WSOP": "WSOP"
            "WSOP PARADISE": "WSOP_PARADISE"
            "WSOPC": "WSOPC"
        location:
          type: "direct"
          source_column: "Location"
        venue:
          type: "direct"
          source_column: "Venue"
        episode:
          type: "direct"
          source_column: "EpisodeEvent"
    source_origin:
      type: "constant"
      value: "WSOP_Database_v1"

  segment_mapping:
    segment_uuid:
      type: "direct"
      source_column: "id"
    title:
      type: "direct"
      source_column: "title"
    time_in_sec:
      type: "direct"
      source_column: "time_start_S"
      transform: "to_float"
    time_out_sec:
      type: "direct"
      source_column: "time_end_S"
      transform: "to_float"
    time_in_ms:
      type: "direct"
      source_column: "time_start_ms"
      transform: "to_int"
    time_out_ms:
      type: "direct"
      source_column: "time_end_ms"
      transform: "to_int"
    rating:
      type: "star_to_int"
      source_column: "HandGrade"
    hand_matchup:
      type: "direct"
      source_column: "HANDTag"
    players:
      type: "split"
      source_column: "PlayersTags"
      delimiter: ","
      normalize: true
    tags_action:
      type: "split"
      source_column: "PokerPlayTags"
      delimiter: ","
    tags_emotion:
      type: "split"
      source_column: "Emotion"
      delimiter: ","
    adjective:
      type: "direct"
      source_column: "Adjective"
    all_in_stage:
      type: "map"
      source_column: "All-in"
      mapping:
        "preflop allin": "preflop"
        "flop allin": "flop"
        "turn allin": "turn"
        "river allin": "river"
        "": "none"
    runout_type:
      type: "direct"
      source_column: "RUNOUTTag"
    post_flop:
      type: "boolean"
      source_column: "PostFlop"
    is_cooler:
      type: "boolean"
      source_column: "Cooler"
    is_badbeat:
      type: "boolean"
      source_column: "Badbeat"
    is_bluff:
      type: "boolean"
      source_column: "Bluff"
    is_suckout:
      type: "boolean"
      source_column: "Suckout"
```

---

## 7. Validation Rules

### 7.1 Schema Validation

```python
SCHEMA_RULES = {
    # Required fields
    "segment_uuid": {"required": True, "type": "uuid"},
    "parent_asset_uuid": {"required": True, "type": "uuid"},
    "time_in_sec": {"required": True, "type": "float", "min": 0},
    "time_out_sec": {"required": True, "type": "float", "min": 0},
    "game_type": {"required": True, "type": "enum", "values": ["TOURNAMENT", "CASH_GAME", "SIT_N_GO"]},

    # Optional with constraints
    "rating": {"required": False, "type": "int", "min": 0, "max": 5},
    "players": {"required": False, "type": "array", "min_items": 2},
}
```

### 7.2 Business Rules

```python
BUSINESS_RULES = [
    {
        "id": "BR-001",
        "name": "time_consistency",
        "description": "time_out_sec > time_in_sec",
        "severity": "ERROR"
    },
    {
        "id": "BR-002",
        "name": "winner_in_players",
        "description": "winner가 players 리스트에 포함",
        "severity": "WARNING"
    },
    {
        "id": "BR-003",
        "name": "reasonable_duration",
        "description": "핸드 길이 10초-3600초",
        "severity": "WARNING"
    },
    {
        "id": "BR-004",
        "name": "unique_segment_uuid",
        "description": "segment_uuid 유일성",
        "severity": "ERROR"
    },
    {
        "id": "BR-005",
        "name": "situation_flag_consistency",
        "description": "is_cooler=true면 tags_situation에 'cooler' 포함",
        "severity": "INFO"
    }
]
```

---

## 8. Migration & Compatibility

### 8.1 Version History

| Version | Changes | Breaking |
|---------|---------|----------|
| 1.0.0 | Initial schema | - |

### 8.2 Future Extensions

```python
# 향후 추가 예정 필드
PLANNED_FIELDS = {
    # v1.1.0
    "board_cards": "플롭/턴/리버 카드",
    "hole_cards": "플레이어별 홀카드",
    "betting_action": "베팅 시퀀스",

    # v1.2.0
    "thumbnail_url": "썸네일 이미지",
    "clip_url": "클립 URL",
    "ai_analysis": "AI 분석 결과"
}
```

---

## 9. Related PRDs

- **PRD-0001**: Master Orchestrator (Parent)
- **PRD-0003**: Transform Agent (스키마 적용)
- **PRD-0004**: Validate Agent (검증 규칙)
- **PRD-0006**: Profile Manager (프로파일 관리)

---

## 10. Appendix

### A. Field Type Reference

| Type | Python | JSON | Description |
|------|--------|------|-------------|
| `uuid` | `UUID` | `string` | UUID v4 형식 |
| `string` | `str` | `string` | 문자열 |
| `int` | `int` | `number` | 정수 |
| `float` | `float` | `number` | 소수점 숫자 |
| `bool` | `bool` | `boolean` | 불리언 |
| `array` | `list[T]` | `array` | 배열 |
| `object` | `dict` | `object` | 객체 |
| `datetime` | `datetime` | `string` | ISO 8601 형식 |
| `enum` | `Enum` | `string` | 열거형 |

### B. Timecode Conversion

```python
def timecode_to_seconds(tc: str, fps: float = 29.97) -> float:
    """타임코드 → 초 변환

    Args:
        tc: "HH:MM:SS:FF" 형식 타임코드
        fps: 프레임레이트

    Returns:
        초 단위 (소수점 3자리)
    """
    parts = tc.split(":")
    if len(parts) == 4:
        h, m, s, f = map(int, parts)
        return round(h * 3600 + m * 60 + s + f / fps, 3)
    elif len(parts) == 3:
        h, m, s = map(int, parts)
        return round(h * 3600 + m * 60 + s, 3)
    raise ValueError(f"Invalid timecode format: {tc}")
```

### C. Star Rating Conversion

```python
def star_to_int(stars: str) -> int:
    """별점 → 정수 변환

    Args:
        stars: "★", "★★", "★★★" 등

    Returns:
        1-5 정수
    """
    if not stars:
        return 0
    count = stars.count("★")
    return min(max(count, 0), 5)
```
