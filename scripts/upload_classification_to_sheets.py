"""
NAS 분류 결과를 Google Sheets에 업로드

Usage:
    python scripts/upload_classification_to_sheets.py
"""

import sqlite3
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 설정
SPREADSHEET_ID = "1h27Ha7pR-iYK_Gik8F4FfSvsk4s89sxk49CsU3XP_m4"
SERVICE_ACCOUNT_FILE = r"D:\AI\claude01\json\service_account_key.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_service():
    """Google Sheets 서비스 객체 생성"""
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("sheets", "v4", credentials=creds)


def create_new_sheet(service, title: str):
    """새 시트 생성"""
    request = {
        "requests": [
            {
                "addSheet": {
                    "properties": {
                        "title": title,
                    }
                }
            }
        ]
    }
    result = service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID, body=request
    ).execute()
    return result["replies"][0]["addSheet"]["properties"]["sheetId"]


def format_sheet(service, sheet_id: int):
    """시트 포맷팅 (헤더 고정, 색상 등)"""
    requests = [
        # 헤더 행 고정
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "gridProperties": {"frozenRowCount": 1},
                },
                "fields": "gridProperties.frozenRowCount",
            }
        },
        # 헤더 배경색 (파란색)
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.8},
                        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat)",
            }
        },
        # 열 너비 자동 조정
        {
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": 0,
                    "endIndex": 15,
                }
            }
        },
    ]

    service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID, body={"requests": requests}
    ).execute()


def upload_classification_data(service, sheet_title: str):
    """분류 데이터 업로드"""
    # DB에서 데이터 로드
    conn = sqlite3.connect("data/nas_classified.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT
            natural_title,
            brand,
            year,
            event_type,
            event_num,
            day_or_episode,
            day_type,
            game_type,
            content_type,
            confidence,
            parse_method,
            original_filename,
            original_path
        FROM classified_files
        ORDER BY year DESC, brand, event_type, day_or_episode
    """)
    rows = cur.fetchall()
    conn.close()

    # 헤더 + 데이터
    headers = [
        "Natural Title",
        "Brand",
        "Year",
        "Event Type",
        "Event #",
        "Day/Episode",
        "Type",
        "Game",
        "Content",
        "Confidence",
        "Parse Method",
        "Original Filename",
        "Original Path",
    ]

    data = [headers]
    for row in rows:
        data.append(list(row))

    # 시트에 쓰기
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"'{sheet_title}'!A1",
        valueInputOption="USER_ENTERED",
        body={"values": data},
    ).execute()

    return len(rows)


def upload_summary_sheet(service, sheet_title: str):
    """요약 시트 업로드"""
    conn = sqlite3.connect("data/nas_classified.db")
    cur = conn.cursor()

    # 요약 데이터 준비
    summary_data = [
        ["NAS File Classification Summary"],
        ["Generated: 2025-12-18"],
        [""],
        ["=== Brand Distribution ==="],
        ["Brand", "Count", "Percentage"],
    ]

    cur.execute("SELECT COUNT(*) FROM classified_files")
    total = cur.fetchone()[0]

    cur.execute("SELECT brand, COUNT(*) FROM classified_files GROUP BY brand ORDER BY COUNT(*) DESC")
    for row in cur.fetchall():
        pct = f"{row[1] * 100 / total:.1f}%"
        summary_data.append([row[0], row[1], pct])

    summary_data.append([""])
    summary_data.append(["=== Event Type Distribution ==="])
    summary_data.append(["Event Type", "Count", "Percentage"])

    cur.execute("SELECT event_type, COUNT(*) FROM classified_files GROUP BY event_type ORDER BY COUNT(*) DESC")
    for row in cur.fetchall():
        pct = f"{row[1] * 100 / total:.1f}%"
        summary_data.append([row[0], row[1], pct])

    summary_data.append([""])
    summary_data.append(["=== Year Distribution (Top 20) ==="])
    summary_data.append(["Year", "Count"])

    cur.execute("SELECT year, COUNT(*) FROM classified_files GROUP BY year ORDER BY year DESC LIMIT 20")
    for row in cur.fetchall():
        summary_data.append([row[0], row[1]])

    summary_data.append([""])
    summary_data.append(["=== Confidence Distribution ==="])
    summary_data.append(["Level", "Count"])

    cur.execute("SELECT COUNT(*) FROM classified_files WHERE confidence >= 0.85")
    summary_data.append(["High (>=0.85)", cur.fetchone()[0]])

    cur.execute("SELECT COUNT(*) FROM classified_files WHERE confidence >= 0.7 AND confidence < 0.85")
    summary_data.append(["Medium (0.7-0.85)", cur.fetchone()[0]])

    cur.execute("SELECT COUNT(*) FROM classified_files WHERE confidence < 0.7")
    summary_data.append(["Low (<0.7)", cur.fetchone()[0]])

    summary_data.append([""])
    summary_data.append(["Total Files", total])

    conn.close()

    # 시트에 쓰기
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"'{sheet_title}'!A1",
        valueInputOption="USER_ENTERED",
        body={"values": summary_data},
    ).execute()


def main():
    print("=" * 60)
    print("Upload NAS Classification to Google Sheets")
    print("=" * 60)

    service = get_service()

    # 1. 요약 시트 생성
    summary_sheet = "NAS_Classification_Summary"
    print(f"\nCreating sheet: {summary_sheet}")
    try:
        sheet_id = create_new_sheet(service, summary_sheet)
        format_sheet(service, sheet_id)
    except Exception as e:
        print(f"Sheet may already exist: {e}")

    print("Uploading summary data...")
    upload_summary_sheet(service, summary_sheet)

    # 2. 전체 데이터 시트 생성
    data_sheet = "NAS_Classification_Data"
    print(f"\nCreating sheet: {data_sheet}")
    try:
        sheet_id = create_new_sheet(service, data_sheet)
        format_sheet(service, sheet_id)
    except Exception as e:
        print(f"Sheet may already exist: {e}")

    print("Uploading classification data...")
    count = upload_classification_data(service, data_sheet)

    print(f"\n[OK] Uploaded {count} records to Google Sheets")
    print(f"\nSpreadsheet URL:")
    print(f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")


if __name__ == "__main__":
    main()
