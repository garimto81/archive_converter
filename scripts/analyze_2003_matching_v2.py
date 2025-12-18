"""
2003년 NAS vs PokerGO 매칭 분석 스크립트 v2 (개선된 매칭 로직)
"""
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Tuple, Optional
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

def extract_sequence_from_filename(filename: str) -> Optional[int]:
    """
    파일명에서 순번 추출
    WSOP_2003-01.mxf → 1
    WSOP_2003-07.mxf → 7
    """
    # WSOP_2003-XX 패턴
    match = re.search(r'WSOP_2003-(\d+)', filename)
    if match:
        return int(match.group(1))
    return None

def extract_day_from_title(title: str) -> Optional[int]:
    """
    PokerGO 제목에서 Day 번호 추출
    'Wsop Main Event 2003  Day 1' → 1
    'Wsop Main Event 2003  Day 3 Part 1' → 3
    """
    match = re.search(r'Day\s+(\d+)', title, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None

def extract_part_from_title(title: str) -> Optional[int]:
    """
    PokerGO 제목에서 Part 번호 추출
    'Day 3 Part 1' → 1
    'Day 3 Part 2' → 2
    'Final Table Part 1' → 1
    """
    match = re.search(r'Part\s+(\d+)', title, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None

def is_final_table(text: str) -> bool:
    """Final Table 키워드 확인"""
    return 'final table' in text.lower() or 'final_table' in text.lower()

def is_commentary(text: str) -> bool:
    """Commentary 키워드 확인"""
    return 'commentary' in text.lower()

def is_best_of(text: str) -> bool:
    """Best Of 시리즈 확인"""
    return 'best of' in text.lower() or 'best_of' in text.lower()

def categorize_nas_files(nas_files: List[Dict]) -> Dict[str, List[Dict]]:
    """NAS 파일을 카테고리별로 분류"""
    categorized = {
        'main_episodes': [],  # WSOP_2003-XX.mxf
        'final_table': [],    # Final Table
        'best_of': [],        # Best Of 시리즈
        'show_episodes': [],  # WSOP_2003 Show XX
        'other': []
    }

    for nas_file in nas_files:
        filename = nas_file['filename']

        if is_best_of(filename):
            categorized['best_of'].append(nas_file)
        elif is_final_table(filename):
            categorized['final_table'].append(nas_file)
        elif re.match(r'WSOP_2003-\d+\.mxf', filename):
            categorized['main_episodes'].append(nas_file)
        elif 'Show' in filename:
            categorized['show_episodes'].append(nas_file)
        else:
            categorized['other'].append(nas_file)

    # 순번 정렬
    categorized['main_episodes'].sort(key=lambda x: extract_sequence_from_filename(x['filename']) or 0)

    return categorized

def categorize_pokergo_videos(videos: List[Dict]) -> Dict[str, List[Dict]]:
    """PokerGO 영상을 카테고리별로 분류"""
    categorized = {
        'day_episodes': [],   # Day X
        'final_table': [],    # Final Table
        'commentary': []      # Commentary
    }

    for video in videos:
        title = video['title']

        if is_commentary(title):
            categorized['commentary'].append(video)
        elif is_final_table(title):
            categorized['final_table'].append(video)
        elif extract_day_from_title(title):
            categorized['day_episodes'].append(video)

    # Day 순번 정렬
    categorized['day_episodes'].sort(
        key=lambda x: (extract_day_from_title(x['title']) or 0, extract_part_from_title(x['title']) or 0)
    )

    return categorized

def match_main_episodes(nas_episodes: List[Dict], pgo_day_episodes: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    메인 에피소드 매칭
    WSOP_2003-01.mxf → Day 1
    WSOP_2003-07.mxf → Show 7 (Final Table Part 1과 유사)
    """
    matches = []
    unmatched_nas = []
    unmatched_pgo = list(pgo_day_episodes)

    # Day별 그룹핑 (Part 1, Part 2 등)
    day_groups = {}
    for video in pgo_day_episodes:
        day_num = extract_day_from_title(video['title'])
        if day_num not in day_groups:
            day_groups[day_num] = []
        day_groups[day_num].append(video)

    for nas_file in nas_episodes:
        filename = nas_file['filename']
        seq = extract_sequence_from_filename(filename)

        if seq is None:
            unmatched_nas.append(nas_file)
            continue

        # seq가 7인 경우 특수 처리 (Show 7 = Final Table과 유사)
        if seq == 7:
            # Final Table 매칭은 별도로 처리
            unmatched_nas.append(nas_file)
            continue

        # seq를 Day로 매핑 (1~6)
        if seq in day_groups and day_groups[seq]:
            # 해당 Day의 모든 Part 매칭
            for pgo_video in day_groups[seq]:
                part = extract_part_from_title(pgo_video['title'])
                part_text = f"Part {part}" if part else ""

                matches.append({
                    'nas_file': filename,
                    'pokergo_title': pgo_video['title'],
                    'nas_size_gb': nas_file.get('size_gb'),
                    'pokergo_duration': pgo_video.get('duration'),
                    'reason': f"Day {seq} {part_text}".strip()
                })

                if pgo_video in unmatched_pgo:
                    unmatched_pgo.remove(pgo_video)
        else:
            unmatched_nas.append(nas_file)

    return matches, unmatched_nas, unmatched_pgo

def match_final_table(nas_final: List[Dict], pgo_final: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Final Table 매칭"""
    matches = []
    unmatched_nas = list(nas_final)
    unmatched_pgo = list(pgo_final)

    # 간단 매칭: NAS Final Table → PokerGO Final Table Part 1, Part 2
    for nas_file in nas_final[:]:
        for pgo_video in pgo_final[:]:
            part = extract_part_from_title(pgo_video['title'])
            part_text = f"Part {part}" if part else ""

            matches.append({
                'nas_file': nas_file['filename'],
                'pokergo_title': pgo_video['title'],
                'nas_size_gb': nas_file.get('size_gb'),
                'pokergo_duration': pgo_video.get('duration'),
                'reason': f"Final Table {part_text}".strip()
            })

            if pgo_video in unmatched_pgo:
                unmatched_pgo.remove(pgo_video)

        if nas_file in unmatched_nas:
            unmatched_nas.remove(nas_file)

    return matches, unmatched_nas, unmatched_pgo

def perform_matching(nas_files: List[Dict], pokergo_videos: List[Dict]) -> Dict:
    """전체 매칭 수행"""
    # 카테고리 분류
    nas_cat = categorize_nas_files(nas_files)
    pgo_cat = categorize_pokergo_videos(pokergo_videos)

    all_matches = []
    all_unmatched_nas = []
    all_unmatched_pgo = []

    # 1. 메인 에피소드 매칭
    main_matches, main_nas_unmatched, main_pgo_unmatched = match_main_episodes(
        nas_cat['main_episodes'],
        pgo_cat['day_episodes']
    )
    all_matches.extend(main_matches)
    all_unmatched_pgo.extend(main_pgo_unmatched)

    # 2. Final Table 매칭
    final_matches, final_nas_unmatched, final_pgo_unmatched = match_final_table(
        nas_cat['final_table'],
        pgo_cat['final_table']
    )
    all_matches.extend(final_matches)
    all_unmatched_nas.extend(final_nas_unmatched)
    all_unmatched_pgo.extend(final_pgo_unmatched)

    # 3. 매칭 안 된 NAS 파일들
    all_unmatched_nas.extend(main_nas_unmatched)
    all_unmatched_nas.extend(nas_cat['best_of'])  # Best Of는 추가 콘텐츠
    all_unmatched_nas.extend(nas_cat['show_episodes'])
    all_unmatched_nas.extend(nas_cat['other'])

    # 4. Commentary는 별도 추가 콘텐츠
    all_unmatched_pgo.extend(pgo_cat['commentary'])

    return {
        'matches': all_matches,
        'unmatched_nas': all_unmatched_nas,
        'unmatched_pokergo': all_unmatched_pgo,
        'nas_categories': nas_cat,
        'pgo_categories': pgo_cat
    }

def generate_markdown_report(nas_files: List[Dict], pokergo_videos: List[Dict], result: Dict) -> str:
    """Markdown 형식 리포트 생성"""
    lines = []

    lines.append("# 2003년 NAS vs PokerGO 매칭 분석 결과\n")

    # 1. PokerGO 영상 목록
    lines.append("## 1. PokerGO 영상 목록 (2003)\n")
    for i, video in enumerate(pokergo_videos, 1):
        title = video['title']
        lines.append(f"{i}. **{title}**")

    lines.append(f"\n**총 {len(pokergo_videos)}개 영상**\n")

    # 2. NAS 파일 목록
    lines.append("## 2. NAS 파일 목록 (2003)\n")
    for i, nas in enumerate(nas_files, 1):
        filename = nas['filename']
        size = nas.get('size_gb', 0)
        lines.append(f"{i}. `{filename}` ({size:.2f}GB)")

    lines.append(f"\n**총 {len(nas_files)}개 파일**\n")

    # 3. 매칭 테이블
    lines.append("## 3. 매칭 테이블\n")
    lines.append("| No. | PokerGO Title | NAS File | Size (GB) | 매칭 근거 |")
    lines.append("|-----|---------------|----------|-----------|----------|")

    for i, match in enumerate(result['matches'], 1):
        pgo_title = match['pokergo_title']
        nas_file = match['nas_file']
        size = match.get('nas_size_gb', 0)
        reason = match['reason']
        lines.append(f"| {i} | {pgo_title} | `{nas_file}` | {size:.2f} | {reason} |")

    lines.append(f"\n**총 {len(result['matches'])}개 매칭**\n")

    # 4. 추가 NAS 파일
    lines.append("## 4. 추가 NAS 파일 (PokerGO에 없는 파일)\n")

    # Best Of 시리즈
    best_of = result['nas_categories']['best_of']
    if best_of:
        lines.append("### Best Of 시리즈 (추가 콘텐츠)\n")
        for nas in best_of:
            size = nas.get('size_gb', 0)
            lines.append(f"- `{nas['filename']}` ({size:.2f}GB)")
        lines.append("")

    # Show 에피소드
    show_eps = result['nas_categories']['show_episodes']
    if show_eps:
        lines.append("### Show 에피소드\n")
        for nas in show_eps:
            size = nas.get('size_gb', 0)
            lines.append(f"- `{nas['filename']}` ({size:.2f}GB)")
        lines.append("")

    # 기타
    other_unmatched = [n for n in result['unmatched_nas'] if n not in best_of and n not in show_eps]
    if other_unmatched:
        lines.append("### 기타 미매칭\n")
        for nas in other_unmatched:
            size = nas.get('size_gb', 0)
            lines.append(f"- `{nas['filename']}` ({size:.2f}GB)")
        lines.append("")

    lines.append(f"**총 {len(result['unmatched_nas'])}개 추가 파일**\n")

    # 5. 미매칭 PokerGO 영상
    lines.append("## 5. 매칭되지 않은 PokerGO 영상\n")

    for video in result['unmatched_pokergo']:
        title = video['title']
        category = ""
        if is_commentary(title):
            category = " (Commentary - 추가 콘텐츠)"

        lines.append(f"- **{title}**{category}")

    lines.append(f"\n**총 {len(result['unmatched_pokergo'])}개 미매칭**\n")

    # 6. Summary 통계
    lines.append("## 6. Summary 통계\n")

    match_rate = (len(result['matches']) / len(pokergo_videos) * 100) if pokergo_videos else 0

    lines.append(f"- **PokerGO 영상 수**: {len(pokergo_videos)}개")
    lines.append(f"- **NAS 파일 수**: {len(nas_files)}개")
    lines.append(f"- **매칭 성공**: {len(result['matches'])}개 ({match_rate:.1f}%)")
    lines.append(f"- **NAS 추가 파일**: {len(result['unmatched_nas'])}개")
    lines.append(f"  - Best Of 시리즈: {len(best_of)}개")
    lines.append(f"  - Show 에피소드: {len(show_eps)}개")
    lines.append(f"- **PokerGO 미매칭**: {len(result['unmatched_pokergo'])}개")
    lines.append(f"  - Commentary: {len(result['pgo_categories']['commentary'])}개")

    # 7. 분석 및 권장사항
    lines.append("\n## 7. 분석 및 권장사항\n")

    lines.append("### 매칭 품질")
    lines.append(f"- Day 에피소드 매칭률: {len([m for m in result['matches'] if 'Day' in m['reason']])} / {len(result['pgo_categories']['day_episodes'])}")
    lines.append(f"- Final Table 매칭률: {len([m for m in result['matches'] if 'Final' in m['reason']])} / {len(result['pgo_categories']['final_table'])}")

    lines.append("\n### 권장사항")
    lines.append("1. **WSOP_2003-07.mxf** (25.3GB) - 'Show 7'로 표기되어 있으나 내용 확인 필요")
    lines.append("2. **Best Of 시리즈** (4개, 총 ~40GB) - PokerGO에 대응하는 영상 없음. 추가 콘텐츠로 분류")
    lines.append("3. **Commentary 영상** - 기존 영상의 추가 해설 버전으로 추정")
    lines.append("4. **Day 3 Part 1, Part 2** - 하나의 NAS 파일(WSOP_2003-03.mxf)에 대응. 분할 여부 확인 필요")

    return "\n".join(lines)

def main():
    print("데이터 로딩 중...")

    # 데이터 로드
    nas_files = get_nas_2003_files()
    pokergo_videos = get_pokergo_2003_videos()

    print(f"NAS 파일: {len(nas_files)}개")
    print(f"PokerGO 영상: {len(pokergo_videos)}개\n")

    # 매칭 수행
    result = perform_matching(nas_files, pokergo_videos)

    # Markdown 리포트 생성
    markdown_report = generate_markdown_report(nas_files, pokergo_videos, result)

    # Markdown 저장
    output_md = PROJECT_ROOT / "data" / "matching_2003_report.md"
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write(markdown_report)

    print(f"Markdown 리포트 저장: {output_md}")

    # JSON 저장
    output_json = PROJECT_ROOT / "data" / "matching_2003_report_v2.json"
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump({
            'nas_files': nas_files,
            'pokergo_videos': pokergo_videos,
            'matches': result['matches'],
            'unmatched_nas': result['unmatched_nas'],
            'unmatched_pokergo': result['unmatched_pokergo']
        }, f, indent=2, ensure_ascii=False)

    print(f"JSON 리포트 저장: {output_json}")

    # 콘솔 출력 (요약)
    print("\n=== 매칭 결과 요약 ===")
    print(f"매칭 성공: {len(result['matches'])}개")
    print(f"NAS 추가 파일: {len(result['unmatched_nas'])}개")
    print(f"PokerGO 미매칭: {len(result['unmatched_pokergo'])}개")

    print("\n매칭된 파일:")
    for match in result['matches']:
        print(f"  - {match['pokergo_title']} ← {match['nas_file']} ({match['reason']})")

if __name__ == "__main__":
    main()
