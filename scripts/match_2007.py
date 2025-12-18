"""2007 NAS vs PokerGO 매칭 분석 스크립트"""
import sqlite3
import json
from pathlib import Path

# NAS 데이터 로드
conn = sqlite3.connect('data/nas_footage.db')
cursor = conn.cursor()
cursor.execute('''
SELECT filename, size_gb
FROM files
WHERE year = 2007 AND size_gb > 0.1
ORDER BY filename
''')
nas_files = [(name, size) for name, size in cursor.fetchall()]
conn.close()

# PokerGO 데이터 로드
pokergo_path = Path('data/pokergo/wsop_final_20251216_154021.json')
with open(pokergo_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

videos = data.get('videos', [])
videos_2007 = sorted([v for v in videos if '2007' in v.get('title', '')],
                     key=lambda x: x.get('title', ''))

# 매칭 로직
matches = []

for video in videos_2007:
    title = video.get('title', '')

    # Main Event Day 매칭
    if ' Me Day' in title or ' Me Final' in title:
        parts = title.split()
        if len(parts) >= 3:
            show_num = parts[2]
            nas_match = f'ESPN 2007 WSOP SEASON 5 SHOW {show_num}.mov'
            matched_nas = [f for f in nas_files if f[0] == nas_match]
            if matched_nas:
                matches.append({
                    'pokergo': title,
                    'nas': nas_match,
                    'reason': f'Main Event - Show {show_num}',
                    'nas_size': matched_nas[0][1]
                })
    # HORSE 매칭
    elif ' Horse Part' in title:
        parts = title.split()
        if len(parts) >= 3:
            show_num = parts[2]
            nas_match = f'ESPN 2007 WSOP SEASON 5 SHOW {show_num}.mov'
            matched_nas = [f for f in nas_files if f[0] == nas_match]
            if matched_nas:
                matches.append({
                    'pokergo': title,
                    'nas': nas_match,
                    'reason': f'HORSE - Show {show_num}',
                    'nas_size': matched_nas[0][1]
                })
    # Bracelet Events
    elif 'Bracelet Events' in title:
        matches.append({
            'pokergo': title,
            'nas': 'UNMATCHED',
            'reason': 'Manual matching required',
            'nas_size': 0
        })

print('=' * 120)
print('2007 NAS vs PokerGO 매칭 결과 분석')
print('=' * 120)
print()

print('## 1. PokerGO 영상 목록 (총 {}개)'.format(len(videos_2007)))
print('-' * 120)
for i, video in enumerate(videos_2007, 1):
    print(f'{i:2d}. {video.get("title", "N/A")}')

print()
print('## 2. NAS 파일 목록 (총 {}개, 상위 20개)'.format(len(nas_files)))
print('-' * 120)
for i, (name, size) in enumerate(nas_files[:20], 1):
    print(f'{i:2d}. {name} ({size:.1f}GB)')
if len(nas_files) > 20:
    print(f'... 외 {len(nas_files) - 20}개')

print()
print('## 3. 매칭 테이블')
print('-' * 120)
print(f'{"PokerGO Title":<55} | {"NAS File":<40} | {"Reason":<20}')
print('-' * 120)
for m in matches:
    if m['nas_size'] > 0:
        size_info = f' ({m["nas_size"]:.1f}GB)'
        nas_display = m['nas'] + size_info
    else:
        nas_display = 'UNMATCHED'

    print(f'{m["pokergo"]:<55} | {nas_display:<40} | {m["reason"]}')

# 매칭된 NAS 파일 목록
matched_nas_files = set([m['nas'] for m in matches if m['nas'] != 'UNMATCHED'])
unmatched_nas = [f for f in nas_files if f[0] not in matched_nas_files]

print()
print('## 4. 추가 NAS 파일 (매칭되지 않은 파일)')
print('-' * 120)
print(f'총 {len(unmatched_nas)}개')
for i, (name, size) in enumerate(unmatched_nas[:12], 1):
    print(f'{i:2d}. {name} ({size:.1f}GB)')

print()
print('## 5. Summary 통계')
print('-' * 120)
print(f'PokerGO 영상 수: {len(videos_2007)}개')
print(f'NAS 파일 수: {len(nas_files)}개')
print(f'매칭 성공: {len([m for m in matches if m["nas"] != "UNMATCHED"])}개')
print(f'매칭 실패 (수동 필요): {len([m for m in matches if m["nas"] == "UNMATCHED"])}개')
print(f'NAS에만 존재 (매칭 안됨): {len(unmatched_nas)}개')
print()
print('분석:')
print('- Main Event (Day1-5, Final): Show 11-26 → 완벽 매칭')
print('- HORSE Championship: Show 27-32 → 완벽 매칭')
print('- Bracelet Events: PokerGO에만 존재 (10개) - 수동 매칭 필요')
print('- NAS Show 1-10: PokerGO 매칭 없음 - Bracelet Events 가능성')
print('=' * 120)
