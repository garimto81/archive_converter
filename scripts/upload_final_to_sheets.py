"""
최종 WSOP 데이터를 Google Sheets에 업로드
- PokerGO URL (비디오 페이지)
- NAS 매칭 정보
"""

import json
from pathlib import Path

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "gspread", "google-auth"], check=True)
    import gspread
    from google.oauth2.service_account import Credentials


def upload_pokergo_list():
    """PokerGO 전체 리스트 업로드"""
    data_file = Path(__file__).parent.parent / "data" / "pokergo" / "wsop_final_20251216_154021.json"
    sheet_id = "1h27Ha7pR-iYK_Gik8F4FfSvsk4s89sxk49CsU3XP_m4"

    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    videos = data.get("videos", [])
    print(f"Loaded {len(videos)} videos")

    # 인증
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds_path = Path(r'd:\AI\claude01\json\service_account_key.json')
    creds = Credentials.from_service_account_file(str(creds_path), scopes=scopes)
    client = gspread.authorize(creds)

    sheet = client.open_by_key(sheet_id)

    # 워크시트 생성/가져오기
    worksheet_name = "PokerGO Videos (Full)"
    try:
        worksheet = sheet.worksheet(worksheet_name)
        worksheet.clear()
        print(f"Cleared existing: {worksheet_name}")
    except gspread.WorksheetNotFound:
        worksheet = sheet.add_worksheet(worksheet_name, rows=len(videos) + 1, cols=10)
        print(f"Created new: {worksheet_name}")

    # 헤더
    headers = [
        'Year', 'Category', 'Title', 'PokerGO URL', 'Slug', 'Source', 'Thumbnail'
    ]

    # 정렬: 연도 내림차순
    def sort_key(v):
        y = v.get('year')
        return (-int(y) if y else 0, v.get('category', ''), v.get('title', ''))

    videos.sort(key=sort_key)

    # 데이터 준비
    rows = [headers]
    for v in videos:
        rows.append([
            v.get('year', ''),
            v.get('category', ''),
            v.get('title', ''),
            v.get('url', ''),
            v.get('slug', ''),
            v.get('source', ''),
            v.get('thumbnail', ''),
        ])

    # 업로드
    worksheet.update(rows, value_input_option='USER_ENTERED')

    print(f"\n[OK] Uploaded {len(videos)} rows to '{worksheet_name}'")
    print(f"Sheet: https://docs.google.com/spreadsheets/d/{sheet_id}")

    # 카테고리별 통계
    cat_counts = {}
    for v in videos:
        c = v.get('category', 'unknown')
        cat_counts[c] = cat_counts.get(c, 0) + 1

    print("\n[BY CATEGORY]")
    for c, count in sorted(cat_counts.items()):
        print(f"  {c}: {count}")


if __name__ == "__main__":
    upload_pokergo_list()
