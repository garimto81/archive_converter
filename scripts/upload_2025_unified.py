"""
2025년 NAS-PokerGO 통합 시트
공통 엔티티(Year, Category, Event#, Day) 기준으로 같은 행에 배치
"""

import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build

# 설정
SERVICE_ACCOUNT_FILE = Path(r"D:\AI\claude01\json\service_account_key.json")
SPREADSHEET_ID = "1h27Ha7pR-iYK_Gik8F4FfSvsk4s89sxk49CsU3XP_m4"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

PROJECT_ROOT = Path(r"D:\AI\claude01\Archive_Converter")
UNIFIED_DB = PROJECT_ROOT / "data" / "unified_archive.db"


def get_sheets_service():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("sheets", "v4", credentials=credentials).spreadsheets()


def clear_and_upload(sheets, sheet_name: str, data: list[list]):
    # Create if not exists
    try:
        spreadsheet = sheets.get(spreadsheetId=SPREADSHEET_ID).execute()
        existing = [s["properties"]["title"] for s in spreadsheet.get("sheets", [])]
        if sheet_name not in existing:
            sheets.batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body={"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]}
            ).execute()
    except:
        pass

    # Clear
    try:
        sheets.values().clear(spreadsheetId=SPREADSHEET_ID, range=f"{sheet_name}!A:Z").execute()
    except:
        pass

    # Upload
    sheets.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{sheet_name}!A1",
        valueInputOption="RAW",
        body={"values": data}
    ).execute()
    print(f"  Uploaded {len(data)} rows to '{sheet_name}'")


def extract_event_number(text: str) -> str:
    patterns = [r"#(\d+)", r"Event\s*#?\s*(\d+)", r"EV[_-]?(\d+)"]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1).zfill(2)  # 01, 02, ... 형태로 정렬용
    return ""


def extract_day(text: str, path: str = "") -> str:
    """Day 정보 추출 - 매칭 로직과 동일하게"""
    combined = text + " " + path

    # FINAL TABLE 먼저 체크 (경로 포함)
    if re.search(r"FINAL\s*TABLE", combined, re.IGNORECASE):
        return "Final"
    # Final 키워드 (Day가 없는 경우만)
    if re.search(r"\bFinal\b", combined, re.IGNORECASE) and not re.search(r"Day\s*\d", combined, re.IGNORECASE):
        return "Final"

    # Day N 패턴
    m = re.search(r"Day\s*(\d+[A-D]?)", combined, re.IGNORECASE)
    if m:
        day = m.group(1).upper()
        # Part 정보도 추출
        part_m = re.search(r"Part\s*(\d+)", combined, re.IGNORECASE)
        if part_m:
            return f"Day {day} Part {part_m.group(1)}"
        return f"Day {day}"

    # Event# 있는데 Day 없으면 Final로 간주
    if re.search(r"Event\s*#\s*\d+", text, re.IGNORECASE):
        return "Final"

    return ""


def categorize(text: str) -> str:
    text_upper = text.upper()
    if "CIRCUIT" in text_upper or "CYPRUS" in text_upper:
        return "CIRCUIT"
    if "WSOPE" in text_upper or "EUROPE" in text_upper:
        return "WSOPE"
    if "MAIN EVENT" in text_upper or "MAIN_EVENT" in text_upper:
        return "MAIN_EVENT"
    if "BRACELET" in text_upper:
        return "BRACELET"
    if "HYPERDECK" in text_upper:
        return "HYPERDECK"
    return "OTHER"


def make_key(year, category, event_num, day) -> str:
    """공통 키 생성"""
    return f"{year}|{category}|{event_num}|{day}"


def main():
    print("=" * 60)
    print("2025 Unified Sheet - Common Entity Based")
    print("=" * 60)

    conn = sqlite3.connect(str(UNIFIED_DB))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    sheets = get_sheets_service()

    # 공통 키 기준 데이터 수집
    data_by_key = defaultdict(lambda: {"nas": [], "pokergo": []})

    # ========== NAS 데이터 수집 ==========
    c.execute("""
        SELECT file_name, relative_path, folder_path, size_gb, pokergo_matched
        FROM assets
        WHERE year = 2025 AND brand = 'WSOP'
    """)

    for row in c.fetchall():
        fname = row['file_name']
        path = row['relative_path'] or ""
        combined = fname + " " + path

        category = categorize(combined)
        event_num = extract_event_number(combined)
        day = extract_day(fname, path)  # path 별도 전달

        key = make_key(2025, category, event_num, day)

        data_by_key[key]["nas"].append({
            "file_name": fname,
            "path": path,
            "folder": row['folder_path'] or "",
            "size_gb": row['size_gb'],
            "matched": row['pokergo_matched'],
        })

    # ========== PokerGO 데이터 수집 (원본 DB에서, 중복 제거) ==========
    pg_conn = sqlite3.connect(str(PROJECT_ROOT / "data" / "pokergo" / "pokergo.db"))
    pg_conn.row_factory = sqlite3.Row
    pg_c = pg_conn.cursor()

    pg_c.execute("""
        SELECT id, title, show, season, episode, year, duration, duration_str, url
        FROM videos
        WHERE year = 2025
    """)

    seen_titles = set()  # 타이틀 중복 체크용

    for row in pg_c.fetchall():
        title = row['title'] or ""

        # 이미 처리한 타이틀은 스킵 (중복 제거)
        if title in seen_titles:
            continue
        seen_titles.add(title)

        show = row['show'] or ""
        season = row['season'] or ""
        episode = row['episode'] or ""
        combined = title + " " + show

        category = categorize(combined)
        event_num = extract_event_number(combined)
        day = extract_day(title)  # PokerGO는 title만 사용

        key = make_key(2025, category, event_num, day)

        dur_str = row['duration_str'] or ""
        if not dur_str and row['duration']:
            duration = row['duration']
            dur_str = f"{duration//60}:{duration%60:02d}"

        data_by_key[key]["pokergo"].append({
            "video_id": row['id'],
            "title": title,
            "show": show,
            "season": season,
            "episode": episode,
            "duration": dur_str,
            "url": row['url'] or "",
            "matched": False,  # 나중에 unified_db에서 확인
        })

    pg_conn.close()

    # ========== 시트 데이터 생성 ==========
    headers = [
        # 공통 엔티티
        "Year", "Category", "Event#", "Day",
        # NAS 컬럼
        "NAS_File", "NAS_Path", "NAS_Size(GB)", "NAS_Count",
        # PokerGO 컬럼
        "PG_Title", "PG_Show", "PG_Season", "PG_Episode", "PG_Duration", "PG_Count",
        # 매칭 상태
        "Match_Status", "Notes"
    ]

    sheet_data = [headers]

    # 키 정렬
    def sort_key(k):
        parts = k.split("|")
        cat_order = {"WSOPE": 1, "CIRCUIT": 2, "MAIN_EVENT": 3, "BRACELET": 4, "HYPERDECK": 5, "OTHER": 9}
        return (
            cat_order.get(parts[1], 9),
            parts[2],  # event_num (이미 zfill로 정렬 가능)
            parts[3],  # day
        )

    sorted_keys = sorted(data_by_key.keys(), key=sort_key)

    for key in sorted_keys:
        parts = key.split("|")
        year, category, event_num, day = parts

        nas_list = data_by_key[key]["nas"]
        pg_list = data_by_key[key]["pokergo"]

        # NAS 정보 (여러 개면 첫번째 + 카운트)
        if nas_list:
            nas_first = nas_list[0]
            nas_file = nas_first["file_name"]  # 전체 파일명
            nas_path = nas_first["path"]
            nas_size = f"{nas_first['size_gb']:.1f}" if nas_first['size_gb'] else ""
            nas_count = len(nas_list) if len(nas_list) > 1 else ""
        else:
            nas_file = ""
            nas_path = ""
            nas_size = ""
            nas_count = ""

        # PokerGO 정보
        if pg_list:
            pg_first = pg_list[0]
            pg_title = pg_first["title"]  # 전체 제목
            pg_show = pg_first["show"]
            pg_season = pg_first["season"]
            pg_episode = pg_first["episode"]
            pg_duration = pg_first["duration"]
            pg_count = len(pg_list) if len(pg_list) > 1 else ""
        else:
            pg_title = ""
            pg_show = ""
            pg_season = ""
            pg_episode = ""
            pg_duration = ""
            pg_count = ""

        # 매칭 상태
        if nas_list and pg_list:
            # 둘 다 있음
            if any(n["matched"] for n in nas_list):
                match_status = "MATCHED"
            else:
                match_status = "MATCH_POSSIBLE"
        elif nas_list and not pg_list:
            match_status = "NAS_ONLY"
        elif pg_list and not nas_list:
            match_status = "PG_ONLY"
        else:
            match_status = ""

        sheet_data.append([
            year,
            category,
            event_num,
            day,
            nas_file,
            nas_path,
            nas_size,
            nas_count,
            pg_title,
            pg_show,
            pg_season,
            pg_episode,
            pg_duration,
            pg_count,
            match_status,
            "",  # Notes
        ])

    clear_and_upload(sheets, "2025_Unified", sheet_data)

    # ========== 상세 시트 (NAS 여러개인 경우) ==========
    print("\n[2] Detail sheets for multi-file entries...")

    # NAS 상세
    nas_detail = [["Year", "Category", "Event#", "Day", "File", "Path", "Size(GB)", "Matched"]]
    for key in sorted_keys:
        parts = key.split("|")
        for nas in data_by_key[key]["nas"]:
            nas_detail.append([
                parts[0], parts[1], parts[2], parts[3],
                nas["file_name"],
                nas["path"],
                f"{nas['size_gb']:.1f}" if nas['size_gb'] else "",
                "Y" if nas["matched"] else "",
            ])

    clear_and_upload(sheets, "2025_NAS_Detail", nas_detail)

    # PokerGO 상세
    pg_detail = [["Year", "Category", "Event#", "Day", "Title", "Show", "Season", "Episode", "Duration", "URL", "Matched"]]
    for key in sorted_keys:
        parts = key.split("|")
        for pg in data_by_key[key]["pokergo"]:
            pg_detail.append([
                parts[0], parts[1], parts[2], parts[3],
                pg["title"],
                pg["show"],
                pg["season"],
                pg["episode"],
                pg["duration"],
                pg["url"],
                "Y" if pg["matched"] else "",
            ])

    clear_and_upload(sheets, "2025_PG_Detail", pg_detail)

    conn.close()

    print("\n" + "=" * 60)
    print("Done!")
    print(f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    print("=" * 60)
    print("\nSheets created:")
    print("  - 2025_Unified: 공통 키 기준 NAS + PokerGO 통합")
    print("  - 2025_NAS_Detail: NAS 파일 상세 목록")
    print("  - 2025_PG_Detail: PokerGO 영상 상세 목록")


if __name__ == "__main__":
    main()
