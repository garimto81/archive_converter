# NAS-Google Sheets 연동 매칭 분석

**Version**: 1.0.0
**Created**: 2025-12-11
**Purpose**: NAS 저장소와 Google Sheets 데이터 소스 간의 연동 전략

---

## 1. 핵심 개념

### 1.1 데이터 소스 계층

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRIMARY SOURCE (진실의 원천)                   │
│                                                                 │
│   ┌─────────────┐                                               │
│   │     NAS     │  물리적 파일 저장소                             │
│   │  (194 폴더) │  - 파일 존재 여부의 진실                        │
│   │             │  - 경로, 파일명, 용량, 생성일                   │
│   └─────────────┘                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 METADATA SOURCES (메타데이터 소스)                │
│                                                                 │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│   │  Archive    │    │   Iconik    │    │   Future    │        │
│   │  Metadata   │    │  Metadata   │    │   Sources   │        │
│   │  (38 rows)  │    │  (200+ rows)│    │  (MAM API)  │        │
│   └─────────────┘    └─────────────┘    └─────────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      UDM (통합 데이터 모델)                       │
│                                                                 │
│   Asset (파일) ←──────────────────────→ Segment (핸드)          │
│   - NAS 경로 기반 UUID                  - 시트 데이터 기반 UUID   │
│   - 파일명, 경로, 기술사양               - 시간, 플레이어, 태그    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 연동의 핵심 질문

| 질문 | 답변 |
|------|------|
| **연결 키(Key)는?** | `File Name` (파일명) |
| **NAS에만 있으면?** | Asset 생성, Segment 없음 |
| **시트에만 있으면?** | Orphan 레코드 (경고) |
| **양쪽 다 있으면?** | Asset + Segment 완전 매칭 |

---

## 2. 데이터 소스 상세 분석

### 2.1 NAS 저장소

**위치**: `Z:\` (마운트) / `\\10.10.100.122\docker\GGPNAs\`

**최종 스캔일**: 2025-12-12

#### 폴더 구조 (전체)

```
Z:\
├── .isg/                              # 시스템 폴더
│   └── d2de5d18-ee58-11ef-852e-da5f3e9a002a/
├── Clips/                             # 클립 저장소
├── Player Emotion  & ETC/             # 플레이어 감정/기타
└── ARCHIVE/                           # 메인 아카이브
    ├── GGMillions/                    # GGMillions 브랜드
    ├── GOG 최종/                       # Game of Gold
    │   ├── e01/ ~ e12/                # 12개 에피소드
    ├── HCL/                           # Hustler Casino Live
    │   ├── HCL Poker Clip/            # 클립
    │   │   ├── 2023/
    │   │   ├── 2024/
    │   │   └── 2025/
    │   └── SHOW, SERIES/              # 쇼/시리즈
    ├── MPP/                           # ??? Poker
    │   └── 2025 MPP Cyprus/           # 2025 사이프러스
    │       ├── $1M GTD   $1K PokerOK Mystery Bounty/
    │       ├── $2M GTD   $2K Luxon Pay Grand Final/
    │       └── $5M GTD   $5K MPP Main Event/
    ├── PAD/                           # Poker After Dark
    │   ├── PAD S12/
    │   └── PAD S13/
    └── WSOP/                          # World Series of Poker
        ├── WSOP ARCHIVE (PRE-2016)/   # 레거시 (1973~2016)
        │   ├── WSOP 1973/
        │   ├── WSOP 1978/ ~ WSOP 2016/
        ├── WSOP Bracelet Event/       # 브레이슬릿 이벤트
        │   ├── WSOP-EUROPE/
        │   ├── WSOP-LAS VEGAS/
        │   └── WSOP-PARADISE/
        └── WSOP Circuit Event/        # 서킷 이벤트
            ├── WSOP Super Ciruit/
            └── WSOP-Circuit/
```

#### 브랜드별 폴더 요약

| 브랜드 | 하위 폴더 | 특징 |
|--------|----------|------|
| **WSOP** | 3개 분류 | Archive(1973~2016), Bracelet(EU/LV/Paradise), Circuit |
| **HCL** | 2개 | Poker Clip(2023~2025), SHOW/SERIES |
| **PAD** | 2개 | S12, S13 |
| **MPP** | 1개 | 2025 Cyprus (3개 이벤트) |
| **GOG** | 12개 | e01~e12 에피소드 |
| **GGMillions** | - | (하위 폴더 없음) |

#### NAS에서 추출 가능한 정보

| 정보 | 추출 방법 | 예시 |
|------|----------|------|
| `file_name` | 파일명 직접 | `WCLA24-15.mp4` |
| `file_path_nas` | 전체 경로 | `//10.10.100.122/.../SUBCLIP/` |
| `asset_type` | 폴더명 | `STREAM`, `SUBCLIP`, `Mastered` |
| `brand` | 경로 패턴 | `/WSOP/` → WSOP |
| `event_type` | 경로 패턴 | `/Circuit Event/` → CIRCUIT |
| `year` | 폴더명/파일명 | `2024`, `WCLA24` |
| `tech_spec` | ffprobe | fps, resolution, duration |

### 2.2 Archive Metadata Sheet

**Sheet Name**: Archive Metadata
**Google Sheet ID**: `1_RN_W_ZQclSZA0Iez6XniCXVtjkkd5HNZwiT6l-z6d4`
**Tab**: WSOP Circuit 2024

#### 컬럼 구조 (20개 유효 컬럼)

| # | 컬럼명 | 타입 | 용도 | UDM 필드 |
|---|--------|------|------|----------|
| 1 | `File No.` | Integer | 파일 순번 | `Asset.file_number` |
| 2 | `File Name` | String | **연결 키** | `Asset.file_name` |
| 3 | `Nas Folder Link` | URL | NAS 링크 | `Asset.nas_folder_link` |
| 4 | `In` | HH:MM:SS | 시작 시간 | `Segment.time_in_sec` |
| 5 | `Out` | HH:MM:SS | 종료 시간 | `Segment.time_out_sec` |
| 6 | `Hand Grade` | ★★★★★ | 별점 | `Segment.rating` |
| 7 | `Winner` | String | 승자 | `Segment.winner` |
| 8 | `Hands` | String | 핸드 매치업 | `Segment.hand_tag`, `players` |
| 9-11 | `Tag (Player)` x3 | String | 플레이어 태그 | `Segment.tags_player` |
| 12-18 | `Tag (Poker Play)` x7 | String | 액션 태그 | `Segment.tags_action` |
| 19-20 | `Tag (Emotion)` x2 | String | 감정 태그 | `Segment.tags_emotion` |

#### 특징

- **1 파일 = 1 핸드**: 각 행이 하나의 파일, 하나의 핸드
- **시간 형식**: `HH:MM:SS` → 초 변환 필요
- **별점 형식**: `★★★` → 숫자 변환 필요
- **다중 태그 컬럼**: 병합 필요

### 2.3 Iconik Metadata Sheet

**Sheet Name**: Iconik Metadata
**Google Sheet ID**: `1pUMPKe-OsKc-Xd8lH1cP9ctJO4hj3keXY5RwNFp2Mtk`
**Tab**: Database

#### 컬럼 구조 (35개 컬럼)

| # | 컬럼명 | 타입 | 용도 | UDM 필드 |
|---|--------|------|------|----------|
| 1 | `id` | UUID | **Segment PK** | `Segment.segment_uuid` |
| 2 | `title` | String | 제목 | `Segment.title` |
| 3 | `time_start_ms` | Integer | 시작 (ms) | `Segment.time_in_ms` |
| 4 | `time_end_ms` | Integer | 종료 (ms) | `Segment.time_out_ms` |
| 5 | `time_start_S` | Float | 시작 (초) | `Segment.time_in_sec` |
| 6 | `time_end_S` | Float | 종료 (초) | `Segment.time_out_sec` |
| 7 | `Description` | String | 설명 | `Segment.description` |
| 8 | `ProjectName` | String | 프로젝트명 | `EventContext.brand` |
| 9 | `ProjectNameTag` | String | 프로젝트 태그 | `Asset.project_name_tag` |
| 10 | `SearchTag` | String | 검색 태그 | `Segment.tags_search` |
| 11 | `Year_` | Integer | 연도 | `EventContext.year` |
| 12 | `Location` | String | 장소 | `EventContext.location` |
| 13 | `Venue` | String | 베뉴 | `EventContext.venue` |
| 14 | `EpisodeEvent` | String | 에피소드/이벤트 | `EventContext.episode` |
| 15 | `Source` | String | 소스 타입 | `Segment.source_type` |
| 16 | `Scene` | String | 장면 | `Segment.scene` |
| 17 | `GameType` | String | 게임 타입 | `Segment.game_type` |
| 18 | `PlayersTags` | String | 플레이어 (콤마) | `Segment.players` |
| 19 | `HandGrade` | String | 별점 | `Segment.rating` |
| 20 | `HANDTag` | String | 핸드 태그 | `Segment.hand_tag` |
| 21 | `EPICHAND` | Boolean | 에픽 핸드 | `Segment.is_epic_hand` |
| 22 | `Tournament` | String | 토너먼트명 | `Asset.tournament_name` |
| 23 | `PokerPlayTags` | String | 액션 (콤마) | `Segment.tags_action` |
| 24 | `Adjective` | String | 형용사 | `Segment.adjective` |
| 25 | `Emotion` | String | 감정 | `Segment.tags_emotion` |
| 26 | `AppearanceOutfit` | String | 외모/복장 | `Segment.appearance_outfit` |
| 27 | `SceneryObject` | String | 장면 오브젝트 | `Segment.scenery_object` |
| 28 | `_gcvi_tags` | String | 내부 태그 | (무시) |
| 29 | `Badbeat` | Boolean | 배드빗 | `SituationFlags.is_badbeat` |
| 30 | `Bluff` | Boolean | 블러프 | `SituationFlags.is_bluff` |
| 31 | `Suckout` | Boolean | 석아웃 | `SituationFlags.is_suckout` |
| 32 | `Cooler` | Boolean | 쿨러 | `SituationFlags.is_cooler` |
| 33 | `RUNOUTTag` | String | 런아웃 | `Segment.runout_type` |
| 34 | `PostFlop` | String | 포스트플롭 | `Segment.postflop_action` |
| 35 | `All-in` | String | 올인 스테이지 | `Segment.all_in_stage` |

#### 특징

- **1 파일 = N 핸드**: 하나의 영상에 여러 Segment
- **UUID 제공**: `id` 컬럼에 UUID 존재
- **시간 이중 제공**: ms와 초 둘 다 제공
- **Boolean 플래그**: TRUE/FALSE 문자열
- **콤마 구분 태그**: 단일 컬럼에 다중 값

---

## 3. 연동 전략

### 3.1 매칭 키 분석

```
┌─────────────────────────────────────────────────────────────┐
│                    MATCHING KEY STRATEGY                     │
│                                                             │
│   NAS File                    Google Sheet                  │
│   ─────────                   ────────────                  │
│                                                             │
│   WCLA24-15.mp4  ←─────────→  File Name: WCLA24-15.mp4     │
│        │                            │                       │
│        │         PRIMARY KEY        │                       │
│        └────────────────────────────┘                       │
│                                                             │
│   Alternative Keys (Fallback):                              │
│   - NAS Folder Link ←→ nas_folder_link                     │
│   - File Path Pattern ←→ ProjectName + Year                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 매칭 시나리오

#### 시나리오 1: 완전 매칭 (NAS + Sheet)

```python
# NAS 파일 존재 + Sheet 레코드 존재
{
    "asset": {
        "asset_uuid": "hash(file_path)",  # NAS 기반
        "file_name": "WCLA24-15.mp4",     # 양쪽 일치
        "file_path_nas": "//10.10.../SUBCLIP/WCLA24-15.mp4",
        "source_origin": "NAS_WSOPC_LA_2024",
        "segments": [
            {
                "segment_uuid": "uuid4()",  # 시트 기반 또는 생성
                "time_in_sec": 125.5,       # 시트 데이터
                "time_out_sec": 245.8,
                "rating": 4,
                "winner": "Phil Ivey",
                "tags_action": ["bluff", "hero-call"]
            }
        ]
    }
}
```

#### 시나리오 2: NAS Only (메타데이터 없음)

```python
# NAS 파일 존재 + Sheet 레코드 없음
{
    "asset": {
        "asset_uuid": "hash(file_path)",
        "file_name": "WCLA24-99.mp4",      # NAS에만 존재
        "file_path_nas": "//10.10.../SUBCLIP/WCLA24-99.mp4",
        "source_origin": "NAS_WSOPC_LA_2024",
        "segments": []  # 메타데이터 없음 - 수동 입력 필요
    },
    "_warnings": ["NO_METADATA: 시트에 매칭 레코드 없음"]
}
```

#### 시나리오 3: Sheet Only (Orphan)

```python
# NAS 파일 없음 + Sheet 레코드 존재
{
    "_orphan": True,
    "_error": "FILE_NOT_FOUND",
    "sheet_record": {
        "file_name": "WCLA24-XX.mp4",  # NAS에 없는 파일
        "time_in": "00:02:05",
        "rating": "★★★★"
    },
    "_action": "SKIP or MANUAL_RESOLVE"
}
```

### 3.3 연동 파이프라인

```
┌─────────────────────────────────────────────────────────────────┐
│                     INTEGRATION PIPELINE                         │
│                                                                 │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐     │
│  │  SCAN   │───▶│  MATCH  │───▶│  MERGE  │───▶│ VALIDATE│     │
│  │   NAS   │    │  FILES  │    │   DATA  │    │   UDM   │     │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘     │
│       │              │              │              │           │
│       ▼              ▼              ▼              ▼           │
│   File List     Matched Set    UDM Records    Valid JSON      │
│   (1,400+)      (NAS↔Sheet)   (Asset+Seg)    (Export)        │
│                                                                │
└─────────────────────────────────────────────────────────────────┘

Step 1: SCAN NAS
  - 전체 폴더 스캔
  - 파일 목록 추출
  - file_name을 키로 인덱싱

Step 2: MATCH FILES
  - Sheet 데이터 로드
  - file_name 기준 매칭
  - 3가지 그룹 분류:
    a) 완전 매칭 (NAS + Sheet)
    b) NAS Only
    c) Orphan (Sheet Only)

Step 3: MERGE DATA
  - Asset 생성 (NAS 정보)
  - Segment 생성 (Sheet 정보)
  - 관계 연결 (parent_asset_uuid)

Step 4: VALIDATE UDM
  - 스키마 검증
  - 비즈니스 규칙 검증
  - 경고/에러 리포트
```

---

## 4. 소스별 매핑 상세

### 4.1 Archive Metadata Sheet → UDM 매핑

```python
def transform_archive_metadata_row(row: dict, nas_file_info: dict) -> tuple[Asset, Segment]:
    """Archive Metadata Sheet 행을 Asset + Segment로 변환"""

    # Asset (NAS + Sheet 병합)
    asset = Asset(
        asset_uuid=generate_uuid_from_path(nas_file_info["path"]),
        file_name=row["File Name"],
        file_path_nas=nas_file_info["path"],
        file_number=int(row["File No."]),
        nas_folder_link=row["Nas Folder Link"],
        asset_type=infer_asset_type_from_path(nas_file_info["path"]),
        event_context=EventContext(
            year=2024,
            brand=Brand.WSOPC,
            event_type=EventType.CIRCUIT,
            location=Location.LOS_ANGELES
        ),
        source_origin="ARCHIVE_METADATA_SHEET"
    )

    # Segment (Sheet 데이터)
    segment = Segment(
        segment_uuid=uuid4(),
        parent_asset_uuid=asset.asset_uuid,
        time_in_sec=parse_time_hms(row["In"]),
        time_out_sec=parse_time_hms(row["Out"]),
        rating=parse_star_rating(row["Hand Grade"]),
        winner=row["Winner"],
        hand_tag=row["Hands"],
        players=parse_hand_matchup(row["Hands"]),
        tags_player=merge_tag_columns(
            row["Tag (Player)_1"],
            row["Tag (Player)_2"],
            row["Tag (Player)_3"]
        ),
        tags_action=merge_tag_columns(
            row["Tag (Poker Play)_1"],
            row["Tag (Poker Play)_2"],
            # ... 7개 컬럼
        ),
        tags_emotion=merge_tag_columns(
            row["Tag (Emotion)_1"],
            row["Tag (Emotion)_2"]
        )
    )

    return asset, segment
```

### 4.2 Iconik Metadata Sheet → UDM 매핑

```python
def transform_iconik_metadata_row(row: dict, nas_file_info: Optional[dict]) -> tuple[Asset, Segment]:
    """Iconik Metadata Sheet 행을 Asset + Segment로 변환

    Note: Iconik Metadata Sheet는 Asset 정보가 불완전할 수 있음
          - NAS 매칭 시: nas_file_info 사용
          - NAS 미매칭 시: Sheet 정보만으로 Asset 생성
    """

    # Asset
    asset = Asset(
        asset_uuid=generate_uuid_from_content(row["id"]),
        file_name=extract_filename_from_context(row),  # 추론 필요
        file_path_nas=nas_file_info["path"] if nas_file_info else None,
        tournament_name=row.get("Tournament"),
        project_name_tag=row.get("ProjectNameTag"),
        event_context=EventContext(
            year=int(row["Year_"]),
            brand=map_project_to_brand(row["ProjectName"]),
            location=row.get("Location"),
            venue=row.get("Venue"),
            episode=row.get("EpisodeEvent")
        ),
        source_origin="ICONIK_METADATA_SHEET"
    )

    # Segment (풍부한 메타데이터)
    segment = Segment(
        segment_uuid=UUID(row["id"]),  # 시트에서 제공
        parent_asset_uuid=asset.asset_uuid,
        title=row.get("title"),
        time_in_sec=float(row["time_start_S"]),
        time_out_sec=float(row["time_end_S"]),
        time_in_ms=int(row["time_start_ms"]) if row.get("time_start_ms") else None,
        time_out_ms=int(row["time_end_ms"]) if row.get("time_end_ms") else None,
        rating=parse_star_rating(row.get("HandGrade")),
        game_type=map_game_type(row.get("GameType")),
        hand_tag=row.get("HANDTag"),
        players=parse_hand_matchup(row.get("HANDTag")),
        tags_search=parse_comma_separated(row.get("SearchTag")),
        tags_action=parse_comma_separated(row.get("PokerPlayTags")),
        tags_emotion=parse_comma_separated(row.get("Emotion")),
        scene=row.get("Scene"),
        source_type=row.get("Source"),
        is_epic_hand=parse_boolean(row.get("EPICHAND")),
        appearance_outfit=row.get("AppearanceOutfit"),
        scenery_object=row.get("SceneryObject"),
        postflop_action=row.get("PostFlop"),
        adjective=row.get("Adjective"),
        all_in_stage=parse_all_in_tags(row.get("All-in")),
        runout_type=row.get("RUNOUTTag"),
        situation_flags=parse_situation_flags_from_columns(row),
        description=row.get("Description")
    )

    return asset, segment
```

---

## 5. 연동 매트릭스

### 5.1 NAS 폴더 ↔ Sheet 매핑

| NAS 경로 | 대상 Sheet | 매칭 키 | 예상 레코드 |
|----------|-----------|---------|-------------|
| `/WSOP/WSOP Circuit Event/WSOP-Circuit/2024 WSOP Circuit LA/2024 WSOP-C LA SUBCLIP/` | Archive Metadata | `File Name` | 38 |
| `/WSOP/WSOP Bracelet Event/WSOP-LAS VEGAS/` | Iconik Metadata | `ProjectName` + `Year_` | 100+ |
| `/WSOP/WSOP Bracelet Event/WSOP-PARADISE/` | Iconik Metadata | `ProjectName` + `Year_` | 50+ |
| `/HCL/HCL Poker Clip/` | Iconik Metadata | `ProjectName` = "HCL" | 50+ |
| `/PAD/` | Iconik Metadata | `ProjectName` = "PAD" | 30+ |

### 5.2 데이터 커버리지 분석 (2025-12-12 업데이트)

```
┌──────────────────────────────────────────────────────────────────────┐
│                    NAS FILE INVENTORY                                 │
│                    스캔일: 2025-12-12                                  │
│                                                                       │
│   브랜드          │ 파일 수 │ 하위 분류                                │
│   ───────────────┼─────────┼─────────────────────────────────────────│
│   WSOP           │  1,286  │ Archive(545) + Bracelet(693) + Circuit(48)│
│   HCL            │      0  │ 폴더만 존재 (파일 없음)                    │
│   PAD            │     44  │ S12(21) + S13(23)                        │
│   MPP            │     11  │ 2025 Cyprus (3개 이벤트)                  │
│   GOG            │     27  │ E01~E12 (에피소드별 2~3개 버전)           │
│   GGMillions     │     13  │ Super High Roller FT 시리즈              │
│   ───────────────┼─────────┼─────────────────────────────────────────│
│   TOTAL          │  1,381  │                                          │
│                                                                       │
│   파일 형식: MP4(990) + MOV(269) + MXF(114) + 기타(8)                  │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                    WSOP 상세 분석                                     │
│                                                                       │
│   분류                │ 파일 수 │ 연도 범위      │ 파일명 패턴         │
│   ───────────────────┼─────────┼───────────────┼────────────────────│
│   ARCHIVE (PRE-2016) │   545   │ 1973~2016     │ wsop-YYYY-me*.mp4  │
│   Bracelet Event     │   693   │ 2008~현재     │ WSOPE/WSE/WP*.mp4  │
│   ├─ EUROPE          │         │               │ WSOPE08~현재       │
│   ├─ LAS VEGAS       │         │               │ WSOP ME/Side       │
│   └─ PARADISE        │         │               │ WP24-*.mp4         │
│   Circuit Event      │    48   │ 2023~2025     │ WCLA24-*.mp4 등    │
│   ├─ LA 2024 STREAM  │    10   │               │ 2024 WSOP-C LA*    │
│   ├─ LA 2024 SUBCLIP │    29   │               │ WCLA24-01~29.mp4   │
│   └─ Cyprus/London   │     9   │               │ Super Circuit*     │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                 METADATA COVERAGE                                     │
│                                                                       │
│   Source          │ Files │ Has Metadata │ Coverage     │ 시트       │
│   ────────────────┼───────┼──────────────┼─────────────┼────────────│
│   Circuit 2024    │  29   │     29       │   100%      │ Archive MD │
│   WSOP Bracelet   │ 693   │    200+      │   ~29%      │ Iconik MD  │
│   WSOP Archive    │ 545   │      0       │    0%       │ 없음       │
│   PAD             │  44   │     30+      │   ~70%      │ Iconik MD  │
│   GOG             │  27   │      0       │    0%       │ 없음       │
│   GGMillions      │  13   │      0       │    0%       │ 없음       │
│   MPP             │  11   │      0       │    0%       │ 없음       │
│   HCL             │   0   │      -       │    -        │ Iconik MD  │
│   ────────────────┼───────┼──────────────┼─────────────┼────────────│
│   TOTAL           │1,381  │    259+      │   ~19%      │            │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 6. 구현 우선순위

### Phase 1: Archive Metadata Sheet 완전 연동 (MVP)

```
목표: Archive Metadata Sheet 38개 레코드 100% UDM 변환

작업:
1. NAS 스캔 → WCLA24-*.mp4 파일 목록
2. Archive Metadata Sheet 로드 → 38 rows
3. File Name 매칭
4. Asset + Segment 생성
5. JSON 출력

검증:
- 38개 Asset 생성
- 38개 Segment 생성
- 누락 없음 확인
```

### Phase 2: Iconik Metadata Sheet 연동

```
목표: Iconik Metadata Sheet 200+ 레코드 UDM 변환

작업:
1. Iconik Metadata Sheet 로드
2. ProjectName별 그룹화
3. NAS 경로 추론 및 매칭
4. Asset 생성 (그룹 단위)
5. Segment 생성 (행 단위)

챌린지:
- File Name 없음 → 경로 추론 필요
- 1 Asset : N Segments 관계 처리
```

### Phase 3: NAS 전체 스캔

```
목표: 1,400+ 파일 전체 Asset 카탈로그

작업:
1. NAS 전체 폴더 재귀 스캔
2. 파일별 Asset 생성
3. 기존 Sheet 데이터 매칭
4. Orphan 리포트

결과:
- 전체 Asset 카탈로그
- 메타데이터 있는 Asset (Segments 포함)
- 메타데이터 없는 Asset (향후 입력 대기)
```

---

## 7. 연동 검증 체크리스트

### 7.1 데이터 무결성

- [ ] 모든 Sheet 레코드가 UDM으로 변환됨
- [ ] 데이터 손실 없음 (원본 컬럼 전체 매핑)
- [ ] 시간 변환 정확도 (HH:MM:SS ↔ seconds)
- [ ] 별점 변환 정확도 (★ ↔ integer)
- [ ] Boolean 변환 정확도 (TRUE/FALSE ↔ bool)

### 7.2 관계 무결성

- [ ] 모든 Segment가 유효한 Asset을 참조
- [ ] parent_asset_uuid 일치
- [ ] Orphan 레코드 리포트 생성

### 7.3 NAS 일관성

- [ ] file_path_nas가 실제 존재하는 경로
- [ ] file_name이 실제 파일명과 일치
- [ ] asset_type이 폴더 구조와 일치

---

## 8. 관련 문서

| 문서 | 설명 |
|------|------|
| `PRD-0008-UDM-FINAL-SCHEMA.md` | UDM 스키마 정의 (v3.1.0) |
| `PRD-0009-SOURCE-DATA-SPEC.md` | 소스 데이터 명세 |
| `PROJECT_STATUS.md` | 프로젝트 현황 |
| `profiles/*.yaml` | 소스별 변환 프로파일 |

---

## Appendix: 헬퍼 함수 참조

```python
# 시간 변환
parse_time_hms("01:23:45") → 5025.0

# 별점 변환
parse_star_rating("★★★") → 3

# 핸드 파싱
parse_hand_matchup("AA vs KK") → [PlayerInHand(hand="AA"), PlayerInHand(hand="KK")]

# 플레이어 파싱
parse_players_tags("Phil Ivey, Doyle Brunson") → ["Phil Ivey", "Doyle Brunson"]

# 태그 병합
merge_tag_columns("bluff", "hero-call", "") → ["bluff", "hero-call"]

# 올인 파싱
parse_all_in_tags("Preflop") → AllInStage.PREFLOP

# Boolean 플래그
parse_situation_flags_from_columns({"Cooler": "TRUE"}) → SituationFlags(is_cooler=True)
```
