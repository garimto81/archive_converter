"""
2004년 NAS vs PokerGO 매칭 분석 스크립트
"""

import json
import sqlite3
import re
from pathlib import Path
from typing import List, Dict, Tuple

# Paths
BASE_DIR = Path(__file__).parent.parent
NAS_DB = BASE_DIR / "data" / "nas_footage.db"
POKERGO_JSON = BASE_DIR / "data" / "pokergo" / "wsop_final_20251216_154021.json"


def load_pokergo_2004(json_path: Path) -> List[Dict]:
    """PokerGO JSON에서 2004년 데이터 추출"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # videos 리스트 추출
    videos = data.get('videos', [])

    # 2004년 데이터 필터링
    videos_2004 = [v for v in videos if v.get('year') == '2004' or '2004' in v.get('title', '')]

    return sorted(videos_2004, key=lambda x: x.get('title', ''))


def load_nas_2004(db_path: Path) -> List[Dict]:
    """NAS DB에서 2004년 파일 추출"""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("""
        SELECT filename, size_gb, folder, path
        FROM files
        WHERE year = 2004 AND filename NOT LIKE '._%'
        ORDER BY filename
    """)

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            'file_name': row[0],
            'size_mb': row[1] * 1024 if row[1] else 0,  # GB to MB
            'duration_minutes': 0,  # duration not available in DB
            'folder_path': row[2]
        }
        for row in rows
    ]


def extract_event_number(text: str) -> str:
    """이벤트 번호 추출 (01, 02, 03 등)"""
    # Event 01, EV 01, EV#1, Episode 1, Show 1 등
    patterns = [
        r'show[_\s-]+(\d+)',  # "Show 1", "Show 13" 등
        r'event[_\s-]*#?(\d+)',
        r'ev[_\s-]*#?(\d+)',
        r'episode[_\s-]*(\d+)',
        r'\bday[_\s-]*(\d+)',
        r'\s(\d{2})\s',  # " 01 ", " 02 " 형식
    ]

    text_lower = text.lower()

    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            num = match.group(1)
            return num.zfill(2)  # 01, 02 형식으로 변환

    return None


def is_main_event(text: str) -> bool:
    """Main Event 여부 확인"""
    text_lower = text.lower()
    return 'main event' in text_lower or ' me ' in text_lower or text_lower.startswith('me ')


def extract_main_event_day(text: str) -> str:
    """Main Event Day 번호 추출"""
    text_lower = text.lower()

    # "ME 01", "ME 09" 형식
    match = re.search(r'\bme\s+(\d+)', text_lower)
    if match:
        return match.group(1).zfill(2)

    # "Day 1A", "Day 2", "Day 6 Part 1" 형식
    match = re.search(r'day\s+(\d+)', text_lower)
    if match:
        return match.group(1).zfill(2)

    return None


def is_toc(text: str) -> bool:
    """TOC (Tournament of Champions) 여부 확인"""
    text_lower = text.lower()
    return 'toc' in text_lower or 'tournament of champ' in text_lower or 'tounament of champ' in text_lower  # typo도 포함


def match_videos(pokergo_list: List[Dict], nas_list: List[Dict]) -> List[Dict]:
    """PokerGO 영상과 NAS 파일 매칭"""
    matches = []

    for pg in pokergo_list:
        pg_title = pg.get('title', '')
        pg_event_num = extract_event_number(pg_title)
        pg_is_me = is_main_event(pg_title)
        pg_is_toc = is_toc(pg_title)
        pg_me_day = extract_main_event_day(pg_title) if pg_is_me else None

        matched_nas = []

        for nas in nas_list:
            nas_name = nas['file_name']
            nas_event_num = extract_event_number(nas_name)
            nas_is_me = is_main_event(nas_name)
            nas_is_toc = is_toc(nas_name)
            nas_me_day = extract_main_event_day(nas_name) if nas_is_me else None

            # 매칭 로직
            reasons = []

            # TOC 매칭
            if pg_is_toc and nas_is_toc:
                reasons.append("TOC")

            # Main Event 매칭
            if pg_is_me and nas_is_me:
                if pg_me_day and nas_me_day and pg_me_day == nas_me_day:
                    reasons.append(f"Main Event Day {pg_me_day}")
                elif pg_me_day is None and nas_me_day is None:
                    # 둘 다 Day 번호가 없으면 매칭
                    reasons.append("Main Event")

            # 일반 이벤트 번호 매칭 (Main Event가 아닌 경우)
            if not pg_is_me and not nas_is_me:
                if pg_event_num and nas_event_num and pg_event_num == nas_event_num:
                    reasons.append(f"Event #{pg_event_num}")

            if reasons:
                matched_nas.append({
                    'nas_file': nas_name,
                    'nas_size_mb': nas['size_mb'],
                    'nas_duration_min': nas['duration_minutes'],
                    'match_reasons': reasons
                })

        matches.append({
            'pokergo_title': pg_title,
            'pokergo_id': pg.get('id', ''),
            'matched_nas': matched_nas
        })

    return matches


def print_report(pokergo_list: List[Dict], nas_list: List[Dict], matches: List[Dict]):
    """매칭 결과 리포트 출력"""

    print("=" * 100)
    print("2004년 NAS vs PokerGO 매칭 분석 결과")
    print("=" * 100)

    # 1. PokerGO 영상 목록
    print("\n[1] PokerGO 영상 목록 (2004)")
    print("-" * 100)
    for i, pg in enumerate(pokergo_list, 1):
        print(f"{i:2d}. {pg['title']}")

    # 2. NAS 파일 목록 (상위 20개)
    print(f"\n[2] NAS 파일 목록 (상위 20개, 전체 {len(nas_list)}개)")
    print("-" * 100)
    for i, nas in enumerate(nas_list[:20], 1):
        print(f"{i:2d}. {nas['file_name']} ({nas['size_mb']:.1f}MB, {nas['duration_minutes']:.0f}분)")

    if len(nas_list) > 20:
        print(f"... 외 {len(nas_list) - 20}개 파일")

    # 3. 매칭 테이블
    print("\n[3] 매칭 테이블")
    print("-" * 100)
    print(f"{'PokerGO Title':<50} | {'NAS File':<40} | {'매칭 근거':<20}")
    print("-" * 100)

    total_matches = 0
    for match in matches:
        pg_title = match['pokergo_title'][:47] + "..." if len(match['pokergo_title']) > 50 else match['pokergo_title']

        if match['matched_nas']:
            for nas_match in match['matched_nas']:
                nas_file = nas_match['nas_file'][:37] + "..." if len(nas_match['nas_file']) > 40 else nas_match['nas_file']
                reasons = ", ".join(nas_match['match_reasons'])
                print(f"{pg_title:<50} | {nas_file:<40} | {reasons:<20}")
                total_matches += 1
        else:
            print(f"{pg_title:<50} | {'(매칭 없음)':<40} | {'':<20}")

    # 4. 추가 NAS 파일 개수
    matched_nas_files = set()
    for match in matches:
        for nas_match in match['matched_nas']:
            matched_nas_files.add(nas_match['nas_file'])

    unmatched_nas = [nas for nas in nas_list if nas['file_name'] not in matched_nas_files]
    unmatched_nas_count = len(unmatched_nas)

    print(f"\n[4] 추가 NAS 파일 (PokerGO에 매칭되지 않음)")
    print("-" * 100)
    print(f"매칭되지 않은 NAS 파일: {unmatched_nas_count}개")
    print()
    for i, nas in enumerate(unmatched_nas[:20], 1):
        print(f"{i:2d}. {nas['file_name']}")
    if unmatched_nas_count > 20:
        print(f"... 외 {unmatched_nas_count - 20}개")

    # 5. Summary 통계
    print(f"\n[5] Summary 통계")
    print("-" * 100)
    print(f"PokerGO 영상 수: {len(pokergo_list)}개")
    print(f"NAS 파일 수: {len(nas_list)}개")
    print(f"총 매칭 수: {total_matches}개")
    print(f"PokerGO 매칭률: {len([m for m in matches if m['matched_nas']]) / len(pokergo_list) * 100:.1f}%")
    print(f"NAS 매칭률: {len(matched_nas_files) / len(nas_list) * 100:.1f}%")
    print("=" * 100)


def main():
    """메인 실행 함수"""

    # 데이터 로드
    print("Loading data...")
    pokergo_list = load_pokergo_2004(POKERGO_JSON)
    nas_list = load_nas_2004(NAS_DB)

    print(f"PokerGO 2004: {len(pokergo_list)}개")
    print(f"NAS 2004: {len(nas_list)}개")

    # 매칭 수행
    print("\nMatching videos...")
    matches = match_videos(pokergo_list, nas_list)

    # 리포트 출력
    print_report(pokergo_list, nas_list, matches)


if __name__ == "__main__":
    main()
