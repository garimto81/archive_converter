"""WSOPE 2008 매칭 디버깅"""

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
        r'Episode\s+(\d+)',
        r'WSOPE08_Episode_(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def is_europe(text: str) -> bool:
    return bool(re.search(r'europe|wsope', text, re.IGNORECASE))


# PokerGO Europe 영상
with open(POKERGO_JSON, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("PokerGO Europe 2008 영상:")
for item in data['videos']:
    year = item.get('year')
    title = item.get('title', '')
    # year는 정수로 저장됨
    if year == 2008 or '2008' in str(title):
        if 'Europe' in title or 'WSOPE' in title:
            ep = extract_episode_number(title)
            print(f"  Title: {title}")
            print(f"    - year type: {type(year)}, value: {year}")
            print(f"    - is_europe: {is_europe(title)}")
            print(f"    - episode: {ep}")
            print()

# NAS WSOPE 파일
conn = sqlite3.connect(NAS_DB)
cursor = conn.cursor()
cursor.execute("SELECT filename FROM files WHERE year = 2008 AND (filename LIKE '%WSOPE%' OR filename LIKE '%Europe%')")
rows = cursor.fetchall()
conn.close()

print("\nNAS WSOPE 파일:")
for (filename,) in rows:
    if not filename.startswith('._'):
        ep = extract_episode_number(filename)
        print(f"  File: {filename}")
        print(f"    - is_europe: {is_europe(filename)}")
        print(f"    - episode: {ep}")
        print()
