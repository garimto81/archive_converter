"""
2008년 NAS vs PokerGO 매칭 분석 스크립트
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Tuple
import re

# 경로 설정
BASE_DIR = Path(r"D:\AI\claude01\Archive_Converter")
NAS_DB = BASE_DIR / "data" / "nas_footage.db"
POKERGO_JSON = BASE_DIR / "data" / "pokergo" / "wsop_final_20251216_154021.json"


def extract_episode_number(text: str) -> int | None:
    """에피소드 번호 추출 (Show 1, Show 2, EP01 등)"""
    patterns = [
        r'Wsop\s+2008\s+(\d+)',  # PokerGO 제목 앞부분 숫자 (Wsop 2008 09)
        r'WSOP_2008_(\d+)',  # NAS 파일 (WSOP_2008_09.mp4)
        r'WSOPE08_Episode_(\d+)',  # WSOPE08_Episode_1_H264.mov
        r'Episode\s+(\d+)',  # Episode 1
        r'Show\s+(\d+)',  # ESPN SHOW
        r'EP\s*(\d+)',
        r'Ep\s*(\d+)',
        r'Day\s+(\d+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def extract_event_number(text: str) -> int | None:
    """이벤트 번호 추출 (Event #1, ev-01 등)"""
    patterns = [
        r'Event\s+#?(\d+)',
        r'ev-(\d+)',
        r'EV(\d+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def is_main_event(text: str) -> bool:
    """Main Event 여부 확인"""
    return bool(re.search(r'main\s*event|ME', text, re.IGNORECASE))


def is_horse(text: str) -> bool:
    """HORSE 이벤트 여부 확인"""
    return bool(re.search(r'horse|50k', text, re.IGNORECASE))


def is_europe(text: str) -> bool:
    """Europe 이벤트 여부 확인"""
    return bool(re.search(r'europe|wsope', text, re.IGNORECASE))


def load_pokergo_2008() -> List[Dict]:
    """PokerGO 2008 영상 로드"""
    with open(POKERGO_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    videos_2008 = []
    for item in data.get('videos', []):
        title = item.get('title', '')
        year = item.get('year')
        # year는 정수로 저장됨
        if year == 2008 or '2008' in str(title):
            videos_2008.append({
                'title': title,
                'episode': extract_episode_number(title),
                'event': extract_event_number(title),
                'is_main': is_main_event(title),
                'is_horse': is_horse(title),
                'is_europe': is_europe(title),
            })

    return sorted(videos_2008, key=lambda x: x['title'])


def load_nas_2008() -> List[Dict]:
    """NAS 2008 파일 로드"""
    conn = sqlite3.connect(NAS_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT filename, size_bytes, size_gb
        FROM files
        WHERE year = 2008
        ORDER BY filename
    """)

    rows = cursor.fetchall()
    conn.close()

    files = []
    for filename, size_bytes, size_gb in rows:
        files.append({
            'file_name': filename,
            'duration_sec': None,  # DB에 duration 컬럼 없음
            'file_size_gb': size_gb,
            'episode': extract_episode_number(filename),
            'event': extract_event_number(filename),
            'is_main': is_main_event(filename),
            'is_horse': is_horse(filename),
            'is_europe': is_europe(filename),
        })

    return files


def match_videos(pokergo_list: List[Dict], nas_list: List[Dict]) -> List[Tuple[Dict, Dict, str]]:
    """PokerGO와 NAS 매칭"""
    matches = []
    used_nas_files = set()

    # Europe 먼저 매칭
    for pg in [v for v in pokergo_list if v['is_europe']]:
        for nas in nas_list:
            if nas['file_name'] in used_nas_files:
                continue
            if nas['file_name'].startswith('._'):
                continue

            if nas['is_europe'] and pg['episode'] and nas['episode'] and pg['episode'] == nas['episode']:
                matches.append((pg, nas, f"WSOPE Episode {pg['episode']}"))
                used_nas_files.add(nas['file_name'])
                break

    # 일반 WSOP 매칭
    for pg in [v for v in pokergo_list if not v['is_europe']]:
        best_match = None
        best_reason = ""

        for nas in nas_list:
            if nas['file_name'] in used_nas_files:
                continue
            if nas['file_name'].startswith('._'):
                continue
            if nas['is_europe']:  # Europe 파일은 건너뛰기
                continue

            reasons = []

            # Episode 번호 매칭
            if pg['episode'] and nas['episode'] and pg['episode'] == nas['episode']:
                # Main Event 구분
                if pg['is_main']:
                    reasons.append(f"Main Event Episode {pg['episode']}")
                # HORSE 구분
                elif pg['is_horse']:
                    reasons.append(f"50K HORSE Episode {pg['episode']}")
                # 일반 Bracelet Event
                else:
                    reasons.append(f"WSOP 2008 Episode {pg['episode']}")

            # Event 번호 매칭
            if pg['event'] and nas['event'] and pg['event'] == nas['event']:
                reasons.append(f"Event #{pg['event']}")

            if reasons:
                reason_str = ", ".join(reasons)
                if not best_match or len(reasons) > len(best_reason.split(", ")):
                    best_match = nas
                    best_reason = reason_str

        if best_match:
            matches.append((pg, best_match, best_reason))
            used_nas_files.add(best_match['file_name'])

    return matches


def print_analysis(output_file=None):
    """분석 결과 출력"""
    import sys

    # 파일 출력 설정
    if output_file:
        f = open(output_file, 'w', encoding='utf-8')
        original_stdout = sys.stdout
        sys.stdout = f

    print("=" * 100)
    print("2008년 NAS vs PokerGO 매칭 분석")
    print("=" * 100)
    print()

    # 데이터 로드
    pokergo_videos = load_pokergo_2008()
    nas_files = load_nas_2008()

    print(f"[데이터 소스]")
    print(f"- NAS DB: {NAS_DB}")
    print(f"- PokerGO JSON: {POKERGO_JSON}")
    print()

    # 1. PokerGO 영상 목록
    print("[1. PokerGO 영상 목록]")
    print(f"총 {len(pokergo_videos)}개")
    print("-" * 100)
    for i, video in enumerate(pokergo_videos, 1):
        print(f"{i:2d}. {video['title']}")
    print()

    # 2. NAS 파일 목록 (상위 20개)
    print("[2. NAS 파일 목록]")
    print(f"총 {len(nas_files)}개 (상위 20개만 표시)")
    print("-" * 100)
    for i, file in enumerate(nas_files[:20], 1):
        size = f"{file['file_size_gb']:.2f}GB" if file['file_size_gb'] else 'N/A'
        print(f"{i:2d}. {file['file_name']:80s} ({size})")

    if len(nas_files) > 20:
        print(f"... (나머지 {len(nas_files) - 20}개)")
    print()

    # 3. 매칭 테이블
    matches = match_videos(pokergo_videos, nas_files)

    print("[3. 매칭 테이블]")
    print(f"총 {len(matches)}개 매칭")
    print("-" * 100)
    print(f"{'PokerGO Title':<60s} | {'NAS File':<60s} | {'매칭 근거':<30s}")
    print("-" * 100)

    # PokerGO 제목 순으로 정렬
    sorted_matches = sorted(matches, key=lambda x: x[0]['title'])

    for pg, nas, reason in sorted_matches:
        print(f"{pg['title']:<60s} | {nas['file_name']:<60s} | {reason:<30s}")

    if not matches:
        print("(매칭된 항목 없음)")
    print()

    # 4. 매칭 안 된 항목
    matched_pg = {m[0]['title'] for m in matches}
    matched_nas = {m[1]['file_name'] for m in matches}

    unmatched_pg = [v for v in pokergo_videos if v['title'] not in matched_pg]
    unmatched_nas = [f for f in nas_files if f['file_name'] not in matched_nas]

    print("[4. 매칭 안 된 항목]")
    print(f"- PokerGO: {len(unmatched_pg)}개")
    for video in unmatched_pg:
        print(f"  • {video['title']}")

    print()
    print(f"- NAS: {len(unmatched_nas)}개")
    for file in unmatched_nas:
        print(f"  • {file['file_name']}")
    print()

    # 5. Summary 통계
    print("[5. Summary 통계]")
    print("-" * 100)
    print(f"{'항목':<30s} | {'개수':<10s} | {'비율':<10s}")
    print("-" * 100)
    print(f"{'PokerGO 총 영상':<30s} | {len(pokergo_videos):<10d} | {'':<10s}")
    print(f"{'NAS 총 파일':<30s} | {len(nas_files):<10d} | {'':<10s}")
    print(f"{'매칭 성공':<30s} | {len(matches):<10d} | {f'{len(matches)/len(pokergo_videos)*100:.1f}%':<10s}")
    print(f"{'PokerGO 미매칭':<30s} | {len(unmatched_pg):<10d} | {f'{len(unmatched_pg)/len(pokergo_videos)*100:.1f}%':<10s}")
    print(f"{'NAS 미매칭':<30s} | {len(unmatched_nas):<10d} | {f'{len(unmatched_nas)/len(nas_files)*100:.1f}%':<10s}")
    print()

    # 카테고리별 통계
    pg_main = sum(1 for v in pokergo_videos if v['is_main'])
    pg_horse = sum(1 for v in pokergo_videos if v['is_horse'])
    pg_europe = sum(1 for v in pokergo_videos if v['is_europe'])

    nas_main = sum(1 for f in nas_files if f['is_main'])
    nas_horse = sum(1 for f in nas_files if f['is_horse'])
    nas_europe = sum(1 for f in nas_files if f['is_europe'])

    print("[카테고리별 통계]")
    print(f"{'카테고리':<30s} | {'PokerGO':<10s} | {'NAS':<10s}")
    print("-" * 100)
    print(f"{'Main Event':<30s} | {pg_main:<10d} | {nas_main:<10d}")
    print(f"{'50K HORSE':<30s} | {pg_horse:<10d} | {nas_horse:<10d}")
    print(f"{'Europe':<30s} | {pg_europe:<10d} | {nas_europe:<10d}")
    print()

    print("=" * 100)
    print("분석 완료")
    print("=" * 100)

    # 파일 출력 종료
    if output_file:
        sys.stdout = original_stdout
        f.close()
        print(f"분석 결과가 저장되었습니다: {output_file}")


if __name__ == "__main__":
    output_path = Path(r"D:\AI\claude01\Archive_Converter\data\2008_matching_analysis.txt")
    print_analysis(str(output_path))
