# PRD-0009: Source Data Specification

**Version**: 1.0.0
**Status**: Draft
**Created**: 2025-12-11
**Updated**: 2025-12-11
**Parent**: PRD-0001-MASTER-ORCHESTRATOR

---

## 1. Executive Summary

### 1.1 문서 목적

이 문서는 Archive Converter 프로젝트의 핵심인 **"다양한 소스 → UDM 변환"**을 위한 각 소스별 데이터 명세를 정의합니다.

### 1.2 범위

| 소스 유형 | 상태 | 데이터 수 |
|----------|------|----------|
| **Google Sheets** | 분석 완료 | 2개 시트, 238+ 레코드 |
| **NAS 폴더 스캔** | 분석 완료 | 194개 폴더, 1,400+ 파일 |
| **MAM (Iconik)** | 스키마 정의 필요 | TBD |
| **MAM (CatDV)** | 스키마 정의 필요 | TBD |
| **Legacy Excel** | 스키마 정의 필요 | TBD |

### 1.3 핵심 목표

1. **소스별 컬럼 구조 정의**: 모든 소스 필드 명세
2. **UDM 매핑 테이블 제공**: Source → UDM 변환 규칙
3. **데이터 품질 규칙 수립**: 필수/선택 필드, 검증 규칙
4. **프로파일 설계 지원**: Profile Manager가 사용할 매핑 스키마 제공

---

## 2. Google Sheets 소스

### 2.1 WSOP Circuit 2024 Sheet

#### 2.1.1 기본 정보

| 항목 | 값 |
|------|-----|
| **Sheet ID** | `1_RN_W_ZQclSZA0Iez6XniCXVtjkkd5HNZwiT6l-z6d4` |
| **레코드 수** | 38 |
| **시트명** | Circuit DB |
| **데이터 유형** | 핸드 단위 (Segment Level) |
| **시간 형식** | 타임코드 (`HH:MM:SS:FF` 또는 `HH:MM:SS`) |

#### 2.1.2 컬럼 구조

| 컬럼명 | 데이터 타입 | 예시 | 필수 여부 | UDM 필드 | 비고 |
|--------|------------|------|----------|----------|------|
| `File Name` | String | `WCLA24-01.mp4` | ✅ | `asset.file_name` | 에셋 식별자 |
| `In` | Timecode | `00:01:30:15` | ✅ | `segment.time_in_sec` | **변환 필요** (TC→Sec) |
| `Out` | Timecode | `00:02:45:20` | ✅ | `segment.time_out_sec` | **변환 필요** (TC→Sec) |
| `Hand Grade` | String (★) | `★★★★★` | ❌ | `segment.rating` | ★ 개수 → Integer |
| `Winner` | String | `Daniel Negreanu` | ❌ | `segment.winner` | **정규화 필요** |
| `Hands` | String | `AA vs KK` | ❌ | `segment.players[].hand` | **파싱 필요** → `PlayerInHand` |
| `Player 1` | String | `Daniel Negreanu` | ❌ | `segment.players[0].name` | 배열 수집 |
| `Player 2` | String | `Phil Hellmuth` | ❌ | `segment.players[1].name` | 배열 수집 |
| `Player 3` | String | `Unknown Player` | ❌ | `segment.players[2].name` | 배열 수집 |
| `Play Tag 1` | String | `Preflop All-in` | ❌ | `segment.tags_action[0]` | 배열 수집 |
| `Play Tag 2` | String | `Cooler` | ❌ | `segment.tags_action[1]` | 배열 수집 |
| `Play Tag 3~7` | String | - | ❌ | `segment.tags_action[2~6]` | 배열 수집 |
| `Emotion Tag 1` | String | `Excitement` | ❌ | `segment.tags_emotion[0]` | 배열 수집 |
| `Emotion Tag 2` | String | `Suckout` | ❌ | `segment.tags_emotion[1]` | 배열 수집 |
| `Nas Folder Link` | String (URL) | `/ARCHIVE/WSOP/...` | ❌ | `asset.file_path_rel` | 경로 정보 |

#### 2.1.3 추론 필드 (File Name 기반)

| 추출 항목 | 정규식 패턴 | 예시 | UDM 필드 |
|----------|------------|------|----------|
| **코드** | `^(WCLA)` | `WCLA` | `file_name_meta.code_prefix` |
| **연도** | `(\d{2})` | `24` → 2024 | `event_context.year` |
| **시퀀스** | `-(\d+)` | `01` | `file_name_meta.sequence_num` |
| **브랜드** | 고정값 | - | `event_context.brand = "WSOPC"` |
| **이벤트 유형** | 고정값 | - | `event_context.event_type = "CIRCUIT"` |
| **장소** | 고정값 | - | `event_context.location = "Los Angeles"` |

#### 2.1.4 변환 로직

```python
# Timecode → Seconds 변환
def timecode_to_seconds(tc: str, fps: float = 29.97) -> float:
    """
    타임코드 → 초 변환

    지원 형식:
    - HH:MM:SS:FF (29.97fps 기준)
    - HH:MM:SS
    """
    parts = tc.split(":")
    if len(parts) == 4:  # HH:MM:SS:FF
        h, m, s, f = map(int, parts)
        return h * 3600 + m * 60 + s + (f / fps)
    elif len(parts) == 3:  # HH:MM:SS
        h, m, s = map(int, parts)
        return h * 3600 + m * 60 + s
    else:
        raise ValueError(f"Invalid timecode format: {tc}")

# Hand Matchup 파싱
def parse_hand_matchup(matchup: str, players: list[str]) -> list[PlayerInHand]:
    """
    "AA vs KK" → [PlayerInHand, PlayerInHand]

    가정:
    - players[0]이 첫 번째 핸드 소유
    - players[1]이 두 번째 핸드 소유
    """
    hands = matchup.split(" vs ")
    result = []
    for i, hand in enumerate(hands):
        if i < len(players):
            result.append(PlayerInHand(
                name=players[i],
                hand=hand.strip()
            ))
    return result

# Rating 변환
def stars_to_rating(stars: str) -> int:
    """★★★★★ → 5"""
    return stars.count("★")
```

#### 2.1.5 샘플 레코드 → UDM

**Raw Data**:
```csv
File Name,In,Out,Hand Grade,Winner,Hands,Player 1,Player 2,Emotion Tag 1
WCLA24-01.mp4,00:01:30:15,00:02:45:20,★★★★★,Daniel Negreanu,AA vs KK,Daniel Negreanu,Phil Hellmuth,Excitement
```

**변환 후 UDM**:
```json
{
  "asset": {
    "asset_uuid": "generated-from-file-hash",
    "file_name": "WCLA24-01.mp4",
    "asset_type": "SUBCLIP",
    "event_context": {
      "year": 2024,
      "brand": "WSOPC",
      "event_type": "CIRCUIT",
      "location": "Los Angeles"
    },
    "file_name_meta": {
      "code_prefix": "WCLA",
      "year_code": "24",
      "sequence_num": 1
    },
    "source_origin": "GoogleSheets_Circuit_2024",
    "segments": [
      {
        "segment_uuid": "generated-uuid",
        "parent_asset_uuid": "generated-from-file-hash",
        "segment_type": "HAND",
        "time_in_sec": 90.5,
        "time_out_sec": 165.67,
        "game_type": "TOURNAMENT",
        "rating": 5,
        "winner": "Daniel Negreanu",
        "players": [
          {"name": "Daniel Negreanu", "hand": "AA"},
          {"name": "Phil Hellmuth", "hand": "KK"}
        ],
        "tags_emotion": ["Excitement"]
      }
    ]
  }
}
```

---

### 2.2 WSOP Database Sheet

#### 2.2.1 기본 정보

| 항목 | 값 |
|------|-----|
| **Sheet ID** | `1pUMPKe-OsKc-Xd8lH1cP9ctJO4hj3keXY5RwNFp2Mtk` |
| **레코드 수** | 200+ |
| **데이터 유형** | 핸드 단위 (Segment Level) |
| **시간 형식** | 초 (Float) - **변환 불필요** |
| **특징** | UUID 존재, Boolean 플래그 풍부 |

#### 2.2.2 컬럼 구조

| 컬럼명 | 데이터 타입 | 예시 | 필수 | UDM 필드 | 비고 |
|--------|------------|------|------|----------|------|
| `id` | UUID | `550e8400-...` | ✅ | `segment.segment_uuid` | **그대로 사용** |
| `ProjectName` | String | `WSOP` | ✅ | `event_context.brand` | 매핑 필요 |
| `Year_` | Integer | `2024` | ✅ | `event_context.year` | Direct |
| `Location` | String | `Las Vegas` | ❌ | `event_context.location` | Enum 변환 |
| `Venue` | String | `Horseshoe Casino` | ❌ | `event_context.venue` | Direct |
| `EpisodeEvent` | String | `Main Event` | ❌ | `event_context.episode_title` | Direct |
| `time_start_S` | Float | `425.5` | ✅ | `segment.time_in_sec` | **변환 불필요** |
| `time_end_S` | Float | `510.2` | ✅ | `segment.time_out_sec` | **변환 불필요** |
| `title` | String | `Epic cooler` | ❌ | `segment.title` | Direct |
| `HandGrade` | String (★) | `★★★★★` | ❌ | `segment.rating` | ★ 개수 → Integer |
| `HANDTag` | String | `AA vs KK` | ❌ | `segment.players[].hand` | 파싱 필요 |
| `PlayersTags` | String (CSV) | `Player A, Player B` | ❌ | `segment.players[].name` | Split by `,` |
| `PokerPlayTags` | String (CSV) | `preflop-allin, cooler` | ❌ | `segment.tags_action` | Split by `,` |
| `Emotion` | String (CSV) | `brutal, excitement` | ❌ | `segment.tags_emotion` | Split by `,` |
| `Adjective` | String | `brutal` | ❌ | `segment.adjective` | Direct |
| `All-in` | String | `preflop` | ❌ | `segment.all_in_stage` | Enum 변환 |
| `RUNOUTTag` | String | `runner-runner` | ❌ | `segment.runout_type` | Direct |
| `Cooler` | Boolean | `TRUE` | ❌ | `situation_flags.is_cooler` | Boolean |
| `Badbeat` | Boolean | `FALSE` | ❌ | `situation_flags.is_badbeat` | Boolean |
| `Suckout` | Boolean | `TRUE` | ❌ | `situation_flags.is_suckout` | Boolean |
| `Bluff` | Boolean | `FALSE` | ❌ | `situation_flags.is_bluff` | Boolean |
| `Hero Call` | Boolean | `FALSE` | ❌ | `situation_flags.is_hero_call` | Boolean |
| `Hero Fold` | Boolean | `FALSE` | ❌ | `situation_flags.is_hero_fold` | Boolean |
| `River Killer` | Boolean | `FALSE` | ❌ | `situation_flags.is_river_killer` | Boolean |

#### 2.2.3 ProjectName → Brand 매핑

| ProjectName (Source) | Brand (UDM) | EventType |
|---------------------|-------------|-----------|
| `WSOP` | `WSOP` | `BRACELET` |
| `WSOPC` | `WSOPC` | `CIRCUIT` |
| `WSOPE` | `WSOPE` | `BRACELET` |
| `WSOPP` | `WSOPP` | `SUPER_MAIN` |
| `HCL` | `HCL` | `CASH_GAME_SHOW` |
| `PAD` | `PAD` | `CASH_GAME_SHOW` |
| `GGMillions` | `GG_MILLIONS` | `CASH_GAME_SHOW` |
| `MPP` | `MPP` | `BRACELET` |
| `GOG` | `GOG` | `CASH_GAME_SHOW` |

#### 2.2.4 변환 로직

```python
def parse_players_tags(players_str: str, hands_str: str) -> list[PlayerInHand]:
    """
    players_str: "Player A, Player B, Player C"
    hands_str: "AA vs KK"

    → [PlayerInHand(...), PlayerInHand(...)]
    """
    players = [p.strip() for p in players_str.split(",")]
    hands = [h.strip() for h in hands_str.split(" vs ")] if hands_str else []

    result = []
    for i, player in enumerate(players):
        result.append(PlayerInHand(
            name=player,
            hand=hands[i] if i < len(hands) else None
        ))
    return result

def build_situation_flags(row: dict) -> SituationFlags:
    """Boolean 컬럼들을 SituationFlags 객체로 변환"""
    return SituationFlags(
        is_cooler=row.get("Cooler", False),
        is_badbeat=row.get("Badbeat", False),
        is_suckout=row.get("Suckout", False),
        is_bluff=row.get("Bluff", False),
        is_hero_call=row.get("Hero Call", False),
        is_hero_fold=row.get("Hero Fold", False),
        is_river_killer=row.get("River Killer", False)
    )
```

#### 2.2.5 샘플 레코드 → UDM

**Raw Data**:
```csv
id,ProjectName,Year_,time_start_S,time_end_S,title,PlayersTags,HANDTag,Cooler,All-in
550e8400-...,WSOP,2024,425.5,510.2,Epic cooler,"Player A, Player B",AA vs KK,TRUE,preflop
```

**변환 후 UDM**:
```json
{
  "asset": {
    "asset_uuid": "generated-from-project-context",
    "file_name": "inferred-or-unknown.mp4",
    "asset_type": "SUBCLIP",
    "event_context": {
      "year": 2024,
      "brand": "WSOP",
      "event_type": "BRACELET"
    },
    "source_origin": "GoogleSheets_Database",
    "segments": [
      {
        "segment_uuid": "550e8400-...",
        "parent_asset_uuid": "generated-from-project-context",
        "segment_type": "HAND",
        "time_in_sec": 425.5,
        "time_out_sec": 510.2,
        "title": "Epic cooler",
        "game_type": "TOURNAMENT",
        "players": [
          {"name": "Player A", "hand": "AA"},
          {"name": "Player B", "hand": "KK"}
        ],
        "situation_flags": {
          "is_cooler": true
        },
        "all_in_stage": "preflop"
      }
    ]
  }
}
```

---

### 2.3 두 시트 간 차이점 요약

| 항목 | Circuit Sheet | Database Sheet |
|------|---------------|----------------|
| **ID 생성** | 필요 (자동 생성) | 불필요 (UUID 존재) |
| **시간 변환** | 필수 (TC→Sec) | 불필요 (이미 Sec) |
| **이벤트 정보** | 파일명 파싱 필요 | 컬럼에 명시 |
| **태그 방식** | 다중 컬럼 (Play Tag 1~7) | 쉼표 구분 문자열 |
| **상황 플래그** | 없음 | Boolean 컬럼 풍부 |
| **플레이어 구조** | 개별 컬럼 (Player 1~3) | CSV 문자열 |
| **데이터 품질** | 파일명 의존도 높음 | 구조화 잘 됨 |

---

## 3. NAS 폴더 스캔 소스

### 3.1 기본 정보

| 항목 | 값 |
|------|-----|
| **경로** | `\\10.10.100.122\docker\GGPNAs\ARCHIVE\` |
| **폴더 수** | 194개 |
| **파일 수** | 1,400+ |
| **총 용량** | ~17 TB |
| **브랜드** | WSOP, HCL, PAD, GGMillions, MPP, GOG |
| **연도 범위** | 1973-2025 (52년) |

### 3.2 폴더 계층 구조 (6 Levels)

| 레벨 | 의미 | 예시 | UDM 필드 |
|------|------|------|----------|
| **L1** | Brand | `WSOP/`, `HCL/`, `PAD/` | `event_context.brand` |
| **L2** | Event Category | `WSOP Bracelet Event/`, `Circuit Event/` | `event_context.event_type` |
| **L3** | Location | `WSOP-EUROPE/`, `WSOP-LAS VEGAS/` | `event_context.location` |
| **L4** | Year + Event | `2025 WSOP-Europe/`, `2024 WSOP Circuit LA/` | `event_context.year` |
| **L5** | Specific Event | `#14 MAIN EVENT/`, `Event #21/` | `event_context.event_number` |
| **L6** | Asset Type/Day | `STREAM/`, `SUBCLIP/`, `Day 1A/` | `asset.asset_type` |

### 3.3 경로 → UDM 매핑

```python
# NAS 경로 기반 브랜드 추출
NAS_PATH_BRAND_MAP = {
    "/ARCHIVE/WSOP/WSOP Bracelet Event/": {
        "brand": "WSOP",
        "event_type": "BRACELET"
    },
    "/ARCHIVE/WSOP/WSOP Circuit Event/": {
        "brand": "WSOPC",
        "event_type": "CIRCUIT"
    },
    "/ARCHIVE/HCL/": {
        "brand": "HCL",
        "event_type": "CASH_GAME_SHOW"
    },
    "/ARCHIVE/PAD/": {
        "brand": "PAD",
        "event_type": "CASH_GAME_SHOW"
    },
    "/ARCHIVE/GGMillions/": {
        "brand": "GGMillions",
        "event_type": "CASH_GAME_SHOW"
    },
    "/ARCHIVE/MPP/": {
        "brand": "MPP",
        "event_type": "BRACELET"
    },
    "/ARCHIVE/GOG 최종/": {
        "brand": "GOG",
        "event_type": "CASH_GAME_SHOW"
    }
}

# 폴더명 기반 AssetType 추출
FOLDER_ASSET_TYPE_MAP = {
    "STREAM": "STREAM",
    "SUBCLIP": "SUBCLIP",
    "Mastered": "MASTER",
    "Clean": "CLEAN",
    "NO COMMENTARY": "NO_COMMENTARY",
    "Hand Clip": "HAND_CLIP",
    "MOVs": "MOV",
    "MXFs": "MXF",
    "Generic": "GENERIC"
}
```

### 3.4 파일명 패턴 분석

#### 3.4.1 패턴 1: Circuit Subclip (WCLA)

**패턴**: `WCLA{YY}-{NN}.mp4`

**예시**: `WCLA24-15.mp4`

**정규식**:
```python
r"^(?P<code>WCLA)(?P<year>\d{2})-(?P<num>\d+)\.(?P<ext>\w+)$"
```

**UDM 매핑**:
| 추출값 | UDM 필드 | 변환 |
|--------|----------|------|
| `WCLA` | `file_name_meta.code_prefix` | Direct |
| `24` | `event_context.year` | `2000 + int(year)` |
| `15` | `file_name_meta.sequence_num` | `int(num)` |
| - | `event_context.brand` | `"WSOPC"` (고정) |
| - | `event_context.location` | `"Los Angeles"` (고정) |

#### 3.4.2 패턴 2: Paradise Subclip (WP)

**패턴**: `WP{YY}-{TYPE}-{NN}.mp4`

**예시**: `WP23-PE-01.mp4` (Player Emotion)

**정규식**:
```python
r"^(?P<code>WP)(?P<year>\d{2})-(?P<type>PE|ET|HB)-(?P<num>\d+)\.(?P<ext>\w+)$"
```

**UDM 매핑**:
| 추출값 | UDM 필드 | 변환 |
|--------|----------|------|
| `WP` | `file_name_meta.code_prefix` | Direct |
| `23` | `event_context.year` | `2000 + int(year)` |
| `PE` | `segment.segment_type` | `"PE"` → `SegmentType.PLAYER_EMOTION` |
| `01` | `file_name_meta.sequence_num` | `int(num)` |
| - | `event_context.brand` | `"WSOPP"` (고정) |

**Type 코드 매핑**:
| 코드 | SegmentType | 설명 |
|------|-------------|------|
| `PE` | `PLAYER_EMOTION` | Player Emotion |
| `ET` | `HAND` | Episode/Tournament |
| `HB` | `HIGHLIGHT` | Highlight/Best |

#### 3.4.3 패턴 3: PAD Episode

**패턴**: `PAD_S{SS}_EP{NN}_{DESC}.mp4`

**예시**: `PAD_S13_EP01_GGPoker-001.mp4`

**정규식**:
```python
r"^PAD_S(?P<season>\d+)_EP(?P<episode>\d+)_(?P<desc>.+)\.(?P<ext>\w+)$"
```

**UDM 매핑**:
| 추출값 | UDM 필드 | 변환 |
|--------|----------|------|
| `13` | `event_context.season` | `int(season)` |
| `01` | `event_context.episode` | `int(episode)` |
| `GGPoker-001` | `file_name_meta.raw_description` | Direct |
| - | `event_context.brand` | `"PAD"` (고정) |

#### 3.4.4 패턴 4: WSOP Mastered

**패턴**: `{순번}-wsop-{년도}-be-ev-{이벤트번호}-{바이인}-{게임}-{태그}-{설명}.mp4`

**예시**: `10-wsop-2024-be-ev-21-25k-nlh-hr-ft-schutten-reclaims-chip-lead.mp4`

**정규식**:
```python
r"^(?P<num>\d+)-wsop-(?P<year>\d{4})-be-ev-(?P<event>\d+)-(?P<buyin>\d+k?)-(?P<game>nlh|plo|stud)-(?P<tags>.+)\.(?P<ext>\w+)$"
```

**UDM 매핑**:
| 추출값 | UDM 필드 | 변환 |
|--------|----------|------|
| `10` | `file_name_meta.sequence_num` | `int(num)` |
| `2024` | `event_context.year` | `int(year)` |
| `21` | `event_context.event_number` | `int(event)` |
| `25k` | `event_context.buyin_usd` | `25000` (k 제거 후 * 1000) |
| `nlh` | `event_context.game_variant` | `"NLH"` (대문자 변환) |
| `hr-ft-...` | 태그/설명 파싱 | `is_high_roller=True`, `is_final_table=True` |

**태그 파싱 로직**:
| 태그 | UDM 필드 | 값 |
|------|----------|-----|
| `hr` | `event_context.is_high_roller` | `True` |
| `shr` | `event_context.is_super_high_roller` | `True` |
| `ft` | `event_context.is_final_table` | `True` |

#### 3.4.5 패턴 5: GGMillions

**패턴**: `{날짜}_Super High Roller Poker FINAL TABLE with {플레이어}.mp4`

**예시**: `250507_Super High Roller Poker FINAL TABLE with Joey ingram.mp4`

**정규식**:
```python
r"^(?P<date>\d{6})_Super High Roller Poker FINAL TABLE with (?P<player>.+)\.(?P<ext>\w+)$"
```

**UDM 매핑**:
| 추출값 | UDM 필드 | 변환 |
|--------|----------|------|
| `250507` | `event_context.year` | `2025` (앞 2자리) |
| `Joey ingram` | `file_name_meta.raw_description` | Direct |
| - | `event_context.is_super_high_roller` | `True` |
| - | `event_context.is_final_table` | `True` |
| - | `event_context.brand` | `"GGMillions"` |

### 3.5 NAS 스캔 파이프라인

```python
import os
from pathlib import Path

async def scan_nas_folder(root_path: str) -> list[Asset]:
    """
    NAS 폴더 스캔하여 Asset 리스트 생성

    Process:
    1. 폴더 재귀 탐색
    2. 파일 발견 시:
       a. 경로에서 Brand/EventType 추출
       b. 폴더명에서 AssetType 추출
       c. 파일명 패턴 매칭하여 메타데이터 추출
       d. Asset 객체 생성 (Segment는 빈 배열)
    """
    assets = []

    for root, dirs, files in os.walk(root_path):
        for file in files:
            if file.lower().endswith(('.mp4', '.mov', '.mxf', '.mkv')):
                file_path = Path(root) / file

                # 경로에서 브랜드 추출
                brand_info = infer_brand_from_path(str(file_path))

                # 폴더명에서 AssetType 추출
                asset_type = infer_asset_type_from_path(str(file_path))

                # 파일명 파싱
                file_meta = parse_filename(file)

                # Asset 생성
                asset = Asset(
                    asset_uuid=generate_asset_uuid(file_path),
                    file_name=file,
                    file_path_nas=str(file_path),
                    file_path_rel=str(file_path.relative_to(root_path)),
                    asset_type=asset_type,
                    event_context=EventContext(
                        year=file_meta.year_code or 2024,
                        brand=brand_info["brand"],
                        event_type=brand_info["event_type"]
                    ),
                    file_name_meta=file_meta,
                    source_origin="NAS_SCAN",
                    segments=[]  # NAS 스캔에서는 Segment 정보 없음
                )

                assets.append(asset)

    return assets
```

---

## 4. MAM 시스템 소스

### 4.1 Iconik Export

#### 4.1.1 기본 정보

| 항목 | 값 |
|------|-----|
| **출력 형식** | JSON (API) 또는 CSV (Export) |
| **API 엔드포인트** | `/API/assets/v1/assets/{asset_id}` |
| **인증** | App ID + Auth Token |
| **데이터 레벨** | Asset + Custom Metadata |

#### 4.1.2 예상 필드 구조

| Iconik 필드 | 데이터 타입 | UDM 필드 | 비고 |
|-------------|------------|----------|------|
| `id` | UUID | `asset.asset_uuid` | Direct |
| `title` | String | `asset.file_name` | 또는 `segment.title` |
| `files[0].name` | String | `asset.file_name` | 실제 파일명 |
| `metadata.year` | Integer | `event_context.year` | 커스텀 메타 |
| `metadata.series` | String | `event_context.brand` | 커스텀 메타 |
| `metadata.timecodes[]` | Array | `segments[]` | 타임코드 배열 |
| `metadata.timecodes[].in` | String (TC) | `segment.time_in_sec` | 변환 필요 |
| `metadata.timecodes[].out` | String (TC) | `segment.time_out_sec` | 변환 필요 |
| `metadata.tags` | Array | `segment.tags_action` | 직접 매핑 |

#### 4.1.3 Profile 요구사항

```yaml
# profiles/iconik_export_v1.yaml
source_type: iconik_api
version: 1.0.0

mappings:
  asset:
    asset_uuid:
      source: "$.id"
      transform: direct
    file_name:
      source: "$.files[0].name"
      transform: direct
    event_context.year:
      source: "$.metadata.year"
      transform: int
    event_context.brand:
      source: "$.metadata.series"
      transform: lookup
      lookup_table:
        "WSOP": "WSOP"
        "Circuit": "WSOPC"

  segments:
    source: "$.metadata.timecodes"
    foreach:
      segment_uuid:
        transform: generate_uuid
      time_in_sec:
        source: "$.in"
        transform: timecode_to_seconds
      time_out_sec:
        source: "$.out"
        transform: timecode_to_seconds
```

### 4.2 CatDV Export

#### 4.2.1 기본 정보

| 항목 | 값 |
|------|-----|
| **출력 형식** | XML |
| **루트 엘리먼트** | `<catalog>` |
| **클립 엘리먼트** | `<clip>` |
| **커스텀 필드** | `<userFields>` |

#### 4.2.2 예상 XML 구조

```xml
<catalog>
  <clip>
    <id>550e8400-e29b-41d4-a716-446655440000</id>
    <name>WCLA24-01.mp4</name>
    <in>00:01:30:15</in>
    <out>00:02:45:20</out>
    <userFields>
      <field name="Year">2024</field>
      <field name="Series">WSOPC</field>
      <field name="Location">Los Angeles</field>
      <field name="Winner">Daniel Negreanu</field>
      <field name="Players">Daniel Negreanu, Phil Hellmuth</field>
      <field name="Tags">preflop-allin, cooler</field>
    </userFields>
  </clip>
</catalog>
```

#### 4.2.3 필드 매핑

| CatDV 필드 (XPath) | UDM 필드 | 변환 |
|-------------------|----------|------|
| `/catalog/clip/id` | `segment.segment_uuid` | Direct (UUID) |
| `/catalog/clip/name` | `asset.file_name` | Direct |
| `/catalog/clip/in` | `segment.time_in_sec` | Timecode → Seconds |
| `/catalog/clip/out` | `segment.time_out_sec` | Timecode → Seconds |
| `//field[@name='Year']` | `event_context.year` | Direct (int) |
| `//field[@name='Series']` | `event_context.brand` | Lookup |
| `//field[@name='Players']` | `segment.players[].name` | Split by `,` |
| `//field[@name='Tags']` | `segment.tags_action` | Split by `,` |

#### 4.2.4 Profile 요구사항

```yaml
# profiles/catdv_export_v1.yaml
source_type: catdv_xml
version: 1.0.0

namespaces:
  catdv: "http://catdv.example.com/schema"

mappings:
  asset:
    file_name:
      xpath: "//clip/name"
      transform: direct
    event_context.year:
      xpath: "//field[@name='Year']"
      transform: int

  segments:
    xpath: "//clip"
    foreach:
      segment_uuid:
        xpath: "./id"
        transform: direct
      time_in_sec:
        xpath: "./in"
        transform: timecode_to_seconds
      time_out_sec:
        xpath: "./out"
        transform: timecode_to_seconds
```

---

## 5. Legacy Excel 소스

### 5.1 기본 정보

| 항목 | 값 |
|------|-----|
| **파일 형식** | `.xlsx` (Excel 2007+) |
| **시트 구조** | 단일 시트 또는 다중 시트 |
| **헤더 행** | 1행 (고정) |
| **데이터 시작** | 2행부터 |

### 5.2 예상 컬럼 구조

| 컬럼명 | 데이터 타입 | UDM 필드 | 비고 |
|--------|------------|----------|------|
| `File Name` | String | `asset.file_name` | Direct |
| `TC In` | Timecode | `segment.time_in_sec` | 변환 필요 |
| `TC Out` | Timecode | `segment.time_out_sec` | 변환 필요 |
| `Year` | Integer | `event_context.year` | Direct |
| `Event` | String | `event_context.brand` | Lookup |
| `Winner` | String | `segment.winner` | Normalize |
| `Player 1~N` | String | `segment.players[].name` | 배열 수집 |
| `Tags` | String (CSV) | `segment.tags_action` | Split by `,` |

### 5.3 Profile 요구사항

```yaml
# profiles/excel_legacy_v1.yaml
source_type: excel
version: 1.0.0

excel:
  sheet_name: "Sheet1"  # 또는 sheet_index: 0
  header_row: 1
  data_start_row: 2

mappings:
  asset:
    file_name:
      column: "File Name"
      transform: direct
    event_context.year:
      column: "Year"
      transform: int
    event_context.brand:
      column: "Event"
      transform: lookup
      lookup_table:
        "Main Event": "WSOP"
        "Circuit": "WSOPC"

  segments:
    time_in_sec:
      column: "TC In"
      transform: timecode_to_seconds
    time_out_sec:
      column: "TC Out"
      transform: timecode_to_seconds
    players:
      columns: ["Player 1", "Player 2", "Player 3"]
      transform: collect_array
      ignore_empty: true
```

---

## 6. 소스별 프로파일 요구사항

### 6.1 프로파일 구조

```yaml
# 프로파일 메타데이터
profile_id: "wsop_circuit_2024_v1"
name: "WSOP Circuit 2024"
version: "1.0.0"
source_type: "google_sheets"  # csv | excel | json | google_sheets | iconik_api | catdv_xml | nas_scan
created_at: "2025-12-11T10:00:00Z"
author: "Archive Converter Team"

# 소스 설정
source:
  type: "google_sheets"
  config:
    sheet_id: "1_RN_W_ZQclSZA0Iez6XniCXVtjkkd5HNZwiT6l-z6d4"
    range: "Circuit DB!A2:Z"
    credentials_file: "credentials.json"

# 필드 매핑
mappings:
  asset:
    asset_uuid:
      source: "File Name"
      transform: generate_asset_uuid
    file_name:
      source: "File Name"
      transform: direct

  segments:
    time_in_sec:
      source: "In"
      transform: timecode_to_seconds
      params:
        fps: 29.97

# 검증 규칙
validation:
  required_fields:
    - "File Name"
    - "In"
    - "Out"
  business_rules:
    - rule: "time_out > time_in"
      severity: "ERROR"
```

### 6.2 소스 타입별 필수 설정

| Source Type | 필수 Config | 선택 Config |
|-------------|------------|------------|
| `csv` | `file_path`, `delimiter` | `encoding`, `skip_rows` |
| `excel` | `file_path`, `sheet_name` | `header_row`, `data_start_row` |
| `json` | `file_path` | `json_path` |
| `google_sheets` | `sheet_id`, `range`, `credentials_file` | - |
| `iconik_api` | `api_url`, `app_id`, `auth_token` | `batch_size` |
| `catdv_xml` | `file_path` | `namespaces` |
| `nas_scan` | `root_path` | `file_extensions`, `exclude_patterns` |

### 6.3 변환 타입별 적용 가능 소스

| Transform | 적용 소스 | 설명 |
|-----------|----------|------|
| `direct` | All | 그대로 복사 |
| `int` | All | Integer 변환 |
| `float` | All | Float 변환 |
| `timecode_to_seconds` | CSV, Excel, Sheets, XML | 타임코드 → 초 |
| `stars_to_rating` | CSV, Excel, Sheets | ★★★ → 3 |
| `split_csv` | All | 쉼표로 분리하여 배열 |
| `lookup` | All | 룩업 테이블 적용 |
| `generate_uuid` | All | UUID 생성 |
| `generate_asset_uuid` | All | 파일 해시 기반 UUID |
| `normalize_name` | All | 이름 정규화 (공백 제거 등) |
| `parse_hand_matchup` | All | "AA vs KK" → PlayerInHand 배열 |
| `infer_from_filename` | NAS Scan | 파일명 패턴 매칭 |

---

## 7. 데이터 품질 규칙

### 7.1 필수 필드 검증

#### Asset Level

| 필드 | 규칙 | 에러 레벨 |
|------|------|----------|
| `asset_uuid` | Not Null, Valid UUID | ERROR |
| `file_name` | Not Null, Min Length 1 | ERROR |
| `asset_type` | Valid Enum | ERROR |
| `event_context.year` | 1970 ≤ year ≤ 2100 | ERROR |
| `event_context.brand` | Valid Enum | ERROR |
| `source_origin` | Not Null | ERROR |

#### Segment Level

| 필드 | 규칙 | 에러 레벨 |
|------|------|----------|
| `segment_uuid` | Not Null, Valid UUID | ERROR |
| `parent_asset_uuid` | Not Null, FK 존재 | ERROR |
| `time_in_sec` | ≥ 0 | ERROR |
| `time_out_sec` | > time_in_sec | ERROR |
| `game_type` | Valid Enum | ERROR |

### 7.2 값 범위 검증

| 필드 | 최소값 | 최대값 | 기본값 |
|------|--------|--------|--------|
| `rating` | 0 | 5 | - |
| `time_in_sec` | 0 | - | - |
| `time_out_sec` | 0 | - | - |
| `event_context.year` | 1970 | 2100 | - |
| `event_context.season` | 1 | 100 | - |
| `event_context.episode` | 1 | 1000 | - |
| `event_context.buyin_usd` | 0 | 10,000,000 | - |

### 7.3 비즈니스 규칙

| Rule ID | 규칙 | Severity | 설명 |
|---------|------|----------|------|
| **BR-001** | `time_out_sec > time_in_sec` | ERROR | 종료 시간이 시작 시간보다 커야 함 |
| **BR-002** | `winner in players` | WARNING | 승자가 참여자 리스트에 포함되어야 함 |
| **BR-003** | `10 ≤ duration ≤ 3600` | WARNING | 핸드 길이 10초~60분 권장 |
| **BR-004** | `is_cooler=True → "cooler" in tags_action` | INFO | 쿨러 플래그 설정 시 태그도 권장 |
| **BR-005** | `file_path_nas contains brand` | WARNING | NAS 경로와 브랜드 일치 권장 |
| **BR-006** | `players count ≥ 2` | WARNING | 핸드 참여자 2명 이상 권장 |
| **BR-007** | `asset_type=MASTER → tech_spec not null` | INFO | 마스터 에셋은 기술 스펙 권장 |

### 7.4 중복 검출 규칙

| 중복 유형 | 판단 기준 | 처리 방식 |
|----------|----------|----------|
| **Asset 중복** | `asset_uuid` 동일 | 에러 (PK 위반) |
| **Segment 중복** | `segment_uuid` 동일 | 에러 (PK 위반) |
| **파일명 중복** | `file_name` + `source_origin` 동일 | 경고 (덮어쓰기 확인) |
| **시간 중복** | 동일 Asset 내 `time_in_sec ~ time_out_sec` 겹침 | 경고 (타임라인 검증) |

---

## 8. Transform Agent 연동 인터페이스

### 8.1 입력 인터페이스

```python
@dataclass
class SourceRecord:
    """원본 소스 레코드"""
    source_type: str            # "google_sheets" | "nas_scan" | ...
    raw_data: dict              # 원본 데이터 (컬럼명: 값)
    source_metadata: dict       # 소스 메타데이터 (파일 경로, 시트 ID 등)
    row_number: Optional[int]   # 행 번호 (디버깅용)

@dataclass
class TransformRequest:
    """변환 요청"""
    profile_name: str           # 사용할 프로파일 이름
    source_records: list[SourceRecord]
    options: dict               # 변환 옵션 (예: strict_mode=True)
```

### 8.2 출력 인터페이스

```python
@dataclass
class TransformResult:
    """변환 결과"""
    asset: Asset                        # 변환된 UDM Asset
    source_record: SourceRecord         # 원본 레코드 참조
    warnings: list[ValidationWarning]   # 경고 목록
    errors: list[ValidationError]       # 에러 목록

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

@dataclass
class TransformResponse:
    """변환 응답"""
    results: list[TransformResult]
    summary: TransformSummary
```

### 8.3 에러 처리

```python
class TransformError(Exception):
    """변환 에러 베이스"""
    pass

class ProfileNotFoundError(TransformError):
    """프로파일을 찾을 수 없음"""
    pass

class MappingError(TransformError):
    """매핑 오류 (필드 없음, 변환 실패 등)"""
    field_name: str
    source_value: Any
    reason: str

class ValidationError(TransformError):
    """검증 오류"""
    rule_id: str
    field_name: str
    actual_value: Any
    expected: str
```

---

## 9. 프로파일 예제

### 9.1 Google Sheets - Circuit 2024

```yaml
# profiles/google_sheets_circuit_2024.yaml
profile_id: "google_sheets_circuit_2024"
name: "WSOP Circuit 2024 Google Sheets"
version: "1.0.0"
source_type: "google_sheets"
created_at: "2025-12-11T10:00:00Z"

source:
  type: "google_sheets"
  config:
    sheet_id: "1_RN_W_ZQclSZA0Iez6XniCXVtjkkd5HNZwiT6l-z6d4"
    range: "Circuit DB!A2:Z"
    credentials_file: "config/google_credentials.json"

mappings:
  asset:
    asset_uuid:
      source: "File Name"
      transform: generate_asset_uuid
    file_name:
      source: "File Name"
      transform: direct
    asset_type:
      constant: "SUBCLIP"
    event_context:
      year:
        source: "File Name"
        transform: infer_from_filename
        params:
          pattern: "WCLA(\\d{2})"
          year_offset: 2000
      brand:
        constant: "WSOPC"
      event_type:
        constant: "CIRCUIT"
      location:
        constant: "Los Angeles"
    file_path_rel:
      source: "Nas Folder Link"
      transform: direct
    source_origin:
      constant: "GoogleSheets_Circuit_2024"

  segments:
    segment_uuid:
      transform: generate_uuid
    segment_type:
      constant: "HAND"
    time_in_sec:
      source: "In"
      transform: timecode_to_seconds
      params:
        fps: 29.97
    time_out_sec:
      source: "Out"
      transform: timecode_to_seconds
      params:
        fps: 29.97
    game_type:
      constant: "TOURNAMENT"
    rating:
      source: "Hand Grade"
      transform: stars_to_rating
    winner:
      source: "Winner"
      transform: normalize_name
    players:
      sources: ["Player 1", "Player 2", "Player 3"]
      transform: collect_players
      params:
        hands_column: "Hands"
    tags_action:
      sources: ["Play Tag 1", "Play Tag 2", "Play Tag 3", "Play Tag 4", "Play Tag 5", "Play Tag 6", "Play Tag 7"]
      transform: collect_array
      params:
        ignore_empty: true
    tags_emotion:
      sources: ["Emotion Tag 1", "Emotion Tag 2"]
      transform: collect_array
      params:
        ignore_empty: true

validation:
  required_fields:
    - "File Name"
    - "In"
    - "Out"
  business_rules:
    - rule: "time_out > time_in"
      severity: "ERROR"
    - rule: "winner in players"
      severity: "WARNING"
```

### 9.2 NAS Scan - WSOP Archive

```yaml
# profiles/nas_scan_wsop.yaml
profile_id: "nas_scan_wsop"
name: "NAS WSOP Archive Scan"
version: "1.0.0"
source_type: "nas_scan"
created_at: "2025-12-11T10:00:00Z"

source:
  type: "nas_scan"
  config:
    root_path: "\\\\10.10.100.122\\docker\\GGPNAs\\ARCHIVE"
    file_extensions: [".mp4", ".mov", ".mxf", ".mkv"]
    exclude_patterns: [".*\\.tmp", ".*_BACKUP.*"]
    recursive: true

mappings:
  asset:
    asset_uuid:
      source: "file_path"
      transform: generate_asset_uuid
    file_name:
      source: "file_name"
      transform: direct
    file_path_nas:
      source: "file_path"
      transform: direct
    file_path_rel:
      source: "file_path"
      transform: relative_to_root
    asset_type:
      source: "file_path"
      transform: infer_asset_type_from_path
    event_context:
      brand:
        source: "file_path"
        transform: infer_brand_from_path
      event_type:
        source: "file_path"
        transform: infer_event_type_from_path
      year:
        source: "file_name"
        transform: infer_from_filename
        fallback:
          source: "file_path"
          transform: extract_year_from_path
    file_name_meta:
      source: "file_name"
      transform: parse_filename
    source_origin:
      constant: "NAS_SCAN"

  segments:
    # NAS 스캔에서는 Segment 정보 없음 (빈 배열)
    default: []

validation:
  required_fields:
    - "file_name"
    - "file_path"
  business_rules:
    - rule: "file_path contains brand"
      severity: "WARNING"
```

---

## 10. Success Metrics

| Metric | Target | 측정 방법 |
|--------|--------|----------|
| **소스 커버리지** | 100% | 정의된 모든 소스 타입 문서화 |
| **매핑 정확도** | 99%+ | 변환된 UDM 데이터 검증 통과율 |
| **프로파일 재사용률** | 80%+ | 신규 소스에 기존 프로파일 활용 |
| **변환 에러율** | < 1% | 변환 실패 레코드 비율 |
| **데이터 손실률** | 0% | 원본 데이터 필드 누락 없음 |
| **문서 완성도** | 100% | 모든 섹션 작성 완료 |

---

## 11. Related PRDs

- **PRD-0001**: Master Orchestrator
- **PRD-0002**: Ingest Agent (소스 읽기)
- **PRD-0003**: Transform Agent (프로파일 기반 변환)
- **PRD-0004**: Validate Agent (품질 검증)
- **PRD-0006**: Profile Manager (프로파일 관리)
- **PRD-0008**: UDM Final Schema (타겟 스키마)

---

## 12. Next Steps

| 우선순위 | 작업 | 담당 | 설명 |
|---------|------|------|------|
| 1 | **프로파일 YAML 작성** | Transform Team | 섹션 9 예제 기반 실제 파일 생성 |
| 2 | **MAM 스키마 분석** | Ingest Team | Iconik/CatDV 실제 출력 분석 |
| 3 | **변환 함수 구현** | Transform Team | `timecode_to_seconds`, `parse_hand_matchup` 등 |
| 4 | **통합 테스트** | QA Team | 각 소스별 E2E 테스트 |

---

## Appendix A: Timecode Conversion Reference

### A.1 지원 타임코드 형식

| 형식 | 예시 | FPS |
|------|------|-----|
| `HH:MM:SS:FF` | `01:30:15:24` | 29.97, 30, 25, 24 |
| `HH:MM:SS` | `01:30:15` | N/A |
| `HH:MM:SS.mmm` | `01:30:15.500` | N/A |

### A.2 FPS 기본값

| 소스 | 기본 FPS |
|------|---------|
| Google Sheets - Circuit | 29.97 |
| Google Sheets - Database | N/A (초 단위) |
| Legacy Excel | 29.97 |
| CatDV XML | 29.97 |
| Iconik API | 29.97 |

---

## Appendix B: Name Normalization Rules

### B.1 플레이어 이름 정규화

| Raw | Normalized | 규칙 |
|-----|------------|------|
| `daniel negreanu` | `Daniel Negreanu` | Title Case |
| `Daniel  Negreanu` | `Daniel Negreanu` | 다중 공백 제거 |
| `negreanu, daniel` | `Daniel Negreanu` | 성, 이름 → 이름 성 |
| `D. Negreanu` | `Daniel Negreanu` | 약어 확장 (룩업 테이블) |

### B.2 정규화 룩업 테이블

```yaml
name_normalization:
  aliases:
    "D. Negreanu": "Daniel Negreanu"
    "Kid Poker": "Daniel Negreanu"
    "Phil H": "Phil Hellmuth"
    "Poker Brat": "Phil Hellmuth"

  corrections:
    "Daneil": "Daniel"
    "Negreanu": "Negreanu"
```

---

## Appendix C: Sample Data

### C.1 Google Sheets - Circuit (CSV)

```csv
File Name,In,Out,Hand Grade,Winner,Hands,Player 1,Player 2,Play Tag 1,Emotion Tag 1
WCLA24-01.mp4,00:01:30:15,00:02:45:20,★★★★★,Daniel Negreanu,AA vs KK,Daniel Negreanu,Phil Hellmuth,Preflop All-in,Excitement
WCLA24-02.mp4,00:00:15:00,00:01:20:10,★★★,Alice Chen,,Alice Chen,Bob Smith,,
```

### C.2 Google Sheets - Database (CSV)

```csv
id,ProjectName,Year_,time_start_S,time_end_S,title,PlayersTags,HANDTag,Cooler,All-in
550e8400-e29b-41d4-a716-446655440000,WSOP,2024,425.5,510.2,Epic cooler,"Player A, Player B",AA vs KK,TRUE,preflop
661f9511-f30c-52e5-b827-557766551111,WSOPC,2024,120.0,180.5,Standard hand,"Player C, Player D",AK vs QQ,FALSE,flop
```

---

## Appendix D: Glossary

| 용어 | 정의 |
|------|------|
| **Source** | 원본 데이터 소스 (Sheets, NAS, MAM 등) |
| **Profile** | 소스 → UDM 매핑 설정 YAML |
| **Transform** | 데이터 변환 함수 (타임코드 변환, 정규화 등) |
| **Mapping** | 소스 필드 → UDM 필드 대응 관계 |
| **Validation Rule** | 데이터 품질 검증 규칙 |
| **Normalization** | 데이터 표준화 (이름, 태그 등) |
| **Lookup Table** | 값 변환 테이블 (ProjectName → Brand 등) |

---

**End of PRD-0009**
