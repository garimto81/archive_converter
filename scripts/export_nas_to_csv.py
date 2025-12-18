"""
NAS 파일 목록을 CSV로 내보내기
"""

import csv
import importlib.util
from pathlib import Path

BASE_DIR = Path(r"D:\AI\claude01\Archive_Converter")
OUTPUT_DIR = BASE_DIR / "data" / "sheets_export"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# nas_scanner 모듈 직접 로드 (패키지 __init__ 우회)
_nas_scanner_path = BASE_DIR / "src" / "extractors" / "nas_scanner.py"
_spec = importlib.util.spec_from_file_location("nas_scanner", _nas_scanner_path)
_nas_scanner_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_nas_scanner_module)
NasScanner = _nas_scanner_module.NasScanner

# udm 모듈 직접 로드
_udm_path = BASE_DIR / "src" / "models" / "udm.py"
_spec_udm = importlib.util.spec_from_file_location("udm", _udm_path)
_udm_module = importlib.util.module_from_spec(_spec_udm)
_spec_udm.loader.exec_module(_udm_module)
parse_filename = _udm_module.parse_filename


def export_nas_files():
    """NAS 파일 목록을 CSV로 내보내기"""

    # NAS 경로 확인
    nas_paths = [
        Path(r"Z:\ARCHIVE"),
        Path(r"\\10.10.100.122\docker\GGPNAs\ARCHIVE"),
    ]

    nas_path = None
    for p in nas_paths:
        if p.exists():
            nas_path = p
            print(f"[OK] NAS found: {nas_path}")
            break

    if nas_path is None:
        print("[ERROR] NAS not accessible!")
        print("Tried paths:")
        for p in nas_paths:
            print(f"  - {p}")
        return 0

    # 스캐너 초기화
    scanner = NasScanner(
        root_path=str(nas_path),
        include_hidden=False,
        compute_hash=False,
    )

    print("[INFO] Scanning NAS... (this may take a while)")
    files, stats = scanner.scan_with_stats(video_only=True)

    print(f"[OK] Found {len(files)} video files")
    print(f"     Total size: {stats.total_size_gb:.2f} GB")
    print(f"     Scan duration: {stats.scan_duration_sec:.2f} sec")

    # CSV 출력
    output_file = OUTPUT_DIR / "sheet3_nas_files.csv"

    with open(output_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)

        # 헤더
        writer.writerow([
            "File Name", "Extension", "Size (MB)", "Modified At",
            "Brand (Inferred)", "Asset Type (Inferred)", "Folder Path",
            "Pattern Matched", "Year", "Event Num", "Full Path"
        ])

        # 데이터
        for file_info in files:
            # 파일명 파싱 시도
            try:
                parsed = parse_filename(file_info.filename)
                pattern_matched = parsed.pattern_matched or ""
                year = parsed.year_code or ""
                event_num = parsed.sequence_num or ""
            except Exception:
                pattern_matched = ""
                year = ""
                event_num = ""

            writer.writerow([
                file_info.filename,
                file_info.extension,
                round(file_info.size_mb, 2),
                file_info.modified_at.strftime("%Y-%m-%d %H:%M:%S") if file_info.modified_at else "",
                file_info.inferred_brand or "",
                file_info.inferred_asset_type or "",
                file_info.folder_path,
                pattern_matched,
                year,
                event_num,
                file_info.path,
            ])

    print(f"[OK] Exported: {output_file}")

    # 브랜드별 통계
    print("\n[STATS] Brand distribution:")
    for brand, count in sorted(stats.brand_counts.items(), key=lambda x: -x[1]):
        print(f"     {brand}: {count}")

    # 확장자별 통계
    print("\n[STATS] Extension distribution:")
    for ext, count in sorted(stats.extension_counts.items(), key=lambda x: -x[1]):
        print(f"     {ext}: {count}")

    return len(files)


if __name__ == "__main__":
    print("=" * 60)
    print("NAS File Export to CSV")
    print("=" * 60)

    count = export_nas_files()

    print("\n" + "=" * 60)
    if count > 0:
        print(f"DONE! Exported {count} files")
    else:
        print("No files exported (NAS not accessible)")
    print("=" * 60)
