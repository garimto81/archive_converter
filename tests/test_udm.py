"""
Unit Tests for UDM (Unified Data Model)

PRD-0008-UDM-FINAL-SCHEMA.md v3.0.0 기반 검증
TDD AAA 패턴 (Arrange-Act-Assert) 적용

Test Coverage:
1. Enum 테스트: 모든 Enum 값 존재 확인
2. Model 생성 테스트: 최소/전체 필드 검증
3. 유효성 검증 테스트: 비즈니스 규칙 검증
4. 유틸리티 함수 테스트: 파싱/추론 함수
5. 관계 테스트: Asset-Segment 관계
"""

from datetime import datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

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
    TechSpec,
    UDMDocument,
    UDMMetadata,
    generate_json_schema,
    generate_minimal_asset,
    infer_asset_type_from_path,
    infer_brand_from_path,
    parse_filename,
)


# =============================================================================
# 1. Enum 테스트
# =============================================================================


class TestEnums:
    """모든 Enum 값 존재 확인"""

    def test_brand_enum_values(self):
        """Brand Enum 값 검증"""
        # Arrange & Act
        brands = list(Brand)

        # Assert
        assert Brand.WSOP in brands
        assert Brand.WSOPC in brands
        assert Brand.WSOPE in brands
        assert Brand.WSOPP in brands
        assert Brand.HCL in brands
        assert Brand.PAD in brands
        assert Brand.GG_MILLIONS in brands
        assert Brand.MPP in brands
        assert Brand.GOG in brands
        assert Brand.WPT in brands
        assert Brand.EPT in brands
        assert Brand.OTHER in brands
        assert len(brands) == 12

    def test_event_type_enum_values(self):
        """EventType Enum 값 검증"""
        # Arrange & Act
        event_types = list(EventType)

        # Assert
        assert EventType.BRACELET in event_types
        assert EventType.CIRCUIT in event_types
        assert EventType.CASH_GAME_SHOW in event_types
        assert EventType.SUPER_MAIN in event_types
        assert EventType.ARCHIVE in event_types
        assert EventType.SIDE_EVENT in event_types
        assert len(event_types) == 6

    def test_asset_type_enum_values(self):
        """AssetType Enum 값 검증"""
        # Arrange & Act
        asset_types = list(AssetType)

        # Assert
        assert AssetType.STREAM in asset_types
        assert AssetType.SUBCLIP in asset_types
        assert AssetType.HAND_CLIP in asset_types
        assert AssetType.MASTER in asset_types
        assert AssetType.CLEAN in asset_types
        assert AssetType.NO_COMMENTARY in asset_types
        assert AssetType.RAW in asset_types
        assert AssetType.GENERIC in asset_types
        assert AssetType.MOV in asset_types
        assert AssetType.MXF in asset_types
        assert len(asset_types) == 10

    def test_location_enum_values(self):
        """Location Enum 값 검증"""
        # Arrange & Act
        locations = list(Location)

        # Assert
        assert Location.LAS_VEGAS in locations
        assert Location.PARADISE in locations
        assert Location.EUROPE in locations
        assert Location.LOS_ANGELES in locations
        assert Location.CYPRUS in locations
        assert Location.ROZVADOV in locations
        assert Location.OTHER in locations
        assert len(locations) == 7

    def test_game_variant_enum_values(self):
        """GameVariant Enum 값 검증"""
        # Arrange & Act
        game_variants = list(GameVariant)

        # Assert
        assert GameVariant.NLH in game_variants
        assert GameVariant.PLO in game_variants
        assert GameVariant.STUD in game_variants
        assert GameVariant.RAZZ in game_variants
        assert GameVariant.HORSE in game_variants
        assert GameVariant.MIXED in game_variants
        assert GameVariant.OMAHA_HI_LO in game_variants
        assert GameVariant.TD_27 in game_variants
        assert GameVariant.OTHER in game_variants
        assert len(game_variants) == 9

    def test_game_type_enum_values(self):
        """GameType Enum 값 검증"""
        # Arrange & Act
        game_types = list(GameType)

        # Assert
        assert GameType.TOURNAMENT in game_types
        assert GameType.CASH_GAME in game_types
        assert len(game_types) == 2

    def test_all_in_stage_enum_values(self):
        """AllInStage Enum 값 검증"""
        # Arrange & Act
        stages = list(AllInStage)

        # Assert
        assert AllInStage.PREFLOP in stages
        assert AllInStage.FLOP in stages
        assert AllInStage.TURN in stages
        assert AllInStage.RIVER in stages
        assert AllInStage.NONE in stages
        assert len(stages) == 5

    def test_segment_type_enum_values(self):
        """SegmentType Enum 값 검증"""
        # Arrange & Act
        segment_types = list(SegmentType)

        # Assert
        assert SegmentType.HAND in segment_types
        assert SegmentType.HIGHLIGHT in segment_types
        assert SegmentType.PLAYER_EMOTION in segment_types
        assert SegmentType.INTRO_OUTRO in segment_types
        assert SegmentType.COMMENTARY in segment_types
        assert len(segment_types) == 5


# =============================================================================
# 2. Model 생성 테스트
# =============================================================================


class TestEventContextCreation:
    """EventContext 모델 생성 테스트"""

    def test_create_minimal_event_context(self, minimal_event_context):
        """최소 필수 필드로 EventContext 생성"""
        # Assert
        assert minimal_event_context.year == 2024
        assert minimal_event_context.brand == Brand.WSOP
        assert minimal_event_context.event_type is None
        assert minimal_event_context.location is None

    def test_create_full_event_context(self, full_event_context):
        """모든 필드를 포함한 EventContext 생성"""
        # Assert
        assert full_event_context.year == 2024
        assert full_event_context.brand == Brand.WSOP
        assert full_event_context.event_type == EventType.BRACELET
        assert full_event_context.location == Location.LAS_VEGAS
        assert full_event_context.venue == "Horseshoe Casino"
        assert full_event_context.event_number == 21
        assert full_event_context.buyin_usd == 25000
        assert full_event_context.game_variant == GameVariant.NLH
        assert full_event_context.is_high_roller is True
        assert full_event_context.is_final_table is True

    def test_event_context_year_validation_min(self):
        """연도 최소값 검증 (1970)"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            EventContext(year=1969, brand=Brand.WSOP)

        assert "greater than or equal to 1970" in str(exc_info.value)

    def test_event_context_year_validation_max(self):
        """연도 최대값 검증 (2100)"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            EventContext(year=2101, brand=Brand.WSOP)

        assert "less than or equal to 2100" in str(exc_info.value)


class TestTechSpecCreation:
    """TechSpec 모델 생성 테스트"""

    def test_create_minimal_tech_spec(self, minimal_tech_spec):
        """최소 필수 필드로 TechSpec 생성 (기본값 사용)"""
        # Assert
        assert minimal_tech_spec.fps == 29.97
        assert minimal_tech_spec.resolution is None
        assert minimal_tech_spec.duration_sec is None

    def test_create_full_tech_spec(self, full_tech_spec):
        """모든 필드를 포함한 TechSpec 생성"""
        # Assert
        assert full_tech_spec.fps == 29.97
        assert full_tech_spec.resolution == "1080p"
        assert full_tech_spec.duration_sec == 3600.5
        assert full_tech_spec.file_size_mb == 5120.0
        assert full_tech_spec.codec == "H.264"

    def test_tech_spec_resolution_pattern_valid(self):
        """해상도 패턴 검증 - 유효한 값"""
        # Arrange & Act
        spec = TechSpec(resolution="1080p")

        # Assert
        assert spec.resolution == "1080p"

    def test_tech_spec_resolution_pattern_custom(self):
        """해상도 패턴 검증 - 커스텀 해상도"""
        # Arrange & Act
        spec = TechSpec(resolution="1920x1080")

        # Assert
        assert spec.resolution == "1920x1080"


class TestPlayerInHandCreation:
    """PlayerInHand 모델 생성 테스트"""

    def test_create_player_minimal(self):
        """최소 필수 필드로 PlayerInHand 생성"""
        # Arrange & Act
        player = PlayerInHand(name="Phil Hellmuth")

        # Assert
        assert player.name == "Phil Hellmuth"
        assert player.hand is None
        assert player.position is None
        assert player.is_winner is False
        assert player.chips_won is None

    def test_create_player_full(self, sample_player):
        """모든 필드를 포함한 PlayerInHand 생성"""
        # Assert
        assert sample_player.name == "Phil Hellmuth"
        assert sample_player.hand == "AA"
        assert sample_player.position == "BTN"
        assert sample_player.is_winner is True
        assert sample_player.chips_won == 100000

    def test_player_hand_validation_valid(self):
        """홀카드 형식 검증 - 유효한 패턴"""
        # Arrange & Act
        valid_hands = ["AA", "KK", "AKs", "AKo", "T9s", "AsAd", "KhKs"]

        # Assert
        for hand in valid_hands:
            player = PlayerInHand(name="Test", hand=hand)
            assert player.hand == hand

    def test_player_position_validation_valid(self):
        """포지션 검증 - 유효한 값"""
        # Arrange & Act
        valid_positions = ["UTG", "UTG+1", "MP", "HJ", "CO", "BTN", "SB", "BB"]

        # Assert
        for pos in valid_positions:
            player = PlayerInHand(name="Test", position=pos)
            assert player.position == pos

    def test_player_position_validation_invalid(self):
        """포지션 검증 - 잘못된 값"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            PlayerInHand(name="Test", position="INVALID_POS")


class TestSituationFlagsCreation:
    """SituationFlags 모델 생성 테스트"""

    def test_create_situation_flags_default(self):
        """기본값으로 SituationFlags 생성"""
        # Arrange & Act
        flags = SituationFlags()

        # Assert
        assert flags.is_cooler is False
        assert flags.is_badbeat is False
        assert flags.is_suckout is False
        assert flags.is_bluff is False
        assert flags.is_hero_call is False
        assert flags.is_hero_fold is False
        assert flags.is_river_killer is False

    def test_situation_flags_to_tags(self, sample_situation_flags):
        """SituationFlags를 태그 리스트로 변환"""
        # Arrange
        flags = SituationFlags(
            is_cooler=True,
            is_badbeat=True,
            is_bluff=True
        )

        # Act
        tags = flags.to_tags()

        # Assert
        assert "cooler" in tags
        assert "badbeat" in tags
        assert "bluff" in tags
        assert len(tags) == 3

    def test_situation_flags_to_tags_empty(self):
        """모든 플래그 False인 경우 빈 태그 리스트"""
        # Arrange
        flags = SituationFlags()

        # Act
        tags = flags.to_tags()

        # Assert
        assert tags == []


class TestSegmentCreation:
    """Segment 모델 생성 테스트"""

    def test_create_minimal_segment(self, minimal_segment):
        """최소 필수 필드로 Segment 생성"""
        # Assert
        assert minimal_segment.time_in_sec == 0.0
        assert minimal_segment.time_out_sec == 60.0
        assert minimal_segment.segment_type == SegmentType.HAND
        assert minimal_segment.game_type == GameType.TOURNAMENT
        assert minimal_segment.title is None

    def test_create_full_segment(self, full_segment):
        """모든 필드를 포함한 Segment 생성"""
        # Assert
        assert full_segment.time_in_sec == 120.5
        assert full_segment.time_out_sec == 300.8
        assert full_segment.title == "Epic AA vs KK Cooler"
        assert full_segment.rating == 5
        assert full_segment.winner == "Phil Hellmuth"
        assert full_segment.winning_hand == "Full House"
        assert len(full_segment.players) == 2
        assert full_segment.all_in_stage == AllInStage.PREFLOP
        assert full_segment.board == "Ah Kd 7c 2s 9h"

    def test_segment_uuid_auto_generation(self, sample_uuid):
        """Segment UUID 자동 생성 확인"""
        # Arrange & Act
        segment = Segment(
            parent_asset_uuid=sample_uuid,
            time_in_sec=0.0,
            time_out_sec=60.0
        )

        # Assert
        assert segment.segment_uuid is not None
        assert isinstance(segment.segment_uuid, UUID)

    def test_segment_duration_computed_field(self, minimal_segment):
        """duration_sec computed field 검증"""
        # Act
        duration = minimal_segment.duration_sec

        # Assert
        assert duration == 60.0


class TestAssetCreation:
    """Asset 모델 생성 테스트"""

    def test_create_minimal_asset(self, minimal_asset):
        """최소 필수 필드로 Asset 생성"""
        # Assert
        assert minimal_asset.file_name == "test_video.mp4"
        assert minimal_asset.event_context.year == 2024
        assert minimal_asset.event_context.brand == Brand.WSOP
        assert minimal_asset.source_origin == "TEST_SOURCE"
        assert minimal_asset.asset_type == AssetType.SUBCLIP
        assert len(minimal_asset.segments) == 0

    def test_create_full_asset(self, full_asset):
        """모든 필드를 포함한 Asset 생성"""
        # Assert
        assert full_asset.file_name.endswith(".mp4")
        assert full_asset.asset_type == AssetType.MASTER
        assert full_asset.event_context.event_number == 21
        assert full_asset.tech_spec.resolution == "1080p"
        assert full_asset.file_name_meta.buyin_code == "25k"
        assert len(full_asset.segments) == 1

    def test_asset_uuid_auto_generation(self, minimal_event_context):
        """Asset UUID 자동 생성 확인"""
        # Arrange & Act
        asset = Asset(
            file_name="test.mp4",
            event_context=minimal_event_context,
            source_origin="TEST"
        )

        # Assert
        assert asset.asset_uuid is not None
        assert isinstance(asset.asset_uuid, UUID)


class TestUDMDocumentCreation:
    """UDMDocument 모델 생성 테스트"""

    def test_create_minimal_udm_document(self, minimal_udm_document):
        """최소 필수 필드로 UDMDocument 생성"""
        # Assert
        assert minimal_udm_document.asset is not None
        assert minimal_udm_document.metadata.schema_version == "3.0.0"
        assert minimal_udm_document.metadata.source == "Archive_Converter"

    def test_create_udm_document_from_asset(self, minimal_asset):
        """Asset에서 UDMDocument 생성"""
        # Act
        doc = UDMDocument.from_asset(minimal_asset, source="TEST_SOURCE")

        # Assert
        assert doc.asset == minimal_asset
        assert doc.metadata.source == "TEST_SOURCE"

    def test_udm_document_to_json_dict(self, minimal_udm_document):
        """UDMDocument를 JSON dict로 변환"""
        # Act
        json_dict = minimal_udm_document.to_json_dict()

        # Assert
        assert "_metadata" in json_dict
        assert "asset" in json_dict
        assert json_dict["_metadata"]["schema_version"] == "3.0.0"


# =============================================================================
# 3. 유효성 검증 테스트
# =============================================================================


class TestSegmentValidation:
    """Segment 유효성 검증 테스트"""

    def test_time_out_greater_than_time_in(self, sample_uuid):
        """BR-001: time_out_sec > time_in_sec 검증"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Segment(
                parent_asset_uuid=sample_uuid,
                time_in_sec=100.0,
                time_out_sec=50.0  # INVALID: 시작보다 작음
            )

        assert "must be greater than" in str(exc_info.value)

    def test_time_equal_allowed(self, sample_uuid):
        """time_out_sec == time_in_sec 허용 (duration=0)"""
        # Arrange & Act
        segment = Segment(
            parent_asset_uuid=sample_uuid,
            time_in_sec=100.0,
            time_out_sec=100.0  # 허용: duration=0
        )

        # Assert
        assert segment.duration_sec == 0.0

    def test_rating_range_validation_min(self, sample_uuid):
        """rating 범위 검증 (0-5) - 최소값"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            Segment(
                parent_asset_uuid=sample_uuid,
                time_in_sec=0.0,
                time_out_sec=60.0,
                rating=-1  # INVALID: 0보다 작음
            )

    def test_rating_range_validation_max(self, sample_uuid):
        """rating 범위 검증 (0-5) - 최대값"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            Segment(
                parent_asset_uuid=sample_uuid,
                time_in_sec=0.0,
                time_out_sec=60.0,
                rating=6  # INVALID: 5보다 큼
            )

    def test_rating_range_valid_values(self, sample_uuid):
        """rating 유효 범위 (0-5) 검증"""
        # Arrange & Act
        for rating in range(0, 6):
            segment = Segment(
                parent_asset_uuid=sample_uuid,
                time_in_sec=0.0,
                time_out_sec=60.0,
                rating=rating
            )

            # Assert
            assert segment.rating == rating

    def test_duration_validation_warning_range(self, sample_uuid):
        """BR-003: 핸드 길이 10초-3600초 경고 (검증은 통과)"""
        # Arrange & Act - 너무 짧은 핸드 (경고만)
        short_segment = Segment(
            parent_asset_uuid=sample_uuid,
            time_in_sec=0.0,
            time_out_sec=5.0  # 5초
        )

        # Assert - 검증은 통과
        assert short_segment.duration_sec == 5.0

        # Arrange & Act - 너무 긴 핸드 (경고만)
        long_segment = Segment(
            parent_asset_uuid=sample_uuid,
            time_in_sec=0.0,
            time_out_sec=4000.0  # 1시간 이상
        )

        # Assert - 검증은 통과
        assert long_segment.duration_sec == 4000.0


class TestAssetValidation:
    """Asset 유효성 검증 테스트"""

    def test_segment_parent_uuid_mismatch(self, minimal_asset, sample_uuid):
        """Segment의 parent_asset_uuid 불일치 검증"""
        # Arrange
        wrong_segment = Segment(
            parent_asset_uuid=sample_uuid,  # 다른 UUID
            time_in_sec=0.0,
            time_out_sec=60.0
        )

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            minimal_asset.segments = [wrong_segment]
            # Trigger validation
            Asset.model_validate(minimal_asset.model_dump())

        assert "mismatched parent_asset_uuid" in str(exc_info.value)

    def test_file_name_validation_valid_extensions(self, minimal_event_context):
        """파일명 확장자 검증 - 유효한 확장자"""
        # Arrange & Act
        valid_extensions = [".mp4", ".mov", ".mxf", ".mkv", ".avi", ".wmv"]

        # Assert
        for ext in valid_extensions:
            asset = Asset(
                file_name=f"test{ext}",
                event_context=minimal_event_context,
                source_origin="TEST"
            )
            assert asset.file_name.endswith(ext)


# =============================================================================
# 4. 유틸리티 함수 테스트
# =============================================================================


class TestParseFilename:
    """parse_filename() 함수 테스트"""

    def test_parse_circuit_subclip(self):
        """WCLA24-15.mp4 패턴 파싱"""
        # Arrange
        filename = "WCLA24-15.mp4"

        # Act
        meta = parse_filename(filename)

        # Assert
        assert meta.code_prefix == "WCLA"
        assert meta.year_code == "24"
        assert meta.sequence_num == 15

    def test_parse_paradise_pe(self):
        """WP23-PE-01.mp4 패턴 파싱"""
        # Arrange
        filename = "WP23-PE-01.mp4"

        # Act
        meta = parse_filename(filename)

        # Assert
        assert meta.code_prefix == "WP"
        assert meta.year_code == "23"
        assert meta.clip_type == "PE"
        assert meta.sequence_num == 1

    def test_parse_paradise_subclip(self):
        """WP23-03.mp4 패턴 파싱"""
        # Arrange
        filename = "WP23-03.mp4"

        # Act
        meta = parse_filename(filename)

        # Assert
        assert meta.code_prefix == "WP"
        assert meta.year_code == "23"
        assert meta.sequence_num == 3

    def test_parse_pad_episode(self):
        """PAD_S13_EP01_GGPoker-001.mp4 패턴 파싱"""
        # Arrange
        filename = "PAD_S13_EP01_GGPoker-001.mp4"

        # Act
        meta = parse_filename(filename)

        # Assert
        assert meta.code_prefix == "PAD"
        assert meta.clip_type == "EP"
        assert meta.season == 13
        assert meta.episode == 1
        assert "GGPoker" in meta.raw_description

    def test_parse_wsop_mastered(self):
        """10-wsop-2024-be-ev-21-25k-nlh-hr-ft-description.mp4 패턴 파싱"""
        # Arrange
        filename = "10-wsop-2024-be-ev-21-25k-nlh-hr-ft-description.mp4"

        # Act
        meta = parse_filename(filename)

        # Assert
        assert meta.sequence_num == 10
        assert meta.year_code == "2024"
        assert meta.event_number == 21
        assert meta.buyin_code == "25k"
        assert meta.game_code == "nlh"

    def test_parse_ggmillions(self):
        """250507_Super High Roller Poker FINAL TABLE with Player.mp4 패턴 파싱"""
        # Arrange
        filename = "250507_Super High Roller Poker FINAL TABLE with Tom Dwan.mp4"

        # Act
        meta = parse_filename(filename)

        # Assert
        assert meta.year_code == "25"
        assert "Tom Dwan" in meta.raw_description

    def test_parse_unknown_pattern(self):
        """매칭되지 않는 패턴 - 빈 메타데이터 반환"""
        # Arrange
        filename = "random_file_name.mp4"

        # Act
        meta = parse_filename(filename)

        # Assert
        assert meta.code_prefix is None
        assert meta.year_code is None
        assert meta.sequence_num is None


class TestInferBrandFromPath:
    """infer_brand_from_path() 함수 테스트"""

    def test_infer_wsop_bracelet(self):
        """WSOP Bracelet 경로 추론"""
        # Arrange
        path = "/ARCHIVE/WSOP/WSOP Bracelet Event/2024/Mastered/test.mp4"

        # Act
        result = infer_brand_from_path(path)

        # Assert
        assert result["brand"] == Brand.WSOP
        assert result["event_type"] == EventType.BRACELET

    def test_infer_wsopc(self):
        """WSOP Circuit 경로 추론"""
        # Arrange
        path = "/ARCHIVE/WSOP/WSOP Circuit Event/2024/test.mp4"

        # Act
        result = infer_brand_from_path(path)

        # Assert
        assert result["brand"] == Brand.WSOPC
        assert result["event_type"] == EventType.CIRCUIT

    def test_infer_hcl(self):
        """HCL 경로 추론"""
        # Arrange
        path = "/ARCHIVE/HCL/Season 5/Episode 1/test.mp4"

        # Act
        result = infer_brand_from_path(path)

        # Assert
        assert result["brand"] == Brand.HCL
        assert result["event_type"] == EventType.CASH_GAME_SHOW

    def test_infer_pad(self):
        """PAD 경로 추론"""
        # Arrange
        path = "/ARCHIVE/PAD/Season 13/Episode 1/test.mp4"

        # Act
        result = infer_brand_from_path(path)

        # Assert
        assert result["brand"] == Brand.PAD
        assert result["event_type"] == EventType.CASH_GAME_SHOW

    def test_infer_ggmillions(self):
        """GGMillions 경로 추론"""
        # Arrange
        path = "/ARCHIVE/GGMillions/2025/test.mp4"

        # Act
        result = infer_brand_from_path(path)

        # Assert
        assert result["brand"] == Brand.GG_MILLIONS
        assert result["event_type"] == EventType.CASH_GAME_SHOW

    def test_infer_unknown_path(self):
        """매칭되지 않는 경로 - OTHER 브랜드"""
        # Arrange
        path = "/ARCHIVE/UNKNOWN/test.mp4"

        # Act
        result = infer_brand_from_path(path)

        # Assert
        assert result["brand"] == Brand.OTHER
        assert result["event_type"] is None

    def test_infer_windows_path(self):
        """Windows 경로 정규화 테스트"""
        # Arrange
        path = r"\ARCHIVE\WSOP\WSOP Bracelet Event\2024\test.mp4"

        # Act
        result = infer_brand_from_path(path)

        # Assert
        assert result["brand"] == Brand.WSOP
        assert result["event_type"] == EventType.BRACELET


class TestInferAssetTypeFromPath:
    """infer_asset_type_from_path() 함수 테스트"""

    def test_infer_stream(self):
        """STREAM 경로 추론"""
        # Arrange
        path = "/ARCHIVE/WSOP/2024/STREAM/test.mp4"

        # Act
        result = infer_asset_type_from_path(path)

        # Assert
        assert result == AssetType.STREAM

    def test_infer_subclip(self):
        """SUBCLIP 경로 추론"""
        # Arrange
        path = "/ARCHIVE/WSOP/2024/SUBCLIP/test.mp4"

        # Act
        result = infer_asset_type_from_path(path)

        # Assert
        assert result == AssetType.SUBCLIP

    def test_infer_master(self):
        """MASTER 경로 추론"""
        # Arrange
        path = "/ARCHIVE/WSOP/2024/Mastered/test.mp4"

        # Act
        result = infer_asset_type_from_path(path)

        # Assert
        assert result == AssetType.MASTER

    def test_infer_hand_clip(self):
        """HAND_CLIP 경로 추론"""
        # Arrange
        path = "/ARCHIVE/WSOPP/2024/Hand Clip/test.mp4"

        # Act
        result = infer_asset_type_from_path(path)

        # Assert
        assert result == AssetType.HAND_CLIP

    def test_infer_clean(self):
        """CLEAN 경로 추론"""
        # Arrange
        path = "/ARCHIVE/WSOP/2024/Clean/test.mp4"

        # Act
        result = infer_asset_type_from_path(path)

        # Assert
        assert result == AssetType.CLEAN

    def test_infer_default_subclip(self):
        """매칭되지 않는 경로 - 기본값 SUBCLIP"""
        # Arrange
        path = "/ARCHIVE/WSOP/2024/Unknown/test.mp4"

        # Act
        result = infer_asset_type_from_path(path)

        # Assert
        assert result == AssetType.SUBCLIP


class TestGenerateJsonSchema:
    """generate_json_schema() 함수 테스트"""

    def test_generate_schema(self):
        """JSON Schema 생성 확인"""
        # Act
        schema = generate_json_schema()

        # Assert
        assert schema is not None
        assert "$defs" in schema or "definitions" in schema
        assert "properties" in schema

    def test_schema_contains_metadata(self):
        """Schema에 metadata 필드 존재 확인"""
        # Act
        schema = generate_json_schema()

        # Assert
        assert "properties" in schema
        properties = schema["properties"]
        # metadata는 serialization_alias로 _metadata로 직렬화됨
        assert "metadata" in properties or "_metadata" in properties


class TestGenerateMinimalAsset:
    """generate_minimal_asset() 함수 테스트"""

    def test_generate_minimal_asset(self):
        """최소 Asset 생성 함수 테스트"""
        # Arrange
        file_name = "test.mp4"
        year = 2024
        brand = Brand.WSOP
        source_origin = "TEST_SOURCE"

        # Act
        asset = generate_minimal_asset(
            file_name=file_name,
            year=year,
            brand=brand,
            source_origin=source_origin
        )

        # Assert
        assert asset.file_name == file_name
        assert asset.event_context.year == year
        assert asset.event_context.brand == brand
        assert asset.source_origin == source_origin


# =============================================================================
# 5. 관계 테스트
# =============================================================================


class TestAssetSegmentRelationship:
    """Asset-Segment 관계 테스트"""

    def test_add_segment_auto_parent_uuid(self, minimal_asset, sample_uuid):
        """Asset.add_segment()로 parent_uuid 자동 설정"""
        # Arrange
        segment = Segment(
            parent_asset_uuid=sample_uuid,  # 임시 UUID
            time_in_sec=0.0,
            time_out_sec=60.0
        )

        # Act
        minimal_asset.add_segment(segment)

        # Assert
        assert segment.parent_asset_uuid == minimal_asset.asset_uuid
        assert len(minimal_asset.segments) == 1

    def test_get_segments_by_type(self, minimal_asset):
        """Asset.get_segments_by_type() 필터링 테스트"""
        # Arrange
        hand_segment = Segment(
            parent_asset_uuid=minimal_asset.asset_uuid,
            segment_type=SegmentType.HAND,
            time_in_sec=0.0,
            time_out_sec=60.0
        )
        highlight_segment = Segment(
            parent_asset_uuid=minimal_asset.asset_uuid,
            segment_type=SegmentType.HIGHLIGHT,
            time_in_sec=60.0,
            time_out_sec=120.0
        )

        minimal_asset.add_segment(hand_segment)
        minimal_asset.add_segment(highlight_segment)

        # Act
        hand_segments = minimal_asset.get_segments_by_type(SegmentType.HAND)
        highlight_segments = minimal_asset.get_segments_by_type(SegmentType.HIGHLIGHT)

        # Assert
        assert len(hand_segments) == 1
        assert len(highlight_segments) == 1
        assert hand_segments[0].segment_type == SegmentType.HAND
        assert highlight_segments[0].segment_type == SegmentType.HIGHLIGHT

    def test_get_total_duration(self, minimal_asset):
        """Asset.get_total_duration() 전체 길이 계산"""
        # Arrange
        segment1 = Segment(
            parent_asset_uuid=minimal_asset.asset_uuid,
            time_in_sec=0.0,
            time_out_sec=60.0  # 60초
        )
        segment2 = Segment(
            parent_asset_uuid=minimal_asset.asset_uuid,
            time_in_sec=60.0,
            time_out_sec=150.0  # 90초
        )

        minimal_asset.add_segment(segment1)
        minimal_asset.add_segment(segment2)

        # Act
        total_duration = minimal_asset.get_total_duration()

        # Assert
        assert total_duration == 150.0  # 60 + 90


class TestSegmentPlayerRelationship:
    """Segment-PlayerInHand 관계 테스트"""

    def test_get_player_names(self, full_segment):
        """Segment.get_player_names() 플레이어 이름 목록"""
        # Act
        names = full_segment.get_player_names()

        # Assert
        assert "Phil Hellmuth" in names
        assert "Daniel Negreanu" in names
        assert len(names) == 2

    def test_get_player_names_empty(self, minimal_segment):
        """플레이어 없는 경우 빈 리스트"""
        # Act
        names = minimal_segment.get_player_names()

        # Assert
        assert names == []

    def test_add_tag_action(self, minimal_segment):
        """Segment.add_tag() 액션 태그 추가"""
        # Act
        minimal_segment.add_tag("preflop-allin", tag_type="action")

        # Assert
        assert "preflop-allin" in minimal_segment.tags_action

    def test_add_tag_emotion(self, minimal_segment):
        """Segment.add_tag() 감정 태그 추가"""
        # Act
        minimal_segment.add_tag("brutal", tag_type="emotion")

        # Assert
        assert "brutal" in minimal_segment.tags_emotion

    def test_add_tag_duplicate(self, minimal_segment):
        """중복 태그 추가 방지"""
        # Act
        minimal_segment.add_tag("cooler", tag_type="action")
        minimal_segment.add_tag("cooler", tag_type="action")

        # Assert
        assert minimal_segment.tags_action.count("cooler") == 1


class TestUDMDocumentConversion:
    """UDMDocument 변환 테스트"""

    def test_from_asset_default_source(self, minimal_asset):
        """Asset에서 UDMDocument 생성 - 기본 source"""
        # Act
        doc = UDMDocument.from_asset(minimal_asset)

        # Assert
        assert doc.asset == minimal_asset
        assert doc.metadata.source == minimal_asset.source_origin

    def test_from_asset_custom_source(self, minimal_asset):
        """Asset에서 UDMDocument 생성 - 커스텀 source"""
        # Act
        doc = UDMDocument.from_asset(minimal_asset, source="CUSTOM_SOURCE")

        # Assert
        assert doc.metadata.source == "CUSTOM_SOURCE"

    def test_to_json_dict_exclude_none(self, minimal_asset):
        """to_json_dict() None 값 제외"""
        # Arrange
        doc = UDMDocument.from_asset(minimal_asset)

        # Act
        json_dict = doc.to_json_dict()

        # Assert
        assert json_dict is not None
        # None 값이 제외되었는지 확인 (예: tech_spec은 None이므로 제외)
        assert "tech_spec" not in json_dict["asset"]


# =============================================================================
# Edge Cases & Integration Tests
# =============================================================================


class TestEdgeCases:
    """엣지 케이스 테스트"""

    def test_empty_segments_list(self, minimal_asset):
        """빈 segments 리스트 처리"""
        # Assert
        assert minimal_asset.segments == []
        assert minimal_asset.get_total_duration() == 0.0

    def test_segment_with_no_players(self, minimal_segment):
        """플레이어 정보 없는 Segment"""
        # Assert
        assert minimal_segment.players is None
        assert minimal_segment.get_player_names() == []

    def test_unicode_characters_in_names(self, sample_uuid):
        """유니코드 문자 지원 (한글, 특수문자)"""
        # Arrange & Act
        player = PlayerInHand(name="이민수 (Lee Min-Soo)")
        segment = Segment(
            parent_asset_uuid=sample_uuid,
            time_in_sec=0.0,
            time_out_sec=60.0,
            title="대박 핸드 🔥",
            winner="이민수 (Lee Min-Soo)"
        )

        # Assert
        assert player.name == "이민수 (Lee Min-Soo)"
        assert segment.title == "대박 핸드 🔥"

    def test_very_long_description(self, sample_uuid):
        """긴 설명 문자열 처리"""
        # Arrange
        long_description = "A" * 10000

        # Act
        segment = Segment(
            parent_asset_uuid=sample_uuid,
            time_in_sec=0.0,
            time_out_sec=60.0,
            description=long_description
        )

        # Assert
        assert len(segment.description) == 10000

    def test_multiple_segments_same_time_range(self, minimal_asset):
        """같은 시간 범위의 여러 Segment (허용)"""
        # Arrange
        segment1 = Segment(
            parent_asset_uuid=minimal_asset.asset_uuid,
            segment_type=SegmentType.HAND,
            time_in_sec=0.0,
            time_out_sec=60.0
        )
        segment2 = Segment(
            parent_asset_uuid=minimal_asset.asset_uuid,
            segment_type=SegmentType.COMMENTARY,
            time_in_sec=0.0,
            time_out_sec=60.0
        )

        # Act
        minimal_asset.add_segment(segment1)
        minimal_asset.add_segment(segment2)

        # Assert
        assert len(minimal_asset.segments) == 2


class TestIntegration:
    """통합 테스트"""

    def test_full_workflow_asset_with_segments(
        self,
        minimal_event_context,
        sample_players
    ):
        """전체 워크플로우: Asset 생성 → Segment 추가 → UDMDocument 변환"""
        # Arrange - Asset 생성
        asset = Asset(
            file_name="test.mp4",
            event_context=minimal_event_context,
            source_origin="TEST"
        )

        # Act - Segment 추가
        segment = Segment(
            parent_asset_uuid=asset.asset_uuid,
            time_in_sec=0.0,
            time_out_sec=120.0,
            title="Test Hand",
            players=sample_players,
            rating=4
        )
        asset.add_segment(segment)

        # Act - UDMDocument 생성
        doc = UDMDocument.from_asset(asset)

        # Assert
        assert len(doc.asset.segments) == 1
        assert doc.asset.segments[0].title == "Test Hand"
        assert len(doc.asset.segments[0].players) == 2

        # Act - JSON 직렬화
        json_dict = doc.to_json_dict()

        # Assert
        assert json_dict["asset"]["file_name"] == "test.mp4"
        assert json_dict["asset"]["segments"][0]["rating"] == 4

    def test_parse_filename_and_create_asset(self):
        """파일명 파싱 → Asset 생성 통합 테스트"""
        # Arrange
        filename = "WCLA24-15.mp4"

        # Act - 파일명 파싱
        meta = parse_filename(filename)

        # Act - Asset 생성
        asset = Asset(
            file_name=filename,
            event_context=EventContext(year=2024, brand=Brand.WSOPC),
            file_name_meta=meta,
            source_origin="NAS"
        )

        # Assert
        assert asset.file_name_meta.code_prefix == "WCLA"
        assert asset.file_name_meta.year_code == "24"
        assert asset.file_name_meta.sequence_num == 15

    def test_infer_path_and_create_asset(self):
        """경로 추론 → Asset 생성 통합 테스트"""
        # Arrange
        path = "/ARCHIVE/WSOP/WSOP Bracelet Event/2024/Mastered/test.mp4"

        # Act - 경로 추론
        brand_info = infer_brand_from_path(path)
        asset_type = infer_asset_type_from_path(path)

        # Act - Asset 생성
        asset = Asset(
            file_name="test.mp4",
            file_path_nas=path,
            asset_type=asset_type,
            event_context=EventContext(
                year=2024,
                brand=brand_info["brand"],
                event_type=brand_info["event_type"]
            ),
            source_origin="NAS"
        )

        # Assert
        assert asset.event_context.brand == Brand.WSOP
        assert asset.event_context.event_type == EventType.BRACELET
        assert asset.asset_type == AssetType.MASTER


# =============================================================================
# Google Sheets 파싱 헬퍼 테스트 (Issue #7)
# =============================================================================


class TestParseTimeHMS:
    """parse_time_hms() 함수 테스트"""

    def test_parse_time_hms_full_format(self):
        """HH:MM:SS 전체 형식"""
        from src.models import parse_time_hms
        assert parse_time_hms("6:58:55") == 6 * 3600 + 58 * 60 + 55
        assert parse_time_hms("0:12:47") == 12 * 60 + 47
        assert parse_time_hms("01:00:00") == 3600.0

    def test_parse_time_hms_mm_ss_format(self):
        """MM:SS 형식"""
        from src.models import parse_time_hms
        assert parse_time_hms("12:30") == 12 * 60 + 30
        assert parse_time_hms("0:45") == 45.0

    def test_parse_time_hms_empty_or_invalid(self):
        """빈 값 또는 잘못된 형식"""
        from src.models import parse_time_hms
        assert parse_time_hms("") == 0.0
        assert parse_time_hms(None) == 0.0
        assert parse_time_hms("invalid") == 0.0


class TestParseStarRating:
    """parse_star_rating() 함수 테스트"""

    def test_parse_star_rating_stars(self):
        """별 문자 파싱"""
        from src.models import parse_star_rating
        assert parse_star_rating("★") == 1
        assert parse_star_rating("★★") == 2
        assert parse_star_rating("★★★") == 3

    def test_parse_star_rating_numbers(self):
        """숫자 파싱"""
        from src.models import parse_star_rating
        assert parse_star_rating("3") == 3
        assert parse_star_rating("5") == 5
        assert parse_star_rating("10") == 5  # 최대 5

    def test_parse_star_rating_empty_or_invalid(self):
        """빈 값 또는 잘못된 형식"""
        from src.models import parse_star_rating
        assert parse_star_rating("") == 0
        assert parse_star_rating(None) == 0


class TestParseHandMatchup:
    """parse_hand_matchup() 함수 테스트"""

    def test_parse_hand_matchup_simple(self):
        """단순 매치업 파싱"""
        from src.models import parse_hand_matchup
        result = parse_hand_matchup("88 vs JJ")
        assert len(result) == 2
        assert result[0].hand == "88"
        assert result[1].hand == "JJ"

    def test_parse_hand_matchup_triple(self):
        """3-way 매치업 파싱"""
        from src.models import parse_hand_matchup
        result = parse_hand_matchup("AKo vs KK vs QQ")
        assert len(result) == 3
        assert result[0].hand == "AKo"
        assert result[1].hand == "KK"
        assert result[2].hand == "QQ"

    def test_parse_hand_matchup_empty(self):
        """빈 값 처리"""
        from src.models import parse_hand_matchup
        assert parse_hand_matchup("") == []
        assert parse_hand_matchup(None) == []


class TestParsePlayersTags:
    """parse_players_tags() 함수 테스트"""

    def test_parse_players_tags_simple(self):
        """쉼표 구분 플레이어 파싱"""
        from src.models import parse_players_tags
        result = parse_players_tags("Phil Ivey, Daniel Negreanu")
        assert len(result) == 2
        assert result[0].name == "Phil Ivey"
        assert result[1].name == "Daniel Negreanu"

    def test_parse_players_tags_with_duplicates(self):
        """중복 제거"""
        from src.models import parse_players_tags
        result = parse_players_tags("Steve YEA,YEA,FAN,chih fan")
        assert len(result) == 4  # 중복 없음 (대소문자 구분)

    def test_parse_players_tags_empty(self):
        """빈 값 처리"""
        from src.models import parse_players_tags
        assert parse_players_tags("") == []


class TestMergeTagColumns:
    """merge_tag_columns() 함수 테스트"""

    def test_merge_tag_columns_simple(self):
        """태그 병합"""
        from src.models import merge_tag_columns
        result = merge_tag_columns("Nice Fold", "Preflop All-in", "", None)
        assert result == ["Nice Fold", "Preflop All-in"]

    def test_merge_tag_columns_dedup(self):
        """중복 제거"""
        from src.models import merge_tag_columns
        result = merge_tag_columns("Cooler", "cooler", "COOLER")
        assert len(result) == 1


class TestParseAllInTags:
    """parse_all_in_tags() 함수 테스트"""

    def test_parse_all_in_tags_preflop(self):
        """프리플랍 올인 파싱"""
        from src.models import parse_all_in_tags, AllInStage
        stage, tags = parse_all_in_tags("4bet,preflop allin")
        assert stage == AllInStage.PREFLOP
        assert "4bet" in tags

    def test_parse_all_in_tags_flop(self):
        """플랍 올인 파싱"""
        from src.models import parse_all_in_tags, AllInStage
        stage, tags = parse_all_in_tags("flop")
        assert stage == AllInStage.FLOP

    def test_parse_all_in_tags_empty(self):
        """빈 값 처리"""
        from src.models import parse_all_in_tags
        stage, tags = parse_all_in_tags("")
        assert stage is None
        assert tags == []


class TestParseSituationFlagsFromColumns:
    """parse_situation_flags_from_columns() 함수 테스트"""

    def test_parse_situation_flags_true_values(self):
        """다양한 true 값 파싱"""
        from src.models import parse_situation_flags_from_columns
        flags = parse_situation_flags_from_columns(
            badbeat="TRUE",
            bluff="1",
            suckout="yes",
            cooler="x"
        )
        assert flags.is_badbeat is True
        assert flags.is_bluff is True
        assert flags.is_suckout is True
        assert flags.is_cooler is True

    def test_parse_situation_flags_false_values(self):
        """false/빈 값 파싱"""
        from src.models import parse_situation_flags_from_columns
        flags = parse_situation_flags_from_columns(
            badbeat="",
            bluff=None,
            suckout="FALSE"
        )
        assert flags.is_badbeat is False
        assert flags.is_bluff is False
        assert flags.is_suckout is False
        assert flags.is_cooler is False


class TestNewSegmentFields:
    """Issue #7: 새로운 Segment 필드 테스트"""

    def test_segment_with_new_fields(self, sample_uuid):
        """새로 추가된 Segment 필드 테스트"""
        segment = Segment(
            parent_asset_uuid=sample_uuid,
            time_in_sec=0.0,
            time_out_sec=60.0,
            # 새로 추가된 필드
            tags_player=["Phil Ivey", "Daniel Negreanu"],
            tags_search=["epic", "cooler"],
            hand_tag="AA vs KK",
            scene="Final Table",
            source_type="PGM",
            is_epic_hand=True,
            appearance_outfit="Black suit",
            scenery_object="Poker table",
            postflop_action="check-raise",
            time_in_ms=0,
            time_out_ms=60000,
        )

        assert segment.tags_player == ["Phil Ivey", "Daniel Negreanu"]
        assert segment.tags_search == ["epic", "cooler"]
        assert segment.hand_tag == "AA vs KK"
        assert segment.scene == "Final Table"
        assert segment.source_type == "PGM"
        assert segment.is_epic_hand is True
        assert segment.appearance_outfit == "Black suit"
        assert segment.scenery_object == "Poker table"
        assert segment.postflop_action == "check-raise"
        assert segment.time_in_ms == 0
        assert segment.time_out_ms == 60000


class TestNewAssetFields:
    """Issue #7: 새로운 Asset 필드 테스트"""

    def test_asset_with_new_fields(self, minimal_event_context):
        """새로 추가된 Asset 필드 테스트"""
        asset = Asset(
            file_name="test.mp4",
            event_context=minimal_event_context,
            source_origin="GoogleSheets",
            # 새로 추가된 필드
            file_number=42,
            tournament_name="$1,500 NLH Main Event",
            project_name_tag="WSOP2024",
            nas_folder_link=r"\\10.10.100.122\docker\GGPNAs\ARCHIVE\WSOP",
        )

        assert asset.file_number == 42
        assert asset.tournament_name == "$1,500 NLH Main Event"
        assert asset.project_name_tag == "WSOP2024"
        assert asset.nas_folder_link == r"\\10.10.100.122\docker\GGPNAs\ARCHIVE\WSOP"
