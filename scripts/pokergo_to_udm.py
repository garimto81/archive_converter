"""
PokerGO 데이터를 UDM (Universal Data Model)로 변환

수집된 PokerGO 비디오 메타데이터를 UDM Asset 형식으로 변환합니다.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

# 프로젝트 루트를 PYTHONPATH에 추가
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.udm import (
    Asset,
    AssetType,
    Brand,
    EventContext,
    EventType,
    GameVariant,
    Location,
    SourceOrigin,
    TechSpec,
)

DATA_DIR = Path(__file__).parent.parent / "data" / "pokergo"


def map_event_to_brand(event: str, show_name: str, title: str) -> Brand:
    """이벤트/쇼 이름을 Brand enum으로 매핑"""
    event_lower = (event or "").lower()
    show_lower = (show_name or "").lower()
    title_lower = (title or "").lower()
    combined = f"{event_lower} {show_lower} {title_lower}"

    # 브랜드 매핑
    if "wsop" in combined or "world series of poker" in combined:
        return Brand.WSOP
    elif "wpt" in combined or "world poker tour" in combined:
        return Brand.WPT
    elif "hustler casino live" in combined or "hcl" in combined:
        return Brand.HCL
    elif "poker after dark" in combined or "pad" in combined:
        return Brand.PAD
    elif "ept" in combined or "european poker tour" in combined:
        return Brand.EPT
    elif "ggmillions" in combined or "gg millions" in combined:
        return Brand.GG_MILLIONS

    return Brand.OTHER


def map_event_type(event: str, title: str) -> Optional[EventType]:
    """이벤트 유형 매핑"""
    combined = f"{event or ''} {title or ''}".lower()

    if "cash game" in combined or "no gamble no future" in combined:
        return EventType.CASH_GAME_SHOW
    elif "circuit" in combined:
        return EventType.CIRCUIT
    elif "bracelet" in combined or "main event" in combined:
        return EventType.BRACELET
    elif "high roller" in combined:
        return EventType.SIDE_EVENT

    return None


def extract_year_from_title(title: str, url: str) -> int:
    """제목이나 URL에서 연도 추출"""
    # 제목에서 4자리 연도 추출
    match = re.search(r'\b(20\d{2})\b', title)
    if match:
        return int(match.group(1))

    # URL에서 연도 추출
    match = re.search(r'[-_](20\d{2})[-_]', url)
    if match:
        return int(match.group(1))

    # 기본값: 현재 연도
    return datetime.now().year


def extract_game_variant(title: str, description: str) -> Optional[GameVariant]:
    """게임 종류 추출"""
    combined = f"{title or ''} {description or ''}".lower()

    if "plo" in combined or "pot limit omaha" in combined or "omaha" in combined:
        return GameVariant.PLO
    elif "stud" in combined:
        return GameVariant.STUD
    elif "razz" in combined:
        return GameVariant.RAZZ
    elif "horse" in combined:
        return GameVariant.HORSE
    elif "mixed" in combined:
        return GameVariant.MIXED
    elif "nlh" in combined or "no limit hold" in combined or "hold'em" in combined:
        return GameVariant.NLH

    # 포커 영상은 기본적으로 NLH
    return GameVariant.NLH


def convert_video_to_asset(video: dict) -> dict:
    """PokerGO 비디오를 UDM Asset으로 변환"""
    url = video.get("url", "")
    title = video.get("title", "")
    description = video.get("description", "")
    show_name = video.get("show_name", "")
    event = video.get("event", "")
    season = video.get("season", "")
    episode = video.get("episode", "")
    duration_seconds = video.get("duration_seconds", 0)
    thumbnail = video.get("thumbnail", "")

    # URL에서 video_id 추출
    video_id = url.split("/")[-1] if url else str(uuid4())

    # 연도 추출
    year = extract_year_from_title(title, url)

    # 브랜드 매핑
    brand = map_event_to_brand(event, show_name, title)

    # 이벤트 타입 매핑
    event_type = map_event_type(event, title)

    # 게임 종류
    game_variant = extract_game_variant(title, description)

    # 시즌/에피소드 숫자 추출
    season_num = None
    episode_num = None

    if season:
        match = re.search(r'\d+', str(season))
        if match:
            season_num = int(match.group())

    if episode:
        match = re.search(r'\d+', str(episode))
        if match:
            episode_num = int(match.group())

    # Final Table 여부
    is_final_table = "final table" in title.lower() or "ft" in url.lower()

    # 파일명 생성 (URL 기반)
    file_name = f"pokergo_{video_id}.mp4"

    # UDM Asset 구조
    asset = {
        "id": str(uuid4()),
        "file_name": file_name,
        "asset_type": AssetType.STREAM.value,

        "event_context": {
            "year": year,
            "brand": brand.value,
            "event_type": event_type.value if event_type else None,
            "game_variant": game_variant.value if game_variant else None,
            "is_final_table": is_final_table,
            "season": season_num,
            "episode": episode_num,
            "episode_title": title,
        },

        "tech_spec": {
            "duration_sec": duration_seconds if duration_seconds else None,
        },

        "source_origin": {
            "platform": "PokerGO",
            "url": url,
            "external_id": video_id,
        },

        # 추가 메타데이터 (UDM 확장)
        "metadata": {
            "title": title,
            "description": description,
            "show_name": show_name,
            "event": event,
            "thumbnail": thumbnail,
            "scraped_from": "pokergo.com",
        },

        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    return asset


def convert_all_videos(input_file: str = None, output_file: str = None):
    """모든 PokerGO 비디오를 UDM으로 변환"""
    # 입력 파일 찾기
    if input_file:
        input_path = Path(input_file)
    else:
        # 가장 최근 details 파일 찾기
        files = list(DATA_DIR.glob("pokergo_details_*.json"))
        if not files:
            print("[ERROR] 입력 파일이 없습니다. pokergo_detail_scraper.py를 먼저 실행하세요.")
            return None
        input_path = max(files, key=lambda f: f.stat().st_mtime)

    print(f"[INFO] 입력 파일: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    videos = data.get("videos", [])
    print(f"  - {len(videos)}개 비디오 발견")

    # 변환
    assets = []
    brand_counts = {}

    for video in videos:
        asset = convert_video_to_asset(video)
        assets.append(asset)

        # 브랜드별 카운트
        brand = asset["event_context"]["brand"]
        brand_counts[brand] = brand_counts.get(brand, 0) + 1

    # 결과 저장
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if output_file:
        output_path = Path(output_file)
    else:
        output_path = DATA_DIR / f"pokergo_udm_{timestamp}.json"

    output_data = {
        "converted_at": datetime.now().isoformat(),
        "source_file": str(input_path),
        "total_assets": len(assets),
        "brand_distribution": brand_counts,
        "assets": assets,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"[SUCCESS] UDM 변환 완료!")
    print(f"{'='*60}")
    print(f"  출력 파일: {output_path}")
    print(f"  총 Asset 수: {len(assets)}개")
    print(f"\n[브랜드별 분포]")
    for brand, count in sorted(brand_counts.items(), key=lambda x: -x[1]):
        print(f"  - {brand}: {count}개")

    return output_path


def main():
    import argparse

    parser = argparse.ArgumentParser(description='PokerGO → UDM 변환')
    parser.add_argument('--input', type=str, default=None, help='입력 파일 경로')
    parser.add_argument('--output', type=str, default=None, help='출력 파일 경로')
    args = parser.parse_args()

    print("=" * 60)
    print("PokerGO → UDM 변환기")
    print("=" * 60)

    convert_all_videos(args.input, args.output)


if __name__ == "__main__":
    main()
