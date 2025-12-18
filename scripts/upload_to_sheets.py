"""
Google Sheets에 CSV 데이터 직접 업로드
서비스 계정 인증 사용
"""

import csv
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# 설정
SERVICE_ACCOUNT_FILE = Path(r"D:\AI\claude01\json\service_account_key.json")
SPREADSHEET_ID = "1h27Ha7pR-iYK_Gik8F4FfSvsk4s89sxk49CsU3XP_m4"
CSV_DIR = Path(r"D:\AI\claude01\Archive_Converter\data\sheets_export")

# 스코프
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_sheets_service():
    """Google Sheets API 서비스 생성"""
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build("sheets", "v4", credentials=credentials)
    return service.spreadsheets()


def read_csv_data(csv_file: Path) -> list[list[str]]:
    """CSV 파일 읽기"""
    data = []
    with open(csv_file, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            data.append(row)
    return data


def clear_sheet(sheets, sheet_name: str):
    """시트 내용 삭제"""
    try:
        sheets.values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A:Z"
        ).execute()
        print(f"  [OK] Cleared: {sheet_name}")
    except HttpError as e:
        if e.resp.status == 400:
            # 시트가 없으면 생성
            print(f"  [INFO] Sheet '{sheet_name}' not found, will create")
        else:
            raise


def create_sheet_if_not_exists(sheets, sheet_name: str):
    """시트가 없으면 생성"""
    try:
        # 기존 시트 목록 가져오기
        spreadsheet = sheets.get(spreadsheetId=SPREADSHEET_ID).execute()
        existing_sheets = [s["properties"]["title"] for s in spreadsheet.get("sheets", [])]

        if sheet_name not in existing_sheets:
            # 새 시트 생성
            request = {
                "requests": [{
                    "addSheet": {
                        "properties": {"title": sheet_name}
                    }
                }]
            }
            sheets.batchUpdate(spreadsheetId=SPREADSHEET_ID, body=request).execute()
            print(f"  [OK] Created sheet: {sheet_name}")
        else:
            print(f"  [OK] Sheet exists: {sheet_name}")
    except HttpError as e:
        print(f"  [ERROR] Failed to create sheet: {e}")
        raise


def upload_data(sheets, sheet_name: str, data: list[list[str]]):
    """데이터 업로드"""
    try:
        # 시트 생성 (없으면)
        create_sheet_if_not_exists(sheets, sheet_name)

        # 기존 내용 삭제
        clear_sheet(sheets, sheet_name)

        # 데이터 업로드
        body = {"values": data}
        result = sheets.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A1",
            valueInputOption="RAW",
            body=body
        ).execute()

        updated_cells = result.get("updatedCells", 0)
        print(f"  [OK] Uploaded {len(data)} rows ({updated_cells} cells)")
        return True
    except HttpError as e:
        print(f"  [ERROR] Upload failed: {e}")
        return False


def format_header(sheets, sheet_name: str):
    """헤더 행 포맷팅 (굵게, 배경색)"""
    try:
        # 시트 ID 가져오기
        spreadsheet = sheets.get(spreadsheetId=SPREADSHEET_ID).execute()
        sheet_id = None
        for sheet in spreadsheet.get("sheets", []):
            if sheet["properties"]["title"] == sheet_name:
                sheet_id = sheet["properties"]["sheetId"]
                break

        if sheet_id is None:
            return

        # 헤더 포맷팅
        requests = [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.6},
                            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat)"
                }
            },
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheet_id,
                        "gridProperties": {"frozenRowCount": 1}
                    },
                    "fields": "gridProperties.frozenRowCount"
                }
            }
        ]

        sheets.batchUpdate(spreadsheetId=SPREADSHEET_ID, body={"requests": requests}).execute()
        print("  [OK] Formatted header")
    except HttpError as e:
        print(f"  [WARN] Format failed: {e}")


def main():
    print("=" * 60)
    print("Google Sheets Upload")
    print(f"Spreadsheet ID: {SPREADSHEET_ID}")
    print("=" * 60)

    # CSV 파일 매핑
    csv_files = [
        ("sheet1_pokergo_udm.csv", "PokerGO_UDM"),
        ("sheet2_pokergo_raw.csv", "PokerGO_Raw"),
        ("sheet3_nas_files.csv", "NAS_Files"),
    ]

    sheets = get_sheets_service()

    for csv_name, sheet_name in csv_files:
        csv_path = CSV_DIR / csv_name

        print(f"\n[Processing] {csv_name} -> {sheet_name}")

        if not csv_path.exists():
            print(f"  [SKIP] File not found: {csv_path}")
            continue

        # CSV 읽기
        data = read_csv_data(csv_path)
        print(f"  [OK] Read {len(data)} rows from CSV")

        # 업로드
        if upload_data(sheets, sheet_name, data):
            format_header(sheets, sheet_name)

    print("\n" + "=" * 60)
    print("DONE!")
    print(f"View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
    print("=" * 60)


if __name__ == "__main__":
    main()
