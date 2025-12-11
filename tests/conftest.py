"""
Pytest Configuration and Shared Fixtures for UDM Tests

공통 테스트 픽스처 및 설정
"""

from datetime import datetime
from uuid import UUID, uuid4

import pytest

from src.models.udm import (
    AllInStage,
    Asset,
    AssetType,
    Brand,
    EventContext,
    EventType,
    FileNameMeta,
    GameType,
    GameVariant,
    Location,
    PlayerInHand,
    Segment,
    SegmentType,
    SituationFlags,
    SourceOrigin,
    TechSpec,
    UDMDocument,
    UDMMetadata,
)


# =============================================================================
# Basic Fixtures
# =============================================================================


@pytest.fixture
def sample_uuid() -> UUID:
    """테스트용 고정 UUID"""
    return UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def sample_year() -> int:
    """테스트용 연도"""
    return 2024


@pytest.fixture
def sample_brand() -> Brand:
    """테스트용 브랜드"""
    return Brand.WSOP


# =============================================================================
# EventContext Fixtures
# =============================================================================


@pytest.fixture
def minimal_event_context(sample_year: int, sample_brand: Brand) -> EventContext:
    """최소 필수 필드만 포함한 EventContext"""
    return EventContext(
        year=sample_year,
        brand=sample_brand
    )


@pytest.fixture
def full_event_context(sample_year: int) -> EventContext:
    """모든 필드를 포함한 EventContext"""
    return EventContext(
        year=sample_year,
        brand=Brand.WSOP,
        event_type=EventType.BRACELET,
        location=Location.LAS_VEGAS,
        venue="Horseshoe Casino",
        event_number=21,
        buyin_usd=25000,
        game_variant=GameVariant.NLH,
        is_high_roller=True,
        is_super_high_roller=False,
        is_final_table=True,
        season=None,
        episode=None,
        episode_title=None
    )


# =============================================================================
# TechSpec Fixtures
# =============================================================================


@pytest.fixture
def minimal_tech_spec() -> TechSpec:
    """최소 필수 필드만 포함한 TechSpec"""
    return TechSpec()


@pytest.fixture
def full_tech_spec() -> TechSpec:
    """모든 필드를 포함한 TechSpec"""
    return TechSpec(
        fps=29.97,
        resolution="1080p",
        duration_sec=3600.5,
        file_size_mb=5120.0,
        codec="H.264"
    )


# =============================================================================
# PlayerInHand Fixtures
# =============================================================================


@pytest.fixture
def sample_player() -> PlayerInHand:
    """테스트용 플레이어"""
    return PlayerInHand(
        name="Phil Hellmuth",
        hand="AA",
        position="BTN",
        is_winner=True,
        chips_won=100000
    )


@pytest.fixture
def sample_players() -> list[PlayerInHand]:
    """테스트용 플레이어 리스트"""
    return [
        PlayerInHand(
            name="Phil Hellmuth",
            hand="AA",
            position="BTN",
            is_winner=True,
            chips_won=100000
        ),
        PlayerInHand(
            name="Daniel Negreanu",
            hand="KK",
            position="BB",
            is_winner=False,
            chips_won=0
        )
    ]


# =============================================================================
# SituationFlags Fixtures
# =============================================================================


@pytest.fixture
def sample_situation_flags() -> SituationFlags:
    """테스트용 상황 플래그"""
    return SituationFlags(
        is_cooler=True,
        is_badbeat=False,
        is_suckout=False,
        is_bluff=False,
        is_hero_call=False,
        is_hero_fold=False,
        is_river_killer=False
    )


# =============================================================================
# Segment Fixtures
# =============================================================================


@pytest.fixture
def minimal_segment(sample_uuid: UUID) -> Segment:
    """최소 필수 필드만 포함한 Segment"""
    return Segment(
        parent_asset_uuid=sample_uuid,
        time_in_sec=0.0,
        time_out_sec=60.0
    )


@pytest.fixture
def full_segment(sample_uuid: UUID, sample_players: list[PlayerInHand]) -> Segment:
    """모든 필드를 포함한 Segment"""
    return Segment(
        parent_asset_uuid=sample_uuid,
        segment_type=SegmentType.HAND,
        time_in_sec=120.5,
        time_out_sec=300.8,
        title="Epic AA vs KK Cooler",
        game_type=GameType.TOURNAMENT,
        rating=5,
        winner="Phil Hellmuth",
        winning_hand="Full House",
        losing_hand="Flush",
        players=sample_players,
        tags_action=["preflop-allin", "cooler"],
        tags_emotion=["brutal", "insane"],
        tags_content=["ft", "dirty"],
        situation_flags=SituationFlags(is_cooler=True),
        all_in_stage=AllInStage.PREFLOP,
        runout_type="runner-runner",
        adjective="brutal",
        board="Ah Kd 7c 2s 9h",
        event_stage="ft",
        hand_description="Hellmuth's Aces Hold",
        is_dirty=True,
        description="Final table cooler with massive pot"
    )


# =============================================================================
# Asset Fixtures
# =============================================================================


@pytest.fixture
def minimal_asset(minimal_event_context: EventContext) -> Asset:
    """최소 필수 필드만 포함한 Asset"""
    return Asset(
        file_name="test_video.mp4",
        event_context=minimal_event_context,
        source_origin="TEST_SOURCE"
    )


@pytest.fixture
def full_asset(
    full_event_context: EventContext,
    full_tech_spec: TechSpec,
    full_segment: Segment
) -> Asset:
    """모든 필드를 포함한 Asset"""
    asset = Asset(
        file_name="10-wsop-2024-be-ev-21-25k-nlh-hr-ft-description.mp4",
        file_path_rel="/ARCHIVE/WSOP/2024/Mastered/10-wsop-2024-be-ev-21-25k-nlh-hr-ft-description.mp4",
        file_path_nas="//NAS/ARCHIVE/WSOP/2024/Mastered/10-wsop-2024-be-ev-21-25k-nlh-hr-ft-description.mp4",
        asset_type=AssetType.MASTER,
        event_context=full_event_context,
        tech_spec=full_tech_spec,
        file_name_meta=FileNameMeta(
            code_prefix="WSOP",
            year_code="2024",
            sequence_num=10,
            event_number=21,
            buyin_code="25k",
            game_code="nlh"
        ),
        source_origin="NAS_WSOP_2024",
        created_at=datetime(2024, 1, 15, 10, 30, 0),
        last_modified=datetime(2024, 1, 15, 12, 0, 0),
        segments=[]
    )
    # Segment 추가 (parent_uuid 자동 설정 테스트)
    asset.add_segment(full_segment)
    return asset


# =============================================================================
# UDMDocument Fixtures
# =============================================================================


@pytest.fixture
def minimal_udm_document(minimal_asset: Asset) -> UDMDocument:
    """최소 필수 필드만 포함한 UDMDocument"""
    return UDMDocument(asset=minimal_asset)


@pytest.fixture
def full_udm_document(full_asset: Asset) -> UDMDocument:
    """모든 필드를 포함한 UDMDocument"""
    metadata = UDMMetadata(
        schema_version="3.0.0",
        exported_at=datetime(2024, 1, 15, 12, 0, 0),
        source="Archive_Converter",
        exporter_version="1.0.0"
    )
    return UDMDocument(metadata=metadata, asset=full_asset)


# =============================================================================
# Test Data Factories
# =============================================================================


@pytest.fixture
def make_segment(sample_uuid: UUID):
    """Segment 팩토리 함수"""
    def _make_segment(**kwargs):
        defaults = {
            "parent_asset_uuid": sample_uuid,
            "time_in_sec": 0.0,
            "time_out_sec": 60.0
        }
        defaults.update(kwargs)
        return Segment(**defaults)
    return _make_segment


@pytest.fixture
def make_asset(minimal_event_context: EventContext):
    """Asset 팩토리 함수"""
    def _make_asset(**kwargs):
        defaults = {
            "file_name": "test.mp4",
            "event_context": minimal_event_context,
            "source_origin": "TEST"
        }
        defaults.update(kwargs)
        return Asset(**defaults)
    return _make_asset
