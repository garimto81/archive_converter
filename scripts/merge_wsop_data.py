"""
Merge WSOP data from multiple sources
"""

import json
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "pokergo"


def merge_wsop_data():
    # Load old data (has titles and 2011-2016)
    old_file = OUTPUT_DIR / "wsop_all_20251215_165040.json"
    with open(old_file, "r", encoding="utf-8") as f:
        old_data = json.load(f)

    # Load new data (fresh from today)
    new_file = OUTPUT_DIR / "wsop_v2_20251216_133354.json"
    with open(new_file, "r", encoding="utf-8") as f:
        new_data = json.load(f)

    print(f"Old data: {old_data['total_videos']} videos")
    print(f"New data: {new_data['total_videos']} videos")

    # Create merged dataset
    # Use URL as key for deduplication
    merged = {}

    # Add old data first (has titles)
    for v in old_data.get("videos", []):
        url = v.get("url", "")
        if url:
            merged[url] = {
                "url": url,
                "title": v.get("title", ""),
                "year": v.get("year"),
                "source": v.get("source", ""),
                "thumbnail": v.get("thumbnail", ""),
                "slug": url.split("/")[-1].split("?")[0] if url else "",
            }

    # Update/add from new data
    for v in new_data.get("videos", []):
        url = v.get("url", "")
        if url:
            if url in merged:
                # Update thumbnail if new has one
                if v.get("thumbnail") and not merged[url].get("thumbnail"):
                    merged[url]["thumbnail"] = v["thumbnail"]
                # Keep the title from old data if it exists
                if not merged[url].get("title") and v.get("title"):
                    merged[url]["title"] = v["title"]
            else:
                merged[url] = {
                    "url": url,
                    "title": v.get("title", ""),
                    "year": v.get("year"),
                    "source": v.get("source", ""),
                    "thumbnail": v.get("thumbnail", ""),
                    "slug": v.get("slug", ""),
                }

    videos = list(merged.values())

    # Extract year from URL/title if missing
    for v in videos:
        if not v.get("year"):
            url = v.get("url", "")
            title = v.get("title", "")
            for year in range(2011, 2026):
                if str(year) in url or str(year) in title:
                    v["year"] = year
                    break

    # Count by year
    year_counts = {}
    for v in videos:
        y = v.get("year", "unknown")
        year_counts[y] = year_counts.get(y, 0) + 1

    # Convert year to int for sorting
    def get_year_int(v):
        y = v.get("year")
        if y is None:
            return 0
        return int(y) if isinstance(y, (int, str)) and str(y).isdigit() else 0

    # Sort by year descending
    videos.sort(key=lambda x: (-get_year_int(x), x.get("title", "")))

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output = {
        "scraped_at": datetime.now().isoformat(),
        "merged_from": [str(old_file.name), str(new_file.name)],
        "total_videos": len(videos),
        "by_year": dict(sorted([(str(k), v) for k, v in year_counts.items()], reverse=True)),
        "videos": videos,
    }

    output_file = OUTPUT_DIR / f"wsop_merged_{timestamp}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print("[MERGED RESULT]")
    print(f"{'='*60}")
    print(f"  File: {output_file}")
    print(f"  Total: {len(videos)} videos")
    print("\n[BY YEAR]")
    for y, c in sorted(year_counts.items(), key=lambda x: str(x[0]), reverse=True):
        print(f"  {y}: {c}")

    return output_file


if __name__ == "__main__":
    merge_wsop_data()
