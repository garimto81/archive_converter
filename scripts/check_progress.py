# -*- coding: utf-8 -*-
"""
다운로드 진행률 확인 스크립트

사용법:
    python scripts/check_progress.py           # 1회 확인
    python scripts/check_progress.py --watch   # 실시간 모니터링
"""
import argparse
import time
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "pokergo"
PROGRESS_FILE = DATA_DIR / "progress.txt"
CONFIG_FILE = DATA_DIR / "download_config.yaml"
DOWNLOAD_DIR = DATA_DIR / "downloads" / "wsop_2023"


def get_file_sizes():
    """다운로드된 파일 크기 확인"""
    if not DOWNLOAD_DIR.exists():
        return {}

    sizes = {}
    for f in DOWNLOAD_DIR.glob("*.mp4*"):
        size_mb = f.stat().st_size / (1024 * 1024)
        sizes[f.name] = size_mb
    return sizes


def draw_progress_bar(percent: float, width: int = 40) -> str:
    """진행률 바 그리기"""
    filled = int(width * percent / 100)
    bar = "#" * filled + "-" * (width - filled)
    return f"[{bar}] {percent:.1f}%"


def check_progress():
    """현재 진행률 확인"""
    print("=" * 70)
    print("Download Progress")
    print("=" * 70)

    # 진행률 파일 확인
    if PROGRESS_FILE.exists():
        content = PROGRESS_FILE.read_text(encoding="utf-8").strip().split("\n")
        if len(content) >= 2:
            video_id = content[0]
            progress_info = content[1]

            print(f"\n>> Now Downloading: {video_id}")
            print(f"   {progress_info}")

            # 퍼센트 추출해서 프로그레스 바 표시
            try:
                percent_str = progress_info.split("|")[0].strip().replace("%", "")
                percent = float(percent_str)
                print(f"   {draw_progress_bar(percent)}")
            except Exception:
                pass
    else:
        print("\n-- No active download")

    # 파일 크기 확인
    sizes = get_file_sizes()
    completed = []
    in_progress = []

    for name, size in sorted(sizes.items()):
        if name.endswith(".part"):
            in_progress.append((name, size))
        elif name.endswith(".ytdl"):
            pass  # 무시
        else:
            completed.append((name, size))

    if completed:
        print(f"\n[OK] Completed ({len(completed)} files):")
        print("-" * 50)
        total_completed = 0
        for name, size in completed:
            print(f"  {name}: {size/1024:.2f} GB")
            total_completed += size
        print("-" * 50)
        print(f"  Subtotal: {total_completed/1024:.2f} GB")

    if in_progress:
        print(f"\n[..] In Progress ({len(in_progress)} files):")

        # .part 파일에서 진행률 추정
        main_part = None
        frag_num = 0
        for name, size in in_progress:
            if name.endswith(".part") and "Frag" not in name:
                main_part = (name, size)
            elif "Frag" in name:
                try:
                    import re
                    frag_match = re.search(r"Frag(\d+)", name)
                    if frag_match:
                        frag_num = int(frag_match.group(1))
                except Exception:
                    pass

        if main_part:
            name, size = main_part
            size_gb = size / 1024

            # 현재 크기와 fragment 번호로 총 크기 추정
            if frag_num > 0 and size > 0:
                _bytes_per_frag = (size * 1024 * 1024) / frag_num  # bytes per fragment (for reference)
                # FT 영상은 보통 6-8시간 → 에피소드(1.27GB, ~1h) 대비 6-8배
                # 실제 데이터로 추정
                _est_total_frags = int(frag_num * (10 / size_gb))  # 10GB 목표로 추정 (for reference)
                est_total_gb = 10.0  # FT 예상 크기

                # 파일 크기 기반 진행률
                progress = min(99, (size_gb / est_total_gb) * 100)

                print(f"  {name}")
                print(f"     Current:  {size_gb:.2f} GB")
                print(f"     Estimate: ~{est_total_gb:.0f} GB (FT Day 1)")
                print(f"     Fragment: {frag_num:,}")
                print(f"     Progress: {draw_progress_bar(progress)}")
            else:
                print(f"  {name}: {size_gb:.2f} GB")

    # 전체 요약
    total_size = sum(sizes.values())
    print(f"\n[TOTAL] {total_size/1024:.2f} GB")
    print("=" * 70)


def watch_progress(interval: int = 2):
    """실시간 진행률 모니터링"""
    print("진행률 모니터링 (Ctrl+C로 종료)")
    print("=" * 60)

    try:
        while True:
            # 화면 클리어 (Windows)
            print("\033[H\033[J", end="")

            if PROGRESS_FILE.exists():
                content = PROGRESS_FILE.read_text(encoding="utf-8").strip().split("\n")
                if len(content) >= 2:
                    video_id = content[0]
                    progress = content[1]
                    print(f"다운로드 중: {video_id}")
                    print(f"진행률: {progress}")
                else:
                    print("대기 중...")
            else:
                print("다운로드 대기 중...")

            # 파일 크기
            sizes = get_file_sizes()
            if sizes:
                total = sum(sizes.values())
                print(f"\n완료된 파일: {len(sizes)}개 ({total:.1f} MB)")

            print(f"\n[{time.strftime('%H:%M:%S')}] 새로고침 중... (Ctrl+C로 종료)")
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n모니터링 종료")


def main():
    parser = argparse.ArgumentParser(description="다운로드 진행률 확인")
    parser.add_argument("--watch", "-w", action="store_true", help="실시간 모니터링")
    parser.add_argument("--interval", "-i", type=int, default=2, help="새로고침 간격(초)")
    args = parser.parse_args()

    if args.watch:
        watch_progress(args.interval)
    else:
        check_progress()


if __name__ == "__main__":
    main()
