"""
PokerGO 데이터 마이그레이션 스크립트

기존 pokergo.db의 videos 테이블 데이터를
unified_archive.db의 pokergo_videos 테이블로 마이그레이션
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(r"D:\AI\claude01\Archive_Converter")
DATA_DIR = PROJECT_ROOT / "data"

# 소스 DB
POKERGO_DB = DATA_DIR / "pokergo" / "pokergo.db"

# 대상 DB
UNIFIED_DB = DATA_DIR / "unified_archive.db"


def migrate_pokergo():
    """PokerGO 데이터 마이그레이션"""

    print("=" * 60)
    print("PokerGO Data Migration")
    print("=" * 60)

    if not POKERGO_DB.exists():
        print(f"[ERROR] Source DB not found: {POKERGO_DB}")
        return

    # 소스 DB 연결
    src_conn = sqlite3.connect(str(POKERGO_DB))
    src_conn.row_factory = sqlite3.Row
    src_cursor = src_conn.cursor()

    # 대상 DB 연결
    dst_conn = sqlite3.connect(str(UNIFIED_DB))
    dst_cursor = dst_conn.cursor()

    # 기존 데이터 삭제
    dst_cursor.execute("DELETE FROM pokergo_videos")
    deleted = dst_cursor.rowcount
    print(f"Deleted existing pokergo_videos: {deleted} rows")

    # 소스 테이블 스키마 확인
    src_cursor.execute("PRAGMA table_info(videos)")
    src_columns = [col[1] for col in src_cursor.fetchall()]
    print(f"Source columns: {src_columns}")

    # 데이터 조회
    src_cursor.execute("SELECT * FROM videos")
    rows = src_cursor.fetchall()

    print(f"Migrating {len(rows)} videos...")

    migrated = 0
    errors = 0

    for row in rows:
        try:
            # 컬럼 매핑
            video_data = dict(row)

            # 브랜드 추론
            title = video_data.get("title", "") or ""
            brand = infer_brand_from_title(title)

            # 연도 추론
            year = extract_year_from_title(title)

            # 통합 DB에 삽입
            dst_cursor.execute("""
                INSERT INTO pokergo_videos (
                    video_id, jwplayer_id, title, description, thumbnail_url,
                    duration_sec, published_at, brand, year,
                    content_type, series_name, download_status,
                    metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                video_data.get("video_id") or video_data.get("id"),
                video_data.get("jwplayer_id"),
                video_data.get("title"),
                video_data.get("description"),
                video_data.get("thumbnail_url") or video_data.get("thumbnail"),
                video_data.get("duration") or video_data.get("duration_sec"),
                video_data.get("published_at") or video_data.get("created_at"),
                brand,
                year,
                video_data.get("content_type"),
                video_data.get("series_name") or video_data.get("series"),
                video_data.get("download_status", "pending"),
                json.dumps(video_data, ensure_ascii=False, default=str),
                datetime.now().isoformat()
            ))

            migrated += 1

        except Exception as e:
            errors += 1
            print(f"[WARN] Migration error: {e}")

    dst_conn.commit()

    print("\n" + "=" * 60)
    print("Migration Complete!")
    print("=" * 60)
    print(f"Migrated: {migrated}")
    print(f"Errors: {errors}")

    # 통계 확인
    dst_cursor.execute("""
        SELECT brand, COUNT(*) as cnt
        FROM pokergo_videos
        GROUP BY brand
        ORDER BY cnt DESC
    """)
    print("\nBrand Statistics:")
    for row in dst_cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    src_conn.close()
    dst_conn.close()


def infer_brand_from_title(title: str) -> str:
    """제목에서 브랜드 추론"""
    title_upper = title.upper()

    brand_patterns = {
        "WSOP": ["WSOP", "WORLD SERIES OF POKER", "BRACELET"],
        "HCL": ["HCL", "HUSTLER CASINO LIVE", "HUSTLER"],
        "PAD": ["PAD", "POKER AFTER DARK"],
        "GGMillions": ["GGMILLIONS", "GGM", "GG MILLIONS"],
        "MPP": ["MPP", "MALTA POKER PARTY"],
        "GOG": ["GOG", "GAME OF GOLD"],
        "WPT": ["WPT", "WORLD POKER TOUR"],
        "EPT": ["EPT", "EUROPEAN POKER TOUR"],
    }

    for brand, patterns in brand_patterns.items():
        for pattern in patterns:
            if pattern in title_upper:
                return brand

    return "OTHER"


def extract_year_from_title(title: str) -> int | None:
    """제목에서 연도 추출"""
    import re

    # 4자리 연도 패턴 (2000-2030)
    year_match = re.search(r"(20[0-3]\d)", title)
    if year_match:
        return int(year_match.group(1))

    return None


if __name__ == "__main__":
    migrate_pokergo()
