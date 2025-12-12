"""
UDM (Unified Data Model) Schema - Pydantic V2 Implementation

PRD-0008-UDM-FINAL-SCHEMA.md v3.0.0 기반
비디오 아카이빙 시스템을 위한 2-Level 스키마 구조

Level 1: Asset (물리적 파일)
Level 2: Segment (논리적 구간 - 포커 핸드)

Author: Archive Converter Team
Version: 3.0.0
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Optional
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
    model_validator,
)


# =============================================================================
# Enumerations (NAS 기반 확장)
# =============================================================================


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
    BRACELET = "BRACELET"           # 브레이슬릿 이벤트 (메인)
    CIRCUIT = "CIRCUIT"             # 서킷 이벤트
    CASH_GAME_SHOW = "CASH_GAME_SHOW"  # 캐시게임 쇼
    SUPER_MAIN = "SUPER_MAIN"       # 슈퍼 메인 이벤트
    ARCHIVE = "ARCHIVE"             # 아카이브 (역사적 자료)
    SIDE_EVENT = "SIDE_EVENT"       # 사이드 이벤트


class AssetType(str, Enum):
    """Asset 유형 (폴더 구조 기반)"""
    STREAM = "STREAM"               # 풀 스트림 영상
    SUBCLIP = "SUBCLIP"             # 편집된 서브클립
    HAND_CLIP = "HAND_CLIP"         # 핸드별 클립 (WSOP Paradise)
    MASTER = "MASTER"               # 마스터링 완료 (Mastered/)
    CLEAN = "CLEAN"                 # 클린 버전 (자막/그래픽 없음)
    NO_COMMENTARY = "NO_COMMENTARY" # 해설 없는 버전
    RAW = "RAW"                     # 원본 영상
    GENERIC = "GENERIC"             # 레거시 Generic 폴더
    MOV = "MOV"                     # 레거시 MOV 포맷
    MXF = "MXF"                     # 레거시 MXF 포맷


class Location(str, Enum):
    """개최 장소"""
    LAS_VEGAS = "Las Vegas"
    PARADISE = "Paradise"           # Bahamas
    EUROPE = "Europe"
    LOS_ANGELES = "Los Angeles"
    CYPRUS = "Cyprus"
    ROZVADOV = "Rozvadov"           # King's Casino
    OTHER = "Other"


class GameVariant(str, Enum):
    """게임 종류"""
    NLH = "NLH"                     # No Limit Hold'em
    PLO = "PLO"                     # Pot Limit Omaha
    STUD = "STUD"                   # Seven Card Stud
    RAZZ = "RAZZ"
    HORSE = "HORSE"
    MIXED = "MIXED"
    OMAHA_HI_LO = "OMAHA_HI_LO"
    TD_27 = "2-7_TD"                # 2-7 Triple Draw
    OTHER = "OTHER"


class GameType(str, Enum):
    """게임 타입"""
    TOURNAMENT = "TOURNAMENT"
    CASH_GAME = "CASH_GAME"


class AllInStage(str, Enum):
    """올인 스테이지"""
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    NONE = "none"


class SegmentType(str, Enum):
    """Segment 유형"""
    HAND = "HAND"                   # 포커 핸드
    HIGHLIGHT = "HIGHLIGHT"         # 하이라이트
    PLAYER_EMOTION = "PE"           # 플레이어 감정
    INTRO_OUTRO = "INTRO"           # 인트로/아웃트로
    COMMENTARY = "COMMENTARY"       # 해설 구간


# =============================================================================
# Supporting Models
# =============================================================================


class EventContext(BaseModel):
    """
    이벤트 컨텍스트 (NAS 계층 구조 반영)

    필수: year, brand
    권장: event_type, location, venue
    선택: event_number, buyin_usd, game_variant, season, episode
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True,
    )

    # === 필수 ===
    year: Annotated[int, Field(ge=1970, le=2100, description="개최 연도")]
    brand: Brand = Field(..., description="브랜드 (WSOP, HCL, PAD 등)")

    # === 권장 ===
    event_type: Optional[EventType] = Field(
        default=None,
        description="이벤트 유형 (BRACELET, CIRCUIT 등)"
    )
    location: Optional[Location] = Field(
        default=None,
        description="개최 장소"
    )
    venue: Optional[str] = Field(
        default=None,
        description="구체적인 장소 (Horseshoe Casino, Hustler Casino)"
    )

    # === 상세 (선택) ===
    event_number: Optional[int] = Field(
        default=None,
        ge=1,
        description="이벤트 번호 (예: Event #21)"
    )
    buyin_usd: Optional[int] = Field(
        default=None,
        ge=0,
        description="바이인 금액 (USD)"
    )
    game_variant: Optional[GameVariant] = Field(
        default=None,
        description="게임 종류 (NLH, PLO 등)"
    )
    is_high_roller: bool = Field(
        default=False,
        description="하이롤러 여부"
    )
    is_super_high_roller: bool = Field(
        default=False,
        description="슈퍼 하이롤러 여부"
    )
    is_final_table: bool = Field(
        default=False,
        description="파이널 테이블 여부"
    )

    # === 시즌/에피소드 (PAD, HCL) ===
    season: Optional[int] = Field(
        default=None,
        ge=1,
        description="시즌 번호 (PAD, HCL)"
    )
    episode: Optional[int] = Field(
        default=None,
        ge=1,
        description="에피소드 번호"
    )
    episode_title: Optional[str] = Field(
        default=None,
        description="에피소드 제목"
    )


class TechSpec(BaseModel):
    """기술 사양"""
    model_config = ConfigDict(str_strip_whitespace=True)

    fps: float = Field(
        default=29.97,
        gt=0,
        description="프레임 레이트"
    )
    resolution: Optional[str] = Field(
        default=None,
        pattern=r"^(480p|720p|1080p|1440p|4K|8K|\d+x\d+)$",
        description="해상도 (1080p, 4K 등)"
    )
    duration_sec: Optional[float] = Field(
        default=None,
        ge=0,
        description="영상 길이 (초)"
    )
    file_size_mb: Optional[float] = Field(
        default=None,
        ge=0,
        description="파일 크기 (MB)"
    )
    codec: Optional[str] = Field(
        default=None,
        description="코덱 (H.264, ProRes 등)"
    )


class FileNameMeta(BaseModel):
    """파일명에서 추출된 메타데이터"""
    model_config = ConfigDict(str_strip_whitespace=True)

    code_prefix: Optional[str] = Field(
        default=None,
        description="코드 접두사 (WCLA, WP, PAD 등)"
    )
    year_code: Optional[str] = Field(
        default=None,
        description="연도 코드 (24, 23, 2024 등)"
    )
    sequence_num: Optional[int] = Field(
        default=None,
        ge=0,
        description="클립 시퀀스 번호"
    )
    clip_type: Optional[str] = Field(
        default=None,
        description="클립 유형 (PE: Player Emotion, HB: Highlight/Best, EP: Episode)"
    )
    raw_description: Optional[str] = Field(
        default=None,
        description="파일명에서 추출된 설명"
    )
    season: Optional[int] = Field(
        default=None,
        ge=1,
        description="시즌 번호 (PAD, HCL)"
    )
    episode: Optional[int] = Field(
        default=None,
        ge=1,
        description="에피소드 번호"
    )
    event_number: Optional[int] = Field(
        default=None,
        ge=1,
        description="이벤트 번호 (WSOP)"
    )
    buyin_code: Optional[str] = Field(
        default=None,
        description="바이인 코드 (25k, 50k 등)"
    )
    game_code: Optional[str] = Field(
        default=None,
        description="게임 코드 (nlh, plo 등)"
    )


class SourceOrigin(BaseModel):
    """데이터 출처 정보"""
    model_config = ConfigDict(str_strip_whitespace=True)

    source_id: str = Field(
        ...,
        min_length=1,
        description="출처 식별자 (NAS_WSOP_2024, Legacy_Excel_v1 등)"
    )
    source_type: Optional[str] = Field(
        default=None,
        description="출처 유형 (NAS, GoogleSheet, Excel 등)"
    )
    import_timestamp: Optional[datetime] = Field(
        default=None,
        description="임포트 시간"
    )
    original_path: Optional[str] = Field(
        default=None,
        description="원본 경로"
    )


class SituationFlags(BaseModel):
    """상황 플래그 (포커 특화)"""
    model_config = ConfigDict(str_strip_whitespace=True)

    is_cooler: bool = Field(
        default=False,
        description="쿨러 상황"
    )
    is_badbeat: bool = Field(
        default=False,
        description="배드비트"
    )
    is_suckout: bool = Field(
        default=False,
        description="석아웃"
    )
    is_bluff: bool = Field(
        default=False,
        description="블러프"
    )
    is_hero_call: bool = Field(
        default=False,
        description="히어로 콜"
    )
    is_hero_fold: bool = Field(
        default=False,
        description="히어로 폴드"
    )
    is_river_killer: bool = Field(
        default=False,
        description="리버 킬러 (NAS 파일명 발견)"
    )

    def to_tags(self) -> list[str]:
        """SituationFlags를 tags_action 형식으로 변환"""
        tags = []
        if self.is_cooler:
            tags.append("cooler")
        if self.is_badbeat:
            tags.append("badbeat")
        if self.is_suckout:
            tags.append("suckout")
        if self.is_bluff:
            tags.append("bluff")
        if self.is_hero_call:
            tags.append("hero-call")
        if self.is_hero_fold:
            tags.append("hero-fold")
        if self.is_river_killer:
            tags.append("river-killer")
        return tags


class PlayerInHand(BaseModel):
    """핸드 참여 플레이어 정보"""
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        ...,
        min_length=1,
        description="플레이어 이름"
    )
    hand: Optional[str] = Field(
        default=None,
        description="홀카드 (AA, KK, AKs 등)"
    )
    position: Optional[str] = Field(
        default=None,
        pattern=r"^(UTG|UTG\+1|UTG\+2|MP|HJ|CO|BTN|SB|BB)$",
        description="포지션 (BTN, BB, UTG 등)"
    )
    is_winner: bool = Field(
        default=False,
        description="승자 여부"
    )
    chips_won: Optional[int] = Field(
        default=None,
        ge=0,
        description="획득 칩 (선택)"
    )

    @field_validator("hand")
    @classmethod
    def validate_hand(cls, v: Optional[str]) -> Optional[str]:
        """홀카드 형식 검증"""
        if v is None:
            return v
        # 포커 핸드 패턴: AA, KK, AKs, AKo, T9s 등
        pattern = r"^([2-9TJQKA]{2}[so]?|[2-9TJQKA][2-9TJQKA])$"
        if not re.match(pattern, v.upper()):
            # 완전한 핸드 표기 허용 (AsAd, KhKs 등)
            full_pattern = r"^[2-9TJQKA][shdc][2-9TJQKA][shdc]$"
            if not re.match(full_pattern, v):
                # 유연한 입력 허용 (검증 실패해도 저장)
                pass
        return v


# =============================================================================
# Level 2: Segment Entity
# =============================================================================


class Segment(BaseModel):
    """
    논리적 구간 엔티티 (포커 핸드)

    Level 2 엔티티: Asset 내 특정 시간 구간
    1 Asset : N Segments 관계
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True,
        validate_assignment=True,
    )

    # === 식별자 ===
    segment_uuid: UUID = Field(
        default_factory=uuid4,
        description="Segment 고유 식별자"
    )
    parent_asset_uuid: UUID = Field(
        ...,
        description="부모 Asset UUID (FK)"
    )

    # === Segment 유형 ===
    segment_type: SegmentType = Field(
        default=SegmentType.HAND,
        description="Segment 유형"
    )

    # === 시간 (필수) ===
    time_in_sec: Annotated[float, Field(ge=0, description="시작 시간 (초)")]
    time_out_sec: Annotated[float, Field(ge=0, description="종료 시간 (초)")]

    # === 기본 정보 ===
    title: Optional[str] = Field(
        default=None,
        description="핸드 제목"
    )
    game_type: GameType = Field(
        default=GameType.TOURNAMENT,
        description="게임 타입"
    )
    rating: Optional[int] = Field(
        default=None,
        ge=0,
        le=5,
        description="별점 (0-5)"
    )

    # === 핸드 결과 ===
    winner: Optional[str] = Field(
        default=None,
        description="승자 이름"
    )
    winning_hand: Optional[str] = Field(
        default=None,
        description="승리 패 (Full House, Flush 등)"
    )
    losing_hand: Optional[str] = Field(
        default=None,
        description="패배 패"
    )

    # === 참여자 (구조화) ===
    players: Optional[list[PlayerInHand]] = Field(
        default=None,
        description="참여 플레이어 리스트"
    )

    # === 태그 시스템 ===
    tags_action: Optional[list[str]] = Field(
        default=None,
        description="액션 태그 (preflop-allin, cooler 등)"
    )
    tags_emotion: Optional[list[str]] = Field(
        default=None,
        description="감정 태그 (brutal, suckout 등)"
    )
    tags_content: Optional[list[str]] = Field(
        default=None,
        description="콘텐츠 태그 (dirty, outro, hs 등)"
    )
    tags_player: Optional[list[str]] = Field(
        default=None,
        description="플레이어 태그 (Circuit Sheet의 Tag Player 컬럼)"
    )
    tags_search: Optional[list[str]] = Field(
        default=None,
        description="검색 태그 (Database Sheet의 SearchTag)"
    )

    # === 포커 도메인 확장 ===
    situation_flags: Optional[SituationFlags] = Field(
        default=None,
        description="상황 플래그"
    )
    all_in_stage: Optional[AllInStage] = Field(
        default=None,
        description="올인 시점"
    )
    runout_type: Optional[str] = Field(
        default=None,
        description="런아웃 타입 (runner-runner, one-outer)"
    )
    adjective: Optional[str] = Field(
        default=None,
        description="형용사 (brutal, insane, incredible)"
    )
    board: Optional[str] = Field(
        default=None,
        description="보드 카드 (Ah Kd 7c 2s 9h)"
    )

    # === Google Sheets 추가 필드 (Issue #7) ===
    hand_tag: Optional[str] = Field(
        default=None,
        description="핸드 태그 원본 ('QQ vs KK' 등, HANDTag 컬럼)"
    )
    scene: Optional[str] = Field(
        default=None,
        description="장면 설명 (Database Sheet Scene 컬럼)"
    )
    source_type: Optional[str] = Field(
        default=None,
        description="소스 유형 (PGM, RAW 등, Source 컬럼)"
    )
    is_epic_hand: bool = Field(
        default=False,
        description="에픽 핸드 여부 (EPICHAND 컬럼)"
    )
    appearance_outfit: Optional[str] = Field(
        default=None,
        description="외모/복장 설명 (AppearanceOutfit 컬럼)"
    )
    scenery_object: Optional[str] = Field(
        default=None,
        description="장면 오브젝트 (SceneryObject 컬럼)"
    )
    postflop_action: Optional[str] = Field(
        default=None,
        description="포스트플롭 액션 (PostFlop 컬럼)"
    )
    time_in_ms: Optional[int] = Field(
        default=None,
        ge=0,
        description="시작 시간 밀리초 (time_start_ms 컬럼)"
    )
    time_out_ms: Optional[int] = Field(
        default=None,
        ge=0,
        description="종료 시간 밀리초 (time_end_ms 컬럼)"
    )

    # === 파일명에서 추출 (NAS 분석 기반) ===
    event_stage: Optional[str] = Field(
        default=None,
        description="이벤트 단계 (ft: Final Table, day2 등)"
    )
    hand_description: Optional[str] = Field(
        default=None,
        description="파일명에서 추출된 핸드 설명"
    )
    is_dirty: bool = Field(
        default=False,
        description="자막 포함 여부"
    )

    # === 메모 ===
    description: Optional[str] = Field(
        default=None,
        description="추가 설명"
    )

    # === Computed Properties ===
    @computed_field
    @property
    def duration_sec(self) -> float:
        """핸드 길이 (초)"""
        return self.time_out_sec - self.time_in_sec

    # === Validators ===
    @model_validator(mode="after")
    def validate_time_range(self) -> "Segment":
        """BR-001: time_out_sec > time_in_sec"""
        if self.time_out_sec < self.time_in_sec:
            raise ValueError(
                f"time_out_sec ({self.time_out_sec}) must be greater than "
                f"time_in_sec ({self.time_in_sec})"
            )
        return self

    @model_validator(mode="after")
    def validate_duration(self) -> "Segment":
        """BR-003: 핸드 길이 10초-3600초 (경고만)"""
        duration = self.time_out_sec - self.time_in_sec
        if duration < 10 or duration > 3600:
            # WARNING 수준 - 검증은 통과하되 기록
            pass
        return self

    @model_validator(mode="after")
    def validate_winner_in_players(self) -> "Segment":
        """BR-002: winner가 players에 포함 (경고만)"""
        if self.winner and self.players:
            player_names = [p.name.lower() for p in self.players]
            if self.winner.lower() not in player_names:
                # WARNING 수준 - 검증은 통과
                pass
        return self

    def get_player_names(self) -> list[str]:
        """플레이어 이름 목록 반환"""
        if not self.players:
            return []
        return [p.name for p in self.players]

    def add_tag(
        self,
        tag: str,
        tag_type: str = "action"
    ) -> None:
        """태그 추가"""
        attr_name = f"tags_{tag_type}"
        tags = getattr(self, attr_name) or []
        if tag not in tags:
            tags.append(tag)
            setattr(self, attr_name, tags)


# =============================================================================
# Level 1: Asset Entity
# =============================================================================


class Asset(BaseModel):
    """
    물리적 파일 엔티티

    Level 1 엔티티: 하나의 영상 파일에 대한 불변 정보
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True,
        validate_assignment=True,
    )

    # === 식별자 ===
    asset_uuid: UUID = Field(
        default_factory=uuid4,
        description="파일 Hash 기반 생성 UUID"
    )

    # === 파일 정보 ===
    file_name: str = Field(
        ...,
        min_length=1,
        description="확장자 포함 파일명"
    )
    file_path_rel: Optional[str] = Field(
        default=None,
        description="NAS 상대 경로"
    )
    file_path_nas: Optional[str] = Field(
        default=None,
        description="전체 NAS 경로"
    )

    # === Asset 유형 ===
    asset_type: AssetType = Field(
        default=AssetType.SUBCLIP,
        description="Asset 유형"
    )

    # === 컨텍스트 (확장) ===
    event_context: EventContext = Field(
        ...,
        description="이벤트 컨텍스트"
    )
    tech_spec: Optional[TechSpec] = Field(
        default=None,
        description="기술 사양"
    )
    file_name_meta: Optional[FileNameMeta] = Field(
        default=None,
        description="파일명 메타데이터"
    )

    # === Google Sheets 추가 필드 (Issue #7) ===
    file_number: Optional[int] = Field(
        default=None,
        ge=1,
        description="파일 순번 (Circuit Sheet의 File No. 컬럼)"
    )
    tournament_name: Optional[str] = Field(
        default=None,
        description="토너먼트명 (Database Sheet의 Tournament 컬럼)"
    )
    project_name_tag: Optional[str] = Field(
        default=None,
        description="프로젝트 태그 (Database Sheet의 ProjectNameTag 컬럼)"
    )
    nas_folder_link: Optional[str] = Field(
        default=None,
        description="NAS 폴더 링크 (Circuit Sheet의 Nas Folder Link 컬럼)"
    )

    # === 메타 ===
    source_origin: str = Field(
        ...,
        min_length=1,
        description="데이터 출처 (NAS_WSOP_2024, Legacy_Excel_v1 등)"
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="생성 시간"
    )
    last_modified: Optional[datetime] = Field(
        default=None,
        description="최종 수정 시간"
    )

    # === 관계 ===
    segments: list[Segment] = Field(
        default_factory=list,
        description="포함된 Segment 목록"
    )

    # === Validators ===
    @field_validator("file_name")
    @classmethod
    def validate_file_name(cls, v: str) -> str:
        """파일명 확장자 검증"""
        valid_extensions = {
            ".mp4", ".mov", ".mxf", ".mkv", ".avi", ".wmv",
            ".MP4", ".MOV", ".MXF", ".MKV", ".AVI", ".WMV"
        }
        if not any(v.endswith(ext) for ext in valid_extensions):
            # 확장자 없는 파일명도 허용 (유연성)
            pass
        return v

    @model_validator(mode="after")
    def validate_segment_parent_uuid(self) -> "Asset":
        """모든 Segment의 parent_asset_uuid가 일치하는지 검증"""
        for segment in self.segments:
            if segment.parent_asset_uuid != self.asset_uuid:
                raise ValueError(
                    f"Segment {segment.segment_uuid} has mismatched "
                    f"parent_asset_uuid: expected {self.asset_uuid}, "
                    f"got {segment.parent_asset_uuid}"
                )
        return self

    def add_segment(self, segment: Segment) -> None:
        """Segment 추가 (parent_uuid 자동 설정)"""
        segment.parent_asset_uuid = self.asset_uuid
        self.segments.append(segment)

    def get_segments_by_type(
        self,
        segment_type: SegmentType
    ) -> list[Segment]:
        """특정 유형의 Segment 목록 반환"""
        return [
            s for s in self.segments
            if s.segment_type == segment_type
        ]

    def get_total_duration(self) -> float:
        """전체 Segment 길이 합계"""
        return sum(s.duration_sec for s in self.segments)


# =============================================================================
# Root Document Model
# =============================================================================


class UDMMetadata(BaseModel):
    """UDM 문서 메타데이터"""
    model_config = ConfigDict(str_strip_whitespace=True)

    schema_version: str = Field(
        default="3.0.0",
        description="스키마 버전"
    )
    exported_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="내보내기 시간"
    )
    source: str = Field(
        default="Archive_Converter",
        description="데이터 소스"
    )
    exporter_version: Optional[str] = Field(
        default=None,
        description="내보내기 도구 버전"
    )


class UDMDocument(BaseModel):
    """
    UDM 문서 루트 모델

    JSON 내보내기/가져오기를 위한 최상위 컨테이너
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True,
        populate_by_name=True,
    )

    metadata: UDMMetadata = Field(
        default_factory=UDMMetadata,
        serialization_alias="_metadata",
        description="문서 메타데이터"
    )
    asset: Asset = Field(
        ...,
        description="Asset 데이터"
    )

    @classmethod
    def from_asset(
        cls,
        asset: Asset,
        source: Optional[str] = None
    ) -> "UDMDocument":
        """Asset에서 UDMDocument 생성"""
        metadata = UDMMetadata(
            source=source or asset.source_origin
        )
        return cls(metadata=metadata, asset=asset)

    def to_json_dict(self) -> dict[str, Any]:
        """JSON 직렬화용 딕셔너리 변환"""
        return self.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True
        )

    @classmethod
    def model_json_schema_static(cls) -> dict[str, Any]:
        """JSON Schema 생성"""
        return cls.model_json_schema()


# =============================================================================
# Utility Functions
# =============================================================================


# =============================================================================
# 파일명 패턴 정의 (v3.2.0 - 24개 패턴, 98.4% 매칭률)
# =============================================================================
FILENAME_PATTERNS: dict[str, str] = {
    # =================================================================
    # 기존 패턴 (6개)
    # =================================================================

    # WCLA24-15.mp4 -> WSOP Circuit LA 2024, #15
    "circuit_subclip": r"^(?P<code>WCLA)(?P<year>\d{2})-(?P<num>\d+)\.(?P<ext>\w+)$",

    # WP23-PE-01.mp4 -> WSOP Paradise 2023, Player Emotion #01
    "paradise_pe": r"^(?P<code>WP)(?P<year>\d{2})-(?P<type>PE|ET|HB)-(?P<num>\d+)\.(?P<ext>\w+)$",

    # WP23-03.mp4 -> WSOP Paradise 2023, #03
    "paradise_subclip": r"^(?P<code>WP)(?P<year>\d{2})-(?P<num>\d+)\.(?P<ext>\w+)$",

    # PAD_S13_EP01_GGPoker-001.mp4 -> PAD Season 13 Episode 01
    "pad_episode": r"^PAD_S(?P<season>\d+)_EP(?P<episode>\d+)_(?P<desc>.+)\.(?P<ext>\w+)$",

    # 10-wsop-2024-be-ev-21-25k-nlh-hr-ft-description.mp4
    "wsop_mastered": (
        r"^(?P<num>\d+)-wsop-(?P<year>\d{4})-be-ev-(?P<event>\d+)-"
        r"(?P<buyin>\d+k?)-(?P<game>nlh|plo|stud)-(?P<tags>.+)\.(?P<ext>\w+)$"
    ),

    # 250507_Super High Roller Poker FINAL TABLE with {player}.mp4
    "ggmillions": (
        r"^(?P<date>\d{6})_Super High Roller Poker FINAL TABLE "
        r"with (?P<player>.+)\.(?P<ext>\w+)$"
    ),

    # =================================================================
    # 1차 신규 패턴 (6개) - WSOP Archive/Modern
    # =================================================================

    # wsop-1973-me-nobug.mp4 -> WSOP Archive 대시 형식
    "wsop_archive_dash": r"^(?P<code>wsope?)-(?P<year>\d{4})-(?P<desc>.+)\.(?P<ext>\w+)$",

    # WSOP_2003-04.mxf -> WSOP Archive 언더스코어 형식
    "wsop_archive_underscore": r"^(?P<code>WSOP)_(?P<year>\d{4})[-_]?(?P<desc>.*)\.(?P<ext>\w+)$",

    # 2009 WSOP ME19.mov -> 연도 선행 형식
    "year_world_series": r"^(?P<year>\d{4})\s+(World Series of Poker|WSOP)(?P<desc>.*)\.(?P<ext>\w+)$",

    # WSOP 2005 Lake Tahoe CC_*.mov -> 공백 구분 형식
    "wsop_year_space": r"^(?P<code>WSOP)\s+(?P<year>\d{4})\s+(?P<desc>.+)\.(?P<ext>\w+)$",

    # 1-wsop-2024-be-ev-01-*.mp4 -> Mastered 유연 형식
    "wsop_mastered_flex": r"^(?P<num>\d+)-wsop-(?P<year>\d{4})-be-ev-(?P<event>\d+)-(?P<desc>.+)\.(?P<ext>\w+)$",

    # WS11_ME02_NB.mp4 -> 짧은 코드 형식
    "ws_short_code": r"^(?P<code>WS)(?P<year>\d{2})_(?P<desc>.+)\.(?P<ext>\w+)$",

    # =================================================================
    # 2차 신규 패턴 (5개) - Hand Clip/WSOP Modern
    # =================================================================

    # 1213_Hand_09_Player1 vs Player2_Clean.mp4 -> Paradise Hand Clip
    "hand_clip": r"^(?P<date>\d{4})_Hand_(?P<hand_num>\d+)_(?P<desc>.+)\.(?P<ext>\w+)$",

    # WSOP13_ME01_NB.mp4 -> WSOP 2자리 연도 코드
    "wsop_yy_code": r"^(?P<code>WSOP)(?P<year>\d{2})_(?P<desc>.+)\.(?P<ext>\w+)$",

    # ESPN 2007 WSOP SEASON 5 SHOW 1.mov -> ESPN 방송 형식
    "espn_wsop": r"^ESPN\s+(?P<year>\d{4})\s+WSOP\s+SEASON\s+(?P<season>\d+)\s+SHOW\s+(?P<show>\d+)\.(?P<ext>\w+)$",

    # 1003_WSOPE_2024_50K_*.mp4 -> 번호_WSOPE_연도 형식
    "num_wsope_year": r"^(?P<num>\d+)_(?P<code>WSOPE?)_(?P<year>\d{4})_(?P<desc>.+)\.(?P<ext>\w+)$",

    # WSOPE09_Episode_8_H264.mov -> WSOPE 2자리 연도
    "wsope_yy_episode": r"^(?P<code>WSOPE?)(?P<year>\d{2})_(?P<desc>.+)\.(?P<ext>\w+)$",

    # =================================================================
    # 3차 신규 패턴 (5개) - WSOP Europe/기타
    # =================================================================

    # WSOP - 1973.avi -> 공백+대시 형식
    "wsop_space_dash_year": r"^(?P<code>WSOP)\s+-\s+(?P<year>\d{4})\.(?P<ext>\w+)$",

    # WSE13-ME01_EuroSprt_NB_TEXT.mp4 -> WSE 축약 코드
    "wse_code": r"^(?P<code>WSE)(?P<year>\d{2})-(?P<desc>.+)\.(?P<ext>\w+)$",

    # WE24-ME-01.mp4 -> WE 축약 코드 (WSOP Europe)
    "we_code": r"^(?P<code>WE)(?P<year>\d{2})-(?P<type>\w+)-(?P<num>\d+)\.(?P<ext>\w+)$",

    # #WSOPE 2024 NLH MAIN EVENT... -> 해시태그 접두사
    "hashtag_wsope": r"^#(?P<code>WSOPE?)\s+(?P<year>\d{4})\s+(?P<desc>.+)\.(?P<ext>\w+)$",

    # 2003 2003 WSOP Best of... -> 중복 연도
    "year_year_wsop": r"^(?P<year>\d{4})\s+\d{4}\s+WSOP\s+(?P<desc>.+)\.(?P<ext>\w+)$",

    # =================================================================
    # 4차 신규 패턴 (4개) - Main Event/기타 브랜드
    # =================================================================

    # 42-wsop-2024-me-day1a-*.mp4 -> Main Event 형식
    "wsop_main_event": r"^(?P<num>\d+)-wsop-(?P<year>\d{4})-me-(?P<desc>.+)\.(?P<ext>\w+)$",

    # $1M GTD $1K PokerOK... -> MPP 토너먼트
    "mpp_tournament": r"^[\$](?P<prize>[\d.]+[MK]?)\s+GTD.+\.(?P<ext>\w+)$",

    # HyperDeck_0009-002.mp4 -> 장비 녹화 파일
    "hyperdeck": r"^HyperDeck_(?P<num>\d+)-(?P<seq>\d+)\.(?P<ext>\w+)$",

    # WSOPE NLH... -> WSOPE 일반 형식
    "wsope_generic": r"^(?P<code>WSOPE?)\s+(?P<desc>.+)\.(?P<ext>\w+)$",

    # =================================================================
    # 기타 브랜드 패턴 (4개)
    # =================================================================

    # pad-s12-ep01-002.mp4 -> PAD 대시 형식
    "pad_dash": r"^(?P<code>pad)-s(?P<season>\d+)-ep(?P<episode>\d+)-(?P<num>\d+)\.(?P<ext>\w+)$",

    # E09_GOG_final_edit_20231123.mp4 -> GOG 에피소드
    "gog_episode": r"^E(?P<episode>\d+)_(?P<code>GOG)_(?P<desc>.+)\.(?P<ext>\w+)$",

    # Super High Roller Poker FINAL TABLE with... -> GGMillions (날짜 없음)
    "ggmillions_no_date": r"^Super High Roller Poker FINAL TABLE with (?P<player>.+)\.(?P<ext>\w+)$",

    # HCL_2024_EP10.mp4 -> Hustler Casino Live 2024 Episode 10
    "hcl_episode": r"^(?P<code>HCL)_(?P<year>\d{4})_EP(?P<episode>\d+)\.(?P<ext>\w+)$",
}


def parse_filename(filename: str) -> FileNameMeta:
    """
    파일명 파싱 (v3.2.0 - 유니코드 정규화 포함)

    NAS 파일명 패턴을 분석하여 FileNameMeta 반환
    24개 패턴으로 98.4% 매칭률 달성

    Args:
        filename: 파일명 (확장자 포함)

    Returns:
        FileNameMeta: 파싱된 메타데이터
    """
    # 유니코드 정규화 (v3.2.0)
    normalized = filename
    normalized = normalized.replace('\u2013', '-')  # en-dash → hyphen
    normalized = normalized.replace('\u2014', '-')  # em-dash → hyphen
    normalized = normalized.replace('\u20ac', 'E')  # Euro sign € → E

    for pattern_name, pattern in FILENAME_PATTERNS.items():
        match = re.match(pattern, normalized, re.IGNORECASE)
        if match:
            groups = match.groupdict()

            # 기본 필드 추출
            meta = FileNameMeta(
                code_prefix=groups.get("code"),
                year_code=groups.get("year") or (
                    groups.get("date", "")[:2] if groups.get("date") else None
                ),
                sequence_num=(
                    int(groups["num"])
                    if groups.get("num")
                    else None
                ),
                clip_type=groups.get("type"),
                raw_description=(
                    groups.get("desc") or
                    groups.get("player") or
                    groups.get("tags")
                ),
                # PAD 전용 필드
                season=(
                    int(groups["season"])
                    if groups.get("season")
                    else None
                ),
                episode=(
                    int(groups["episode"])
                    if groups.get("episode")
                    else None
                ),
                # WSOP mastered 전용 필드
                event_number=(
                    int(groups["event"])
                    if groups.get("event")
                    else None
                ),
                buyin_code=groups.get("buyin"),
                game_code=groups.get("game"),
            )

            # PAD 패턴인 경우 code_prefix와 clip_type 설정
            if pattern_name == "pad_episode":
                meta.code_prefix = "PAD"
                meta.clip_type = "EP"

            # GOG 에피소드 패턴인 경우 code_prefix 설정
            if pattern_name == "gog_episode":
                meta.code_prefix = "GOG"

            # GGMillions 패턴인 경우 code_prefix 설정
            if pattern_name in ("ggmillions", "ggmillions_no_date"):
                meta.code_prefix = "GGMillions"

            # Hand Clip 패턴인 경우 code_prefix 설정
            if pattern_name == "hand_clip":
                meta.code_prefix = "WSOP"

            return meta
    return FileNameMeta()


# NAS 경로 기반 브랜드 매핑
NAS_PATH_MAPPING: dict[str, dict[str, Any]] = {
    "/ARCHIVE/WSOP/WSOP Bracelet Event/": {
        "brand": Brand.WSOP,
        "event_type": EventType.BRACELET
    },
    "/ARCHIVE/WSOP/WSOP Circuit Event/": {
        "brand": Brand.WSOPC,
        "event_type": EventType.CIRCUIT
    },
    "/ARCHIVE/WSOP/WSOP ARCHIVE": {
        "brand": Brand.WSOP,
        "event_type": EventType.ARCHIVE
    },
    "/ARCHIVE/HCL/": {
        "brand": Brand.HCL,
        "event_type": EventType.CASH_GAME_SHOW
    },
    "/ARCHIVE/PAD/": {
        "brand": Brand.PAD,
        "event_type": EventType.CASH_GAME_SHOW
    },
    "/ARCHIVE/GGMillions/": {
        "brand": Brand.GG_MILLIONS,
        "event_type": EventType.CASH_GAME_SHOW
    },
    "/ARCHIVE/MPP/": {
        "brand": Brand.MPP,
        "event_type": EventType.BRACELET
    },
    "/ARCHIVE/GOG": {
        "brand": Brand.GOG,
        "event_type": EventType.CASH_GAME_SHOW
    },
}


# 폴더명 기반 AssetType 매핑
FOLDER_ASSET_TYPE_MAPPING: dict[str, AssetType] = {
    "STREAM": AssetType.STREAM,
    "SUBCLIP": AssetType.SUBCLIP,
    "Hand Clip": AssetType.HAND_CLIP,
    "Mastered": AssetType.MASTER,
    "Clean": AssetType.CLEAN,
    "NO COMMENTARY": AssetType.NO_COMMENTARY,
    "Generic": AssetType.GENERIC,
    "Generics": AssetType.GENERIC,
    "MOVs": AssetType.MOV,
    "MXFs": AssetType.MXF,
    "Masters": AssetType.MASTER,
}


def infer_brand_from_path(path: str) -> dict[str, Any]:
    """
    NAS 경로에서 브랜드 및 이벤트 유형 추론

    Args:
        path: NAS 파일 경로

    Returns:
        dict: brand, event_type 정보
    """
    path_normalized = path.replace("\\", "/")

    for pattern, info in NAS_PATH_MAPPING.items():
        if pattern in path_normalized:
            return info

    return {"brand": Brand.OTHER, "event_type": None}


def infer_asset_type_from_path(path: str) -> AssetType:
    """
    폴더 경로에서 AssetType 추론

    Args:
        path: NAS 파일 경로

    Returns:
        AssetType: 추론된 Asset 유형
    """
    path_normalized = path.replace("\\", "/")

    for folder_name, asset_type in FOLDER_ASSET_TYPE_MAPPING.items():
        if folder_name in path_normalized:
            return asset_type

    return AssetType.SUBCLIP  # 기본값


# JSON Schema 생성 헬퍼
def generate_json_schema() -> dict[str, Any]:
    """
    전체 UDM JSON Schema 생성

    Returns:
        dict: JSON Schema
    """
    return UDMDocument.model_json_schema()


def generate_minimal_asset(
    file_name: str,
    year: int,
    brand: Brand,
    source_origin: str,
) -> Asset:
    """
    최소 필수 필드로 Asset 생성

    Args:
        file_name: 파일명
        year: 연도
        brand: 브랜드
        source_origin: 데이터 출처

    Returns:
        Asset: 생성된 Asset
    """
    return Asset(
        file_name=file_name,
        event_context=EventContext(
            year=year,
            brand=brand
        ),
        source_origin=source_origin
    )


# =============================================================================
# Google Sheets 파싱 헬퍼 (Issue #7)
# =============================================================================


def parse_time_hms(time_str: str) -> float:
    """
    HH:MM:SS 또는 H:MM:SS 형식을 초(seconds)로 변환

    Args:
        time_str: "6:58:55" 또는 "01:23:45"

    Returns:
        float: 초 단위 시간

    Examples:
        >>> parse_time_hms("6:58:55")
        25135.0
        >>> parse_time_hms("0:12:47")
        767.0
    """
    if not time_str or not isinstance(time_str, str):
        return 0.0

    time_str = time_str.strip()
    parts = time_str.split(":")

    try:
        if len(parts) == 3:
            h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
            return h * 3600 + m * 60 + s
        elif len(parts) == 2:
            m, s = int(parts[0]), float(parts[1])
            return m * 60 + s
        else:
            return float(time_str)
    except (ValueError, TypeError):
        return 0.0


def parse_star_rating(rating_str: str) -> int:
    """
    별점 문자열을 숫자로 변환

    Args:
        rating_str: "★★★" 또는 "★★" 또는 "3"

    Returns:
        int: 0-5 사이의 별점

    Examples:
        >>> parse_star_rating("★★★")
        3
        >>> parse_star_rating("★")
        1
    """
    if not rating_str:
        return 0

    rating_str = str(rating_str).strip()

    # 별 개수 세기
    star_count = rating_str.count("★")
    if star_count > 0:
        return min(star_count, 5)

    # 숫자인 경우
    try:
        return min(int(float(rating_str)), 5)
    except (ValueError, TypeError):
        return 0


def parse_hand_matchup(hand_str: str) -> list[PlayerInHand]:
    """
    핸드 매치업 문자열을 PlayerInHand 리스트로 변환

    Args:
        hand_str: "88 vs JJ" 또는 "AKo vs KK vs QQ"

    Returns:
        list[PlayerInHand]: 파싱된 플레이어 리스트

    Examples:
        >>> result = parse_hand_matchup("88 vs JJ")
        >>> len(result)
        2
        >>> result[0].hand
        '88'
    """
    if not hand_str:
        return []

    hand_str = str(hand_str).strip()

    # "vs" 또는 "VS" 또는 " v " 로 분리
    hands = re.split(r"\s+vs\.?\s+|\s+v\s+", hand_str, flags=re.IGNORECASE)

    players = []
    for i, hand in enumerate(hands):
        hand = hand.strip()
        if hand:
            players.append(PlayerInHand(
                name=f"Player {i + 1}",  # 기본 이름 (나중에 업데이트)
                hand=hand
            ))

    return players


def parse_players_tags(
    players_str: str,
    delimiter: str = ","
) -> list[PlayerInHand]:
    """
    쉼표로 구분된 플레이어 문자열을 PlayerInHand 리스트로 변환

    Args:
        players_str: "Steve YEA,YEA,FAN,chih fan"
        delimiter: 구분자 (기본 쉼표)

    Returns:
        list[PlayerInHand]: 파싱된 플레이어 리스트

    Examples:
        >>> result = parse_players_tags("Phil Ivey, Daniel Negreanu")
        >>> len(result)
        2
    """
    if not players_str:
        return []

    players_str = str(players_str).strip()
    names = [n.strip() for n in players_str.split(delimiter) if n.strip()]

    # 중복 제거하면서 순서 유지
    seen = set()
    unique_names = []
    for name in names:
        name_lower = name.lower()
        if name_lower not in seen:
            seen.add(name_lower)
            unique_names.append(name)

    return [PlayerInHand(name=name) for name in unique_names]


def merge_tag_columns(*columns: Optional[str]) -> list[str]:
    """
    여러 태그 컬럼을 하나의 리스트로 병합

    Args:
        columns: 태그 컬럼 값들 (빈 문자열/None 포함 가능)

    Returns:
        list[str]: 병합된 태그 리스트 (빈 값 제외, 중복 제거)

    Examples:
        >>> merge_tag_columns("Nice Fold", "Preflop All-in", "", None)
        ['Nice Fold', 'Preflop All-in']
    """
    tags = []
    seen = set()

    for col in columns:
        if col and isinstance(col, str):
            tag = col.strip()
            if tag and tag.lower() not in seen:
                seen.add(tag.lower())
                tags.append(tag)

    return tags


def parse_all_in_tags(all_in_str: str) -> tuple[Optional[AllInStage], list[str]]:
    """
    올인 태그 문자열 파싱

    Args:
        all_in_str: "4bet,preflop allin" 또는 "preflop"

    Returns:
        tuple: (AllInStage, 추가 태그 리스트)

    Examples:
        >>> stage, tags = parse_all_in_tags("4bet,preflop allin")
        >>> stage
        <AllInStage.PREFLOP: 'preflop'>
        >>> tags
        ['4bet']
    """
    if not all_in_str:
        return None, []

    all_in_str = str(all_in_str).strip().lower()

    # AllInStage 결정
    stage = None
    if "preflop" in all_in_str:
        stage = AllInStage.PREFLOP
    elif "flop" in all_in_str:
        stage = AllInStage.FLOP
    elif "turn" in all_in_str:
        stage = AllInStage.TURN
    elif "river" in all_in_str:
        stage = AllInStage.RIVER

    # 추가 태그 추출
    extra_tags = []
    for tag in all_in_str.split(","):
        tag = tag.strip()
        if tag and tag not in ("preflop", "flop", "turn", "river", "allin", "all-in"):
            extra_tags.append(tag)

    return stage, extra_tags


def parse_situation_flags_from_columns(
    badbeat: Optional[str] = None,
    bluff: Optional[str] = None,
    suckout: Optional[str] = None,
    cooler: Optional[str] = None,
) -> SituationFlags:
    """
    개별 Boolean 컬럼에서 SituationFlags 생성

    Args:
        badbeat: Badbeat 컬럼 값 ("TRUE", "1", "yes" 등)
        bluff: Bluff 컬럼 값
        suckout: Suckout 컬럼 값
        cooler: Cooler 컬럼 값

    Returns:
        SituationFlags: 생성된 플래그 객체
    """
    def is_truthy(val: Optional[str]) -> bool:
        if not val:
            return False
        val = str(val).strip().lower()
        return val in ("true", "1", "yes", "y", "x", "o")

    return SituationFlags(
        is_badbeat=is_truthy(badbeat),
        is_bluff=is_truthy(bluff),
        is_suckout=is_truthy(suckout),
        is_cooler=is_truthy(cooler),
    )
