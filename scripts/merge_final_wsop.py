"""
WSOP 최종 데이터 병합

- 기존 merged 데이터 (558)
- Deep scrape 데이터 (270 - Classic + Europe)
"""

import json
import re
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "pokergo"


def extract_year(text: str) -> int:
    """텍스트에서 연도 추출"""
    match = re.search(r'(19\d{2}|20\d{2})', text)
    if match:
        return int(match.group(1))
    return None


def generate_title(slug: str, source: str) -> str:
    """slug에서 제목 생성"""
    title = slug.replace("-", " ").title()
    title = title.replace("Wsop", "WSOP")
    title = title.replace(" Me ", " Main Event ")
    title = title.replace(" Be ", " Bracelet Events ")
    title = title.replace(" Ft", " Final Table")
    title = title.replace("Nlh", "NLH")
    title = title.replace("Plo", "PLO")
    return title


def merge_all():
    # 기존 데이터 (2011-2025)
    merged_file = OUTPUT_DIR / "wsop_merged_20251216_133457.json"
    with open(merged_file, "r", encoding="utf-8") as f:
        merged_data = json.load(f)

    # Deep scrape 데이터 (Classic + Europe)
    deep_file = OUTPUT_DIR / "wsop_deep_20251216_153930.json"
    with open(deep_file, "r", encoding="utf-8") as f:
        deep_data = json.load(f)

    print(f"Existing data: {merged_data['total_videos']} videos")
    print(f"Deep scrape data: {deep_data['total_videos']} videos")

    # URL 기준 dedup
    all_videos = {}

    # 기존 데이터
    for v in merged_data.get("videos", []):
        url = v.get("url", "")
        if url:
            all_videos[url] = {
                "url": url,
                "slug": v.get("slug", ""),
                "title": v.get("title", ""),
                "year": v.get("year"),
                "source": v.get("source", ""),
                "category": "WSOP",
                "thumbnail": v.get("thumbnail", ""),
            }

    # Deep scrape 데이터 추가
    added = 0
    for v in deep_data.get("videos", []):
        url = v.get("url", "")
        if not url:
            continue

        if url not in all_videos:
            added += 1

        slug = v.get("slug", "")
        source = v.get("source", "")
        title = v.get("title", "")

        # 연도 추출
        year = v.get("year")
        if not year:
            year = extract_year(slug) or extract_year(source) or extract_year(title)

        # 제목 생성
        if not title:
            title = generate_title(slug, source)

        # 카테고리
        category = v.get("category", "")
        if not category:
            if "europe" in source.lower():
                category = "WSOP Europe"
            elif "classic" in source.lower() or (year and year <= 2010):
                category = "WSOP Classic"
            else:
                category = "WSOP"

        all_videos[url] = {
            "url": url,
            "slug": slug,
            "title": title,
            "year": year,
            "source": source,
            "category": category,
            "thumbnail": v.get("thumbnail", ""),
        }

    print(f"New videos added: {added}")

    videos = list(all_videos.values())

    # 통계
    year_counts = {}
    cat_counts = {}
    for v in videos:
        y = v.get("year", "unknown")
        c = v.get("category", "unknown")
        year_counts[y] = year_counts.get(y, 0) + 1
        cat_counts[c] = cat_counts.get(c, 0) + 1

    # 정렬
    def sort_key(v):
        y = v.get("year")
        return (-int(y) if y else 0, v.get("title", ""))

    videos.sort(key=sort_key)

    # 저장
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output = {
        "scraped_at": datetime.now().isoformat(),
        "merged_from": [str(merged_file.name), str(deep_file.name)],
        "total_videos": len(videos),
        "by_year": dict(sorted([(str(k), v) for k, v in year_counts.items()], reverse=True)),
        "by_category": cat_counts,
        "videos": videos,
    }

    output_file = OUTPUT_DIR / f"wsop_final_{timestamp}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print("[FINAL MERGED RESULT]")
    print(f"{'='*60}")
    print(f"  File: {output_file}")
    print(f"  Total: {len(videos)} videos")
    print(f"\n[BY CATEGORY]")
    for c, count in sorted(cat_counts.items()):
        print(f"  {c}: {count}")
    print(f"\n[BY YEAR]")
    valid_years = [k for k in year_counts.keys() if k and k != 'unknown' and str(k).isdigit()]
    for y in sorted(valid_years, key=lambda x: int(x), reverse=True):
        print(f"  {y}: {year_counts[y]}")
    if 'unknown' in year_counts:
        print(f"  unknown: {year_counts['unknown']}")
    if None in year_counts:
        print(f"  None: {year_counts[None]}")

    return output_file


if __name__ == "__main__":
    merge_all()
