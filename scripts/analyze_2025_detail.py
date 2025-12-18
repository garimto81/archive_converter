"""2025년 미매칭 상세 분석"""
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(r"D:\AI\claude01\Archive_Converter")
UNIFIED_DB = PROJECT_ROOT / "data" / "unified_archive.db"
POKERGO_DB = PROJECT_ROOT / "data" / "pokergo" / "pokergo.db"

conn = sqlite3.connect(str(UNIFIED_DB))
conn.row_factory = sqlite3.Row

# PokerGO 원본 DB 연결
pg_conn = sqlite3.connect(str(POKERGO_DB))
pg_conn.row_factory = sqlite3.Row

c = conn.cursor()
pg_c = pg_conn.cursor()

print("=" * 100)
print("2025 NAS Unmatched Files - Detail Analysis")
print("=" * 100)

# NAS 미매칭 파일 상세 분석
c.execute("""
    SELECT file_name, relative_path, folder_path, size_bytes, size_gb, brand, asset_type
    FROM assets
    WHERE year = 2025 AND brand = 'WSOP' AND pokergo_matched = 0
    ORDER BY relative_path, file_name
""")

unmatched_nas = c.fetchall()

# 카테고리별 분류
categories = {
    "WSOP_CIRCUIT_CYPRUS": [],
    "WSOPE": [],
    "HYPERDECK_RAW": [],
    "EMOJI_FILES": [],
    "OTHER": []
}

for row in unmatched_nas:
    fname = row['file_name']
    path = row['relative_path'] or ""
    size_gb = row['size_gb'] or 0

    if "Circuit" in fname or "Circuit" in path or "Cyprus" in fname:
        categories["WSOP_CIRCUIT_CYPRUS"].append(row)
    elif "WSOPE" in fname or "WSOPE" in path:
        categories["WSOPE"].append(row)
    elif "HyperDeck" in fname:
        categories["HYPERDECK_RAW"].append(row)
    elif any(ord(c) > 127 for c in fname[:5]):  # 이모지/특수문자
        categories["EMOJI_FILES"].append(row)
    else:
        categories["OTHER"].append(row)

# 1. WSOP Circuit Cyprus
print("\n" + "=" * 100)
print("[1] WSOP Circuit Cyprus - PokerGO 없음, 수동 입력 필요")
print("=" * 100)
for row in categories["WSOP_CIRCUIT_CYPRUS"]:
    print(f"  Path: {row['relative_path']}")
    print(f"  File: {row['file_name']}")
    print(f"  Size: {row['size_gb']:.2f} GB")
    print()

# 2. WSOPE
print("\n" + "=" * 100)
print("[2] WSOPE (Europe) - PokerGO 없음, 수동 입력 필요")
print("=" * 100)
for row in categories["WSOPE"]:
    print(f"  Path: {row['relative_path']}")
    print(f"  File: {row['file_name']}")
    print(f"  Size: {row['size_gb']:.2f} GB")
    print()

# 3. HyperDeck RAW
print("\n" + "=" * 100)
print("[3] HyperDeck RAW - 경로 기반 분석 필요")
print("=" * 100)
hyperdeck_by_path = {}
for row in categories["HYPERDECK_RAW"]:
    path = row['folder_path'] or "unknown"
    if path not in hyperdeck_by_path:
        hyperdeck_by_path[path] = []
    hyperdeck_by_path[path].append(row)

for path, files in hyperdeck_by_path.items():
    print(f"\n  Folder: {path}")
    print(f"  Files: {len(files)}")
    total_size = sum(f['size_gb'] or 0 for f in files)
    print(f"  Total Size: {total_size:.2f} GB")
    for f in files[:5]:  # 처음 5개만
        print(f"    - {f['file_name']} ({f['size_gb']:.2f} GB)")
    if len(files) > 5:
        print(f"    ... and {len(files)-5} more")

# 4. Emoji Files
print("\n" + "=" * 100)
print("[4] Emoji/Special Char Files - 경로 기반 분석 필요")
print("=" * 100)
for row in categories["EMOJI_FILES"]:
    print(f"  Path: {row['relative_path']}")
    print(f"  File: {row['file_name']}")
    print(f"  Size: {row['size_gb']:.2f} GB")
    print()

# 5. Other
if categories["OTHER"]:
    print("\n" + "=" * 100)
    print("[5] Other Unmatched")
    print("=" * 100)
    for row in categories["OTHER"]:
        print(f"  Path: {row['relative_path']}")
        print(f"  File: {row['file_name']}")
        print(f"  Size: {row['size_gb']:.2f} GB")
        print()

# PokerGO 메타데이터 분석
print("\n" + "=" * 100)
print("2025 PokerGO Metadata Analysis")
print("=" * 100)

# 원본 PokerGO DB에서 show(collection), season 확인
pg_c.execute("""
    SELECT DISTINCT show, season, year
    FROM videos
    WHERE year = 2025
    ORDER BY show, season
""")

print("\nPokerGO Collections (2025):")
for row in pg_c.fetchall():
    print(f"  Show: {row['show']}, Season: {row['season']}, Year: {row['year']}")

# 미매칭 PokerGO 상세
print("\n" + "=" * 100)
print("PokerGO Unmatched Videos - by Collection")
print("=" * 100)

c.execute("""
    SELECT video_id, title, metadata
    FROM pokergo_videos
    WHERE year = 2025 AND nas_matched = 0
""")

unmatched_pg = c.fetchall()

# metadata에서 show 추출
pg_by_show = {}
for row in unmatched_pg:
    metadata = json.loads(row['metadata']) if row['metadata'] else {}
    show = metadata.get('show', 'Unknown')
    season = metadata.get('season', 'Unknown')
    key = f"{show} (S{season})"
    if key not in pg_by_show:
        pg_by_show[key] = []
    pg_by_show[key].append(row)

for show, videos in sorted(pg_by_show.items()):
    print(f"\n{show}: {len(videos)} videos")
    for v in videos[:3]:
        print(f"  - {v['title'][:70]}")
    if len(videos) > 3:
        print(f"  ... and {len(videos)-3} more")

# Summary
print("\n" + "=" * 100)
print("Summary")
print("=" * 100)
print(f"\nNAS Unmatched by Category:")
for cat, files in categories.items():
    if files:
        total_size = sum(f['size_gb'] or 0 for f in files)
        print(f"  {cat}: {len(files)} files ({total_size:.2f} GB)")

print(f"\nPokerGO Unmatched by Collection:")
for show, videos in sorted(pg_by_show.items()):
    print(f"  {show}: {len(videos)} videos")

conn.close()
pg_conn.close()
