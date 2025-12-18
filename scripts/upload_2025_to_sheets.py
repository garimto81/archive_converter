"""
2025년 NAS-PokerGO 매칭 결과를 Google Sheets에 업로드
"""

import json
import sqlite3
import sys
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# 설정
SERVICE_ACCOUNT_FILE = Path(r"D:\AI\claude01\json\service_account_key.json")
SPREADSHEET_ID = "1h27Ha7pR-iYK_Gik8F4FfSvsk4s89sxk49CsU3XP_m4"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

PROJECT_ROOT = Path(r"D:\AI\claude01\Archive_Converter")
UNIFIED_DB = PROJECT_ROOT / "data" / "unified_archive.db"


def get_sheets_service():
    """Google Sheets API 서비스 생성"""
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build("sheets", "v4", credentials=credentials)
    return service.spreadsheets()


def create_sheet_if_not_exists(sheets, sheet_name: str):
    """시트가 없으면 생성"""
    try:
        spreadsheet = sheets.get(spreadsheetId=SPREADSHEET_ID).execute()
        existing_sheets = [s["properties"]["title"] for s in spreadsheet.get("sheets", [])]

        if sheet_name not in existing_sheets:
            request = {
                "requests": [{
                    "addSheet": {
                        "properties": {"title": sheet_name}
                    }
                }]
            }
            sheets.batchUpdate(spreadsheetId=SPREADSHEET_ID, body=request).execute()
            print(f"  Created sheet: {sheet_name}")
    except HttpError as e:
        print(f"  Error: {e}")


def clear_and_upload(sheets, sheet_name: str, data: list[list]):
    """시트 클리어 후 업로드"""
    create_sheet_if_not_exists(sheets, sheet_name)

    # Clear
    try:
        sheets.values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A:Z"
        ).execute()
    except:
        pass

    # Upload
    body = {"values": data}
    result = sheets.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{sheet_name}!A1",
        valueInputOption="RAW",
        body=body
    ).execute()

    print(f"  Uploaded {len(data)} rows to '{sheet_name}'")


def main():
    print("=" * 60)
    print("2025 NAS-PokerGO Matching Results -> Google Sheets")
    print("=" * 60)

    conn = sqlite3.connect(str(UNIFIED_DB))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    sheets = get_sheets_service()

    # ========== 1. NAS 매칭 결과 ==========
    print("\n[1] NAS Matched Files...")
    c.execute("""
        SELECT
            a.file_name,
            a.relative_path,
            a.size_gb,
            a.brand,
            m.match_type,
            m.match_confidence,
            p.title as pokergo_title
        FROM nas_pokergo_matches m
        JOIN assets a ON m.asset_uuid = a.asset_uuid
        JOIN pokergo_videos p ON m.pokergo_video_id = p.video_id
        WHERE a.year = 2025
        ORDER BY m.match_confidence DESC, a.file_name
    """)

    matched_data = [
        ["File Name", "Path", "Size(GB)", "Brand", "Match Type", "Confidence", "PokerGO Title"]
    ]
    for row in c.fetchall():
        matched_data.append([
            row['file_name'],
            row['relative_path'],
            f"{row['size_gb']:.2f}" if row['size_gb'] else "",
            row['brand'],
            row['match_type'],
            f"{row['match_confidence']:.0%}" if row['match_confidence'] else "",
            row['pokergo_title']
        ])

    clear_and_upload(sheets, "2025_NAS_Matched", matched_data)

    # ========== 2. NAS 미매칭 결과 ==========
    print("\n[2] NAS Unmatched Files...")
    c.execute("""
        SELECT
            file_name,
            relative_path,
            folder_path,
            size_gb,
            brand,
            asset_type
        FROM assets
        WHERE year = 2025 AND brand = 'WSOP' AND pokergo_matched = 0
        ORDER BY relative_path, file_name
    """)

    unmatched_nas_data = [
        ["File Name", "Path", "Folder", "Size(GB)", "Brand", "Asset Type", "Category", "Note"]
    ]
    for row in c.fetchall():
        fname = row['file_name']
        path = row['relative_path'] or ""

        # 카테고리 분류
        if "Circuit" in fname or "Circuit" in path or "Cyprus" in fname:
            category = "WSOP_CIRCUIT_CYPRUS"
            note = "PokerGO 없음 - 수동입력"
        elif "WSOPE" in fname or "WSOPE" in path:
            category = "WSOPE"
            note = "PokerGO 없음 - 수동입력"
        elif "HyperDeck" in fname:
            category = "HYPERDECK_RAW"
            note = "NC 원본 파일"
        elif any(ord(ch) > 127 for ch in fname[:5]):
            category = "EMOJI_FILE"
            note = "특수문자 포함"
        else:
            category = "OTHER"
            note = ""

        unmatched_nas_data.append([
            row['file_name'],
            row['relative_path'],
            row['folder_path'],
            f"{row['size_gb']:.2f}" if row['size_gb'] else "",
            row['brand'],
            row['asset_type'],
            category,
            note
        ])

    clear_and_upload(sheets, "2025_NAS_Unmatched", unmatched_nas_data)

    # ========== 3. PokerGO 미매칭 결과 ==========
    print("\n[3] PokerGO Unmatched Videos...")
    c.execute("""
        SELECT
            video_id,
            title,
            duration_sec,
            metadata
        FROM pokergo_videos
        WHERE year = 2025 AND nas_matched = 0
        ORDER BY title
    """)

    unmatched_pg_data = [
        ["Video ID", "Title", "Duration", "Show", "Season", "Note"]
    ]
    for row in c.fetchall():
        metadata = json.loads(row['metadata']) if row['metadata'] else {}
        show = metadata.get('show', '')
        season = metadata.get('season', '')
        duration = row['duration_sec']
        duration_str = f"{duration//60}:{duration%60:02d}" if duration else ""

        # 노트 추가
        title = row['title']
        if "Table B" in title or "Table C" in title:
            note = "멀티테이블 - NAS 없음"
        else:
            note = ""

        unmatched_pg_data.append([
            row['video_id'],
            row['title'],
            duration_str,
            show,
            str(season) if season else "",
            note
        ])

    clear_and_upload(sheets, "2025_PokerGO_Unmatched", unmatched_pg_data)

    # ========== 4. Summary ==========
    print("\n[4] Summary...")
    c.execute("SELECT COUNT(*) FROM assets WHERE year = 2025 AND brand = 'WSOP'")
    nas_total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM assets WHERE year = 2025 AND brand = 'WSOP' AND pokergo_matched = 1")
    nas_matched = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM pokergo_videos WHERE year = 2025")
    pg_total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM pokergo_videos WHERE year = 2025 AND nas_matched = 1")
    pg_matched = c.fetchone()[0]

    summary_data = [
        ["Category", "Total", "Matched", "Unmatched", "Match Rate"],
        ["NAS 2025", nas_total, nas_matched, nas_total - nas_matched, f"{100*nas_matched/nas_total:.1f}%"],
        ["PokerGO 2025", pg_total, pg_matched, pg_total - pg_matched, f"{100*pg_matched/pg_total:.1f}%"],
        [],
        ["NAS Unmatched Categories", "Count", "Size(GB)"],
    ]

    # 카테고리별 통계
    c.execute("""
        SELECT
            CASE
                WHEN file_name LIKE '%Circuit%' OR relative_path LIKE '%Circuit%' OR file_name LIKE '%Cyprus%' THEN 'WSOP_CIRCUIT_CYPRUS'
                WHEN file_name LIKE '%WSOPE%' OR relative_path LIKE '%WSOPE%' THEN 'WSOPE'
                WHEN file_name LIKE '%HyperDeck%' THEN 'HYPERDECK_RAW'
                ELSE 'OTHER'
            END as category,
            COUNT(*) as cnt,
            SUM(size_gb) as total_gb
        FROM assets
        WHERE year = 2025 AND brand = 'WSOP' AND pokergo_matched = 0
        GROUP BY category
    """)
    for row in c.fetchall():
        summary_data.append([row[0], row[1], f"{row[2]:.1f}" if row[2] else "0"])

    clear_and_upload(sheets, "2025_Summary", summary_data)

    conn.close()

    print("\n" + "=" * 60)
    print("Done! Check spreadsheet:")
    print(f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    print("=" * 60)


if __name__ == "__main__":
    main()
