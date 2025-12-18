"""
2025년 매칭 분석용 통합 시트 생성
- 공통 엔티티(Year, Event#, Day)로 정렬 가능
- 매칭 전략 제안 포함
"""

import json
import re
import sqlite3
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
    service = build("sheets", "v4", credentials=credentials)
    return service.spreadsheets()


def create_sheet_if_not_exists(sheets, sheet_name: str):
    try:
        spreadsheet = sheets.get(spreadsheetId=SPREADSHEET_ID).execute()
        existing_sheets = [s["properties"]["title"] for s in spreadsheet.get("sheets", [])]
        if sheet_name not in existing_sheets:
            request = {"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]}
            sheets.batchUpdate(spreadsheetId=SPREADSHEET_ID, body=request).execute()
            print(f"  Created: {sheet_name}")
    except Exception as e:
        print(f"  Error: {e}")


def clear_and_upload(sheets, sheet_name: str, data: list[list]):
    create_sheet_if_not_exists(sheets, sheet_name)
    try:
        sheets.values().clear(spreadsheetId=SPREADSHEET_ID, range=f"{sheet_name}!A:Z").execute()
    except:
        pass
    body = {"values": data}
    sheets.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{sheet_name}!A1",
        valueInputOption="RAW",
        body=body
    ).execute()
    print(f"  Uploaded {len(data)} rows to '{sheet_name}'")


def extract_event_number(text: str) -> str:
    """이벤트 번호 추출"""
    patterns = [
        r"#(\d+)",
        r"Event\s*#?\s*(\d+)",
        r"EV[_-]?(\d+)",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1)
    return ""


def extract_day(text: str) -> str:
    """Day 정보 추출"""
    patterns = [
        r"Day\s*(\d+[A-D]?)",
        r"Final\s*(Table|Day)?",
        r"Part\s*(\d+)",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            if "Final" in p:
                return "Final"
            return f"Day {m.group(1)}"
    return ""


def categorize(fname: str, path: str) -> str:
    """카테고리 분류"""
    combined = (fname + " " + path).upper()
    if "CIRCUIT" in combined or "CYPRUS" in combined:
        return "CIRCUIT_CYPRUS"
    if "WSOPE" in combined or "EUROPE" in combined:
        return "WSOPE"
    if "MAIN EVENT" in combined or "MAIN_EVENT" in combined:
        return "MAIN_EVENT"
    if "BRACELET" in combined:
        return "BRACELET"
    if "HYPERDECK" in fname.upper():
        return "HYPERDECK_NC"
    return "OTHER"


def suggest_strategy(row: dict) -> tuple[str, str]:
    """매칭 전략 및 액션 제안"""
    source = row.get("source", "")
    category = row.get("category", "")
    matched = row.get("matched", False)
    event_num = row.get("event_num", "")

    if matched:
        return "자동매칭 완료", "확인만 필요"

    if source == "NAS":
        if category == "CIRCUIT_CYPRUS":
            return "PokerGO 없음", "메타데이터 수동입력"
        if category == "WSOPE":
            return "PokerGO 없음", "메타데이터 수동입력"
        if category == "HYPERDECK_NC":
            return "NC 원본파일", "STREAM 버전과 연결"
        if event_num:
            return "Event# 있음", "PokerGO에서 동일 Event# 찾기"
        return "패턴 불일치", "파일명 분석 필요"

    if source == "PokerGO":
        if "Table B" in row.get("title", "") or "Table C" in row.get("title", ""):
            return "멀티테이블 영상", "NAS에 없음 - 스킵 가능"
        if event_num:
            return "Event# 있음", "NAS에서 동일 Event# 찾기"
        return "매칭 대상 없음", "NAS 확인 필요"

    return "", ""


def main():
    print("=" * 60)
    print("2025 Analysis Sheet - Unified View")
    print("=" * 60)

    conn = sqlite3.connect(str(UNIFIED_DB))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    sheets = get_sheets_service()

    all_rows = []

    # ========== NAS 매칭된 파일 ==========
    c.execute("""
        SELECT a.*, m.match_confidence, m.match_type, p.title as pg_title
        FROM assets a
        JOIN nas_pokergo_matches m ON a.asset_uuid = m.asset_uuid
        JOIN pokergo_videos p ON m.pokergo_video_id = p.video_id
        WHERE a.year = 2025
    """)
    for row in c.fetchall():
        fname = row['file_name']
        path = row['relative_path'] or ""
        event_num = extract_event_number(fname + " " + path)
        day = extract_day(fname)
        category = categorize(fname, path)

        r = {
            "source": "NAS",
            "category": category,
            "event_num": event_num,
            "matched": True,
            "title": fname,
        }
        strategy, action = suggest_strategy(r)

        all_rows.append({
            "year": 2025,
            "category": category,
            "event_num": event_num,
            "day": day,
            "source": "NAS",
            "title": fname[:80],
            "path": path,
            "size_gb": f"{row['size_gb']:.1f}" if row['size_gb'] else "",
            "duration": "",
            "match_status": "MATCHED",
            "matched_with": row['pg_title'][:60] if row['pg_title'] else "",
            "confidence": f"{row['match_confidence']:.0%}" if row['match_confidence'] else "",
            "strategy": strategy,
            "action": action,
            "notes": "",
        })

    # ========== NAS 미매칭 파일 ==========
    c.execute("""
        SELECT * FROM assets
        WHERE year = 2025 AND brand = 'WSOP' AND pokergo_matched = 0
    """)
    for row in c.fetchall():
        fname = row['file_name']
        path = row['relative_path'] or ""
        event_num = extract_event_number(fname + " " + path)
        day = extract_day(fname)
        category = categorize(fname, path)

        r = {
            "source": "NAS",
            "category": category,
            "event_num": event_num,
            "matched": False,
            "title": fname,
        }
        strategy, action = suggest_strategy(r)

        all_rows.append({
            "year": 2025,
            "category": category,
            "event_num": event_num,
            "day": day,
            "source": "NAS",
            "title": fname[:80],
            "path": path,
            "size_gb": f"{row['size_gb']:.1f}" if row['size_gb'] else "",
            "duration": "",
            "match_status": "UNMATCHED",
            "matched_with": "",
            "confidence": "",
            "strategy": strategy,
            "action": action,
            "notes": "",
        })

    # ========== PokerGO 미매칭 영상 ==========
    c.execute("""
        SELECT * FROM pokergo_videos
        WHERE year = 2025 AND nas_matched = 0
    """)
    for row in c.fetchall():
        title = row['title'] or ""
        event_num = extract_event_number(title)
        day = extract_day(title)

        metadata = json.loads(row['metadata']) if row['metadata'] else {}
        show = metadata.get('show', '')

        if "Main Event" in show or "Main Event" in title:
            category = "MAIN_EVENT"
        elif "Bracelet" in show or "Bracelet" in title:
            category = "BRACELET"
        else:
            category = "OTHER"

        duration = row['duration_sec']
        dur_str = f"{duration//60}:{duration%60:02d}" if duration else ""

        r = {
            "source": "PokerGO",
            "category": category,
            "event_num": event_num,
            "matched": False,
            "title": title,
        }
        strategy, action = suggest_strategy(r)

        all_rows.append({
            "year": 2025,
            "category": category,
            "event_num": event_num,
            "day": day,
            "source": "PokerGO",
            "title": title[:80],
            "path": "",
            "size_gb": "",
            "duration": dur_str,
            "match_status": "UNMATCHED",
            "matched_with": "",
            "confidence": "",
            "strategy": strategy,
            "action": action,
            "notes": "",
        })

    # 정렬: Category > Event# > Day > Source
    def sort_key(r):
        cat_order = {"WSOPE": 1, "CIRCUIT_CYPRUS": 2, "MAIN_EVENT": 3, "BRACELET": 4, "HYPERDECK_NC": 5, "OTHER": 9}
        return (
            cat_order.get(r["category"], 9),
            r["event_num"].zfill(3) if r["event_num"] else "999",
            r["day"],
            0 if r["source"] == "NAS" else 1,
            r["match_status"],
        )

    all_rows.sort(key=sort_key)

    # 시트 데이터 생성
    headers = [
        "Year", "Category", "Event#", "Day", "Source",
        "File/Title", "Path", "Size(GB)", "Duration",
        "Match Status", "Matched With", "Confidence",
        "Strategy", "Action", "Notes"
    ]

    sheet_data = [headers]
    for r in all_rows:
        sheet_data.append([
            r["year"],
            r["category"],
            r["event_num"],
            r["day"],
            r["source"],
            r["title"],
            r["path"],
            r["size_gb"],
            r["duration"],
            r["match_status"],
            r["matched_with"],
            r["confidence"],
            r["strategy"],
            r["action"],
            r["notes"],
        ])

    clear_and_upload(sheets, "2025_Analysis", sheet_data)

    # ========== 전략 요약 시트 ==========
    print("\n[2] Strategy Summary...")

    strategy_summary = [
        ["Category", "Total", "Matched", "Unmatched", "Strategy", "Priority"],
        ["WSOPE", "", "", "", "PokerGO 없음 - 메타데이터 수동입력", "HIGH"],
        ["CIRCUIT_CYPRUS", "", "", "", "PokerGO 없음 - 메타데이터 수동입력", "HIGH"],
        ["HYPERDECK_NC", "", "", "", "NC 원본 - STREAM 버전과 연결", "MEDIUM"],
        ["MAIN_EVENT", "", "", "", "Event#/Day로 매칭", "LOW"],
        ["BRACELET", "", "", "", "Event#로 매칭", "LOW"],
        [],
        ["Action Items"],
        ["1. WSOPE/Circuit: PokerGO에 없음 -> 메타데이터 직접 입력 필요"],
        ["2. HyperDeck: NC 원본파일 -> 해당 STREAM 버전 찾아서 연결"],
        ["3. Main Event Table B/C: PokerGO만 있음 -> NAS 다운로드 or 스킵"],
        ["4. 나머지: Event# 기준 수동 매칭 가능"],
    ]

    # 카테고리별 통계 채우기
    stats = {}
    for r in all_rows:
        cat = r["category"]
        if cat not in stats:
            stats[cat] = {"total": 0, "matched": 0, "unmatched": 0}
        stats[cat]["total"] += 1
        if r["match_status"] == "MATCHED":
            stats[cat]["matched"] += 1
        else:
            stats[cat]["unmatched"] += 1

    for i, row in enumerate(strategy_summary[1:6], 1):
        cat = row[0]
        if cat in stats:
            strategy_summary[i][1] = stats[cat]["total"]
            strategy_summary[i][2] = stats[cat]["matched"]
            strategy_summary[i][3] = stats[cat]["unmatched"]

    clear_and_upload(sheets, "2025_Strategy", strategy_summary)

    conn.close()

    print("\n" + "=" * 60)
    print("Done!")
    print(f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    print("=" * 60)


if __name__ == "__main__":
    main()
