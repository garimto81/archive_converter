"""
PokerGO WSOP 데이터와 NAS 파일 매칭

기능:
1. NAS 파일 스캔 (Z: 드라이브)
2. PokerGO 데이터에서 메타데이터 추출
3. 자동 매칭 (연도, 이벤트 번호, 제목 유사도)
4. 새 시트에 매칭 정보 업로드
"""

import json
import re
import os
from datetime import datetime
from pathlib import Path
from difflib import SequenceMatcher

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.run(["pip", "install", "gspread", "google-auth"], check=True)
    import gspread
    from google.oauth2.service_account import Credentials


# NAS 경로 (Z: 드라이브에 마운트됨)
NAS_BASE = Path("Z:/ARCHIVE/WSOP")

# NAS 폴더 구조
NAS_FOLDERS = {
    "archive_pre2002": NAS_BASE / "WSOP ARCHIVE (PRE-2002)",
    "bracelet_vegas": NAS_BASE / "WSOP Bracelet Event" / "WSOP-LAS VEGAS",
    "bracelet_europe": NAS_BASE / "WSOP Bracelet Event" / "WSOP-EUROPE",
    "bracelet_paradise": NAS_BASE / "WSOP Bracelet Event" / "WSOP-PARADISE",
    "circuit": NAS_BASE / "WSOP Circuit Event",
}

# 필터 규칙 (CLAUDE.md 참조)
EXCLUDE_KEYWORDS = ['clip', 'highlight', 'paradise', 'circuit']
MAX_SIZE_GB = 1.0
MAX_DURATION_HOURS = 1.0


def should_exclude(path: str) -> bool:
    """제외 키워드 포함 여부 확인"""
    path_lower = path.lower()
    for kw in EXCLUDE_KEYWORDS:
        if kw in path_lower:
            return True
    return False


def scan_nas_files() -> list:
    """NAS WSOP 파일 전체 스캔 (필터 규칙 적용)"""
    all_files = []
    excluded_keyword = 0
    excluded_size = 0

    def scan_folder(folder: Path, category: str = ""):
        nonlocal excluded_keyword, excluded_size

        if not folder.exists():
            return

        for item in folder.iterdir():
            if item.is_file() and item.suffix.lower() in ['.mp4', '.mov', '.mxf']:
                # 필터 1: 제외 키워드 확인
                if should_exclude(str(item)):
                    excluded_keyword += 1
                    continue

                # 필터 2: 크기 확인 (1GB 초과 제외)
                size_gb = item.stat().st_size / (1024**3)
                if size_gb > MAX_SIZE_GB:
                    excluded_size += 1
                    continue

                # 연도 추출
                year = None
                for y in range(1973, 2026):
                    if str(y) in str(item):
                        year = y
                        break

                # 이벤트 번호 추출
                event_num = None
                ev_match = re.search(r'Event\s*#?\s*(\d+)|ev-(\d+)|ev(\d+)', item.name, re.IGNORECASE)
                if ev_match:
                    event_num = int(ev_match.group(1) or ev_match.group(2) or ev_match.group(3))

                all_files.append({
                    'filename': item.name,
                    'path': str(item),
                    'folder': str(item.parent),
                    'category': category,
                    'year': year,
                    'event_num': event_num,
                    'size_gb': round(size_gb, 3),
                })
            elif item.is_dir():
                # 필터: 제외 키워드 폴더는 스킵
                if should_exclude(item.name):
                    continue

                # 하위 폴더 카테고리 결정
                sub_cat = category
                if 'main event' in item.name.lower():
                    sub_cat = 'Main Event'
                elif 'bracelet' in item.name.lower():
                    sub_cat = 'Bracelet Events'
                elif 'mastered' in item.name.lower():
                    sub_cat = 'Mastered'
                elif 'clean' in item.name.lower():
                    sub_cat = 'Clean'
                scan_folder(item, sub_cat)

    print("[NAS] Scanning folders (with filter rules)...")
    print(f"  Exclude keywords: {', '.join(EXCLUDE_KEYWORDS)}")
    print(f"  Max size: {MAX_SIZE_GB}GB")

    for name, folder in NAS_FOLDERS.items():
        # 폴더 자체가 제외 키워드에 해당하면 스킵
        if should_exclude(name):
            print(f"  Skipping (excluded): {name}")
            continue
        print(f"  Scanning: {name}")
        scan_folder(folder, name)

    print(f"\n  Excluded by keywords: {excluded_keyword}")
    print(f"  Excluded by size: {excluded_size}")

    return all_files


def parse_pokergo_title(title: str, slug: str, source: str) -> dict:
    """PokerGO 제목에서 메타데이터 추출"""
    result = {
        "year": None,
        "category": None,
        "event_num": None,
        "day": None,
        "episode": None,
        "is_final_table": False,
        "is_livestream": False,
    }

    # 연도 추출
    year_match = re.search(r'(20\d{2})', title) or re.search(r'(20\d{2})', slug)
    if year_match:
        result["year"] = int(year_match.group(1))

    # 카테고리 판별
    title_lower = title.lower()
    source_lower = source.lower() if source else ""

    if "main event" in title_lower or "main event" in source_lower or "-me-" in slug:
        result["category"] = "Main Event"
    elif "bracelet" in title_lower or "bracelet" in source_lower or "-be-" in slug:
        result["category"] = "Bracelet Events"
    else:
        result["category"] = "Other"

    # 이벤트 번호 추출
    event_match = re.search(r'Event\s*#?(\d+)', title, re.IGNORECASE) or \
                  re.search(r'-ev-(\d+)', slug)
    if event_match:
        result["event_num"] = int(event_match.group(1))

    # Day 추출
    day_match = re.search(r'Day\s*(\d+[A-D]?)', title, re.IGNORECASE) or \
                re.search(r'day(\d+[a-d]?)', slug)
    if day_match:
        result["day"] = day_match.group(1).upper()

    # Episode 추출
    ep_match = re.search(r'Episode\s*(\d+)', title, re.IGNORECASE) or \
               re.search(r'-ep(\d+)', slug)
    if ep_match:
        result["episode"] = int(ep_match.group(1))

    # Final Table 여부
    if "final table" in title_lower or "-ft" in slug or "ft" in slug.split("-"):
        result["is_final_table"] = True

    # Livestream 여부
    if "livestream" in source_lower or "live" in source_lower:
        result["is_livestream"] = True

    return result


def similarity(s1: str, s2: str) -> float:
    """두 문자열의 유사도 계산"""
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def match_video_to_nas(video: dict, nas_files: list) -> dict:
    """단일 PokerGO 비디오와 NAS 파일 매칭"""
    meta = video['meta']
    year = meta.get('year')
    event_num = meta.get('event_num')
    day = meta.get('day')
    is_ft = meta.get('is_final_table')
    title = video.get('title', '')

    best_match = None
    best_score = 0

    for nas in nas_files:
        score = 0

        # 연도 매칭 (필수)
        if year and nas['year'] == year:
            score += 50
        elif year and nas['year'] != year:
            continue  # 연도 불일치 시 스킵

        # 이벤트 번호 매칭
        if event_num and nas['event_num'] == event_num:
            score += 30

        # Final Table 매칭
        nas_name_lower = nas['filename'].lower()
        if is_ft and ('final table' in nas_name_lower or '-ft' in nas_name_lower or 'ft' in nas_name_lower):
            score += 15

        # Day 매칭
        if day:
            day_pattern = f"day {day}|day{day}|day-{day}"
            if re.search(day_pattern, nas_name_lower, re.IGNORECASE):
                score += 15

        # 제목 유사도
        title_sim = similarity(title, nas['filename'])
        score += title_sim * 20

        if score > best_score:
            best_score = score
            best_match = nas

    return {
        'matched': best_match is not None and best_score >= 50,
        'score': best_score,
        'nas_file': best_match,
    }


def load_pokergo_data(json_path: Path) -> list:
    """PokerGO 데이터 로드"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('videos', [])


def process_and_match(videos: list, nas_files: list) -> tuple:
    """비디오 처리 및 NAS 매칭, 매칭되지 않은 NAS 파일도 반환"""
    results = []
    matched_nas_paths = set()  # 매칭된 NAS 파일 경로 추적

    for v in videos:
        title = v.get('title', '')
        slug = v.get('slug', '')
        url = v.get('url', '')
        source = v.get('source', '')
        year = v.get('year')
        thumbnail = v.get('thumbnail', '')

        # 메타데이터 파싱
        meta = parse_pokergo_title(title, slug, source)
        if not meta['year'] and year:
            meta['year'] = int(year) if isinstance(year, str) else year

        # 매칭
        video_data = {'title': title, 'meta': meta}
        match_result = match_video_to_nas(video_data, nas_files)

        nas_filename = ''
        nas_path = ''
        match_status = 'NOT_FOUND'
        match_score = 0

        if match_result['matched'] and match_result['nas_file']:
            nas_file = match_result['nas_file']
            nas_filename = nas_file['filename']
            nas_path = nas_file['path']
            match_status = 'MATCHED'
            match_score = match_result['score']
            matched_nas_paths.add(nas_path)

        results.append({
            'year': meta['year'] or '',
            'category': meta['category'] or 'Other',
            'event_num': meta['event_num'] or '',
            'day': meta['day'] or '',
            'episode': meta['episode'] or '',
            'is_final_table': 'Y' if meta['is_final_table'] else '',
            'title': title,
            'pokergo_url': url,
            'nas_filename': nas_filename,
            'nas_full_path': nas_path,
            'match_status': match_status,
            'match_score': match_score,
            'thumbnail': thumbnail,
            'source': 'PokerGO',
        })

    # 매칭되지 않은 NAS 파일 추가
    unmatched_nas = []
    for nas in nas_files:
        if nas['path'] not in matched_nas_paths:
            unmatched_nas.append({
                'year': nas['year'] or '',
                'category': nas.get('category', 'Other'),
                'event_num': nas['event_num'] or '',
                'day': '',
                'episode': '',
                'is_final_table': '',
                'title': nas['filename'],
                'pokergo_url': '',
                'nas_filename': nas['filename'],
                'nas_full_path': nas['path'],
                'match_status': 'NAS_ONLY',
                'match_score': 0,
                'thumbnail': '',
                'source': 'NAS',
            })

    # 정렬 함수
    def sort_key(x):
        year = x['year']
        year_val = -int(year) if year and str(year).isdigit() else 0
        event_val = int(x['event_num']) if x['event_num'] and str(x['event_num']).isdigit() else 999
        ep_or_day = str(x['episode'] or x['day'] or '')
        return (year_val, x['category'], event_val, ep_or_day)

    results.sort(key=sort_key)
    unmatched_nas.sort(key=sort_key)

    return results, unmatched_nas, matched_nas_paths


def upload_to_sheets(data: list, sheet_id: str, worksheet_name: str = "WSOP NAS Matching"):
    """Google Sheets에 업로드"""
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    creds_path = Path(r'd:\AI\claude01\json\service_account_key.json')
    if not creds_path.exists():
        print(f"[ERROR] Credentials not found: {creds_path}")
        return False

    creds = Credentials.from_service_account_file(str(creds_path), scopes=scopes)
    client = gspread.authorize(creds)

    try:
        sheet = client.open_by_key(sheet_id)
    except gspread.SpreadsheetNotFound:
        print(f"[ERROR] Sheet not found: {sheet_id}")
        return False

    # 워크시트 생성 또는 가져오기
    try:
        worksheet = sheet.worksheet(worksheet_name)
        worksheet.clear()
        print(f"[INFO] Cleared existing worksheet: {worksheet_name}")
    except gspread.WorksheetNotFound:
        worksheet = sheet.add_worksheet(worksheet_name, rows=len(data) + 1, cols=15)
        print(f"[INFO] Created new worksheet: {worksheet_name}")

    # 헤더
    headers = [
        'Year', 'Category', 'Event #', 'Day', 'Episode', 'Final Table',
        'Title', 'PokerGO URL',
        'NAS Filename', 'NAS Full Path', 'Match Status', 'Match Score',
        'Source', 'Thumbnail'
    ]

    # 데이터 행 준비
    rows = [headers]
    for item in data:
        rows.append([
            item['year'],
            item['category'],
            item['event_num'],
            item['day'],
            item['episode'],
            item['is_final_table'],
            item['title'],
            item['pokergo_url'],
            item['nas_filename'],
            item['nas_full_path'],
            item['match_status'],
            item['match_score'],
            item.get('source', ''),
            item['thumbnail'],
        ])

    # 업로드
    worksheet.update(rows, value_input_option='USER_ENTERED')

    print(f"\n[OK] Uploaded {len(data)} rows to '{worksheet_name}'")
    print(f"Sheet URL: https://docs.google.com/spreadsheets/d/{sheet_id}")

    return True


def main():
    # 설정 - 최종 병합 데이터 사용
    json_path = Path(__file__).parent.parent / 'data' / 'pokergo' / 'wsop_final_20251216_154021.json'
    sheet_id = '1h27Ha7pR-iYK_Gik8F4FfSvsk4s89sxk49CsU3XP_m4'

    print("=" * 60)
    print("PokerGO WSOP - NAS Matching")
    print("=" * 60)

    # NAS 파일 스캔
    print(f"\n[1/4] Scanning NAS files...")
    nas_files = scan_nas_files()
    print(f"  Found {len(nas_files)} files on NAS")

    # 연도별 NAS 통계
    nas_by_year = {}
    for f in nas_files:
        y = f.get('year', 'unknown')
        nas_by_year[y] = nas_by_year.get(y, 0) + 1
    print(f"\n  NAS files by year:")
    for y in sorted([k for k in nas_by_year.keys() if k and k != 'unknown'], reverse=True)[:10]:
        print(f"    {y}: {nas_by_year[y]}")

    # PokerGO 데이터 로드
    print(f"\n[2/4] Loading PokerGO data...")
    videos = load_pokergo_data(json_path)
    print(f"  Loaded {len(videos)} videos")

    # 처리 및 매칭
    print(f"\n[3/4] Processing and matching...")
    pokergo_results, unmatched_nas, matched_paths = process_and_match(videos, nas_files)

    # 통계
    matched = sum(1 for x in pokergo_results if x['match_status'] == 'MATCHED')
    not_found = sum(1 for x in pokergo_results if x['match_status'] == 'NOT_FOUND')
    nas_only = len(unmatched_nas)

    print(f"\n  Matching Results:")
    print(f"    MATCHED: {matched}")
    print(f"    NOT_FOUND (PokerGO only): {not_found}")
    print(f"    NAS_ONLY (no PokerGO match): {nas_only}")
    print(f"    PokerGO Match Rate: {matched/len(pokergo_results)*100:.1f}%")

    by_year = {}
    for item in pokergo_results:
        y = item['year']
        if y not in by_year:
            by_year[y] = {'total': 0, 'matched': 0}
        by_year[y]['total'] += 1
        if item['match_status'] == 'MATCHED':
            by_year[y]['matched'] += 1

    print(f"\n  PokerGO By Year:")
    for y in sorted([k for k in by_year.keys() if k], reverse=True):
        stats = by_year[y]
        rate = stats['matched']/stats['total']*100 if stats['total'] > 0 else 0
        print(f"    {y}: {stats['matched']}/{stats['total']} ({rate:.0f}%)")

    # NAS Only 연도별 통계
    nas_by_year = {}
    for item in unmatched_nas:
        y = item['year']
        nas_by_year[y] = nas_by_year.get(y, 0) + 1

    print(f"\n  NAS Only By Year:")
    for y in sorted([k for k in nas_by_year.keys() if k], reverse=True)[:10]:
        print(f"    {y}: {nas_by_year[y]}")

    # 전체 데이터 합치기 (PokerGO 먼저, 그 다음 NAS Only)
    all_data = pokergo_results + unmatched_nas

    # 업로드
    print(f"\n[4/4] Uploading to Google Sheets...")
    print(f"  Total rows: {len(all_data)} (PokerGO: {len(pokergo_results)}, NAS Only: {len(unmatched_nas)})")
    upload_to_sheets(all_data, sheet_id, "WSOP NAS Matching")

    print("\n" + "=" * 60)
    print("[DONE] NAS matching complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
