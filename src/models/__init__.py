"""
UDM (Unified Data Model) 스키마 모듈

PRD-0008-UDM-FINAL-SCHEMA.md 기반 Pydantic V2 구현
"""

from .udm import (
    # Enums
    Brand,
    EventType,
    AssetType,
    Location,
    GameVariant,
    GameType,
    AllInStage,
    SegmentType,
    # Models
    EventContext,
    TechSpec,
    FileNameMeta,
    SourceOrigin,
    SituationFlags,
    PlayerInHand,
    Asset,
    Segment,
    # Root model
    UDMDocument,
    UDMMetadata,
    # Utility functions
    parse_filename,
    generate_json_schema,
    generate_minimal_asset,
    infer_brand_from_path,
    infer_asset_type_from_path,
    # Google Sheets 파싱 헬퍼 (Issue #7)
    parse_time_hms,
    parse_star_rating,
    parse_hand_matchup,
    parse_players_tags,
    merge_tag_columns,
    parse_all_in_tags,
    parse_situation_flags_from_columns,
    # Constants
    FILENAME_PATTERNS,
    NAS_PATH_MAPPING,
    FOLDER_ASSET_TYPE_MAPPING,
)

__all__ = [
    # Enums
    "Brand",
    "EventType",
    "AssetType",
    "Location",
    "GameVariant",
    "GameType",
    "AllInStage",
    "SegmentType",
    # Models
    "EventContext",
    "TechSpec",
    "FileNameMeta",
    "SourceOrigin",
    "SituationFlags",
    "PlayerInHand",
    "Asset",
    "Segment",
    # Root model
    "UDMDocument",
    "UDMMetadata",
    # Utility functions
    "parse_filename",
    "generate_json_schema",
    "generate_minimal_asset",
    "infer_brand_from_path",
    "infer_asset_type_from_path",
    # Google Sheets 파싱 헬퍼 (Issue #7)
    "parse_time_hms",
    "parse_star_rating",
    "parse_hand_matchup",
    "parse_players_tags",
    "merge_tag_columns",
    "parse_all_in_tags",
    "parse_situation_flags_from_columns",
    # Constants
    "FILENAME_PATTERNS",
    "NAS_PATH_MAPPING",
    "FOLDER_ASSET_TYPE_MAPPING",
]

__version__ = "3.1.0"  # Issue #7: Google Sheets 파싱 지원 추가
