"""
UDM 통합 DB 초기화 스크립트

기존 3개 DB를 UDM 기반 단일 DB로 통합:
- nas_footage.db (files)
- nas_classified.db (classified_files)
- pokergo.db (videos)

→ unified_archive.db (assets, segments, pokergo_videos, matches)
"""

import sqlite3
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(r"D:\AI\claude01\Archive_Converter")
DATA_DIR = PROJECT_ROOT / "data"
UNIFIED_DB = DATA_DIR / "unified_archive.db"


def create_unified_db():
    """UDM 통합 DB 생성"""

    # 기존 DB 백업
    if UNIFIED_DB.exists():
        backup_path = UNIFIED_DB.with_suffix(f".db.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        UNIFIED_DB.rename(backup_path)
        print(f"기존 DB 백업: {backup_path}")

    conn = sqlite3.connect(str(UNIFIED_DB))
    cursor = conn.cursor()

    # =========================================================================
    # 1. assets 테이블 (UDM Asset - NAS 파일)
    # =========================================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assets (
        -- 식별자
        asset_uuid TEXT PRIMARY KEY,

        -- 파일 정보 (NAS)
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL UNIQUE,
        relative_path TEXT,
        folder_path TEXT,
        extension TEXT,

        -- 크기/시간
        size_bytes INTEGER,
        size_gb REAL,
        modified_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        -- 브랜드/타입 (Enum)
        brand TEXT,                    -- WSOP, HCL, PAD, etc.
        asset_type TEXT,               -- STREAM, SUBCLIP, MASTER, etc.

        -- 이벤트 컨텍스트 (JSON)
        event_context JSON,            -- year, event_type, location, etc.

        -- 기술 사양 (JSON)
        tech_spec JSON,                -- duration_sec, resolution, codec, fps

        -- 파일명 메타 (JSON)
        filename_meta JSON,            -- code_prefix, year_code, sequence_num, etc.

        -- 출처 정보
        source_origin TEXT,            -- NAS, PokerGO, GoogleSheet
        source_id TEXT,                -- 원본 출처 ID

        -- 미디어 정보
        duration_sec REAL,
        resolution TEXT,
        video_codec TEXT,
        audio_codec TEXT,
        bitrate INTEGER,
        fps REAL,
        media_scanned INTEGER DEFAULT 0,

        -- 분류/매칭 상태
        classification TEXT,           -- WSOP, HCL, PAD, SKIP, UNKNOWN
        classification_reason TEXT,
        pokergo_matched INTEGER DEFAULT 0,

        -- 인덱스용 추출 필드
        year INTEGER,
        event_number INTEGER,
        season INTEGER,
        episode INTEGER,

        -- 업데이트 추적
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # =========================================================================
    # 2. segments 테이블 (UDM Segment - 핸드/클립)
    # =========================================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS segments (
        -- 식별자
        segment_uuid TEXT PRIMARY KEY,
        parent_asset_uuid TEXT NOT NULL,

        -- 시간 정보
        time_in_sec REAL NOT NULL,
        time_out_sec REAL NOT NULL,

        -- Segment 유형
        segment_type TEXT DEFAULT 'HAND',  -- HAND, HIGHLIGHT, PE, INTRO

        -- 기본 정보
        title TEXT,
        game_type TEXT DEFAULT 'TOURNAMENT',  -- TOURNAMENT, CASH_GAME
        rating INTEGER,                        -- 0-5

        -- 핸드 결과
        winner TEXT,
        winning_hand TEXT,
        losing_hand TEXT,

        -- 참여자 (JSON)
        players JSON,                  -- [{name, hand, position, is_winner}, ...]

        -- 태그 시스템 (JSON)
        tags_action JSON,              -- [preflop-allin, cooler, ...]
        tags_emotion JSON,             -- [brutal, suckout, ...]
        tags_content JSON,             -- [dirty, outro, hs, ...]
        tags_player JSON,              -- [player names]
        tags_search JSON,              -- [combined searchable tags]

        -- 상황 플래그
        is_cooler INTEGER DEFAULT 0,
        is_badbeat INTEGER DEFAULT 0,
        is_suckout INTEGER DEFAULT 0,
        is_bluff INTEGER DEFAULT 0,
        is_hero_call INTEGER DEFAULT 0,
        is_hero_fold INTEGER DEFAULT 0,
        is_river_killer INTEGER DEFAULT 0,

        -- 올인 정보
        all_in_stage TEXT,             -- preflop, flop, turn, river, none
        pot_size INTEGER,

        -- 출처
        source_sheet TEXT,             -- Google Sheet 이름
        source_row INTEGER,            -- 원본 행 번호

        -- 타임스탬프
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (parent_asset_uuid) REFERENCES assets(asset_uuid)
    )
    """)

    # =========================================================================
    # 3. pokergo_videos 테이블 (PokerGO 영상)
    # =========================================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pokergo_videos (
        -- 식별자
        video_id TEXT PRIMARY KEY,     -- PokerGO video ID
        jwplayer_id TEXT,              -- JWPlayer media ID

        -- 기본 정보
        title TEXT NOT NULL,
        description TEXT,
        thumbnail_url TEXT,

        -- 시간 정보
        duration_sec INTEGER,
        published_at TEXT,

        -- 분류
        brand TEXT,                    -- WSOP, HCL, etc.
        year INTEGER,
        event_number INTEGER,
        season INTEGER,
        episode INTEGER,

        -- 콘텐츠 타입
        content_type TEXT,             -- episode, full_event, highlight
        series_name TEXT,

        -- 다운로드 상태
        download_status TEXT DEFAULT 'pending',  -- pending, downloading, completed, failed
        download_path TEXT,
        downloaded_at TEXT,

        -- 매칭 상태
        nas_matched INTEGER DEFAULT 0,
        matched_asset_uuid TEXT,
        match_confidence REAL,

        -- 메타데이터
        metadata JSON,

        -- 타임스탬프
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (matched_asset_uuid) REFERENCES assets(asset_uuid)
    )
    """)

    # =========================================================================
    # 4. nas_pokergo_matches 테이블 (NAS-PokerGO 매칭)
    # =========================================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nas_pokergo_matches (
        match_id INTEGER PRIMARY KEY AUTOINCREMENT,

        -- 매칭 대상
        asset_uuid TEXT NOT NULL,
        pokergo_video_id TEXT NOT NULL,

        -- 매칭 정보
        match_type TEXT,               -- exact, fuzzy, manual
        match_confidence REAL,         -- 0.0 - 1.0
        match_reason TEXT,             -- 매칭 근거

        -- 검증 상태
        verified INTEGER DEFAULT 0,    -- 수동 검증 여부
        verified_by TEXT,
        verified_at TEXT,

        -- 타임스탬프
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (asset_uuid) REFERENCES assets(asset_uuid),
        FOREIGN KEY (pokergo_video_id) REFERENCES pokergo_videos(video_id),
        UNIQUE(asset_uuid, pokergo_video_id)
    )
    """)

    # =========================================================================
    # 5. scan_history 테이블 (스캔 이력)
    # =========================================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scan_history (
        scan_id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_type TEXT NOT NULL,       -- full, incremental, media_info
        started_at TEXT NOT NULL,
        completed_at TEXT,

        -- 결과
        total_files INTEGER,
        new_files INTEGER,
        modified_files INTEGER,
        errors INTEGER,

        -- 상태
        status TEXT DEFAULT 'running', -- running, completed, failed
        error_message TEXT,

        -- 추가 정보
        scan_path TEXT,
        options JSON
    )
    """)

    # =========================================================================
    # 인덱스 생성
    # =========================================================================
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_assets_brand ON assets(brand)",
        "CREATE INDEX IF NOT EXISTS idx_assets_year ON assets(year)",
        "CREATE INDEX IF NOT EXISTS idx_assets_classification ON assets(classification)",
        "CREATE INDEX IF NOT EXISTS idx_assets_pokergo_matched ON assets(pokergo_matched)",
        "CREATE INDEX IF NOT EXISTS idx_assets_file_name ON assets(file_name)",

        "CREATE INDEX IF NOT EXISTS idx_segments_parent ON segments(parent_asset_uuid)",
        "CREATE INDEX IF NOT EXISTS idx_segments_type ON segments(segment_type)",
        "CREATE INDEX IF NOT EXISTS idx_segments_time ON segments(time_in_sec, time_out_sec)",

        "CREATE INDEX IF NOT EXISTS idx_pokergo_brand ON pokergo_videos(brand)",
        "CREATE INDEX IF NOT EXISTS idx_pokergo_year ON pokergo_videos(year)",
        "CREATE INDEX IF NOT EXISTS idx_pokergo_matched ON pokergo_videos(nas_matched)",

        "CREATE INDEX IF NOT EXISTS idx_matches_asset ON nas_pokergo_matches(asset_uuid)",
        "CREATE INDEX IF NOT EXISTS idx_matches_pokergo ON nas_pokergo_matches(pokergo_video_id)",
    ]

    for idx_sql in indexes:
        cursor.execute(idx_sql)

    conn.commit()
    conn.close()

    print(f"[OK] UDM Unified DB created: {UNIFIED_DB}")
    print("\nTables:")
    print("  - assets (NAS files)")
    print("  - segments (hands/clips)")
    print("  - pokergo_videos (PokerGO videos)")
    print("  - nas_pokergo_matches (match info)")
    print("  - scan_history (scan history)")


def verify_schema():
    """스키마 검증"""
    conn = sqlite3.connect(str(UNIFIED_DB))
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]

    print(f"\nUnified DB Tables ({len(tables)}):")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  - {table}: {count} rows")

    conn.close()


if __name__ == "__main__":
    create_unified_db()
    verify_schema()
