"""
비디오 리스트 JSON 추출 및 출력
"""

import json
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "pokergo"


def main():
    data_file = OUTPUT_DIR / "wsop_final_20251216_154021.json"
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    videos = data.get("videos", [])
    print(f"Total: {len(videos)} videos\n")

    # 앱용 JSON 형식으로 변환
    export_data = []
    for v in videos:
        export_data.append({
            "url": v.get("url", ""),
            "title": v.get("title", ""),
            "year": v.get("year"),
            "category": v.get("category", ""),
            "slug": v.get("slug", ""),
        })

    # JSON 파일 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_file = OUTPUT_DIR / f"pokergo_video_list_{timestamp}.json"
    with open(export_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    print(f"[SAVED] {export_file}\n")

    # 카테고리별 출력
    categories = {}
    for v in videos:
        cat = v.get("category", "unknown")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(v)

    for cat in ["WSOP", "WSOP Classic", "WSOP Europe"]:
        if cat not in categories:
            continue

        vids = categories[cat]
        print(f"{'='*60}")
        print(f"{cat} ({len(vids)} videos)")
        print(f"{'='*60}")

        # 연도별 그룹화
        by_year = {}
        for v in vids:
            y = v.get("year")
            if y is None:
                y = "unknown"
            by_year[y] = by_year.get(y, [])
            by_year[y].append(v)

        # 연도 정렬
        valid_years = [k for k in by_year.keys() if isinstance(k, int)]
        valid_years.sort(reverse=True)

        for y in valid_years[:10]:
            year_vids = by_year[y]
            print(f"\n  [{y}] {len(year_vids)} videos")
            for v in year_vids[:5]:
                title = v.get("title", "")[:55]
                url = v.get("url", "")
                print(f"    - {title}")
                print(f"      {url}")

        print()


if __name__ == "__main__":
    main()
