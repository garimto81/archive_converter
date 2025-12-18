# -*- coding: utf-8 -*-
"""
다운로드 실시간 모니터링

사용법:
    python scripts/monitor_download.py
    python scripts/monitor_download.py --interval 5
"""
import os
import time
import argparse
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent / "data" / "pokergo"
PROGRESS_FILE = DATA_DIR / "progress.txt"
DOWNLOAD_DIR = DATA_DIR / "downloads" / "wsop_2023"


def clear_screen():
    """화면 클리어"""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_files():
    """다운로드 파일 정보"""
    if not DOWNLOAD_DIR.exists():
        return [], [], 0

    completed = []
    in_progress = []
    frag_num = 0

    for f in sorted(DOWNLOAD_DIR.glob("*")):
        size_mb = f.stat().st_size / (1024 * 1024)
        name = f.name

        if name.endswith(".ytdl"):
            continue
        elif "Frag" in name:
            import re
            match = re.search(r"Frag(\d+)", name)
            if match:
                frag_num = int(match.group(1))
        elif name.endswith(".part"):
            in_progress.append((name, size_mb))
        else:
            completed.append((name, size_mb))

    return completed, in_progress, frag_num


def draw_bar(percent, width=50):
    """진행률 바"""
    filled = int(width * percent / 100)
    bar = "#" * filled + "-" * (width - filled)
    return f"[{bar}]"


def format_size(mb):
    """크기 포맷"""
    if mb >= 1024:
        return f"{mb/1024:.2f} GB"
    return f"{mb:.0f} MB"


def monitor(interval=2):
    """실시간 모니터링"""
    print("Download Monitor Started (Ctrl+C to exit)")
    print("=" * 60)

    prev_size = 0
    start_time = time.time()

    try:
        while True:
            clear_screen()

            completed, in_progress, frag_num = get_files()
            now = datetime.now().strftime("%H:%M:%S")

            # 헤더
            print("=" * 60)
            print(f"  WSOP 2023 Download Monitor        [{now}]")
            print("=" * 60)

            # 완료된 파일
            total_completed = sum(s for _, s in completed)
            print(f"\n  Completed: {len(completed)} files ({format_size(total_completed)})")

            if completed:
                for name, size in completed:
                    short_name = name.replace("wsop-2023-", "").replace(".mp4", "")
                    print(f"    [OK] {short_name:20} {format_size(size):>10}")

            # 진행 중
            if in_progress:
                print("\n  In Progress:")
                for name, size in in_progress:
                    short_name = name.replace("wsop-2023-", "").replace(".mp4.part", "")

                    # 예상 크기 (FT = ~10GB)
                    est_total = 10 * 1024  # 10GB in MB
                    percent = min(99, (size / est_total) * 100)

                    # 속도 계산
                    elapsed = time.time() - start_time
                    if elapsed > 0 and prev_size > 0:
                        speed = (size - prev_size) / interval  # MB/s
                        if speed > 0:
                            remaining = (est_total - size) / speed
                            eta = f"ETA: {int(remaining//60)}m {int(remaining%60)}s"
                        else:
                            eta = "ETA: calculating..."
                    else:
                        speed = 0
                        eta = "ETA: calculating..."

                    print(f"\n    >> {short_name}")
                    print(f"       {draw_bar(percent)} {percent:.1f}%")
                    print(f"       {format_size(size)} / ~{format_size(est_total)}")
                    print(f"       Fragment: {frag_num:,}")
                    print(f"       Speed: {speed:.1f} MB/s | {eta}")

                    prev_size = size
            else:
                # 다운로드 완료 체크
                if len(completed) >= 6:
                    print("\n  [DONE] All downloads completed!")
                else:
                    print("\n  -- Waiting for download...")

            # 전체 요약
            total_all = total_completed + sum(s for _, s in in_progress)
            print("\n  " + "-" * 56)
            print(f"  Total Downloaded: {format_size(total_all)}")
            print("=" * 60)
            print(f"\n  Press Ctrl+C to exit | Refresh: {interval}s")

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\nMonitor stopped.")


def main():
    parser = argparse.ArgumentParser(description="Download Monitor")
    parser.add_argument("--interval", "-i", type=int, default=2,
                        help="Refresh interval in seconds (default: 2)")
    args = parser.parse_args()

    monitor(args.interval)


if __name__ == "__main__":
    main()
