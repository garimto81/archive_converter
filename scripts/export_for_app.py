"""
앱용 JSON 형식으로 변환

앱이 요구하는 필드:
- id: str (필수)
- title: str (필수)
- show: str (필수)
- url: str (필수)
- thumbnail_url: str
- year: int
- season: str
- episode: str
"""

import json
import re
import hashlib
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "pokergo"


def generate_id(url: str) -> str:
    """URL에서 고유 ID 생성"""
    return hashlib.md5(url.encode()).hexdigest()[:12]


def extract_season_episode(title: str, slug: str) -> tuple:
    """제목/slug에서 시즌/에피소드 추출"""
    season = None
    episode = None

    # Episode 패턴
    ep_match = re.search(r'Episode\s*(\d+)|ep(\d+)|-ep(\d+)', title + slug, re.IGNORECASE)
    if ep_match:
        episode = ep_match.group(1) or ep_match.group(2) or ep_match.group(3)

    # Day 패턴 -> Episode로 변환
    day_match = re.search(r'Day\s*(\d+[A-D]?)|day(\d+[a-d]?)', title + slug, re.IGNORECASE)
    if day_match and not episode:
        episode = f"Day {day_match.group(1) or day_match.group(2)}"

    # Part 패턴
    part_match = re.search(r'Part\s*(\d+)|part(\d+)', title + slug, re.IGNORECASE)
    if part_match:
        part = part_match.group(1) or part_match.group(2)
        if episode:
            episode = f"{episode} Part {part}"
        else:
            episode = f"Part {part}"

    return season, episode


def main():
    # 최종 데이터 로드
    data_file = OUTPUT_DIR / "wsop_final_20251216_154021.json"
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    videos = data.get("videos", [])
    print(f"Loaded {len(videos)} videos")

    # 앱 형식으로 변환
    app_videos = []

    for v in videos:
        url = v.get("url", "")
        if not url:
            continue

        title = v.get("title", "")
        slug = v.get("slug", "")
        category = v.get("category", "WSOP")
        year_raw = v.get("year")
        year = int(year_raw) if year_raw and str(year_raw).isdigit() else None

        # show 결정
        if category == "WSOP Europe":
            show = "WSOP Europe"
        elif category == "WSOP Classic":
            show = "WSOP Classic"
        else:
            show = "WSOP"

        # 시즌/에피소드 추출
        season, episode = extract_season_episode(title, slug)

        # 제목 정리
        if not title:
            title = slug.replace("-", " ").title()

        app_videos.append({
            "id": generate_id(url),
            "title": title,
            "show": show,
            "url": url,
            "thumbnail_url": v.get("thumbnail", ""),
            "year": year,
            "season": str(year) if year else None,
            "episode": episode,
            "duration": 0,
            "duration_str": "",
            "hls_url": None,
            "status": "pending",
        })

    # show별 통계
    by_show = {}
    for v in app_videos:
        show = v["show"]
        by_show[show] = by_show.get(show, 0) + 1

    print("\n[BY SHOW]")
    for show, count in sorted(by_show.items()):
        print(f"  {show}: {count}")

    # JSON 저장 (앱 import 형식: {"videos": [...]})
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"wsop_for_app_{timestamp}.json"

    export_data = {
        "total": len(app_videos),
        "videos": app_videos
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    print(f"\n[SAVED] {output_file}")
    print(f"  Total: {len(app_videos)} videos")

    # 샘플 출력
    print("\n[SAMPLE - WSOP Classic]")
    classic = [v for v in app_videos if v["show"] == "WSOP Classic"][:5]
    for v in classic:
        print(f"  {v['title'][:50]}")
        print(f"    year: {v['year']}, episode: {v['episode']}")

    print("\n[SAMPLE - WSOP Europe]")
    europe = [v for v in app_videos if v["show"] == "WSOP Europe"][:5]
    for v in europe:
        print(f"  {v['title'][:50]}")
        print(f"    year: {v['year']}, episode: {v['episode']}")

    return output_file


if __name__ == "__main__":
    main()
