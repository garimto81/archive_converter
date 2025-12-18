"""
2005년 NAS vs PokerGO 매칭 분석 스크립트

데이터 소스:
- NAS DB: data/nas_footage.db
- PokerGO: data/pokergo/wsop_final_20251216_154021.json
"""

import json
import sqlite3
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
NAS_DB = PROJECT_ROOT / "data" / "nas_footage.db"
POKERGO_JSON = PROJECT_ROOT / "data" / "pokergo" / "wsop_final_20251216_154021.json"


def load_pokergo_2005() -> List[Dict]:
    """PokerGO 2005년 데이터 로드"""
    with open(POKERGO_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # videos 키에서 데이터 추출
    all_videos = data.get('videos', [])

    # 2005년 데이터 필터링
    videos_2005 = []
    for item in all_videos:
        title = item.get('title', '')
        if '2005' in title:
            videos_2005.append(item)

    return videos_2005


def load_nas_2005() -> List[Dict]:
    """NAS 2005년 데이터 로드"""
    conn = sqlite3.connect(NAS_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM files
        WHERE year = 2005
        ORDER BY filename
    """)

    files = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return files


def parse_event_number(filename: str) -> Optional[int]:
    """파일명에서 이벤트 번호 추출"""
    # wsop-2005-ev-17 패턴
    match = re.search(r'ev[_-](\d+)', filename, re.IGNORECASE)
    if match:
        return int(match.group(1))

    # 다른 패턴들
    match = re.search(r'event[_-](\d+)', filename, re.IGNORECASE)
    if match:
        return int(match.group(1))

    return None


def parse_main_event_day(text: str) -> Optional[int]:
    """Main Event Day 번호 추출"""
    patterns = [
        r'day[_\s-]?(\d+)',
        r'd(\d+)',
        r'(\d+)[_\s-]?day',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))

    return None


def extract_pokergo_features(video: Dict) -> Dict:
    """PokerGO 비디오에서 매칭 특징 추출"""
    title = video.get('title', '')

    features = {
        'title': title,
        'event_num': None,
        'main_event_day': None,
        'is_toc': 'tournament of champions' in title.lower() or 'toc' in title.lower(),
        'is_commentary': 'commentary' in title.lower(),
        'is_main_event': 'main event' in title.lower(),
    }

    # 이벤트 번호
    match = re.search(r'event[_\s#-]*(\d+)', title, re.IGNORECASE)
    if match:
        features['event_num'] = int(match.group(1))

    # Main Event Day
    if features['is_main_event']:
        features['main_event_day'] = parse_main_event_day(title)

    return features


def extract_nas_features(file: Dict) -> Dict:
    """NAS 파일에서 매칭 특징 추출"""
    filename = file.get('filename', '')

    features = {
        'file_name': filename,
        'event_num': parse_event_number(filename),
        'main_event_day': None,
        'is_toc': 'toc' in filename.lower(),
        'is_commentary': 'commentary' in filename.lower(),
        'is_main_event': 'me' in filename.lower() or 'main' in filename.lower(),
    }

    # Main Event Day
    if features['is_main_event']:
        features['main_event_day'] = parse_main_event_day(filename)

    return features


def match_videos(pokergo_features: Dict, nas_features_list: List[Dict]) -> Tuple[Optional[Dict], str]:
    """PokerGO 비디오와 NAS 파일 매칭"""

    best_match = None
    best_reason = ""
    best_score = 0

    for nas_features in nas_features_list:
        score = 0
        reasons = []

        # 이벤트 번호 매칭 (가장 강력)
        if (pokergo_features['event_num'] is not None and
            nas_features['event_num'] is not None and
            pokergo_features['event_num'] == nas_features['event_num']):
            score += 10
            reasons.append(f"Event #{pokergo_features['event_num']}")

        # Main Event Day 매칭
        if (pokergo_features['main_event_day'] is not None and
            nas_features['main_event_day'] is not None and
            pokergo_features['main_event_day'] == nas_features['main_event_day']):
            score += 8
            reasons.append(f"Main Event Day {pokergo_features['main_event_day']}")

        # TOC 매칭
        if pokergo_features['is_toc'] and nas_features['is_toc']:
            score += 7
            reasons.append("TOC")

        # Commentary 매칭
        if pokergo_features['is_commentary'] and nas_features['is_commentary']:
            score += 5
            reasons.append("Commentary")

        # Main Event 매칭 (Day 없이)
        if (pokergo_features['is_main_event'] and
            nas_features['is_main_event'] and
            pokergo_features['main_event_day'] is None and
            nas_features['main_event_day'] is None):
            score += 3
            reasons.append("Main Event")

        if score > best_score:
            best_score = score
            best_match = nas_features
            best_reason = ", ".join(reasons)

    # 최소 스코어 3 이상만 매칭으로 인정
    if best_score >= 3:
        return best_match, best_reason

    return None, ""


def main():
    output_file = PROJECT_ROOT / "data" / "analysis_2005_matching.txt"

    # 출력 버퍼
    lines = []

    lines.append("=== 2005년 NAS vs PokerGO 매칭 분석 ===\n")

    # 데이터 로드
    lines.append("데이터 로딩 중...")
    pokergo_videos = load_pokergo_2005()
    nas_files = load_nas_2005()

    lines.append(f"PokerGO 2005년 비디오: {len(pokergo_videos)}개")
    lines.append(f"NAS 2005년 파일: {len(nas_files)}개\n")

    # 특징 추출
    pokergo_features_list = [extract_pokergo_features(v) for v in pokergo_videos]
    nas_features_list = [extract_nas_features(f) for f in nas_files]

    # 1. PokerGO 영상 목록
    lines.append("\n" + "="*80)
    lines.append("1. PokerGO 영상 목록 (2005)")
    lines.append("="*80)
    for i, features in enumerate(pokergo_features_list, 1):
        event_info = f"Event #{features['event_num']}" if features['event_num'] else ""
        day_info = f"Day {features['main_event_day']}" if features['main_event_day'] else ""
        flags = []
        if features['is_toc']:
            flags.append("TOC")
        if features['is_commentary']:
            flags.append("Commentary")
        if features['is_main_event']:
            flags.append("ME")

        extra = " | ".join(filter(None, [event_info, day_info, ", ".join(flags)]))
        lines.append(f"{i:3d}. {features['title']}")
        if extra:
            lines.append(f"     → {extra}")

    # 2. NAS 파일 목록 (상위 20개)
    print("\n" + "="*80)
    print("2. NAS 파일 목록 (상위 20개)")
    print("="*80)
    for i, features in enumerate(nas_features_list[:20], 1):
        event_info = f"Event #{features['event_num']}" if features['event_num'] else ""
        day_info = f"Day {features['main_event_day']}" if features['main_event_day'] else ""
        flags = []
        if features['is_toc']:
            flags.append("TOC")
        if features['is_commentary']:
            flags.append("Commentary")
        if features['is_main_event']:
            flags.append("ME")

        extra = " | ".join(filter(None, [event_info, day_info, ", ".join(flags)]))
        print(f"{i:3d}. {features['file_name']}")
        if extra:
            print(f"     → {extra}")

    # 3. 매칭 테이블
    print("\n" + "="*80)
    print("3. 매칭 테이블")
    print("="*80)
    print(f"{'PokerGO Title':<60} | {'NAS File':<50} | {'매칭 근거':<30}")
    print("-" * 145)

    matched_count = 0
    unmatched_pokergo = []
    matched_nas_files = set()

    for pokergo_features in pokergo_features_list:
        nas_match, reason = match_videos(pokergo_features, nas_features_list)

        if nas_match:
            matched_count += 1
            matched_nas_files.add(nas_match['file_name'])

            # 제목과 파일명 길이 조절
            title = pokergo_features['title']
            if len(title) > 57:
                title = title[:54] + "..."

            filename = nas_match['file_name']
            if len(filename) > 47:
                filename = filename[:44] + "..."

            print(f"{title:<60} | {filename:<50} | {reason:<30}")
        else:
            unmatched_pokergo.append(pokergo_features['title'])
            print(f"{pokergo_features['title']:<60} | {'매칭 없음':<50} | {'':<30}")

    # 4. 추가 NAS 파일 개수
    unmatched_nas_count = len(nas_files) - len(matched_nas_files)

    print("\n" + "="*80)
    print("4. 매칭되지 않은 NAS 파일")
    print("="*80)
    print(f"총 {unmatched_nas_count}개 파일\n")

    # 매칭 안 된 NAS 파일 일부 출력
    unmatched_nas = [f for f in nas_features_list if f['file_name'] not in matched_nas_files]
    for i, features in enumerate(unmatched_nas[:10], 1):
        print(f"{i:3d}. {features['file_name']}")

    if unmatched_nas_count > 10:
        print(f"     ... 외 {unmatched_nas_count - 10}개")

    # 5. Summary 통계
    print("\n" + "="*80)
    print("5. Summary 통계")
    print("="*80)
    print(f"PokerGO 총 영상:      {len(pokergo_videos):4d}개")
    print(f"NAS 총 파일:          {len(nas_files):4d}개")
    print(f"")
    print(f"매칭 성공:            {matched_count:4d}개")
    print(f"매칭 실패 (PokerGO):  {len(unmatched_pokergo):4d}개")
    print(f"매칭 실패 (NAS):      {unmatched_nas_count:4d}개")
    print(f"")
    print(f"매칭률 (PokerGO):     {matched_count/len(pokergo_videos)*100:5.1f}%")
    print(f"매칭률 (NAS):         {len(matched_nas_files)/len(nas_files)*100:5.1f}%")

    # 매칭 유형별 통계
    print("\n매칭 유형별 통계:")
    match_types = defaultdict(int)
    for pokergo_features in pokergo_features_list:
        nas_match, reason = match_videos(pokergo_features, nas_features_list)
        if nas_match:
            if "Event #" in reason:
                match_types['Event Number'] += 1
            if "Main Event Day" in reason:
                match_types['Main Event Day'] += 1
            if "TOC" in reason:
                match_types['TOC'] += 1
            if "Commentary" in reason:
                match_types['Commentary'] += 1

    for match_type, count in sorted(match_types.items(), key=lambda x: -x[1]):
        print(f"  - {match_type:<20}: {count:3d}개")


if __name__ == "__main__":
    main()
