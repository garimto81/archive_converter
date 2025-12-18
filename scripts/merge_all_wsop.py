"""
WSOP 전체 데이터 병합

- 기존 merged 데이터
- Extended 데이터 (Classic + Europe)
- 연도 추출 수정
"""

import json
import re
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "pokergo"


def extract_year_from_slug(slug: str) -> int:
    """slug에서 연도 추출"""
    # wsop-1995-main-event -> 1995
    # wsop-2007-11-me-day1a -> 2007
    match = re.search(r'wsop-(\d{4})', slug)
    if match:
        return int(match.group(1))

    # wsop-europe-2021 -> 2021
    match = re.search(r'europe-(\d{4})', slug)
    if match:
        return int(match.group(1))

    # 일반적인 4자리 연도
    match = re.search(r'(19\d{2}|20\d{2})', slug)
    if match:
        return int(match.group(1))

    return None


def generate_title_from_slug(slug: str) -> str:
    """slug에서 제목 생성"""
    # wsop-2003-main-event-chris-moneymaker-commentary
    # -> WSOP 2003 Main Event Chris Moneymaker Commentary
    title = slug.replace("-", " ").title()
    title = title.replace("Wsop", "WSOP")
    title = title.replace("Me ", "Main Event ")
    title = title.replace(" Ft", " Final Table")
    title = title.replace("Nl27sd", "NL 2-7 Single Draw")
    title = title.replace("Nlh", "NLH")
    return title


def merge_all_data():
    # 기존 merged 데이터
    merged_file = OUTPUT_DIR / "wsop_merged_20251216_133457.json"
    with open(merged_file, "r", encoding="utf-8") as f:
        merged_data = json.load(f)

    # Extended 데이터
    extended_file = OUTPUT_DIR / "wsop_extended_20251216_152625.json"
    with open(extended_file, "r", encoding="utf-8") as f:
        extended_data = json.load(f)

    print(f"Existing merged data: {merged_data['total_videos']} videos")
    print(f"Extended data: {extended_data['total_videos']} videos")

    # URL 기준 dedup
    all_videos = {}

    # 기존 데이터 추가
    for v in merged_data.get("videos", []):
        url = v.get("url", "")
        if url:
            all_videos[url] = v

    # Extended 데이터 추가 (연도/제목 수정)
    added = 0
    for v in extended_data.get("videos", []):
        url = v.get("url", "")
        if not url:
            continue

        # 연도 추출
        slug = v.get("slug", "")
        year = v.get("year")
        if not year:
            year = extract_year_from_slug(slug)

        # 제목 생성
        title = v.get("title", "")
        if not title:
            title = generate_title_from_slug(slug)

        # 카테고리 설정
        source = v.get("source", "")
        category = v.get("category", "")
        if "europe" in source.lower() or "europe" in slug.lower():
            category = "WSOP Europe"
        elif "classic" in source.lower() or (year and year <= 2010):
            category = "WSOP Classic"
        else:
            category = "WSOP"

        if url not in all_videos:
            added += 1

        all_videos[url] = {
            "url": url,
            "slug": slug,
            "title": title,
            "year": year,
            "category": category,
            "source": v.get("source", ""),
            "thumbnail": v.get("thumbnail", ""),
        }

    print(f"New videos added: {added}")

    videos = list(all_videos.values())

    # 연도별 통계
    year_counts = {}
    for v in videos:
        y = v.get("year", "unknown")
        year_counts[y] = year_counts.get(y, 0) + 1

    # 카테고리별 통계
    cat_counts = {}
    for v in videos:
        c = v.get("category", "WSOP")
        cat_counts[c] = cat_counts.get(c, 0) + 1

    # 정렬
    def get_year_int(v):
        y = v.get("year")
        if y is None:
            return 0
        return int(y) if isinstance(y, (int, str)) and str(y).isdigit() else 0

    videos.sort(key=lambda x: (-get_year_int(x), x.get("title", "")))

    # 저장
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output = {
        "scraped_at": datetime.now().isoformat(),
        "merged_from": [str(merged_file.name), str(extended_file.name)],
        "total_videos": len(videos),
        "by_year": dict(sorted([(str(k), v) for k, v in year_counts.items()], reverse=True)),
        "by_category": cat_counts,
        "videos": videos,
    }

    output_file = OUTPUT_DIR / f"wsop_all_merged_{timestamp}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print("[MERGED RESULT]")
    print(f"{'='*60}")
    print(f"  File: {output_file}")
    print(f"  Total: {len(videos)} videos")
    print("\n[BY CATEGORY]")
    for c, count in sorted(cat_counts.items()):
        print(f"  {c}: {count}")
    print("\n[BY YEAR]")
    for y, c in sorted(year_counts.items(), key=lambda x: str(x[0]), reverse=True):
        print(f"  {y}: {c}")

    return output_file


if __name__ == "__main__":
    merge_all_data()
