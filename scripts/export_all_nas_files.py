"""
전체 NAS 파일 목록 추출 (제외 대상 체크박스 포함)

- 모든 NAS 파일 스캔
- 제외 대상 체크박스로 표시:
  - [x] clip
  - [x] highlight
  - [x] paradise
  - [x] circuit
  - [x] 1GB 초과
"""

import re
from pathlib import Path

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.run(["pip", "install", "gspread", "google-auth"], check=True)
    import gspread
    from google.oauth2.service_account import Credentials


# NAS 경로
NAS_BASE = Path("Z:/ARCHIVE/WSOP")

# 제외 키워드
EXCLUDE_KEYWORDS = ['clip', 'highlight', 'paradise', 'circuit']
MAX_SIZE_GB = 1.0


def scan_all_nas_files() -> list:
    """모든 NAS 파일 스캔 (필터 없이)"""
    all_files = []

    def scan_folder(folder: Path, category: str = ""):
        if not folder.exists():
            return

        for item in folder.iterdir():
            if item.is_file() and item.suffix.lower() in ['.mp4', '.mov', '.mxf']:
                path_str = str(item)
                path_lower = path_str.lower()

                # 크기
                size_gb = item.stat().st_size / (1024**3)

                # 제외 사유 확인
                exclude_reasons = []
                for kw in EXCLUDE_KEYWORDS:
                    if kw in path_lower:
                        exclude_reasons.append(kw)

                if size_gb > MAX_SIZE_GB:
                    exclude_reasons.append(f">{MAX_SIZE_GB}GB")

                is_excluded = len(exclude_reasons) > 0

                # 연도 추출
                year = None
                for y in range(1973, 2026):
                    if str(y) in path_str:
                        year = y
                        break

                # 이벤트 번호 추출
                event_num = None
                ev_match = re.search(r'Event\s*#?\s*(\d+)|ev-(\d+)|ev(\d+)', item.name, re.IGNORECASE)
                if ev_match:
                    event_num = int(ev_match.group(1) or ev_match.group(2) or ev_match.group(3))

                all_files.append({
                    'filename': item.name,
                    'path': path_str,
                    'folder': str(item.parent),
                    'category': category,
                    'year': year,
                    'event_num': event_num,
                    'size_gb': round(size_gb, 3),
                    'is_excluded': is_excluded,
                    'exclude_reasons': ', '.join(exclude_reasons) if exclude_reasons else '',
                })

            elif item.is_dir():
                sub_cat = category
                name_lower = item.name.lower()
                if 'main event' in name_lower:
                    sub_cat = 'Main Event'
                elif 'bracelet' in name_lower:
                    sub_cat = 'Bracelet Events'
                elif 'mastered' in name_lower:
                    sub_cat = 'Mastered'
                elif 'clean' in name_lower:
                    sub_cat = 'Clean'
                scan_folder(item, sub_cat)

    print("[NAS] Scanning ALL files...")

    # 모든 하위 폴더 스캔
    for item in NAS_BASE.iterdir():
        if item.is_dir():
            print(f"  Scanning: {item.name}")
            scan_folder(item, item.name)

    return all_files


def upload_to_sheets(data: list, sheet_id: str, worksheet_name: str = "NAS All Files"):
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
        worksheet = sheet.add_worksheet(worksheet_name, rows=len(data) + 1, cols=12)
        print(f"[INFO] Created new worksheet: {worksheet_name}")

    # 헤더
    headers = [
        'Excluded', 'Exclude Reason', 'Year', 'Category', 'Event #',
        'Filename', 'Size (GB)', 'Folder', 'Full Path'
    ]

    # 데이터 행 준비
    rows = [headers]
    for item in data:
        rows.append([
            'TRUE' if item['is_excluded'] else 'FALSE',  # 체크박스용
            item['exclude_reasons'],
            item['year'] or '',
            item['category'],
            item['event_num'] or '',
            item['filename'],
            item['size_gb'],
            item['folder'],
            item['path'],
        ])

    # 업로드
    worksheet.update(rows, value_input_option='USER_ENTERED')

    # 체크박스 형식 적용 (A열)
    try:
        # 체크박스 데이터 유효성 검사 규칙 설정
        worksheet.format('A2:A' + str(len(data) + 1), {
            "numberFormat": {"type": "TEXT"}
        })
    except Exception as e:
        print(f"  Note: Could not apply checkbox format: {e}")

    print(f"\n[OK] Uploaded {len(data)} rows to '{worksheet_name}'")
    print(f"Sheet URL: https://docs.google.com/spreadsheets/d/{sheet_id}")

    return True


def main():
    sheet_id = '1h27Ha7pR-iYK_Gik8F4FfSvsk4s89sxk49CsU3XP_m4'

    print("=" * 60)
    print("NAS All Files Export")
    print("=" * 60)
    print(f"\nExclude keywords: {', '.join(EXCLUDE_KEYWORDS)}")
    print(f"Max size: {MAX_SIZE_GB}GB")

    # 스캔
    print("\n[1/2] Scanning NAS files...")
    all_files = scan_all_nas_files()
    print(f"  Total files: {len(all_files)}")

    # 통계
    excluded = sum(1 for f in all_files if f['is_excluded'])
    included = len(all_files) - excluded

    print("\n  Statistics:")
    print(f"    Excluded: {excluded}")
    print(f"    Included: {included}")

    # 제외 사유별 통계
    reason_counts = {}
    for f in all_files:
        if f['is_excluded']:
            for reason in f['exclude_reasons'].split(', '):
                if reason:
                    reason_counts[reason] = reason_counts.get(reason, 0) + 1

    print("\n  Exclude Reasons:")
    for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
        print(f"    {reason}: {count}")

    # 연도별 통계
    by_year = {}
    for f in all_files:
        y = f['year'] or 'unknown'
        if y not in by_year:
            by_year[y] = {'total': 0, 'excluded': 0}
        by_year[y]['total'] += 1
        if f['is_excluded']:
            by_year[y]['excluded'] += 1

    print("\n  By Year (top 15):")
    for y in sorted([k for k in by_year.keys() if k != 'unknown'], reverse=True)[:15]:
        stats = by_year[y]
        print(f"    {y}: {stats['total']} (excluded: {stats['excluded']})")

    # 정렬: Excluded 먼저, 그 다음 연도 내림차순
    def sort_key(x):
        year = x['year']
        year_val = -int(year) if year else 0
        return (0 if x['is_excluded'] else 1, year_val, x['filename'])

    all_files.sort(key=sort_key)

    # 업로드
    print("\n[2/2] Uploading to Google Sheets...")
    upload_to_sheets(all_files, sheet_id, "NAS All Files")

    print("\n" + "=" * 60)
    print("[DONE] Export complete")
    print("=" * 60)
    print("\nNote: 'Excluded' column shows TRUE for files matching exclude rules")
    print("      Filter by 'Excluded' = FALSE to see valid files")


if __name__ == "__main__":
    main()
