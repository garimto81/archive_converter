"""
NAS 파일 미디어 정보 스캔 스크립트
ffprobe를 사용하여 재생시간, 코덱, 해상도, 비트레이트 수집

Usage:
    python scripts/scan_nas_media_info.py                    # 전체 스캔
    python scripts/scan_nas_media_info.py --folder "WSOP 1973"  # 특정 폴더만
    python scripts/scan_nas_media_info.py --limit 100        # 처음 100개만
"""

import argparse
import json
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# Windows 콘솔 UTF-8 출력 설정
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def get_media_info(file_path: str) -> dict | None:
    """ffprobe로 미디어 정보 추출"""
    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(file_path)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="replace"
        )

        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)

        # 비디오 스트림 찾기
        video_stream = None
        audio_stream = None
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video" and video_stream is None:
                video_stream = stream
            elif stream.get("codec_type") == "audio" and audio_stream is None:
                audio_stream = stream

        format_info = data.get("format", {})

        # 재생 시간
        duration = None
        if "duration" in format_info:
            duration = float(format_info["duration"])
        elif video_stream and "duration" in video_stream:
            duration = float(video_stream["duration"])

        # 해상도
        resolution = None
        if video_stream:
            width = video_stream.get("width")
            height = video_stream.get("height")
            if width and height:
                resolution = f"{width}x{height}"

        # FPS
        fps = None
        if video_stream and "r_frame_rate" in video_stream:
            fps_str = video_stream["r_frame_rate"]
            if "/" in fps_str:
                num, den = map(int, fps_str.split("/"))
                if den > 0:
                    fps = round(num / den, 2)

        # 비트레이트
        bitrate = None
        if "bit_rate" in format_info:
            bitrate = int(format_info["bit_rate"])

        return {
            "duration_sec": duration,
            "video_codec": video_stream.get("codec_name") if video_stream else None,
            "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
            "resolution": resolution,
            "bitrate": bitrate,
            "fps": fps,
        }

    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"  [JSON ERROR] {file_path}")
        return None
    except Exception as e:
        print(f"  [ERROR] {file_path}: {e}")
        return None


def update_database_schema(db_path: str):
    """DB 스키마에 미디어 정보 컬럼 추가"""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 새 컬럼 추가 (이미 있으면 무시)
    columns_to_add = [
        ("duration_sec", "REAL"),
        ("video_codec", "TEXT"),
        ("audio_codec", "TEXT"),
        ("resolution", "TEXT"),
        ("bitrate", "INTEGER"),
        ("fps", "REAL"),
        ("media_scanned", "INTEGER DEFAULT 0"),
    ]

    for col_name, col_type in columns_to_add:
        try:
            cur.execute(f"ALTER TABLE files ADD COLUMN {col_name} {col_type}")
            print(f"  Added column: {col_name}")
        except sqlite3.OperationalError:
            pass  # 이미 존재

    conn.commit()
    conn.close()


def scan_files(db_path: str, folder_filter: str = None, limit: int = None, workers: int = 4):
    """파일 스캔 실행"""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 스캔 대상 파일 조회
    query = "SELECT id, path, filename FROM files WHERE media_scanned = 0"
    params = []

    if folder_filter:
        query += " AND path LIKE ?"
        params.append(f"%{folder_filter}%")

    query += " ORDER BY year DESC, filename"

    if limit:
        query += f" LIMIT {limit}"

    cur.execute(query, params)
    files = cur.fetchall()
    conn.close()

    total = len(files)
    print(f"\nTotal files to scan: {total}")

    if total == 0:
        print("No files to scan.")
        return

    scanned = 0
    errors = 0
    results = []

    def process_file(file_info):
        file_id, path, filename = file_info
        info = get_media_info(path)
        return file_id, path, filename, info

    print(f"Starting scan with {workers} workers...\n")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_file, f): f for f in files}

        for future in as_completed(futures):
            file_id, path, filename, info = future.result()
            scanned += 1

            if info:
                results.append((file_id, info))
                duration_str = f"{info['duration_sec']:.1f}s" if info['duration_sec'] else "N/A"
                resolution = info['resolution'] or "N/A"
                print(f"[{scanned}/{total}] {filename[:50]} | {duration_str} | {resolution}")
            else:
                errors += 1
                print(f"[{scanned}/{total}] [FAILED] {filename[:50]}")

            # 배치 저장 (100개마다)
            if len(results) >= 100:
                save_results(db_path, results)
                results = []

    # 남은 결과 저장
    if results:
        save_results(db_path, results)

    print(f"\n{'='*60}")
    print(f"Scan Complete")
    print(f"{'='*60}")
    print(f"Total: {total}")
    print(f"Success: {scanned - errors}")
    print(f"Errors: {errors}")


def save_results(db_path: str, results: list):
    """스캔 결과를 DB에 저장"""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    for file_id, info in results:
        cur.execute("""
            UPDATE files SET
                duration_sec = ?,
                video_codec = ?,
                audio_codec = ?,
                resolution = ?,
                bitrate = ?,
                fps = ?,
                media_scanned = 1
            WHERE id = ?
        """, (
            info["duration_sec"],
            info["video_codec"],
            info["audio_codec"],
            info["resolution"],
            info["bitrate"],
            info["fps"],
            file_id
        ))

    conn.commit()
    conn.close()
    print(f"  [SAVED] {len(results)} records")


def get_scan_stats(db_path: str):
    """스캔 통계 조회"""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM files")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM files WHERE media_scanned = 1")
    scanned = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM files WHERE duration_sec IS NOT NULL")
    with_duration = cur.fetchone()[0]

    conn.close()

    return {
        "total": total,
        "scanned": scanned,
        "with_duration": with_duration,
        "remaining": total - scanned
    }


def main():
    parser = argparse.ArgumentParser(description="Scan NAS files for media information")
    parser.add_argument("--db", default="data/nas_footage.db", help="Database path")
    parser.add_argument("--folder", help="Filter by folder name")
    parser.add_argument("--limit", type=int, help="Limit number of files")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers")
    parser.add_argument("--stats", action="store_true", help="Show scan statistics only")
    args = parser.parse_args()

    print("=" * 60)
    print("NAS Media Information Scanner")
    print("=" * 60)

    # DB 스키마 업데이트
    print("\nUpdating database schema...")
    update_database_schema(args.db)

    # 통계 조회
    stats = get_scan_stats(args.db)
    print(f"\nCurrent Status:")
    print(f"  Total files: {stats['total']}")
    print(f"  Already scanned: {stats['scanned']}")
    print(f"  With duration: {stats['with_duration']}")
    print(f"  Remaining: {stats['remaining']}")

    if args.stats:
        return

    if stats['remaining'] == 0:
        print("\nAll files have been scanned.")
        return

    # 스캔 실행
    scan_files(args.db, args.folder, args.limit, args.workers)


if __name__ == "__main__":
    main()
