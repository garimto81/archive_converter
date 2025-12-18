"""매칭 로직 디버깅"""

import json
import sqlite3
from pathlib import Path
import re

BASE_DIR = Path(r"D:\AI\claude01\Archive_Converter")
NAS_DB = BASE_DIR / "data" / "nas_footage.db"
POKERGO_JSON = BASE_DIR / "data" / "pokergo" / "wsop_final_20251216_154021.json"


def extract_episode_number(text: str) -> int | None:
    patterns = [
        r'Wsop\s+2008\s+(\d+)',
        r'WSOP_2008_(\d+)',
        r'Episode\s+(\d+)',
        r'Show\s+(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def is_europe(text: str) -> bool:
    return bool(re.search(r'europe|wsope', text, re.IGNORECASE))


# PokerGO Europe 영상 1개만
with open(POKERGO_JSON, 'r', encoding='utf-8') as f:
    data = json.load(f)

pg_europe_1 = None
for item in data['videos']:
    if item.get('year') == 2008 and 'Europe' in item.get('title', ''):
        title = item['title']
        if 'Episode 1' in title:
            pg_europe_1 = {
                'title': title,
                'episode': extract_episode_number(title),
                'is_europe': is_europe(title)
            }
            break

print("PokerGO Europe Episode 1:")
print(f"  {pg_europe_1}")
print()

# NAS WSOPE 파일들
conn = sqlite3.connect(NAS_DB)
cursor = conn.cursor()
cursor.execute("SELECT filename FROM files WHERE year = 2008")
rows = cursor.fetchall()
conn.close()

nas_files = []
for (filename,) in rows:
    if 'WSOPE' in filename and not filename.startswith('._'):
        nas_files.append({
            'file_name': filename,
            'episode': extract_episode_number(filename),
            'is_europe': is_europe(filename)
        })

print("NAS WSOPE 파일들:")
for nas in nas_files[:3]:
    print(f"  {nas}")
print()

# 매칭 시도
print("매칭 시도:")
for nas in nas_files:
    print(f"\nNAS: {nas['file_name']}")
    print(f"  is_europe: {nas['is_europe']}")
    print(f"  episode: {nas['episode']}")

    # 조건 체크
    print(f"  PG is_europe: {pg_europe_1['is_europe']}")
    print(f"  PG episode: {pg_europe_1['episode']}")

    if pg_europe_1['is_europe'] and nas['is_europe']:
        print("  ✓ 둘 다 Europe")
        if pg_europe_1['episode'] and nas['episode']:
            print(f"  ✓ 에피소드 존재: PG={pg_europe_1['episode']}, NAS={nas['episode']}")
            if pg_europe_1['episode'] == nas['episode']:
                print("  ✓✓✓ 매칭 성공!")
            else:
                print(f"  ✗ 에피소드 불일치")
        else:
            print("  ✗ 에피소드 누락")
    else:
        print("  ✗ Europe 조건 불일치")
