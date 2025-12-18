"""2025년 매칭/미매칭 리스트 리포트"""
import sqlite3
import sys
from pathlib import Path

# Windows 인코딩 문제 해결
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(r"D:\AI\claude01\Archive_Converter")
UNIFIED_DB = PROJECT_ROOT / "data" / "unified_archive.db"

conn = sqlite3.connect(str(UNIFIED_DB))
conn.row_factory = sqlite3.Row
c = conn.cursor()

# 2025년 통계
print("=" * 80)
print("2025 NAS-PokerGO Matching Report")
print("=" * 80)

# NAS 2025 통계
c.execute("SELECT COUNT(*) FROM assets WHERE year = 2025 AND brand = 'WSOP'")
nas_total = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM assets WHERE year = 2025 AND brand = 'WSOP' AND pokergo_matched = 1")
nas_matched = c.fetchone()[0]

# PokerGO 2025 통계
c.execute("SELECT COUNT(*) FROM pokergo_videos WHERE year = 2025")
pg_total = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM pokergo_videos WHERE year = 2025 AND nas_matched = 1")
pg_matched = c.fetchone()[0]

print(f"\nNAS 2025: {nas_matched}/{nas_total} matched ({100*nas_matched/nas_total:.1f}%)")
print(f"PokerGO 2025: {pg_matched}/{pg_total} matched ({100*pg_matched/pg_total:.1f}%)")

# ========== 매칭된 NAS 파일 ==========
print("\n" + "=" * 80)
print("[MATCHED] NAS Files (2025)")
print("=" * 80)
c.execute("""
    SELECT a.file_name, p.title, m.match_type, m.match_confidence
    FROM nas_pokergo_matches m
    JOIN assets a ON m.asset_uuid = a.asset_uuid
    JOIN pokergo_videos p ON m.pokergo_video_id = p.video_id
    WHERE a.year = 2025
    ORDER BY m.match_confidence DESC
""")
for i, row in enumerate(c.fetchall(), 1):
    conf = row['match_confidence']
    mtype = row['match_type'][:3].upper()
    print(f"{i:2d}. [{mtype} {conf:.0%}] {row['file_name'][:50]}")
    print(f"    -> {row['title'][:60]}")

# ========== 미매칭 NAS 파일 ==========
print("\n" + "=" * 80)
print("[UNMATCHED] NAS Files (2025)")
print("=" * 80)
c.execute("""
    SELECT file_name, relative_path
    FROM assets
    WHERE year = 2025 AND brand = 'WSOP' AND pokergo_matched = 0
    ORDER BY file_name
""")
unmatched_nas = c.fetchall()
for i, row in enumerate(unmatched_nas, 1):
    print(f"{i:2d}. {row['file_name'][:70]}")

# ========== 미매칭 PokerGO 영상 ==========
print("\n" + "=" * 80)
print("[UNMATCHED] PokerGO Videos (2025)")
print("=" * 80)
c.execute("""
    SELECT title, video_id
    FROM pokergo_videos
    WHERE year = 2025 AND nas_matched = 0
    ORDER BY title
""")
unmatched_pg = c.fetchall()
for i, row in enumerate(unmatched_pg, 1):
    print(f"{i:2d}. {row['title'][:70]}")

print("\n" + "=" * 80)
print("Summary")
print("=" * 80)
print(f"NAS Unmatched: {len(unmatched_nas)}")
print(f"PokerGO Unmatched: {len(unmatched_pg)}")

conn.close()
