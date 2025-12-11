# Google Sheets → UDM 매칭 결과 보고서

**Version**: 1.0.0
**Date**: 2025-12-11
**Status**: Issue #7 수정 후 완전 매핑 달성
**UDM Version**: 3.1.0

---

## Executive Summary

| 지표 | Archive Metadata | Iconik Metadata | 합계 |
|------|------------------|-----------------|------|
| **총 컬럼 수** | 20 | 35 | 55 |
| **매핑된 컬럼** | 20 | 34 | 54 |
| **무시된 컬럼** | 0 | 1 | 1 |
| **매핑률** | **100%** | **97%** | **98%** |

### Issue #7 수정 전후 비교

| 상태 | 매핑된 컬럼 | 누락된 컬럼 | 매핑률 |
|------|-----------|-----------|--------|
| **수정 전 (v3.0)** | 32 | 23 | 58% |
| **수정 후 (v3.1)** | 54 | 1 | **98%** |
| **개선** | +22 | -22 | +40%p |

---

## 1. Archive Metadata Sheet 매핑 결과

**Sheet Name**: Archive Metadata
**Sheet ID**: `1_RN_W_ZQclSZA0Iez6XniCXVtjkkd5HNZwiT6l-z6d4`
**Tab**: WSOP Circuit 2024
**Records**: 38 rows

### 1.1 컬럼별 매핑 상세

| # | Source Column | UDM Field | Target | 변환 | Status |
|---|--------------|-----------|--------|------|--------|
| 1 | `File No.` | `Asset.file_number` | Asset | Direct (int) | ✅ **NEW** |
| 2 | `File Name` | `Asset.file_name` | Asset | Direct | ✅ |
| 3 | `Nas Folder Link` | `Asset.nas_folder_link` | Asset | Direct | ✅ **NEW** |
| 4 | `In` | `Segment.time_in_sec` | Segment | `parse_time_hms()` | ✅ |
| 5 | `Out` | `Segment.time_out_sec` | Segment | `parse_time_hms()` | ✅ |
| 6 | `Hand Grade` | `Segment.rating` | Segment | `parse_star_rating()` | ✅ |
| 7 | `Winner` | `Segment.winner` | Segment | Direct | ✅ |
| 8 | `Hands` | `Segment.hand_tag` | Segment | Direct | ✅ **NEW** |
| 8 | `Hands` | `Segment.players` | Segment | `parse_hand_matchup()` | ✅ |
| 9 | `Tag (Player) 1` | `Segment.tags_player[0]` | Segment | `merge_tag_columns()` | ✅ **NEW** |
| 10 | `Tag (Player) 2` | `Segment.tags_player[1]` | Segment | `merge_tag_columns()` | ✅ **NEW** |
| 11 | `Tag (Player) 3` | `Segment.tags_player[2]` | Segment | `merge_tag_columns()` | ✅ **NEW** |
| 12 | `Tag (Poker Play) 1` | `Segment.tags_action[0]` | Segment | `merge_tag_columns()` | ✅ |
| 13 | `Tag (Poker Play) 2` | `Segment.tags_action[1]` | Segment | `merge_tag_columns()` | ✅ |
| 14 | `Tag (Poker Play) 3` | `Segment.tags_action[2]` | Segment | `merge_tag_columns()` | ✅ |
| 15 | `Tag (Poker Play) 4` | `Segment.tags_action[3]` | Segment | `merge_tag_columns()` | ✅ |
| 16 | `Tag (Poker Play) 5` | `Segment.tags_action[4]` | Segment | `merge_tag_columns()` | ✅ |
| 17 | `Tag (Poker Play) 6` | `Segment.tags_action[5]` | Segment | `merge_tag_columns()` | ✅ |
| 18 | `Tag (Poker Play) 7` | `Segment.tags_action[6]` | Segment | `merge_tag_columns()` | ✅ |
| 19 | `Tag (Emotion) 1` | `Segment.tags_emotion[0]` | Segment | `merge_tag_columns()` | ✅ |
| 20 | `Tag (Emotion) 2` | `Segment.tags_emotion[1]` | Segment | `merge_tag_columns()` | ✅ |

### 1.2 Archive Metadata Sheet 매핑 요약

```
┌────────────────────────────────────────────────────────────┐
│           ARCHIVE METADATA SHEET MAPPING SUMMARY           │
│                                                            │
│   Total Columns: 20                                        │
│   ├── Mapped to Asset:   3 (15%)                          │
│   ├── Mapped to Segment: 17 (85%)                         │
│   └── Unmapped:          0 (0%)                           │
│                                                            │
│   Mapping Rate: ████████████████████ 100%                 │
│                                                            │
│   NEW Fields Added (Issue #7):                            │
│   ├── Asset.file_number                                   │
│   ├── Asset.nas_folder_link                               │
│   ├── Segment.hand_tag                                    │
│   └── Segment.tags_player[]                               │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 2. Iconik Metadata Sheet 매핑 결과

**Sheet Name**: Iconik Metadata
**Sheet ID**: `1pUMPKe-OsKc-Xd8lH1cP9ctJO4hj3keXY5RwNFp2Mtk`
**Tab**: Database
**Records**: 200+ rows

### 2.1 컬럼별 매핑 상세

| # | Source Column | UDM Field | Target | 변환 | Status |
|---|--------------|-----------|--------|------|--------|
| 1 | `id` | `Segment.segment_uuid` | Segment | Direct (UUID) | ✅ |
| 2 | `title` | `Segment.title` | Segment | Direct | ✅ |
| 3 | `time_start_ms` | `Segment.time_in_ms` | Segment | Direct (int) | ✅ **NEW** |
| 4 | `time_end_ms` | `Segment.time_out_ms` | Segment | Direct (int) | ✅ **NEW** |
| 5 | `time_start_S` | `Segment.time_in_sec` | Segment | Direct (float) | ✅ |
| 6 | `time_end_S` | `Segment.time_out_sec` | Segment | Direct (float) | ✅ |
| 7 | `Description` | `Segment.description` | Segment | Direct | ✅ |
| 8 | `ProjectName` | `EventContext.brand` | Asset | Map to Enum | ✅ |
| 9 | `ProjectNameTag` | `Asset.project_name_tag` | Asset | Direct | ✅ **NEW** |
| 10 | `SearchTag` | `Segment.tags_search` | Segment | Split comma | ✅ **NEW** |
| 11 | `Year_` | `EventContext.year` | Asset | Direct (int) | ✅ |
| 12 | `Location` | `EventContext.location` | Asset | Direct | ✅ |
| 13 | `Venue` | `EventContext.venue` | Asset | Direct | ✅ |
| 14 | `EpisodeEvent` | `EventContext.episode` | Asset | Direct | ✅ |
| 15 | `Source` | `Segment.source_type` | Segment | Direct | ✅ **NEW** |
| 16 | `Scene` | `Segment.scene` | Segment | Direct | ✅ **NEW** |
| 17 | `GameType` | `Segment.game_type` | Segment | Map to Enum | ✅ |
| 18 | `PlayersTags` | `Segment.players` | Segment | `parse_players_tags()` | ✅ |
| 19 | `HandGrade` | `Segment.rating` | Segment | `parse_star_rating()` | ✅ |
| 20 | `HANDTag` | `Segment.hand_tag` | Segment | Direct | ✅ **NEW** |
| 20 | `HANDTag` | `Segment.players` | Segment | `parse_hand_matchup()` | ✅ |
| 21 | `EPICHAND` | `Segment.is_epic_hand` | Segment | Boolean | ✅ **NEW** |
| 22 | `Tournament` | `Asset.tournament_name` | Asset | Direct | ✅ **NEW** |
| 23 | `PokerPlayTags` | `Segment.tags_action` | Segment | Split comma | ✅ |
| 24 | `Adjective` | `Segment.adjective` | Segment | Direct | ✅ |
| 25 | `Emotion` | `Segment.tags_emotion` | Segment | Split comma | ✅ |
| 26 | `AppearanceOutfit` | `Segment.appearance_outfit` | Segment | Direct | ✅ **NEW** |
| 27 | `SceneryObject` | `Segment.scenery_object` | Segment | Direct | ✅ **NEW** |
| 28 | `_gcvi_tags` | - | - | 내부 태그 | ⏭️ SKIP |
| 29 | `Badbeat` | `SituationFlags.is_badbeat` | Segment | Boolean | ✅ |
| 30 | `Bluff` | `SituationFlags.is_bluff` | Segment | Boolean | ✅ |
| 31 | `Suckout` | `SituationFlags.is_suckout` | Segment | Boolean | ✅ |
| 32 | `Cooler` | `SituationFlags.is_cooler` | Segment | Boolean | ✅ |
| 33 | `RUNOUTTag` | `Segment.runout_type` | Segment | Direct | ✅ |
| 34 | `PostFlop` | `Segment.postflop_action` | Segment | Direct | ✅ **NEW** |
| 35 | `All-in` | `Segment.all_in_stage` | Segment | `parse_all_in_tags()` | ✅ |

### 2.2 Iconik Metadata Sheet 매핑 요약

```
┌────────────────────────────────────────────────────────────┐
│           ICONIK METADATA SHEET MAPPING SUMMARY            │
│                                                            │
│   Total Columns: 35                                        │
│   ├── Mapped to Asset:    8 (23%)                         │
│   ├── Mapped to Segment: 26 (74%)                         │
│   └── Skipped (internal): 1 (3%)                          │
│                                                            │
│   Mapping Rate: ███████████████████░ 97%                  │
│                                                            │
│   NEW Fields Added (Issue #7):                            │
│   ├── Asset: project_name_tag, tournament_name            │
│   ├── Segment: time_in_ms, time_out_ms                    │
│   ├── Segment: tags_search, hand_tag, scene               │
│   ├── Segment: source_type, is_epic_hand                  │
│   ├── Segment: appearance_outfit, scenery_object          │
│   └── Segment: postflop_action                            │
│                                                            │
│   Skipped Column:                                         │
│   └── _gcvi_tags (Google internal metadata)               │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 3. UDM 필드 커버리지

### 3.1 Asset 필드 매핑 현황

| UDM Field | Circuit | Database | Source |
|-----------|---------|----------|--------|
| `asset_uuid` | Generated | Generated | 자동 생성 |
| `file_name` | ✅ `File Name` | ❌ (추론 필요) | Circuit |
| `file_path_rel` | - | - | NAS |
| `file_path_nas` | - | - | NAS |
| `asset_type` | - | - | NAS 폴더명 |
| `file_number` | ✅ `File No.` | - | Circuit |
| `tournament_name` | - | ✅ `Tournament` | Database |
| `project_name_tag` | - | ✅ `ProjectNameTag` | Database |
| `nas_folder_link` | ✅ `Nas Folder Link` | - | Circuit |
| `event_context.year` | ✅ 파일명 추출 | ✅ `Year_` | Both |
| `event_context.brand` | ✅ 고정 (WSOPC) | ✅ `ProjectName` | Both |
| `event_context.event_type` | ✅ 고정 (CIRCUIT) | ❌ (추론) | Circuit |
| `event_context.location` | ✅ 고정 (LA) | ✅ `Location` | Both |
| `event_context.venue` | - | ✅ `Venue` | Database |
| `event_context.episode` | - | ✅ `EpisodeEvent` | Database |
| `source_origin` | ✅ 상수 | ✅ 상수 | 자동 |

### 3.2 Segment 필드 매핑 현황

| UDM Field | Circuit | Database | Source |
|-----------|---------|----------|--------|
| `segment_uuid` | Generated | ✅ `id` | Database (UUID) |
| `parent_asset_uuid` | Generated | Generated | 자동 생성 |
| `segment_type` | Default | Default | 기본값 |
| `time_in_sec` | ✅ `In` | ✅ `time_start_S` | Both |
| `time_out_sec` | ✅ `Out` | ✅ `time_end_S` | Both |
| `time_in_ms` | - | ✅ `time_start_ms` | Database |
| `time_out_ms` | - | ✅ `time_end_ms` | Database |
| `title` | - | ✅ `title` | Database |
| `game_type` | Default | ✅ `GameType` | Database |
| `rating` | ✅ `Hand Grade` | ✅ `HandGrade` | Both |
| `winner` | ✅ `Winner` | - | Circuit |
| `winning_hand` | - | - | 미제공 |
| `losing_hand` | - | - | 미제공 |
| `players` | ✅ `Hands` | ✅ `HANDTag` + `PlayersTags` | Both |
| `tags_action` | ✅ `Tag (Poker Play)` x7 | ✅ `PokerPlayTags` | Both |
| `tags_emotion` | ✅ `Tag (Emotion)` x2 | ✅ `Emotion` | Both |
| `tags_content` | - | - | 미제공 |
| `tags_player` | ✅ `Tag (Player)` x3 | - | Circuit |
| `tags_search` | - | ✅ `SearchTag` | Database |
| `hand_tag` | ✅ `Hands` | ✅ `HANDTag` | Both |
| `scene` | - | ✅ `Scene` | Database |
| `source_type` | - | ✅ `Source` | Database |
| `is_epic_hand` | - | ✅ `EPICHAND` | Database |
| `appearance_outfit` | - | ✅ `AppearanceOutfit` | Database |
| `scenery_object` | - | ✅ `SceneryObject` | Database |
| `postflop_action` | - | ✅ `PostFlop` | Database |
| `situation_flags` | - | ✅ 4개 Boolean | Database |
| `all_in_stage` | - | ✅ `All-in` | Database |
| `runout_type` | - | ✅ `RUNOUTTag` | Database |
| `adjective` | - | ✅ `Adjective` | Database |
| `board` | - | - | 미제공 |
| `event_stage` | - | - | 미제공 |
| `hand_description` | - | - | 미제공 |
| `is_dirty` | - | - | 미제공 |
| `description` | - | ✅ `Description` | Database |

---

## 4. 데이터 변환 규칙

### 4.1 시간 변환

| Source Format | Target Field | 변환 함수 | 예시 |
|---------------|-------------|----------|------|
| `HH:MM:SS` | `time_in_sec` | `parse_time_hms()` | "01:23:45" → 5025.0 |
| `MM:SS` | `time_in_sec` | `parse_time_hms()` | "12:30" → 750.0 |
| Float (seconds) | `time_in_sec` | Direct | 125.5 → 125.5 |
| Integer (ms) | `time_in_ms` | Direct | 125500 → 125500 |

### 4.2 별점 변환

| Source Format | Target Field | 변환 함수 | 예시 |
|---------------|-------------|----------|------|
| `★★★★★` | `rating` | `parse_star_rating()` | "★★★" → 3 |
| `1-5` | `rating` | Direct | "4" → 4 |

### 4.3 핸드 매치업 변환

| Source Format | Target Field | 변환 함수 | 예시 |
|---------------|-------------|----------|------|
| `AA vs KK` | `players[]` | `parse_hand_matchup()` | → [PlayerInHand(hand="AA"), PlayerInHand(hand="KK")] |
| `QQ vs JJ vs 99` | `players[]` | `parse_hand_matchup()` | → 3 PlayerInHand 객체 |

### 4.4 Boolean 변환

| Source Format | Target Field | 변환 규칙 | 예시 |
|---------------|-------------|----------|------|
| `TRUE` / `FALSE` | Boolean | Upper match | "TRUE" → True |
| `1` / `0` | Boolean | Numeric | "1" → True |
| `O` / `X` | Boolean | Korean style | "O" → True |

### 4.5 태그 병합

| Source Format | Target Field | 변환 함수 | 예시 |
|---------------|-------------|----------|------|
| 다중 컬럼 | `tags_*[]` | `merge_tag_columns()` | col1="bluff", col2="call" → ["bluff", "call"] |
| 콤마 구분 | `tags_*[]` | Split | "bluff,call" → ["bluff", "call"] |

---

## 5. Issue #7 수정 상세

### 5.1 추가된 UDM 필드 (15개)

#### Segment 신규 필드 (11개)

| 필드 | 타입 | Source | 설명 |
|------|------|--------|------|
| `tags_player` | List[str] | Circuit | 플레이어 태그 |
| `tags_search` | List[str] | Database | 검색 태그 |
| `hand_tag` | str | Both | 핸드 태그 원본 |
| `scene` | str | Database | 장면 설명 |
| `source_type` | str | Database | 소스 타입 (PGM/RAW) |
| `is_epic_hand` | bool | Database | 에픽 핸드 여부 |
| `appearance_outfit` | str | Database | 외모/복장 |
| `scenery_object` | str | Database | 장면 오브젝트 |
| `postflop_action` | str | Database | 포스트플롭 액션 |
| `time_in_ms` | int | Database | 시작 시간 (ms) |
| `time_out_ms` | int | Database | 종료 시간 (ms) |

#### Asset 신규 필드 (4개)

| 필드 | 타입 | Source | 설명 |
|------|------|--------|------|
| `file_number` | int | Circuit | 파일 순번 |
| `tournament_name` | str | Database | 토너먼트명 |
| `project_name_tag` | str | Database | 프로젝트 태그 |
| `nas_folder_link` | str | Both | NAS 폴더 링크 |

### 5.2 추가된 파싱 헬퍼 함수 (7개)

| 함수 | 입력 | 출력 | 용도 |
|------|------|------|------|
| `parse_time_hms()` | "01:23:45" | 5025.0 | HH:MM:SS → 초 |
| `parse_star_rating()` | "★★★" | 3 | 별점 → 숫자 |
| `parse_hand_matchup()` | "AA vs KK" | PlayerInHand[] | 핸드 파싱 |
| `parse_players_tags()` | "A, B, C" | ["A", "B", "C"] | 플레이어 파싱 |
| `merge_tag_columns()` | col1, col2, ... | ["tag1", "tag2"] | 컬럼 병합 |
| `parse_all_in_tags()` | "Preflop" | AllInStage.PREFLOP | 올인 파싱 |
| `parse_situation_flags_from_columns()` | row dict | SituationFlags | Boolean 파싱 |

---

## 6. 누락/무시 항목

### 6.1 무시된 컬럼 (1개)

| 컬럼 | Source | 사유 |
|------|--------|------|
| `_gcvi_tags` | Database | Google 내부 메타데이터, 사용자 데이터 아님 |

### 6.2 UDM 미사용 필드

| 필드 | 사유 | 향후 계획 |
|------|------|----------|
| `winning_hand` | Sheet에 미제공 | 파일명 파싱으로 추출 가능 |
| `losing_hand` | Sheet에 미제공 | 파일명 파싱으로 추출 가능 |
| `board` | Sheet에 미제공 | 수동 입력 또는 OCR |
| `event_stage` | Sheet에 미제공 | 파일명/폴더명에서 추출 |
| `is_dirty` | Sheet에 미제공 | 파일명 패턴 분석 |
| `tags_content` | Sheet에 미제공 | 자동 분류 또는 수동 |

---

## 7. 검증 결과

### 7.1 테스트 현황

```
┌────────────────────────────────────────────────────────────┐
│                    TEST RESULTS                            │
│                                                            │
│   Total Tests: 105                                         │
│   ├── Passed:  105                                         │
│   ├── Failed:  0                                           │
│   └── Skipped: 0                                           │
│                                                            │
│   Test Coverage: 97%                                       │
│                                                            │
│   New Tests Added (Issue #7): 21                           │
│   ├── TestParseTimeHMS: 3                                  │
│   ├── TestParseStarRating: 3                               │
│   ├── TestParseHandMatchup: 3                              │
│   ├── TestParsePlayersTags: 3                              │
│   ├── TestMergeTagColumns: 2                               │
│   ├── TestParseAllInTags: 3                                │
│   ├── TestParseSituationFlagsFromColumns: 2                │
│   ├── TestNewSegmentFields: 1                              │
│   └── TestNewAssetFields: 1                                │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 7.2 샘플 변환 검증

#### Circuit Sheet Row → UDM

**Input (Sheet Row)**:
```
File No.: 15
File Name: WCLA24-15.mp4
Nas Folder Link: //10.10.100.122/.../SUBCLIP/
In: 00:02:05
Out: 00:03:45
Hand Grade: ★★★★
Winner: Phil Ivey
Hands: AA vs KK
Tag (Player) 1: Phil Ivey
Tag (Poker Play) 1: cooler
Tag (Emotion) 1: brutal
```

**Output (UDM)**:
```json
{
  "asset": {
    "asset_uuid": "generated-uuid",
    "file_name": "WCLA24-15.mp4",
    "file_number": 15,
    "nas_folder_link": "//10.10.100.122/.../SUBCLIP/",
    "event_context": {
      "year": 2024,
      "brand": "WSOPC",
      "event_type": "CIRCUIT",
      "location": "Los Angeles"
    }
  },
  "segment": {
    "segment_uuid": "generated-uuid",
    "time_in_sec": 125.0,
    "time_out_sec": 225.0,
    "rating": 4,
    "winner": "Phil Ivey",
    "hand_tag": "AA vs KK",
    "players": [
      {"name": "Player1", "hand": "AA"},
      {"name": "Player2", "hand": "KK"}
    ],
    "tags_player": ["Phil Ivey"],
    "tags_action": ["cooler"],
    "tags_emotion": ["brutal"]
  }
}
```

---

## 8. 결론

### 8.1 매핑 완성도

| 항목 | v3.0 (수정 전) | v3.1 (수정 후) |
|------|--------------|---------------|
| Circuit Sheet | 70% | **100%** |
| Database Sheet | 50% | **97%** |
| 전체 매핑률 | 58% | **98%** |
| 파싱 헬퍼 함수 | 0 | **7개** |
| 테스트 케이스 | 84 | **105** |

### 8.2 달성 목표

- [x] Google Sheets 전체 컬럼 분석
- [x] UDM 스키마 결함 식별 및 수정
- [x] 누락 필드 15개 추가
- [x] 파싱 헬퍼 함수 7개 구현
- [x] 테스트 커버리지 유지 (97%)
- [x] PRD-0008 문서 업데이트

### 8.3 후속 작업

| 우선순위 | 작업 | 설명 |
|---------|------|------|
| 1 | Transform Agent | 실제 변환 파이프라인 구현 |
| 2 | NAS 스캔 연동 | 파일 존재 검증 |
| 3 | Validation Agent | 변환 결과 검증 |
| 4 | Export Agent | JSON/CSV 출력 |

---

## Appendix: 관련 파일

| 파일 | 용도 |
|------|------|
| `src/models/udm.py` | UDM 스키마 (v3.1.0) |
| `src/models/__init__.py` | 모듈 익스포트 |
| `tests/test_udm.py` | 105개 테스트 |
| `prds/PRD-0008-UDM-FINAL-SCHEMA.md` | 스키마 명세 |
| `docs/NAS_SHEETS_INTEGRATION.md` | 연동 전략 |
