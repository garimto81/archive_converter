# PRD-0008: UDM Final Schema Specification

**Version**: 3.1.0
**Status**: Final
**Created**: 2025-12-11
**Updated**: 2025-12-11
**Issue**: #7 - Google Sheets 파싱 완전 지원
**Parent**: PRD-0001-MASTER-ORCHESTRATOR

---

## 1. Executive Summary

### 1.1 결정 사항

| 항목 | 결정 | 근거 |
|------|------|------|
| **기반 스키마** | gemini.md 2-Level 구조 | 비디오 아카이빙 목적에 최적화 |
| **OHH 채택** | ❌ 전체 채택 안함 | 오버엔지니어링, 데이터 수집 비용 |
| **확장 방향** | 포커 도메인 필드 추가 | 구글 시트 + NAS 분석 결과 반영 |
| **NAS 구조 반영** | event_context 계층 확장 | 실제 폴더 구조 기반 분류 체계 |

### 1.2 핵심 철학

> **"이것은 비디오 아카이빙 시스템이지, 포커 핸드 분석 시스템이 아니다."**
>
> 핵심 질문: "이 영상의 **어디**에 **뭐**가 있는가?"

### 1.3 OHH를 채택하지 않는 이유

| 문제 | 설명 |
|------|------|
| **오버엔지니어링** | 베팅 액션 하나하나 기록 불필요 (`"preflop-allin"` 태그면 충분) |
| **데이터 수집 비용** | OHH 수준 = 실시간 게임 로그 필요, 현재 데이터에 없음 |
| **검색 불일치** | 실제 검색: "5점짜리 쿨러" vs OHH 검색: "3벳 팟 체크레이즈" |
| **목적 불일치** | OHH = 게임 재현용 / UDM = 클립 검색/편집용 |

### 1.4 v3.0 업데이트 (NAS 분석 반영)

| 항목 | 변경 내용 |
|------|-----------|
| **EventContext 확장** | brand, event_type, episode 등 계층적 구조 추가 |
| **파일명 코드 체계** | NAS 파일명 패턴 분석 결과 반영 (WCLA24, WP23 등) |
| **AssetType 추가** | STREAM, SUBCLIP, MASTER, CLEAN 구분 |
| **Brand 분류** | WSOP, HCL, GGMillions, PAD, MPP 등 실제 브랜드 체계 |

### 1.5 v3.1.0 업데이트 (Issue #7 - Google Sheets 완전 지원)

| 항목 | 변경 내용 |
|------|-----------|
| **Segment 필드 확장** | Circuit/Database 시트 전체 컬럼 매핑 (11개 신규 필드) |
| **Asset 필드 확장** | 파일 순번, 토너먼트명, 프로젝트 태그, NAS 링크 (4개 신규) |
| **파싱 헬퍼 함수** | 7개 유틸리티 함수 추가 (시간, 별점, 핸드, 태그 파싱) |
| **테스트 커버리지** | 84개 → 105개 테스트 (+21개) |

---

## 2. NAS 폴더 구조 분석 결과

### 2.1 전체 폴더 계층 구조 (실제 NAS 스캔 기준)

**총 194개 폴더** (`find` 명령 기준, ARCHIVE/ 하위)

```
//10.10.100.122/docker/GGPNAs/
│
├── ARCHIVE/                              # 메인 아카이브 (194개 폴더)
│   │
│   ├── WSOP/                             # WSOP 전체
│   │   │
│   │   ├── WSOP ARCHIVE (PRE-2016)/      # 레거시 아카이브 (1973-2016)
│   │   │   ├── WSOP 1973/
│   │   │   ├── WSOP 1978-1979/
│   │   │   ├── WSOP 1981, 1983, 1987-1995, 1997-2003/
│   │   │   ├── WSOP 2004/
│   │   │   │   ├── Generics/
│   │   │   │   ├── MOVs/
│   │   │   │   └── MXFs/
│   │   │   ├── WSOP 2005/
│   │   │   │   ├── Generic/
│   │   │   │   ├── MOVs/
│   │   │   │   └── MXFs/
│   │   │   ├── WSOP 2006-2008/
│   │   │   │   └── MXFs/
│   │   │   ├── WSOP 2009-2010/
│   │   │   │   └── Masters/
│   │   │   ├── WSOP 2011-2014/
│   │   │   ├── WSOP 2015/
│   │   │   │   ├── Main Event MOVs/
│   │   │   │   ├── NC/
│   │   │   │   └── NC MOVs/
│   │   │   └── WSOP 2016/
│   │   │       ├── GCC MXFs/
│   │   │       └── Main Event MXFs/
│   │   │
│   │   ├── WSOP Bracelet Event/          # 브레이슬릿 이벤트 (2008-2025)
│   │   │   │
│   │   │   ├── WSOP-EUROPE/              # WSOP Europe
│   │   │   │   ├── 2008-2013 WSOP-Europe/
│   │   │   │   ├── 2021, 2024 WSOP-Europe/
│   │   │   │   └── 2025 WSOP-Europe/
│   │   │   │       ├── #2 KING'S MILLION FINAL/
│   │   │   │       │   └── NO COMMENTARY WITH GRAPHICS VER/
│   │   │   │       ├── #4 2K MONSTERSTACK FINAL/
│   │   │   │       ├── #5 MINI MAIN EVENT/
│   │   │   │       ├── #6 2K PLO FINAL/
│   │   │   │       ├── #7 COLOSSUS FINAL/
│   │   │   │       ├── #10 10K PLO MY.BO FINAL/
│   │   │   │       ├── #13 GGMILLION€ FINAL/
│   │   │   │       └── #14 MAIN EVENT/
│   │   │   │           ├── STREAM/
│   │   │   │           └── NO COMMENTARY WITH GRAPHICS VER/
│   │   │   │               └── Day 1A, 1B, Day 2-5/
│   │   │   │
│   │   │   ├── WSOP-LAS VEGAS/           # WSOP Las Vegas
│   │   │   │   ├── 2021, 2022 WSOP - LAS Vegas/
│   │   │   │   ├── 2024 WSOP-LAS VEGAS (PokerGo Clip)/
│   │   │   │   │   ├── Clean/
│   │   │   │   │   └── Mastered/
│   │   │   │   └── 2025 WSOP-LAS VEGAS/
│   │   │   │       ├── WSOP 2025 BRACELET SIDE EVENT/
│   │   │   │       │   └── Event #1-76/ (30+ 이벤트 폴더)
│   │   │   │       └── WSOP 2025 MAIN EVENT/
│   │   │   │           ├── Day 1/ (1A, 1B, 1C, 1D)
│   │   │   │           ├── Day 2/ (2ABC, 2D)
│   │   │   │           ├── Day 3-8/
│   │   │   │           └── Final Table/ (Day 1, Day 2)
│   │   │   │
│   │   │   └── WSOP-PARADISE/            # WSOP Paradise
│   │   │       ├── 2023 WSOP-PARADISE/
│   │   │       │   ├── STREAM/
│   │   │       │   └── SUBCLIP/
│   │   │       └── 2024 WSOP-PARADISE SUPER MAIN EVENT/
│   │   │           └── Hand Clip/
│   │   │               └── Day 1B, 1C, 1D, Day 2-4, Final Day/
│   │   │
│   │   └── WSOP Circuit Event/           # 서킷 이벤트
│   │       ├── WSOP Super Ciruit/
│   │       │   ├── 2023 WSOP International Super Circuit - London/
│   │       │   └── 2025 WSOP Super Circuit Cyprus/
│   │       └── WSOP-Circuit/
│   │           └── 2024 WSOP Circuit LA/
│   │               ├── 2024 WSOP-C LA STREAM/
│   │               └── 2024 WSOP-C LA SUBCLIP/
│   │
│   ├── HCL/                              # Hustler Casino Live
│   │   ├── HCL Poker Clip/
│   │   │   ├── 2023/
│   │   │   ├── 2024/
│   │   │   └── 2025/
│   │   └── SHOW, SERIES/
│   │
│   ├── PAD/                              # Poker After Dark
│   │   ├── PAD S12/
│   │   └── PAD S13/
│   │
│   ├── GGMillions/                       # GG Millions
│   │
│   ├── MPP/                              # Malta Poker Party
│   │   └── 2025 MPP Cyprus/
│   │       ├── $1M GTD $1K PokerOK Mystery Bounty/
│   │       ├── $2M GTD $2K Luxon Pay Grand Final/
│   │       └── $5M GTD $5K MPP Main Event/
│   │
│   └── GOG 최종/                         # Game of Gold
│       └── e01-e12/ (에피소드별)
│
├── Clips/                                # 부가 폴더 (작업용)
└── Player Emotion & ETC/                 # 부가 폴더 (PE 클립)
```

### 2.2 폴더 계층 구조 분석

| 레벨 | 의미 | 예시 |
|------|------|------|
| **Level 1** | Brand | `WSOP/`, `HCL/`, `PAD/`, `MPP/`, `GOG 최종/` |
| **Level 2** | Event Category | `WSOP Bracelet Event/`, `WSOP Circuit Event/`, `HCL Poker Clip/` |
| **Level 3** | Location | `WSOP-EUROPE/`, `WSOP-LAS VEGAS/`, `WSOP-PARADISE/` |
| **Level 4** | Year + Event | `2025 WSOP-Europe/`, `2024 WSOP Circuit LA/` |
| **Level 5** | Specific Event | `#14 MAIN EVENT/`, `WSOP 2025 MAIN EVENT/` |
| **Level 6** | Asset Type/Day | `STREAM/`, `NO COMMENTARY.../`, `Day 1A/`, `Hand Clip/` |

### 2.3 저장소 통계

| 브랜드 | 폴더 수 | 비고 |
|--------|---------|------|
| **WSOP** | ~170 | Archive + Bracelet + Circuit |
| **HCL** | 6 | Poker Clip (2023-2025) + SHOW |
| **PAD** | 3 | Season 12-13 |
| **MPP** | 5 | 2025 Cyprus 이벤트 |
| **GOG** | 13 | 에피소드 12개 |
| **GGMillions** | 1 | |
| **총계** | **194** | ARCHIVE/ 하위 전체 |

### 2.4 파일명 패턴 분석

#### 2.4.1 코드 기반 파일명 (Subclip)

| 패턴 | 예시 | 분석 |
|------|------|------|
| `WCLA{YY}-{NN}` | `WCLA24-01.mp4` | WSOP Circuit LA 2024, 클립 #01 |
| `WP{YY}-{NN}` | `WP23-03.mp4` | WSOP Paradise 2023, 클립 #03 |
| `WP{YY}-PE-{NN}` | `WP23-PE-01.mp4` | WSOP Paradise 2023, Player Emotion #01 |
| `WV{YY}-HB-{NN}` | `WV22-HB-02.mp4` | WSOP Vegas 2022, Highlight/Best #02 |
| `PAD_S{SS}_EP{NN}` | `PAD_S13_EP01_GGPoker-001.mp4` | PAD Season 13 Episode 01 |

#### 2.4.2 설명적 파일명 (Mastered/Stream)

```
# WSOP Mastered 예시
{순번}-wsop-{년도}-be-ev-{이벤트번호}-{바이인}-{게임}-{설명}.mp4

예: 10-wsop-2024-be-ev-21-25k-nlh-hr-ft-schutten-reclaims-chip-lead.mp4
    └─ 순번: 10
    └─ 년도: 2024
    └─ be-ev: Bracelet Event
    └─ 이벤트: #21
    └─ 바이인: 25k (USD 25,000)
    └─ 게임: nlh (No Limit Hold'em)
    └─ hr: High Roller
    └─ ft: Final Table
    └─ 설명: schutten reclaims chip lead
```

#### 2.2.3 GGMillions 파일명

```
{날짜}_Super High Roller Poker FINAL TABLE with {플레이어}.mp4

예: 250507_Super High Roller Poker FINAL TABLE with Joey ingram.mp4
    └─ 날짜: 2025-05-07
    └─ 플레이어: Joey Ingram
```

### 2.3 파일명 코드 사전

| 코드 | 의미 | 예시 브랜드 |
|------|------|-------------|
| `WCLA` | WSOP Circuit LA | WSOP Circuit |
| `WP` | WSOP Paradise | WSOP Paradise |
| `WV` | WSOP Vegas | WSOP Las Vegas |
| `WSOPE` | WSOP Europe | WSOP Europe |
| `PAD` | Poker After Dark | PokerGo |
| `HCL` | Hustler Casino Live | HCL |
| `PE` | Player Emotion | - |
| `HB` | Highlight/Best | - |
| `ET` | Episode/Tournament | - |
| `be-ev` | Bracelet Event | WSOP |
| `nlh` | No Limit Hold'em | - |
| `plo` | Pot Limit Omaha | - |
| `hr` | High Roller | - |
| `shr` | Super High Roller | - |
| `ft` | Final Table | - |

---

## 3. Schema Architecture

### 3.1 2-Level 구조 (gemini.md 기반)

```
Level 1: Asset (물리적 파일)
    └── 하나의 영상 파일에 대한 불변 정보

Level 2: Segment (논리적 구간)
    └── Asset 내 특정 구간 (포커 핸드)
    └── 1 Asset : N Segments
```

### 3.2 설계 원칙 (3+1)

| 원칙 | 설명 | 예시 |
|------|------|------|
| **Unique ID First** | 파일명/경로 대신 UUID | `asset_uuid`, `segment_uuid` |
| **Time as Float** | 타임코드 대신 초(Seconds) | `time_in_sec: 3625.500` |
| **Tags as Arrays** | 컬럼 분리 대신 배열 | `players: ["A", "B", "C"]` |
| **Domain Extension** | 포커 특화 필드 확장 | `situation_flags`, `all_in_stage` |

---

## 4. Schema Definition

### 4.1 Enumerations (NAS 기반 확장)

```python
from enum import Enum

class Brand(str, Enum):
    """브랜드 (NAS 기반)"""
    WSOP = "WSOP"               # World Series of Poker
    WSOPC = "WSOPC"             # WSOP Circuit
    WSOPE = "WSOPE"             # WSOP Europe
    WSOPP = "WSOPP"             # WSOP Paradise
    HCL = "HCL"                 # Hustler Casino Live
    PAD = "PAD"                 # Poker After Dark
    GG_MILLIONS = "GGMillions"  # GGPoker Super High Roller
    MPP = "MPP"                 # Malta Poker Party
    GOG = "GOG"                 # Game of Gold
    WPT = "WPT"                 # World Poker Tour
    EPT = "EPT"                 # European Poker Tour
    OTHER = "OTHER"

class EventType(str, Enum):
    """이벤트 유형"""
    BRACELET = "BRACELET"       # 브레이슬릿 이벤트 (메인)
    CIRCUIT = "CIRCUIT"         # 서킷 이벤트
    CASH_GAME_SHOW = "CASH_GAME_SHOW"  # 캐시게임 쇼
    SUPER_MAIN = "SUPER_MAIN"   # 슈퍼 메인 이벤트
    ARCHIVE = "ARCHIVE"         # 아카이브 (역사적 자료)
    SIDE_EVENT = "SIDE_EVENT"   # 사이드 이벤트

class AssetType(str, Enum):
    """Asset 유형 (폴더 구조 기반)"""
    STREAM = "STREAM"           # 풀 스트림 영상
    SUBCLIP = "SUBCLIP"         # 편집된 서브클립
    HAND_CLIP = "HAND_CLIP"     # 핸드별 클립 (WSOP Paradise)
    MASTER = "MASTER"           # 마스터링 완료 (Mastered/)
    CLEAN = "CLEAN"             # 클린 버전 (자막/그래픽 없음)
    NO_COMMENTARY = "NO_COMMENTARY"  # 해설 없는 버전
    RAW = "RAW"                 # 원본 영상
    GENERIC = "GENERIC"         # 레거시 Generic 폴더
    MOV = "MOV"                 # 레거시 MOV 포맷
    MXF = "MXF"                 # 레거시 MXF 포맷

class Location(str, Enum):
    """개최 장소"""
    LAS_VEGAS = "Las Vegas"
    PARADISE = "Paradise"       # Bahamas
    EUROPE = "Europe"
    LOS_ANGELES = "Los Angeles"
    CYPRUS = "Cyprus"
    ROZVADOV = "Rozvadov"       # King's Casino
    OTHER = "Other"

class GameVariant(str, Enum):
    """게임 종류"""
    NLH = "NLH"                 # No Limit Hold'em
    PLO = "PLO"                 # Pot Limit Omaha
    STUD = "STUD"               # Seven Card Stud
    RAZZ = "RAZZ"
    HORSE = "HORSE"
    MIXED = "MIXED"
    OMAHA_HI_LO = "OMAHA_HI_LO"
    TD_27 = "2-7_TD"            # 2-7 Triple Draw
    OTHER = "OTHER"
```

### 4.2 Level 1: Asset Entity

```python
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class EventContext(BaseModel):
    """이벤트 컨텍스트 (NAS 계층 구조 반영)"""

    # === 필수 ===
    year: int = Field(..., ge=1970, le=2100)
    brand: Brand = Field(...)  # WSOP, HCL, PAD, GGMillions...

    # === 권장 ===
    event_type: Optional[EventType] = None  # BRACELET, CIRCUIT...
    location: Optional[Location] = None
    venue: Optional[str] = None  # "Horseshoe Casino", "Hustler Casino"

    # === 상세 (선택) ===
    event_number: Optional[int] = None      # 이벤트 번호 (예: Event #21)
    buyin_usd: Optional[int] = None         # 바이인 (예: 25000)
    game_variant: Optional[GameVariant] = None  # NLH, PLO...
    is_high_roller: bool = False
    is_super_high_roller: bool = False
    is_final_table: bool = False

    # === 시즌/에피소드 (PAD, HCL) ===
    season: Optional[int] = None
    episode: Optional[int] = None
    episode_title: Optional[str] = None

class TechSpec(BaseModel):
    """기술 사양"""
    fps: float = Field(default=29.97)
    resolution: Optional[str] = None  # "1080p", "4K"
    duration_sec: Optional[float] = None
    file_size_mb: Optional[float] = None
    codec: Optional[str] = None  # "H.264", "ProRes"

class FileNameMeta(BaseModel):
    """파일명에서 추출된 메타데이터"""
    code_prefix: Optional[str] = None  # "WCLA", "WP", "PAD"
    year_code: Optional[str] = None    # "24", "23"
    sequence_num: Optional[int] = None  # 클립 번호
    clip_type: Optional[str] = None    # "PE" (Player Emotion), "HB" (Highlight)
    raw_description: Optional[str] = None  # 파일명에서 추출된 설명

class Asset(BaseModel):
    """물리적 파일 엔티티"""

    # === 식별자 ===
    asset_uuid: UUID = Field(..., description="파일 Hash 기반 생성")

    # === 파일 정보 ===
    file_name: str = Field(..., min_length=1)
    file_path_rel: Optional[str] = None  # NAS 상대 경로
    file_path_nas: Optional[str] = None  # 전체 NAS 경로

    # === Asset 유형 ===
    asset_type: AssetType = AssetType.SUBCLIP

    # === 컨텍스트 (확장) ===
    event_context: EventContext
    tech_spec: Optional[TechSpec] = None
    file_name_meta: Optional[FileNameMeta] = None

    # === Google Sheets 추가 필드 (Issue #7) ===
    file_number: Optional[int] = None        # Circuit: File No. (파일 순번)
    tournament_name: Optional[str] = None    # Database: Tournament
    project_name_tag: Optional[str] = None   # Database: ProjectNameTag
    nas_folder_link: Optional[str] = None    # Database: NAS Folder Link

    # === 메타 ===
    source_origin: str = Field(...)  # "NAS_WSOP_2024", "Legacy_Excel_v1"
    created_at: Optional[datetime] = None
    last_modified: Optional[datetime] = None

    # === 관계 ===
    segments: list["Segment"] = Field(default_factory=list)
```

### 4.3 Level 2: Segment Entity

```python
from enum import Enum

class GameType(str, Enum):
    TOURNAMENT = "TOURNAMENT"
    CASH_GAME = "CASH_GAME"

class AllInStage(str, Enum):
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    NONE = "none"

class SegmentType(str, Enum):
    """Segment 유형"""
    HAND = "HAND"               # 포커 핸드
    HIGHLIGHT = "HIGHLIGHT"     # 하이라이트
    PLAYER_EMOTION = "PE"       # 플레이어 감정
    INTRO_OUTRO = "INTRO"       # 인트로/아웃트로
    COMMENTARY = "COMMENTARY"   # 해설 구간

class SituationFlags(BaseModel):
    """상황 플래그 (포커 특화)"""
    is_cooler: bool = False
    is_badbeat: bool = False
    is_suckout: bool = False
    is_bluff: bool = False
    is_hero_call: bool = False
    is_hero_fold: bool = False
    is_river_killer: bool = False  # 리버 킬러 (NAS 파일명 발견)

class PlayerInHand(BaseModel):
    """핸드 참여 플레이어 정보"""
    name: str                           # "Daniel Negreanu"
    hand: Optional[str] = None          # "AA", "KK" (홀카드)
    position: Optional[str] = None      # "BTN", "BB", "UTG"
    is_winner: bool = False             # 승자 여부
    chips_won: Optional[int] = None     # 획득 칩 (선택)

class Segment(BaseModel):
    """논리적 구간 엔티티 (핸드)"""

    # === 식별자 ===
    segment_uuid: UUID
    parent_asset_uuid: UUID  # FK → Asset

    # === Segment 유형 ===
    segment_type: SegmentType = SegmentType.HAND

    # === 시간 (필수) ===
    time_in_sec: float = Field(..., ge=0)
    time_out_sec: float = Field(..., ge=0)

    # === 시간 (밀리초 - Issue #7) ===
    time_in_ms: Optional[int] = None   # Database: time_start_ms
    time_out_ms: Optional[int] = None  # Database: time_end_ms

    # === 기본 정보 ===
    title: Optional[str] = None
    game_type: GameType = GameType.TOURNAMENT
    rating: Optional[int] = Field(None, ge=0, le=5)

    # === 핸드 결과 ===
    winner: Optional[str] = None
    winning_hand: Optional[str] = None  # "Full House" (파일명에서 추출)
    losing_hand: Optional[str] = None   # "Flush"

    # === 참여자 (구조화) ===
    players: Optional[list[PlayerInHand]] = None  # 플레이어별 핸드 정보 포함

    # === 태그 시스템 ===
    tags_action: Optional[list[str]] = None   # ["preflop-allin", "cooler"]
    tags_emotion: Optional[list[str]] = None  # ["brutal", "suckout"]
    tags_content: Optional[list[str]] = None  # ["dirty", "outro", "hs" (highlight)]

    # === Google Sheets 추가 필드 (Issue #7) ===
    tags_player: Optional[list[str]] = None   # Circuit: Tag (Player) 1-3
    tags_search: Optional[list[str]] = None   # Database: SearchTag
    hand_tag: Optional[str] = None            # Database: HANDTag 원본 ("QQ vs KK")
    scene: Optional[str] = None               # Database: Scene 컬럼
    source_type: Optional[str] = None         # Database: Source (PGM, RAW)
    is_epic_hand: bool = False                # Database: EPICHAND Boolean
    appearance_outfit: Optional[str] = None   # Database: AppearanceOutfit
    scenery_object: Optional[str] = None      # Database: SceneryObject
    postflop_action: Optional[str] = None     # Database: PostFlop

    # === 포커 도메인 확장 ===
    situation_flags: Optional[SituationFlags] = None
    all_in_stage: Optional[AllInStage] = None
    runout_type: Optional[str] = None  # "runner-runner", "one-outer"
    adjective: Optional[str] = None     # "brutal", "insane", "incredible"
    board: Optional[str] = None         # "Ah Kd 7c 2s 9h"

    # === 파일명에서 추출 (NAS 분석 기반) ===
    event_stage: Optional[str] = None   # "ft" (Final Table), "day2"
    hand_description: Optional[str] = None  # 파일명에서 추출된 핸드 설명
    is_dirty: bool = False              # "dirty" 태그 (자막 포함)

    # === 메모 ===
    description: Optional[str] = None

    # === 컴퓨티드 ===
    @property
    def duration_sec(self) -> float:
        return self.time_out_sec - self.time_in_sec
```

---

## 5. JSON Golden Record

### 5.1 NAS 기반 완전한 예시 (WSOP Mastered)

```json
{
  "_metadata": {
    "schema_version": "3.0.0",
    "exported_at": "2025-12-11T15:30:00Z",
    "source": "NAS_WSOP_2024_MASTERED"
  },

  "asset": {
    "asset_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "file_name": "10-wsop-2024-be-ev-21-25k-nlh-hr-ft-schutten-reclaims-chip-lead.mp4",
    "file_path_rel": "/ARCHIVE/WSOP/WSOP Bracelet Event/WSOP-LAS VEGAS/2024 WSOP-LAS VEGAS (PokerGo Clip)/Mastered/",
    "file_path_nas": "//10.10.100.122/docker/GGPNAs/ARCHIVE/WSOP/WSOP Bracelet Event/WSOP-LAS VEGAS/2024 WSOP-LAS VEGAS (PokerGo Clip)/Mastered/",

    "asset_type": "MASTER",

    "event_context": {
      "year": 2024,
      "brand": "WSOP",
      "event_type": "BRACELET",
      "location": "Las Vegas",
      "venue": "Horseshoe Casino",
      "event_number": 21,
      "buyin_usd": 25000,
      "game_variant": "NLH",
      "is_high_roller": true,
      "is_final_table": true
    },

    "file_name_meta": {
      "code_prefix": "wsop",
      "year_code": "2024",
      "sequence_num": 10,
      "raw_description": "schutten-reclaims-chip-lead"
    },

    "tech_spec": {
      "fps": 29.97,
      "resolution": "1080p"
    },

    "source_origin": "NAS_WSOP_2024_MASTERED",

    "segments": [
      {
        "segment_uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "parent_asset_uuid": "550e8400-e29b-41d4-a716-446655440000",
        "segment_type": "HAND",

        "time_in_sec": 0.0,
        "time_out_sec": 94.7,

        "title": "Schutten reclaims chip lead",
        "game_type": "TOURNAMENT",
        "rating": 4,

        "winner": "Schutten",
        "players": ["Schutten"],

        "tags_action": ["chip-lead"],
        "tags_content": [],

        "event_stage": "ft",
        "hand_description": "schutten-reclaims-chip-lead"
      }
    ]
  }
}
```

### 5.2 NAS 기반 예시 (WSOP Circuit Subclip)

```json
{
  "_metadata": {
    "schema_version": "3.0.0",
    "source": "NAS_WSOPC_LA_2024"
  },

  "asset": {
    "asset_uuid": "661f9511-f30c-52e5-b827-557766551111",
    "file_name": "WCLA24-15.mp4",
    "file_path_rel": "/ARCHIVE/WSOP/WSOP Circuit Event/WSOP-Circuit/2024 WSOP Circuit LA/2024 WSOP-C LA SUBCLIP/",

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
      "sequence_num": 15
    },

    "source_origin": "NAS_WSOPC_LA_2024",
    "segments": []
  }
}
```

### 5.3 NAS 기반 예시 (PAD Season)

```json
{
  "_metadata": {
    "schema_version": "3.0.0",
    "source": "NAS_PAD_S13"
  },

  "asset": {
    "asset_uuid": "772g0622-g41d-63f6-c938-668877662222",
    "file_name": "PAD_S13_EP01_GGPoker-001.mp4",
    "file_path_rel": "/ARCHIVE/PAD/PAD S13/",

    "asset_type": "STREAM",

    "event_context": {
      "year": 2024,
      "brand": "PAD",
      "event_type": "CASH_GAME_SHOW",
      "season": 13,
      "episode": 1,
      "episode_title": "GGPoker"
    },

    "file_name_meta": {
      "code_prefix": "PAD",
      "sequence_num": 1,
      "clip_type": "EP"
    },

    "source_origin": "NAS_PAD_S13",
    "segments": []
  }
}
```

### 5.4 NAS 기반 예시 (GGMillions)

```json
{
  "_metadata": {
    "schema_version": "3.0.0",
    "source": "NAS_GGMILLIONS"
  },

  "asset": {
    "asset_uuid": "883h1733-h52e-74g7-d049-779988773333",
    "file_name": "250507_Super High Roller Poker FINAL TABLE with Joey ingram.mp4",
    "file_path_rel": "/ARCHIVE/GGMillions/",

    "asset_type": "STREAM",

    "event_context": {
      "year": 2025,
      "brand": "GGMillions",
      "event_type": "CASH_GAME_SHOW",
      "is_super_high_roller": true,
      "is_final_table": true
    },

    "file_name_meta": {
      "code_prefix": "GGMillions",
      "year_code": "25",
      "raw_description": "Joey Ingram"
    },

    "source_origin": "NAS_GGMILLIONS",

    "segments": [
      {
        "segment_uuid": "seg-ggm-001",
        "parent_asset_uuid": "883h1733-h52e-74g7-d049-779988773333",
        "segment_type": "HAND",
        "time_in_sec": 0.0,
        "time_out_sec": 0.0,
        "game_type": "CASH_GAME",
        "players": ["Joey Ingram"]
      }
    ]
  }
}
```

### 5.5 최소 필수 예시

```json
{
  "asset": {
    "asset_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "file_name": "WCLA24-01.mp4",
    "asset_type": "SUBCLIP",
    "event_context": {
      "year": 2024,
      "brand": "WSOPC"
    },
    "source_origin": "NAS_WSOPC_LA_2024",
    "segments": []
  }
}
```

---

## 6. Field Reference

### 6.1 필수 필드

| Level | Field | Type | Description |
|-------|-------|------|-------------|
| Asset | `asset_uuid` | UUID | 파일 해시 기반 PK |
| Asset | `file_name` | String | 확장자 포함 파일명 |
| Asset | `asset_type` | Enum | STREAM, SUBCLIP, MASTER, CLEAN |
| Asset | `event_context.year` | Integer | 개최 연도 |
| Asset | `event_context.brand` | Enum | WSOP, HCL, PAD 등 |
| Asset | `source_origin` | String | 데이터 출처 |
| Segment | `segment_uuid` | UUID | Segment 고유 식별자 (Primary Key) |
| Segment | `parent_asset_uuid` | UUID | FK → Asset |
| Segment | `time_in_sec` | Float | 시작 시간 (초) |
| Segment | `time_out_sec` | Float | 종료 시간 (초) |
| Segment | `game_type` | Enum | TOURNAMENT \| CASH_GAME |

### 6.2 선택 필드 (권장)

| Level | Field | Type | Description |
|-------|-------|------|-------------|
| Asset | `file_path_rel` | String | NAS 상대 경로 |
| Asset | `file_path_nas` | String | 전체 NAS 경로 |
| Asset | `event_context.event_type` | Enum | BRACELET, CIRCUIT 등 |
| Asset | `event_context.location` | Enum | Las Vegas, Paradise 등 |
| Asset | `event_context.event_number` | Integer | 이벤트 번호 |
| Asset | `event_context.buyin_usd` | Integer | 바이인 금액 |
| Asset | `event_context.game_variant` | Enum | NLH, PLO 등 |
| Asset | `event_context.season` | Integer | 시즌 (PAD, HCL) |
| Asset | `event_context.episode` | Integer | 에피소드 번호 |
| Asset | `file_name_meta` | Object | 파일명 파싱 결과 |
| Asset | `tech_spec` | Object | fps, resolution, file_size_mb |
| Segment | `segment_type` | Enum | HAND, HIGHLIGHT, PE |
| Segment | `title` | String | 핸드 제목 |
| Segment | `rating` | Integer | 0-5 별점 |
| Segment | `winner` | String | 승자 (정규화) |
| Segment | `players` | Array[PlayerInHand] | 참여자 리스트 (핸드 정보 포함) |
| Segment | `tags_action` | Array | 액션 태그 |
| Segment | `tags_emotion` | Array | 감정 태그 |
| Segment | `tags_content` | Array | 콘텐츠 태그 (dirty, outro) |

### 6.3 포커 도메인 확장 필드

| Field | Type | Description | 예시 |
|-------|------|-------------|------|
| `situation_flags` | Object | 상황 Boolean 플래그 | `{is_cooler: true}` |
| `all_in_stage` | Enum | 올인 시점 | `preflop`, `flop`, `turn`, `river` |
| `runout_type` | String | 런아웃 타입 | `runner-runner`, `one-outer` |
| `adjective` | String | 형용사 | `brutal`, `insane`, `incredible` |
| `board` | String | 보드 카드 | `"Ah Kd 7c 2s 9h"` |
| `winning_hand` | String | 승리 패 | `"Full House"` |
| `losing_hand` | String | 패배 패 | `"Flush"` |
| `event_stage` | String | 이벤트 단계 | `"ft"`, `"day2"` |
| `is_dirty` | Boolean | 자막 포함 여부 | `true` |

### 6.4 Google Sheets 추가 필드 (Issue #7)

#### Segment 신규 필드

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `tags_player` | Array[str] | Circuit Tag (Player) 1-3 | 플레이어 태그 |
| `tags_search` | Array[str] | Database SearchTag | 검색 태그 |
| `hand_tag` | String | Database HANDTag | 핸드 태그 원본 ("QQ vs KK") |
| `scene` | String | Database Scene | 장면 설명 |
| `source_type` | String | Database Source | 소스 유형 (PGM, RAW) |
| `is_epic_hand` | Boolean | Database EPICHAND | 에픽 핸드 여부 |
| `appearance_outfit` | String | Database AppearanceOutfit | 외모/복장 설명 |
| `scenery_object` | String | Database SceneryObject | 장면 오브젝트 |
| `postflop_action` | String | Database PostFlop | 포스트플롭 액션 |
| `time_in_ms` | Integer | Database time_start_ms | 시작 시간 (밀리초) |
| `time_out_ms` | Integer | Database time_end_ms | 종료 시간 (밀리초) |

#### Asset 신규 필드

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `file_number` | Integer | Circuit File No. | 파일 순번 |
| `tournament_name` | String | Database Tournament | 토너먼트명 |
| `project_name_tag` | String | Database ProjectNameTag | 프로젝트 태그 |
| `nas_folder_link` | String | Both NAS Folder Link | NAS 폴더 링크 |

---

## 7. Controlled Vocabulary

### 7.1 tags_action (액션 태그)

```yaml
action_tags:
  # 프리플롭
  - "open-raise"
  - "3bet"
  - "4bet"
  - "5bet"
  - "limp"
  - "squeeze"

  # 올인
  - "preflop-allin"
  - "flop-allin"
  - "turn-allin"
  - "river-allin"

  # 상황
  - "cooler"
  - "set-over-set"
  - "flush-over-flush"
  - "runner-runner"
  - "one-outer"

  # 플레이
  - "bluff"
  - "hero-call"
  - "hero-fold"
  - "slow-play"
  - "check-raise"

  # NAS 파일명 발견
  - "river-killer"
  - "chip-lead"
  - "doubles"
  - "eliminated"
  - "wins"
```

### 7.2 tags_emotion (감정 태그)

```yaml
emotion_tags:
  # 긍정
  - "excitement"
  - "celebration"
  - "relief"

  # 부정
  - "frustration"
  - "tilt"
  - "disappointment"

  # 중립/강조
  - "dramatic"
  - "intense"
  - "suspense"
  - "shock"
```

### 7.3 tags_content (콘텐츠 태그 - NAS 기반)

```yaml
content_tags:
  # 편집 상태
  - "dirty"           # 자막/그래픽 포함
  - "clean"           # 자막/그래픽 없음
  - "mastered"        # 마스터링 완료

  # 콘텐츠 유형
  - "hs"              # Highlight/Summary
  - "ft"              # Final Table
  - "outro"           # 아웃트로
  - "intro"           # 인트로

  # 특수
  - "day1"            # Day 1
  - "day2"            # Day 2
  - "day3"            # Day 3
  - "final-day"       # Final Day
```

### 7.4 adjective (형용사)

```yaml
adjectives:
  - "brutal"
  - "insane"
  - "incredible"
  - "amazing"
  - "sick"
  - "epic"
  - "legendary"
  - "crazy"           # NAS 파일명 발견
```

---

## 8. Source Mapping Profiles

### 8.1 NAS 폴더 → UDM (신규)

```python
# 파일 경로 기반 매핑
NAS_PATH_MAPPING = {
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
    }
}

# 폴더명 기반 AssetType 추출
FOLDER_ASSET_TYPE = {
    "STREAM": AssetType.STREAM,
    "SUBCLIP": AssetType.SUBCLIP,
    "Mastered": AssetType.MASTER,
    "Clean": AssetType.CLEAN,
}
```

### 8.2 파일명 패턴 파서 (NAS 기반)

```python
import re

FILENAME_PATTERNS = {
    # WCLA24-15.mp4 → WSOP Circuit LA 2024, #15
    "circuit_subclip": r"^(?P<code>WCLA)(?P<year>\d{2})-(?P<num>\d+)\.(?P<ext>\w+)$",

    # WP23-PE-01.mp4 → WSOP Paradise 2023, Player Emotion #01
    "paradise_pe": r"^(?P<code>WP)(?P<year>\d{2})-(?P<type>PE|ET|HB)-(?P<num>\d+)\.(?P<ext>\w+)$",

    # PAD_S13_EP01_GGPoker-001.mp4 → PAD Season 13 Episode 01
    "pad_episode": r"^PAD_S(?P<season>\d+)_EP(?P<episode>\d+)_(?P<desc>.+)\.(?P<ext>\w+)$",

    # 10-wsop-2024-be-ev-21-25k-nlh-hr-ft-description.mp4
    "wsop_mastered": r"^(?P<num>\d+)-wsop-(?P<year>\d{4})-be-ev-(?P<event>\d+)-(?P<buyin>\d+k?)-(?P<game>nlh|plo|stud)-(?P<tags>.+)\.(?P<ext>\w+)$",

    # 250507_Super High Roller Poker FINAL TABLE with {player}.mp4
    "ggmillions": r"^(?P<date>\d{6})_Super High Roller Poker FINAL TABLE with (?P<player>.+)\.(?P<ext>\w+)$",
}

def parse_filename(filename: str) -> FileNameMeta:
    """파일명 파싱"""
    for pattern_name, pattern in FILENAME_PATTERNS.items():
        match = re.match(pattern, filename, re.IGNORECASE)
        if match:
            return FileNameMeta(
                code_prefix=match.groupdict().get("code"),
                year_code=match.groupdict().get("year"),
                sequence_num=int(match.groupdict().get("num", 0)),
                clip_type=match.groupdict().get("type"),
                raw_description=match.groupdict().get("desc") or match.groupdict().get("player")
            )
    return FileNameMeta()
```

### 8.3 파싱 헬퍼 함수 (Issue #7)

```python
# === Google Sheets 파싱 유틸리티 ===

def parse_time_hms(time_str: str) -> Optional[float]:
    """HH:MM:SS 또는 MM:SS 형식을 초(float)로 변환

    Examples:
        "01:23:45" → 5025.0
        "12:30" → 750.0
        "" → None
    """
    if not time_str or not time_str.strip():
        return None
    parts = time_str.strip().split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return None


def parse_star_rating(rating_str: str) -> Optional[int]:
    """★★★ 형식 또는 숫자를 int로 변환

    Examples:
        "★★★" → 3
        "5" → 5
        "" → None
    """
    if not rating_str or not rating_str.strip():
        return None
    rating_str = rating_str.strip()
    if "★" in rating_str:
        return rating_str.count("★")
    if rating_str.isdigit():
        return int(rating_str)
    return None


def parse_hand_matchup(hand_str: str) -> list[PlayerInHand]:
    """'AA vs KK' 또는 'QQ vs JJ vs 99' 형식을 PlayerInHand 리스트로 변환

    Examples:
        "AA vs KK" → [PlayerInHand(name="Player1", hand="AA"), ...]
        "QQ vs JJ vs 99" → 3 players
    """
    if not hand_str or not hand_str.strip():
        return []
    hands = [h.strip() for h in hand_str.split("vs")]
    return [
        PlayerInHand(name=f"Player{i+1}", hand=h)
        for i, h in enumerate(hands) if h
    ]


def parse_players_tags(players_str: str) -> list[str]:
    """콤마로 구분된 플레이어 이름을 리스트로 변환

    Examples:
        "Phil Ivey, Doyle Brunson" → ["Phil Ivey", "Doyle Brunson"]
    """
    if not players_str or not players_str.strip():
        return []
    players = [p.strip() for p in players_str.split(",")]
    return list(dict.fromkeys(p for p in players if p))  # 중복 제거, 순서 유지


def merge_tag_columns(*columns: str) -> list[str]:
    """여러 태그 컬럼을 하나의 리스트로 병합 (중복 제거)

    Examples:
        merge_tag_columns("bluff", "hero-call", "bluff") → ["bluff", "hero-call"]
    """
    merged = []
    for col in columns:
        if col and col.strip():
            merged.append(col.strip())
    return list(dict.fromkeys(merged))


def parse_all_in_tags(all_in_str: str) -> Optional[AllInStage]:
    """All-in 컬럼값을 AllInStage Enum으로 변환

    Examples:
        "Preflop" → AllInStage.PREFLOP
        "flop" → AllInStage.FLOP
    """
    if not all_in_str or not all_in_str.strip():
        return None
    mapping = {
        "preflop": AllInStage.PREFLOP,
        "flop": AllInStage.FLOP,
        "turn": AllInStage.TURN,
        "river": AllInStage.RIVER,
    }
    return mapping.get(all_in_str.strip().lower())


def parse_situation_flags_from_columns(row: dict) -> SituationFlags:
    """Boolean 컬럼들로부터 SituationFlags 객체 생성

    Args:
        row: {"Cooler": "TRUE", "Badbeat": "FALSE", ...}

    Returns:
        SituationFlags(is_cooler=True, is_badbeat=False, ...)
    """
    def to_bool(val) -> bool:
        if val is None:
            return False
        if isinstance(val, bool):
            return val
        return str(val).strip().upper() in ("TRUE", "1", "YES", "O")

    return SituationFlags(
        is_cooler=to_bool(row.get("Cooler")),
        is_badbeat=to_bool(row.get("Badbeat")),
        is_suckout=to_bool(row.get("Suckout")),
        is_bluff=to_bool(row.get("Bluff")),
        is_hero_call=to_bool(row.get("HeroCall")),
        is_hero_fold=to_bool(row.get("HeroFold")),
        is_river_killer=to_bool(row.get("RiverKiller")),
    )
```

### 8.4 Archive Metadata Sheet (Source 1) → UDM (23 컬럼 완전 매핑)

| Source Column | UDM Field | Transform | Helper Function |
|---------------|-----------|-----------|-----------------|
| - | `asset_uuid` | Generate (file_hash) | - |
| `File No.` | `file_number` | Direct (int) | - |
| `File Name` | `file_name` | Direct | - |
| `File Name` | `event_context.year` | Extract (regex) | `parse_filename()` |
| - | `event_context.brand` | Constant ("WSOPC") | - |
| `Nas Folder Link` | `nas_folder_link` | Direct | - |
| - | `segment_uuid` | Generate (uuid4) | - |
| `In` | `time_in_sec` | HH:MM:SS → Seconds | `parse_time_hms()` |
| `Out` | `time_out_sec` | HH:MM:SS → Seconds | `parse_time_hms()` |
| `Hand Grade` | `rating` | ★★★ → Int | `parse_star_rating()` |
| `Winner` | `winner` | Normalize | - |
| `Hands` | `players` | "AA vs KK" → PlayerInHand[] | `parse_hand_matchup()` |
| `Tag (Player) 1-3` | `tags_player` | 3컬럼 병합 | `merge_tag_columns()` |
| `Tag (Play) 1-7` | `tags_action` | 7컬럼 병합 | `merge_tag_columns()` |
| `Tag (Emotion) 1-2` | `tags_emotion` | 2컬럼 병합 | `merge_tag_columns()` |

### 8.5 Iconik Metadata Sheet (Source 2) → UDM (35 컬럼 완전 매핑)

| Source Column | UDM Field | Transform | Helper Function |
|---------------|-----------|-----------|-----------------|
| - | `asset_uuid` | Generate (content_hash) | - |
| `ProjectName` | `event_context.brand` | Map | - |
| `ProjectNameTag` | `project_name_tag` | Direct | - |
| `Year_` | `event_context.year` | Direct | - |
| `Location` | `event_context.location` | Direct | - |
| `Venue` | `event_context.venue` | Direct | - |
| `EpisodeEvent` | `event_context.episode` | Direct | - |
| `Tournament` | `tournament_name` | Direct | - |
| `id` | `segment_uuid` | Direct (UUID) | - |
| `time_start_S` | `time_in_sec` | Direct | - |
| `time_end_S` | `time_out_sec` | Direct | - |
| `time_start_ms` | `time_in_ms` | Direct (int) | - |
| `time_end_ms` | `time_out_ms` | Direct (int) | - |
| `title` | `title` | Direct | - |
| `HandGrade` | `rating` | Stars → Int | `parse_star_rating()` |
| `HANDTag` | `hand_tag` | Direct (원본 저장) | - |
| `HANDTag` | `players` | "AA vs KK" 파싱 | `parse_hand_matchup()` |
| `PlayersTags` | `players` | 이름 리스트 | `parse_players_tags()` |
| `SearchTag` | `tags_search` | Split by comma | - |
| `PokerPlayTags` | `tags_action` | Split by comma | - |
| `Emotion` | `tags_emotion` | Split by comma | - |
| `Scene` | `scene` | Direct | - |
| `Source` | `source_type` | Direct (PGM/RAW) | - |
| `EPICHAND` | `is_epic_hand` | Boolean | - |
| `AppearanceOutfit` | `appearance_outfit` | Direct | - |
| `SceneryObject` | `scenery_object` | Direct | - |
| `PostFlop` | `postflop_action` | Direct | - |
| `Adjective` | `adjective` | Direct | - |
| `All-in` | `all_in_stage` | Map | `parse_all_in_tags()` |
| `RUNOUTTag` | `runout_type` | Direct | - |
| `Cooler` | `situation_flags.is_cooler` | Boolean | `parse_situation_flags_from_columns()` |
| `Badbeat` | `situation_flags.is_badbeat` | Boolean | `parse_situation_flags_from_columns()` |
| `Suckout` | `situation_flags.is_suckout` | Boolean | `parse_situation_flags_from_columns()` |
| `Bluff` | `situation_flags.is_bluff` | Boolean | `parse_situation_flags_from_columns()` |
| `NAS Folder Link` | `nas_folder_link` | Direct | - |

---

## 9. Validation Rules

### 9.1 스키마 검증

```python
SCHEMA_RULES = {
    # 필수 필드
    "asset_uuid": {"required": True, "type": "uuid"},
    "file_name": {"required": True, "type": "string", "min_length": 1},
    "asset_type": {"required": True, "enum": ["STREAM", "SUBCLIP", "MASTER", "CLEAN", "RAW"]},
    "event_context.year": {"required": True, "type": "int", "min": 1970, "max": 2100},
    "event_context.brand": {"required": True, "enum": ["WSOP", "WSOPC", "WSOPE", "WSOPP", "HCL", "PAD", "GGMillions", "MPP", "GOG", "WPT", "EPT", "OTHER"]},
    "source_origin": {"required": True, "type": "string"},

    # Segment 필수 필드
    "segment_uuid": {"required": True, "type": "uuid"},
    "time_in_sec": {"required": True, "type": "float", "min": 0},
    "time_out_sec": {"required": True, "type": "float", "min": 0},
    "game_type": {"required": True, "enum": ["TOURNAMENT", "CASH_GAME"]},

    # 선택 필드 제약
    "rating": {"type": "int", "min": 0, "max": 5},
    "all_in_stage": {"enum": ["preflop", "flop", "turn", "river", "none"]},
    "segment_type": {"enum": ["HAND", "HIGHLIGHT", "PE", "INTRO", "COMMENTARY"]},
}
```

### 9.2 비즈니스 규칙

| Rule ID | 규칙 | Severity |
|---------|------|----------|
| BR-001 | `time_out_sec > time_in_sec` | ERROR |
| BR-002 | `winner`가 `players`에 포함 | WARNING |
| BR-003 | 핸드 길이 10초-3600초 | WARNING |
| BR-004 | `is_cooler=true`면 `tags_action`에 `"cooler"` 권장 | INFO |
| BR-005 | NAS 경로와 `brand` 일치 | WARNING |
| BR-006 | `file_name_meta` 파싱 성공 시 `event_context` 자동 채움 | INFO |

---

## 10. OHH Compatibility Layer (선택적)

향후 상세 핸드 데이터가 필요한 경우를 위한 확장 필드:

```json
{
  "segment": {
    "...기본 필드...",

    "ohh_detail": {
      "spec_version": "1.4.7",
      "game_number": "WSOP-2024-ME-001",
      "players": [
        {"id": 1, "name": "Daniel Negreanu", "cards": ["As", "Ad"]},
        {"id": 2, "name": "Phil Hellmuth", "cards": ["Ks", "Kh"]}
      ],
      "rounds": [
        {
          "street": "Preflop",
          "actions": [
            {"player_id": 1, "action": "Raise", "amount": 900000},
            {"player_id": 2, "action": "Raise", "amount": 32000000, "is_allin": true}
          ]
        }
      ]
    }
  }
}
```

**사용 시점**:
- 상세 베팅 분석 필요 시
- PokerTracker/HM 데이터 import 시
- 게임 재현 필요 시

---

## 11. Migration Guide

### 11.1 PRD-0007 → PRD-0008 변경점

| 항목 | PRD-0007 | PRD-0008 v3.0 |
|------|----------|---------------|
| OHH 필드 | 전체 포함 | 선택적 확장 (`ohh_detail`) |
| `time_in_ms` | 필수 | 제거 (불필요) |
| `situation_flags` | 개별 필드 | 중첩 Object |
| `players.normalized` | 필수 | 단일 `players` |
| `event_context.series` | String | **`brand` Enum으로 변경** |
| `asset_type` | 없음 | **신규 (NAS 기반)** |
| `file_name_meta` | 없음 | **신규 (파일명 파싱)** |
| `segment_type` | 없음 | **신규 (HAND, PE 등)** |
| `tags_content` | 없음 | **신규 (dirty, hs 등)** |

### 11.2 이전 버전 호환

PRD-0007 형식 데이터는 다음으로 변환:
- `time_in_ms` → 제거
- `players.normalized` → `players`
- `event_context.series` → `event_context.brand` (매핑)
- `ohh_detail.rounds` → 유지 (선택적)
- `asset_type` → `SUBCLIP` (기본값)

---

## 12. Success Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| **스키마 커버리지** | 100% | NAS + 구글 시트 데이터 완전 수용 |
| **파일명 파싱 성공률** | 95%+ | 알려진 파일명 패턴 자동 파싱 |
| **필드 활용률** | 80%+ | 선택 필드 채움률 |
| **검색 응답 시간** | < 100ms | 태그 기반 검색 |
| **변환 정확도** | 99.5%+ | 원본 데이터 손실 없음 |
| **브랜드 분류 정확도** | 100% | NAS 경로 기반 브랜드 분류 |

---

## 13. Related PRDs

- **PRD-0001**: Master Orchestrator
- **PRD-0003**: Transform Agent (스키마 적용)
- **PRD-0004**: Validate Agent (검증 규칙)
- **PRD-0006**: Profile Manager (매핑 프로파일)
- **PRD-0007**: UDM Schema v1 (Deprecated → 본 문서로 대체)

---

## Appendix A: Decision Log

| 날짜 | 결정 | 근거 |
|------|------|------|
| 2025-12-11 | gemini.md 기반 채택 | 비디오 아카이빙 목적에 최적화 |
| 2025-12-11 | OHH 전체 채택 거부 | 오버엔지니어링, 목적 불일치 |
| 2025-12-11 | 포커 도메인 확장 추가 | 구글 시트 분석 결과 반영 |
| 2025-12-11 | OHH 선택적 확장 제공 | 향후 확장성 확보 |
| 2025-12-11 | v3.0 NAS 기반 확장 | 실제 폴더 구조/파일명 패턴 분석 반영 |
| 2025-12-11 | Brand Enum 도입 | NAS 브랜드 체계 표준화 (WSOP, HCL, PAD 등) |
| 2025-12-11 | AssetType 추가 | 폴더 구조 (STREAM/SUBCLIP/MASTER/CLEAN) 반영 |
| 2025-12-11 | **v3.1.0 Issue #7** | Google Sheets 23+35 컬럼 완전 매핑 |
| 2025-12-11 | Segment 11개 필드 추가 | Circuit/Database 시트 전체 데이터 수용 |
| 2025-12-11 | Asset 4개 필드 추가 | 파일순번, 토너먼트명, 프로젝트태그, NAS링크 |
| 2025-12-11 | 파싱 헬퍼 7개 함수 추가 | 시간/별점/핸드/태그 변환 자동화 |

## Appendix B: NAS 분석 통계

| 항목 | 값 |
|------|-----|
| **총 폴더 수** | **194** (ARCHIVE/ 하위, find 명령 기준) |
| **총 파일 수** | 1,400+ |
| **총 용량** | ~17 TB |
| **브랜드 수** | 6 (WSOP, HCL, PAD, GGMillions, MPP, GOG) |
| **연도 범위** | 1973-2025 (52년) |
| **파일명 패턴** | 5종 (circuit_subclip, paradise_pe, pad_episode, wsop_mastered, ggmillions) |

### 폴더 계층 분포

| 계층 | 폴더 수 | 예시 |
|------|---------|------|
| L1 (브랜드) | 6 | WSOP, HCL, PAD, GGMillions, MPP, GOG 최종 |
| L2 (이벤트 유형) | 4 | WSOP ARCHIVE, Bracelet Event, Circuit Event |
| L3 (장소) | 3 | WSOP-EUROPE, WSOP-LAS VEGAS, WSOP-PARADISE |
| L4 (연도/이벤트) | 50+ | 2025 WSOP-Europe, 2024 WSOP Circuit LA |
| L5 (이벤트별) | 70+ | Event #46 $250K SHR, MAIN EVENT |
| L6 (Day/Version) | 50+ | Day 1A, Day 1B, NO COMMENTARY VER, Hand Clip |

### 상세 용량 분포

| 기간 | 용량 | 파일 수 |
|------|------|---------|
| WSOP 1973-2002 | 2.4 TB | 85 |
| WSOP 2003-2010 | 10.6 TB | 322 |
| WSOP 2011-2016 | 1.9 TB | 184 |
| WSOP 2017-2025 | 1.0 TB | 600+ |
| HCL | 0.6 TB | 129 |
| PAD | 0.2 TB | 44 |
| 기타 | 0.3 TB | 50+ |

### 발견된 새로운 콘텐츠 유형

| 유형 | 폴더명 | 설명 |
|------|--------|------|
| **NO COMMENTARY** | `NO COMMENTARY WITH GRAPHICS VER/` | 해설 없는 버전 |
| **Hand Clip** | `Hand Clip/` | 핸드별 클립 (WSOP Paradise) |
| **Super Circuit** | `WSOP Super Ciruit/` | 슈퍼 서킷 이벤트 |

### 파일 포맷 분포 (추정)

| 포맷 | 용도 | 폴더 |
|------|------|------|
| MOV | 레거시 마스터 | 2003-2010 |
| MXF | 방송 마스터 | 2004-2016 |
| MP4 | 최신 편집본 | 2017+ |
| MKV | 일부 클립 | Clips |

## Appendix C: References

- [gemini.md](../docs/gemini.md) - 원본 UDM 설계
- [OHH Specification](https://hh-specs.handhistory.org/) - 포커 핸드 표준
- [PHH Standard](https://github.com/uoftcprg/phh-std) - 학술용 표준
- [IPTC Video Metadata Hub](https://iptc.org/standards/video-metadata-hub/) - 비디오 메타데이터 표준
- NAS: `//10.10.100.122/docker/GGPNAs/` - 실제 아카이브 소스
