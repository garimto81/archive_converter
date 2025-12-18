"""
2006년 NAS vs PokerGO 매칭 분석 스크립트
"""

import json
import sqlite3
import re
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict

# 경로 설정
BASE_DIR = Path(r"D:\AI\claude01\Archive_Converter")
NAS_DB = BASE_DIR / "data" / "nas_footage.db"
POKERGO_JSON = BASE_DIR / "data" / "pokergo" / "wsop_final_20251216_154021.json"


def load_pokergo_2006() -> List[Dict]:
    """PokerGO에서 2006년 영상 로드"""
    with open(POKERGO_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # videos 배열에서 2006년 필터링
    videos = data.get('videos', [])
    videos_2006 = []
    for video in videos:
        title = video.get('title', '')
        if '2006' in title:
            videos_2006.append(video)

    return videos_2006


def load_nas_2006() -> List[Dict]:
    """NAS DB에서 2006년 파일 로드"""
    conn = sqlite3.connect(str(NAS_DB))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM files
        WHERE year = 2006
        ORDER BY filename
    """)

    files = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return files


def extract_event_info(title: str) -> Dict:
    """PokerGO 타이틀에서 이벤트 정보 추출"""
    info = {
        'year': None,
        'event_num': None,
        'day': None,
        'is_main_event': False,
        'is_toc': False,
        'special': None
    }

    # 연도 추출
    year_match = re.search(r'20\d{2}', title)
    if year_match:
        info['year'] = int(year_match.group())

    # Event 번호 추출 (Event #15, Ev15, E15 등)
    event_patterns = [
        r'Event\s*#?(\d+)',
        r'Ev\.?\s*(\d+)',
        r'E(\d+)',
        r'Event\s+(\d+)'
    ]
    for pattern in event_patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            info['event_num'] = int(match.group(1))
            break

    # Main Event 체크
    if 'Main Event' in title:
        info['is_main_event'] = True

    # Day 추출 (다양한 패턴)
    day_patterns = [
        r'Day\s*(\d+[A-Z]?)',  # Day 1A, Day 1B, Day 1C, Day 2, etc
        r'D(\d+)',
    ]
    for pattern in day_patterns:
        day_match = re.search(pattern, title, re.IGNORECASE)
        if day_match:
            day_str = day_match.group(1)
            # 1A, 1B, 1C를 모두 1로 처리
            if day_str[-1].isalpha():
                info['day'] = int(day_str[:-1])
            else:
                info['day'] = int(day_str)
            break

    # TOC (Tournament of Champions) 체크
    if 'TOC' in title.upper() or 'Tournament of Champions' in title:
        info['is_toc'] = True

    # Special 이벤트
    if '50K' in title or '50,000' in title:
        info['special'] = '50K_HORSE'

    return info


def extract_nas_info(filename: str) -> Dict:
    """NAS 파일명에서 이벤트 정보 추출"""
    info = {
        'year': None,
        'event_num': None,
        'day': None,
        'is_main_event': False,
        'special': None,
        'show_num': None
    }

    # 2006 파일명 패턴들
    # WSOP 2006 Show 11 ME 1_*.mov (Main Event Day 1)
    # WSOP 2006 Show 31 50k Horse_*.mov
    # WSOP 2006 Show XX TOC_*.mov
    # WSOP 2006 EOE Final Table_*.mov

    # 연도
    if '2006' in filename:
        info['year'] = 2006

    # Show 번호
    show_match = re.search(r'Show\s+(\d+)', filename, re.IGNORECASE)
    if show_match:
        info['show_num'] = int(show_match.group(1))

    # Main Event with Day
    # "Show 11 ME 1" = Main Event Day 1
    # "Show 12 ME 2" = Main Event Day 2
    me_match = re.search(r'ME\s+(\d+)', filename, re.IGNORECASE)
    if me_match:
        info['is_main_event'] = True
        info['day'] = int(me_match.group(1))

    # Main Event alternative patterns
    if 'main event' in filename.lower() or 'ME' in filename:
        info['is_main_event'] = True
        # Day from various patterns
        day_patterns = [
            r'Day\s*(\d+)',
            r'D(\d+)',
            r'ME\s*(\d+)',
        ]
        for pattern in day_patterns:
            day_match = re.search(pattern, filename, re.IGNORECASE)
            if day_match and not info['day']:
                info['day'] = int(day_match.group(1))
                break

    # Final Table
    if 'final table' in filename.lower() or 'finale' in filename.lower():
        info['is_main_event'] = True
        info['special'] = 'FINAL_TABLE'

    # TOC
    if 'toc' in filename.lower() or 'tournament of champions' in filename.lower():
        info['special'] = 'TOC'

    # 50K HORSE
    if '50k' in filename.lower() and 'horse' in filename.lower():
        info['special'] = '50K_HORSE'

    # Event 번호 (일반 이벤트)
    if not info['is_main_event']:
        ev_patterns = [
            r'Show\s+(\d+)(?!\s+ME)',  # Show number but not followed by ME
            r'Event\s*#?(\d+)',
            r'Ev\.?\s*(\d+)',
        ]
        for pattern in ev_patterns:
            ev_match = re.search(pattern, filename, re.IGNORECASE)
            if ev_match:
                info['event_num'] = int(ev_match.group(1))
                break

    return info


def match_videos(pokergo_videos: List[Dict], nas_files: List[Dict]) -> List[Dict]:
    """PokerGO와 NAS 파일 매칭"""
    matches = []
    matched_nas = set()

    for pg_video in pokergo_videos:
        pg_title = pg_video['title']
        pg_info = extract_event_info(pg_title)

        best_match = None
        best_score = 0
        match_reason = []

        for nas_file in nas_files:
            if nas_file['filename'] in matched_nas:
                continue

            nas_name = nas_file['filename']
            nas_info = extract_nas_info(nas_name)

            score = 0
            reasons = []

            # 연도 매칭 (필수)
            if pg_info['year'] == nas_info['year'] == 2006:
                score += 10
                reasons.append("Year 2006")
            else:
                continue

            # Special 이벤트 매칭 (최우선)
            if pg_info['special'] and nas_info['special']:
                if pg_info['special'] == nas_info['special']:
                    score += 60
                    reasons.append(pg_info['special'])

            # TOC 매칭
            if pg_info['is_toc'] and nas_info['special'] == 'TOC':
                score += 60
                reasons.append("TOC")

            # Final Table 매칭
            if 'final table' in pg_title.lower() and nas_info['special'] == 'FINAL_TABLE':
                score += 50
                reasons.append("Final Table")

            # Main Event + Day 매칭
            if pg_info['is_main_event'] and nas_info['is_main_event']:
                score += 30
                reasons.append("Main Event")

                if pg_info['day'] and nas_info['day']:
                    if pg_info['day'] == nas_info['day']:
                        score += 30  # Day 매칭 점수 증가
                        reasons.append(f"Day {pg_info['day']}")
                    else:
                        # Day가 다르면 감점
                        score -= 10

            # Event 번호 매칭 (일반 이벤트)
            elif pg_info['event_num'] and nas_info['event_num']:
                if pg_info['event_num'] == nas_info['event_num']:
                    score += 40
                    reasons.append(f"Event #{pg_info['event_num']}")

            if score > best_score:
                best_score = score
                best_match = nas_file
                match_reason = reasons

        if best_match and best_score >= 30:  # 임계값
            matches.append({
                'pokergo_title': pg_title,
                'pokergo_id': pg_video.get('id'),
                'nas_file': best_match['filename'],
                'nas_path': best_match.get('path', ''),
                'score': best_score,
                'reason': ' + '.join(match_reason)
            })
            matched_nas.add(best_match['filename'])

    return matches


def print_results(pokergo_videos: List[Dict], nas_files: List[Dict], matches: List[Dict]):
    """결과 출력 및 파일 저장"""

    output = []
    output.append("=" * 80)
    output.append("2006년 NAS vs PokerGO 매칭 분석 결과")
    output.append("=" * 80)
    output.append("")

    print("=" * 80)
    print("2006년 NAS vs PokerGO 매칭 분석 결과")
    print("=" * 80)
    print()

    # 1. PokerGO 영상 목록
    print("1. PokerGO 영상 목록 (제목)")
    print("-" * 80)
    for i, video in enumerate(pokergo_videos, 1):
        duration = video.get('duration', 0)
        duration_str = f"{duration//60}분" if duration else "N/A"
        print(f"{i:2d}. {video['title']} ({duration_str})")
    print(f"\n총 {len(pokergo_videos)}개")
    print()

    # 2. NAS 파일 목록 (상위 20개)
    print("2. NAS 파일 목록 (파일명) - 상위 20개")
    print("-" * 80)
    for i, file in enumerate(nas_files[:20], 1):
        size_gb = file.get('size_bytes', 0) / (1024**3)
        print(f"{i:2d}. {file['filename']}")
        print(f"    Size: {size_gb:.2f}GB")
    print()

    # 3. 매칭 테이블
    print("3. 매칭 테이블")
    print("-" * 80)
    print(f"{'PokerGO Title':<50} | {'NAS File':<30} | {'매칭 근거':<30}")
    print("-" * 80)

    if matches:
        for match in sorted(matches, key=lambda x: x['score'], reverse=True):
            pg_title = match['pokergo_title'][:47] + "..." if len(match['pokergo_title']) > 50 else match['pokergo_title']
            nas_file = match['nas_file'][:27] + "..." if len(match['nas_file']) > 30 else match['nas_file']
            reason = match['reason'][:27] + "..." if len(match['reason']) > 30 else match['reason']
            print(f"{pg_title:<50} | {nas_file:<30} | {reason:<30}")
    else:
        print("매칭된 항목이 없습니다.")
    print()

    # 4. 추가 NAS 파일 개수
    matched_count = len(matches)
    unmatched_count = len(nas_files) - matched_count
    print("4. 추가 NAS 파일 개수")
    print("-" * 80)
    print(f"매칭된 NAS 파일: {matched_count}개")
    print(f"매칭되지 않은 NAS 파일: {unmatched_count}개")
    print()

    # 5. Summary 통계
    print("5. Summary 통계")
    print("-" * 80)
    print(f"PokerGO 영상 수: {len(pokergo_videos)}개")
    print(f"NAS 파일 수: {len(nas_files)}개")
    print(f"매칭 성공: {matched_count}개")
    print(f"매칭률: {matched_count/len(pokergo_videos)*100:.1f}% (PokerGO 기준)")
    print(f"매칭률: {matched_count/len(nas_files)*100:.1f}% (NAS 기준)")

    # 매칭되지 않은 PokerGO 영상
    matched_pg_ids = {m['pokergo_id'] for m in matches}
    unmatched_pg = [v for v in pokergo_videos if v.get('id') not in matched_pg_ids]

    if unmatched_pg:
        print()
        print("매칭되지 않은 PokerGO 영상:")
        for video in unmatched_pg:
            print(f"  - {video['title']}")

    # 매칭되지 않은 NAS 파일 샘플
    matched_nas_names = {m['nas_file'] for m in matches}
    unmatched_nas = [f for f in nas_files if f['filename'] not in matched_nas_names]

    if unmatched_nas:
        print()
        print("매칭되지 않은 NAS 파일 샘플 (상위 10개):")
        for file in unmatched_nas[:10]:
            print(f"  - {file['filename']}")

    print()
    print("=" * 80)

    # 결과를 JSON으로 저장
    output_file = BASE_DIR / "data" / "matching_2006_results.json"
    result_data = {
        "summary": {
            "pokergo_count": len(pokergo_videos),
            "nas_count": len(nas_files),
            "matched_count": matched_count,
            "match_rate_pokergo": f"{matched_count/len(pokergo_videos)*100:.1f}%",
            "match_rate_nas": f"{matched_count/len(nas_files)*100:.1f}%"
        },
        "matches": matches,
        "unmatched_pokergo": [{"id": v.get('id'), "title": v['title']} for v in unmatched_pg],
        "unmatched_nas": [{"filename": f['filename'], "path": f.get('path', '')} for f in unmatched_nas]
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)

    print(f"\n결과 저장: {output_file}")


def main():
    """메인 실행"""
    print("Loading data...")

    # 데이터 로드
    pokergo_videos = load_pokergo_2006()
    nas_files = load_nas_2006()

    print(f"Loaded {len(pokergo_videos)} PokerGO videos")
    print(f"Loaded {len(nas_files)} NAS files")
    print()

    # 매칭 실행
    matches = match_videos(pokergo_videos, nas_files)

    # 결과 출력
    print_results(pokergo_videos, nas_files, matches)


if __name__ == "__main__":
    main()
