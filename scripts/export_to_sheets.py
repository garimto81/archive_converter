"""
Google Sheets용 CSV 내보내기 스크립트
PokerGO 데이터를 3개 시트로 분리하여 CSV 생성
"""

import json
import csv
from pathlib import Path

BASE_DIR = Path(r"D:\AI\claude01\Archive_Converter")
DATA_DIR = BASE_DIR / "data" / "pokergo"
OUTPUT_DIR = BASE_DIR / "data" / "sheets_export"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def export_pokergo_udm():
    """PokerGO UDM 데이터를 CSV로 내보내기"""
    udm_file = DATA_DIR / "pokergo_udm_20251212_215045.json"

    with open(udm_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    output_file = OUTPUT_DIR / "sheet1_pokergo_udm.csv"

    with open(output_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)

        # 헤더
        writer.writerow([
            "ID", "File Name", "Title", "Brand", "Year",
            "Event Type", "Game Variant", "Is Final Table",
            "Season", "Episode", "Platform", "URL", "Thumbnail",
            "Created At"
        ])

        # 데이터
        for asset in data.get("assets", []):
            ctx = asset.get("event_context", {})
            src = asset.get("source_origin", {})
            meta = asset.get("metadata", {})

            writer.writerow([
                asset.get("id", ""),
                asset.get("file_name", ""),
                meta.get("title", ""),
                ctx.get("brand", ""),
                ctx.get("year", ""),
                ctx.get("event_type", ""),
                ctx.get("game_variant", ""),
                "Y" if ctx.get("is_final_table") else "N",
                ctx.get("season", ""),
                ctx.get("episode", ""),
                src.get("platform", ""),
                src.get("url", ""),
                meta.get("thumbnail", ""),
                asset.get("created_at", "")
            ])

    print(f"[OK] Sheet 1 (UDM): {output_file}")
    print(f"     - Total {len(data.get('assets', []))} records")
    return len(data.get("assets", []))


def export_pokergo_raw():
    """PokerGO 원본 데이터를 CSV로 내보내기"""
    raw_file = DATA_DIR / "pokergo_merged_20251212_215037.json"

    with open(raw_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    output_file = OUTPUT_DIR / "sheet2_pokergo_raw.csv"

    with open(output_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)

        # 헤더
        writer.writerow([
            "URL", "Title", "Show Name", "Season", "Episode",
            "Event", "Duration", "Air Date", "Players",
            "Description", "Thumbnail", "Source"
        ])

        # 데이터
        for video in data.get("videos", []):
            players = video.get("players", [])
            players_str = "; ".join(players) if players else ""

            writer.writerow([
                video.get("url", ""),
                video.get("title", ""),
                video.get("show_name", ""),
                video.get("season", ""),
                video.get("episode", ""),
                video.get("event", ""),
                video.get("duration", ""),
                video.get("air_date", ""),
                players_str,
                video.get("description", "")[:200] if video.get("description") else "",
                video.get("thumbnail", ""),
                video.get("source", "")
            ])

    print(f"[OK] Sheet 2 (Raw): {output_file}")
    print(f"     - Total {len(data.get('videos', []))} records")
    return len(data.get("videos", []))


def create_nas_template():
    """NAS 파일 목록 템플릿 생성 (스캔 필요)"""
    output_file = OUTPUT_DIR / "sheet3_nas_files_template.csv"

    with open(output_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)

        # 헤더 (NAS 스캔 결과 구조)
        writer.writerow([
            "File Name", "File Path", "Brand", "Asset Type",
            "File Size (MB)", "Extension", "Year", "Event Number",
            "Pattern Matched", "NAS Path"
        ])

        # 샘플 데이터 (실제 스캔 필요)
        writer.writerow([
            "SAMPLE - NAS 스캔 필요", "", "", "",
            "", "", "", "", "", ""
        ])

    print(f"[WARN] Sheet 3 (NAS): {output_file}")
    print("       - Template only (NAS scan required)")
    return 0


def main():
    print("=" * 60)
    print("Google Sheets용 CSV 내보내기")
    print(f"출력 디렉토리: {OUTPUT_DIR}")
    print("=" * 60)

    udm_count = export_pokergo_udm()
    raw_count = export_pokergo_raw()
    _nas_count = create_nas_template()  # template creation only

    print("\n" + "=" * 60)
    print("DONE!")
    print(f"Total {udm_count + raw_count} records exported")
    print("\n[How to upload to Google Sheets]")
    print("1. Open Google Sheets")
    print("2. File > Import > Upload")
    print("3. Add each CSV file as a new sheet")
    print("=" * 60)


if __name__ == "__main__":
    main()
