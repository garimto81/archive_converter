"""
NAS 전체 재스캔 및 통합 DB 적재 스크립트

Z: 드라이브 (\\10.10.100.122\docker\GGPNAs\ARCHIVE) 전체 스캔
→ unified_archive.db의 assets 테이블에 적재
"""

import json
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

# 프로젝트 루트 추가
PROJECT_ROOT = Path(r"D:\AI\claude01\Archive_Converter")
sys.path.insert(0, str(PROJECT_ROOT))

from src.extractors.nas_scanner import NasScanner, NasFileInfo
from src.models.udm import parse_filename, Brand, AssetType

DATA_DIR = PROJECT_ROOT / "data"
UNIFIED_DB = DATA_DIR / "unified_archive.db"

# NAS 경로 설정
NAS_ROOT = Path(r"Z:\ARCHIVE")  # 마운트된 NAS 경로
# NAS_ROOT = Path(r"\\10.10.100.122\docker\GGPNAs\ARCHIVE")  # UNC 경로


def infer_brand_from_path(relative_path: str, filename: str) -> str:
    """경로와 파일명에서 브랜드 추론"""
    path_upper = relative_path.upper()
    filename_upper = filename.upper()

    # 경로 기반 추론
    brand_patterns = {
        "WSOP": ["WSOP", "WSOPE", "WSOPC", "WSOPP"],
        "HCL": ["HCL", "HUSTLER"],
        "PAD": ["PAD", "POKERAFTERDARK", "POKER AFTER DARK"],
        "GGMillions": ["GGMILLIONS", "GGM"],
        "MPP": ["MPP", "MALTA"],
        "GOG": ["GOG", "GAMEOFGOLD", "GAME OF GOLD"],
        "WPT": ["WPT"],
        "EPT": ["EPT"],
    }

    combined = path_upper + " " + filename_upper

    for brand, patterns in brand_patterns.items():
        for pattern in patterns:
            if pattern in combined:
                return brand

    return "OTHER"


def infer_asset_type_from_path(relative_path: str, filename: str) -> str:
    """경로와 파일명에서 AssetType 추론"""
    path_upper = relative_path.upper()
    filename_upper = filename.upper()
    combined = path_upper + " " + filename_upper

    asset_type_patterns = {
        "STREAM": ["STREAM", "STREAMS"],
        "SUBCLIP": ["SUBCLIP", "SUBCLIPS", "SUB_"],
        "MASTER": ["MASTERED", "MASTER"],
        "HAND_CLIP": ["HAND", "HANDS"],
        "CLEAN": ["CLEAN"],
        "RAW": ["RAW"],
        "GENERIC": ["GENERIC"],
    }

    for asset_type, patterns in asset_type_patterns.items():
        for pattern in patterns:
            if pattern in combined:
                return asset_type

    # 확장자 기반 추론
    ext = Path(filename).suffix.lower()
    if ext == ".mov":
        return "MOV"
    elif ext == ".mxf":
        return "MXF"

    return "GENERIC"


def extract_year_from_path(relative_path: str, filename: str) -> int | None:
    """경로와 파일명에서 연도 추출"""
    import re

    combined = relative_path + " " + filename

    # 4자리 연도 패턴 (2000-2030)
    year_match = re.search(r"(20[0-3]\d)", combined)
    if year_match:
        return int(year_match.group(1))

    # 2자리 연도 패턴 (00-30)
    year_2digit = re.search(r"[-_](\d{2})[-_]", combined)
    if year_2digit:
        year = int(year_2digit.group(1))
        if year <= 30:
            return 2000 + year
        elif year >= 90:
            return 1900 + year

    return None


def file_info_to_asset(file_info: NasFileInfo) -> dict:
    """NasFileInfo를 assets 테이블 row로 변환"""

    # 파일명 파싱
    filename_meta = None
    try:
        parsed = parse_filename(file_info.filename)
        if parsed:
            filename_meta = {
                "code_prefix": parsed.code_prefix,
                "year_code": parsed.year_code,
                "sequence_num": parsed.sequence_num,
                "clip_type": parsed.clip_type,
                "raw_description": parsed.raw_description,
                "season": parsed.season,
                "episode": parsed.episode,
                "event_number": parsed.event_number,
                "buyin_code": parsed.buyin_code,
                "game_code": parsed.game_code,
            }
    except Exception:
        pass

    # 브랜드 추론
    brand = infer_brand_from_path(file_info.relative_path, file_info.filename)

    # AssetType 추론
    asset_type = infer_asset_type_from_path(file_info.relative_path, file_info.filename)

    # 연도 추출
    year = extract_year_from_path(file_info.relative_path, file_info.filename)

    # 이벤트 컨텍스트
    event_context = {
        "year": year,
        "brand": brand,
    }

    # 이벤트 번호 추출 (파일명 메타에서)
    event_number = None
    season = None
    episode = None
    if filename_meta:
        event_number = filename_meta.get("event_number")
        season = filename_meta.get("season")
        episode = filename_meta.get("episode")

    return {
        "asset_uuid": str(uuid4()),
        "file_name": file_info.filename,
        "file_path": file_info.path,
        "relative_path": file_info.relative_path,
        "folder_path": file_info.folder_path,
        "extension": file_info.extension,
        "size_bytes": file_info.size_bytes,
        "size_gb": file_info.size_gb,
        "modified_at": file_info.modified_at.isoformat() if file_info.modified_at else None,
        "brand": brand,
        "asset_type": asset_type,
        "event_context": json.dumps(event_context, ensure_ascii=False),
        "filename_meta": json.dumps(filename_meta, ensure_ascii=False) if filename_meta else None,
        "source_origin": "NAS",
        "source_id": f"NAS_{file_info.relative_path}",
        "year": year,
        "event_number": event_number,
        "season": season,
        "episode": episode,
        "classification": brand,  # 초기 분류는 브랜드로
    }


def rescan_nas():
    """NAS 전체 재스캔 실행"""

    print("=" * 60)
    print("NAS Full Rescan Starting")
    print("=" * 60)
    print(f"NAS Path: {NAS_ROOT}")
    print(f"Unified DB: {UNIFIED_DB}")
    print()

    # NAS 경로 확인
    if not NAS_ROOT.exists():
        print(f"[ERROR] NAS path not found: {NAS_ROOT}")
        print("Check if Z: drive is mounted.")
        return

    # DB 연결
    conn = sqlite3.connect(str(UNIFIED_DB))
    cursor = conn.cursor()

    # 스캔 이력 기록 시작
    scan_start = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO scan_history (scan_type, started_at, scan_path, status)
        VALUES ('full', ?, ?, 'running')
    """, (scan_start, str(NAS_ROOT)))
    scan_id = cursor.lastrowid
    conn.commit()

    # 기존 assets 삭제 (전체 재스캔)
    cursor.execute("DELETE FROM assets WHERE source_origin = 'NAS'")
    deleted_count = cursor.rowcount
    print(f"Deleted existing NAS data: {deleted_count} rows")
    conn.commit()

    # NAS 스캐너 초기화
    scanner = NasScanner(str(NAS_ROOT), include_hidden=False, compute_hash=False)

    # 스캔 실행
    start_time = time.time()
    total_files = 0
    error_count = 0
    batch = []
    batch_size = 100

    print("\nScanning...")

    try:
        for file_info in scanner.scan(video_only=True):
            try:
                asset = file_info_to_asset(file_info)
                batch.append(asset)
                total_files += 1

                # 배치 삽입
                if len(batch) >= batch_size:
                    insert_batch(cursor, batch)
                    conn.commit()
                    print(f"  {total_files} files processed...", end="\r")
                    batch = []

            except Exception as e:
                error_count += 1
                print(f"\n[WARN] Error: {file_info.filename} - {e}")

        # 남은 배치 삽입
        if batch:
            insert_batch(cursor, batch)
            conn.commit()

    except Exception as e:
        print(f"\n[ERROR] Scan error: {e}")
        cursor.execute("""
            UPDATE scan_history
            SET status = 'failed', error_message = ?, completed_at = ?
            WHERE scan_id = ?
        """, (str(e), datetime.now().isoformat(), scan_id))
        conn.commit()
        conn.close()
        return

    elapsed = time.time() - start_time

    # 스캔 이력 업데이트
    cursor.execute("""
        UPDATE scan_history
        SET status = 'completed',
            completed_at = ?,
            total_files = ?,
            new_files = ?,
            errors = ?
        WHERE scan_id = ?
    """, (datetime.now().isoformat(), total_files, total_files, error_count, scan_id))
    conn.commit()

    # 통계 출력
    print("\n" + "=" * 60)
    print("Scan Complete!")
    print("=" * 60)
    print(f"Total files: {total_files}")
    print(f"Errors: {error_count}")
    print(f"Elapsed: {elapsed:.1f}s")

    # 브랜드별 통계
    cursor.execute("""
        SELECT brand, COUNT(*) as cnt
        FROM assets
        WHERE source_origin = 'NAS'
        GROUP BY brand
        ORDER BY cnt DESC
    """)
    print("\nBrand Statistics:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    conn.close()


def insert_batch(cursor, batch: list[dict]):
    """배치 삽입"""
    if not batch:
        return

    columns = list(batch[0].keys())
    placeholders = ", ".join(["?" for _ in columns])
    columns_str = ", ".join(columns)

    cursor.executemany(
        f"INSERT INTO assets ({columns_str}) VALUES ({placeholders})",
        [tuple(row.values()) for row in batch]
    )


if __name__ == "__main__":
    # 먼저 DB 초기화 확인
    if not UNIFIED_DB.exists():
        print("통합 DB가 없습니다. 먼저 init_unified_db.py를 실행하세요.")
        sys.exit(1)

    rescan_nas()
