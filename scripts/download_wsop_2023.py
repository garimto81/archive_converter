# -*- coding: utf-8 -*-
"""
WSOP 2023 다운로드 스크립트 (로그 분리 버전)

사용법:
    python scripts/download_wsop_2023.py              # 일반 실행
    python scripts/download_wsop_2023.py --quiet      # 콘솔 최소 출력
    python scripts/download_wsop_2023.py --status     # 상태만 확인
"""
import subprocess
import logging
import argparse
import yaml
from pathlib import Path
from datetime import datetime

# 경로 설정
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data" / "pokergo"
CONFIG_FILE = DATA_DIR / "download_config.yaml"
LOG_FILE = DATA_DIR / "download.log"
DOWNLOAD_DIR = DATA_DIR / "downloads" / "wsop_2023"

# 디렉토리 생성
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 로깅 설정 (파일 + 콘솔 분리)
def setup_logging(quiet: bool = False):
    """로깅 설정 - 상세 로그는 파일, 콘솔은 최소화"""
    logger = logging.getLogger("downloader")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    # 파일 핸들러 (상세 로그)
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(file_handler)

    # 콘솔 핸들러 (최소 출력)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING if quiet else logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console_handler)

    return logger


def load_config() -> dict:
    """YAML 설정 파일 로드"""
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"설정 파일 없음: {CONFIG_FILE}")

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_config(config: dict):
    """YAML 설정 파일 저장 (상태 업데이트)"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def get_all_videos(config: dict) -> list:
    """모든 활성화된 비디오 목록 반환"""
    videos = []
    for key, group in config.items():
        if isinstance(group, dict) and group.get("enabled", False):
            for video in group.get("videos", []):
                video["group"] = key
                videos.append(video)
    return videos


def download_video(video: dict, logger: logging.Logger) -> bool:
    """단일 비디오 다운로드"""
    video_id = video["video_id"]
    hls_url = video["hls"]
    output_path = DOWNLOAD_DIR / f"{video_id}.mp4"

    # 이미 존재하면 스킵
    if output_path.exists():
        logger.info(f"[SKIP] {video_id} - 이미 존재")
        return True

    logger.info(f"[DOWN] {video_id} 시작...")
    logger.debug(f"  URL: {hls_url}")
    logger.debug(f"  경로: {output_path}")

    # 진행률 파일 경로
    progress_file = DATA_DIR / "progress.txt"

    cmd = [
        "yt-dlp",
        "-o", str(output_path),
        "--no-check-certificate",
        "--newline",  # 진행률을 줄바꿈으로 출력
        "--progress-template", "%(progress._percent_str)s | %(progress._downloaded_bytes_str)s / %(progress._total_bytes_str)s | %(progress._speed_str)s | ETA:%(progress._eta_str)s",
        hls_url
    ]

    try:
        # 실시간 진행률 표시
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        _last_progress = ""  # used to track progress state
        for line in process.stdout:
            line = line.strip()
            if line:
                # 진행률 파일에 기록 (외부에서 확인 가능)
                with open(progress_file, "w", encoding="utf-8") as f:
                    f.write(f"{video_id}\n{line}\n")

                # 진행률 줄이면 콘솔에 표시
                if "%" in line:
                    print(f"\r  {line}      ", end="", flush=True)
                    _last_progress = line  # stored for potential future use

                logger.debug(f"  {line}")

        process.wait(timeout=3600)
        print()  # 줄바꿈

        # 진행률 파일 정리
        if progress_file.exists():
            progress_file.unlink()

        if process.returncode == 0:
            logger.info(f"[OK] {video_id} 완료")
            return True
        else:
            logger.warning(f"[FAIL] {video_id} 실패 (code: {process.returncode})")
            return False

    except subprocess.TimeoutExpired:
        process.kill()
        logger.error(f"[TIMEOUT] {video_id} 타임아웃")
        return False
    except Exception as e:
        logger.error(f"[ERROR] {video_id} 예외: {e}")
        return False


def print_status(config: dict):
    """현재 다운로드 상태 출력"""
    print("\n" + "=" * 60)
    print("다운로드 상태")
    print("=" * 60)

    for key, group in config.items():
        if isinstance(group, dict) and "videos" in group:
            enabled = "ON" if group.get("enabled", False) else "OFF"
            print(f"\n[{enabled}] {key}: {group.get('description', '')}")

            for video in group.get("videos", []):
                status = video.get("status", "pending")
                video_id = video["video_id"]
                notes = video.get("notes", "")

                # 파일 존재 여부 확인
                output_path = DOWNLOAD_DIR / f"{video_id}.mp4"
                exists = "O" if output_path.exists() else "X"

                status_icon = {
                    "pending": "[ ]",
                    "downloading": "[~]",
                    "completed": "[v]",
                    "failed": "[!]",
                    "skipped": "[-]"
                }.get(status, "[?]")

                print(f"  {status_icon} {video_id} (파일:{exists}) {notes}")

    print("\n" + "=" * 60)
    print(f"설정 파일: {CONFIG_FILE}")
    print(f"다운로드 경로: {DOWNLOAD_DIR}")
    print(f"로그 파일: {LOG_FILE}")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="WSOP 2023 다운로드")
    parser.add_argument("--quiet", "-q", action="store_true", help="콘솔 출력 최소화")
    parser.add_argument("--status", "-s", action="store_true", help="상태만 확인")
    args = parser.parse_args()

    # 설정 로드
    try:
        config = load_config()
    except FileNotFoundError as e:
        print(f"오류: {e}")
        return

    # 상태만 확인
    if args.status:
        print_status(config)
        return

    # 로깅 설정
    logger = setup_logging(quiet=args.quiet)
    logger.info("=" * 60)
    logger.info(f"다운로드 시작: {datetime.now()}")
    logger.info("=" * 60)

    # 비디오 목록
    videos = get_all_videos(config)
    total = len(videos)
    logger.info(f"총 {total}개 영상")
    logger.info(f"저장 위치: {DOWNLOAD_DIR}")

    # 다운로드 실행
    success = 0
    for i, video in enumerate(videos, 1):
        video_id = video["video_id"]
        group = video["group"]

        # 상태 업데이트: downloading
        for v in config[group]["videos"]:
            if v["video_id"] == video_id:
                v["status"] = "downloading"
                break
        save_config(config)

        # 콘솔 진행률 (한 줄로)
        print(f"\r[{i}/{total}] {video_id}...", end="", flush=True)

        # 다운로드
        result = download_video(video, logger)

        # 상태 업데이트: completed/failed
        new_status = "completed" if result else "failed"
        for v in config[group]["videos"]:
            if v["video_id"] == video_id:
                v["status"] = new_status
                break
        save_config(config)

        if result:
            success += 1

    # 완료
    print()  # 줄바꿈
    logger.info("=" * 60)
    logger.info(f"완료: {success}/{total}")
    logger.info(f"종료: {datetime.now()}")
    logger.info("=" * 60)

    print(f"\n완료: {success}/{total}")
    print(f"로그: {LOG_FILE}")


if __name__ == "__main__":
    main()
