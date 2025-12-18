"""
2003년 NAS vs PokerGO 매칭 분석 스크립트
"""
import json
import sqlite3
from pathlib import Path
from typing import List, Dict
import re

# 경로 설정
PROJECT_ROOT = Path(r"D:\AI\claude01\Archive_Converter")
NAS_DB = PROJECT_ROOT / "data" / "nas_footage.db"
POKERGO_JSON = PROJECT_ROOT / "data" / "pokergo" / "wsop_final_20251216_154021.json"

def get_nas_2003_files() -> List[Dict]:
    """NAS DB에서 2003년 파일 조회"""
    conn = sqlite3.connect(str(NAS_DB))
    cursor = conn.cursor()

    query = """
    SELECT filename, size_gb, brand, year,
           event_num, asset_type
    FROM files
    WHERE year = 2003
    ORDER BY filename
    """

    cursor.execute(query)
    columns = [desc[0] for desc in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]

    conn.close()
    return results

def get_pokergo_2003_videos() -> List[Dict]:
    """PokerGO JSON에서 2003년 영상 추출"""
    with open(POKERGO_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # videos 키에서 비디오 목록 가져오기
    all_videos = data.get('videos', [])

    # 2003년 영상 필터링
    videos_2003 = []
    for video in all_videos:
        title = video.get('title', '')
        description = video.get('description', '')

        # 제목이나 설명에 2003이 포함된 경우
        if '2003' in title or '2003' in description:
            videos_2003.append({
                'title': title,
                'description': description,
                'duration': video.get('duration'),
                'permalink': video.get('permalink', '')
            })

    return videos_2003

def extract_event_number(filename: str) -> str:
    """파일명에서 이벤트 번호 추출"""
    # wsop-2003-ev-04-* 패턴
    match = re.search(r'ev-(\d+)', filename, re.IGNORECASE)
    if match:
        return match.group(1)

    # 04-wsop-2003-* 패턴
    match = re.search(r'^(\d+)-wsop', filename, re.IGNORECASE)
    if match:
        return match.group(1)

    return ""

def extract_day_number(text: str) -> str:
    """텍스트에서 Day 번호 추출"""
    match = re.search(r'Day\s+(\d+)', text, re.IGNORECASE)
    if match:
        return match.group(1).zfill(2)
    return ""

def extract_event_from_title(title: str) -> str:
    """PokerGO 제목에서 이벤트 번호 추출"""
    # Event #4, Event 4 패턴
    match = re.search(r'Event\s*#?(\d+)', title, re.IGNORECASE)
    if match:
        return match.group(1).zfill(2)
    return ""

def match_videos(nas_files: List[Dict], pokergo_videos: List[Dict]) -> Dict:
    """NAS 파일과 PokerGO 영상 매칭"""
    matches = []
    unmatched_nas = []
    unmatched_pokergo = list(pokergo_videos)  # 복사본

    for nas_file in nas_files:
        filename = nas_file['filename']
        nas_event = extract_event_number(filename)
        nas_day = extract_day_number(filename)

        # 매칭 시도
        matched = False
        for pgo_video in unmatched_pokergo[:]:  # 복사본으로 순회
            pgo_title = pgo_video['title']
            pgo_event = extract_event_from_title(pgo_title)
            pgo_day = extract_day_number(pgo_title)

            reasons = []

            # 이벤트 번호 매칭
            if nas_event and pgo_event and nas_event == pgo_event:
                reasons.append(f"Event #{pgo_event}")

            # Day 매칭
            if nas_day and pgo_day and nas_day == pgo_day:
                reasons.append(f"Day {pgo_day}")

            # Final Table 키워드
            if 'final' in filename.lower() and 'Final Table' in pgo_title:
                reasons.append("Final Table")

            # Best Of 시리즈는 추가 콘텐츠로 제외
            if 'Best Of' in pgo_title:
                continue

            # 매칭 조건: 이벤트 + Day 또는 Final Table
            if len(reasons) >= 2 or (len(reasons) >= 1 and 'Final Table' in reasons):
                matches.append({
                    'nas_file': filename,
                    'pokergo_title': pgo_title,
                    'nas_duration': nas_file.get('duration_sec'),
                    'pokergo_duration': pgo_video.get('duration'),
                    'reason': ', '.join(reasons)
                })
                unmatched_pokergo.remove(pgo_video)
                matched = True
                break

        if not matched:
            unmatched_nas.append(nas_file)

    return {
        'matches': matches,
        'unmatched_nas': unmatched_nas,
        'unmatched_pokergo': unmatched_pokergo
    }

def print_report(nas_files: List[Dict], pokergo_videos: List[Dict], result: Dict):
    """매칭 결과 리포트 출력"""
    print("=" * 100)
    print("2003년 NAS vs PokerGO 매칭 분석 결과")
    print("=" * 100)

    # 1. PokerGO 영상 목록
    print("\n1. PokerGO 영상 목록 (2003)")
    print("-" * 100)
    for i, video in enumerate(pokergo_videos, 1):
        duration = video.get('duration', 0)
        duration_min = duration // 60 if duration else 0
        print(f"{i:2d}. {video['title']}")
        print(f"    Duration: {duration_min}분 | {video.get('description', '')[:80]}")

    print(f"\n총 {len(pokergo_videos)}개 영상")

    # 2. NAS 파일 목록
    print("\n" + "=" * 100)
    print("2. NAS 파일 목록 (2003)")
    print("-" * 100)
    for i, nas in enumerate(nas_files, 1):
        size = nas.get('size_gb', 0)
        print(f"{i:2d}. {nas['filename']}")
        print(f"    Size: {size:.2f}GB | Brand: {nas.get('brand', 'N/A')}")

    print(f"\n총 {len(nas_files)}개 파일")

    # 3. 매칭 테이블
    print("\n" + "=" * 100)
    print("3. 매칭 테이블")
    print("-" * 100)
    print(f"{'No.':<4} {'PokerGO Title':<50} {'NAS File':<30} {'매칭 근거':<20}")
    print("-" * 100)

    for i, match in enumerate(result['matches'], 1):
        pgo_title = match['pokergo_title'][:48]
        nas_file = match['nas_file'][:28]
        reason = match['reason']
        print(f"{i:<4} {pgo_title:<50} {nas_file:<30} {reason:<20}")

    print(f"\n총 {len(result['matches'])}개 매칭")

    # 4. 추가 NAS 파일 (PokerGO에 없는 것)
    print("\n" + "=" * 100)
    print("4. 추가 NAS 파일 (PokerGO에 없는 파일)")
    print("-" * 100)

    for i, nas in enumerate(result['unmatched_nas'], 1):
        size = nas.get('size_gb', 0)
        print(f"{i:2d}. {nas['filename']} ({size:.2f}GB)")

    print(f"\n총 {len(result['unmatched_nas'])}개 추가 파일")

    # 5. 매칭되지 않은 PokerGO 영상
    print("\n" + "=" * 100)
    print("5. 매칭되지 않은 PokerGO 영상")
    print("-" * 100)

    for i, video in enumerate(result['unmatched_pokergo'], 1):
        print(f"{i:2d}. {video['title']}")
        if 'Best Of' in video['title']:
            print(f"    → 추가 콘텐츠 (Best Of 시리즈)")

    print(f"\n총 {len(result['unmatched_pokergo'])}개 미매칭")

    # 6. Summary 통계
    print("\n" + "=" * 100)
    print("6. Summary 통계")
    print("-" * 100)

    match_rate = (len(result['matches']) / len(pokergo_videos) * 100) if pokergo_videos else 0

    print(f"PokerGO 영상 수: {len(pokergo_videos)}개")
    print(f"NAS 파일 수: {len(nas_files)}개")
    print(f"매칭 성공: {len(result['matches'])}개 ({match_rate:.1f}%)")
    print(f"NAS 추가 파일: {len(result['unmatched_nas'])}개")
    print(f"PokerGO 미매칭: {len(result['unmatched_pokergo'])}개")

    # Best Of 분석
    best_of_count = sum(1 for v in result['unmatched_pokergo'] if 'Best Of' in v['title'])
    print(f"\n미매칭 중 Best Of 시리즈: {best_of_count}개 (추가 콘텐츠)")

    print("=" * 100)

def main():
    print("데이터 로딩 중...")

    # 데이터 로드
    nas_files = get_nas_2003_files()
    pokergo_videos = get_pokergo_2003_videos()

    print(f"NAS 파일: {len(nas_files)}개")
    print(f"PokerGO 영상: {len(pokergo_videos)}개\n")

    # 매칭 수행
    result = match_videos(nas_files, pokergo_videos)

    # 리포트 출력
    print_report(nas_files, pokergo_videos, result)

    # JSON 저장
    output_file = PROJECT_ROOT / "data" / "matching_2003_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'nas_files': nas_files,
            'pokergo_videos': pokergo_videos,
            'matches': result['matches'],
            'unmatched_nas': result['unmatched_nas'],
            'unmatched_pokergo': result['unmatched_pokergo']
        }, f, indent=2, ensure_ascii=False)

    print(f"\n결과 저장: {output_file}")

if __name__ == "__main__":
    main()
