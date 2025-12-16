"""
NAS 파일 필터링

조건:
- 1GB 이하
- 1시간 이하 재생시간
- 제외: clip, highlight, paradise (폴더/파일명)
"""

import subprocess
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# NAS 경로
NAS_BASE = Path("Z:/ARCHIVE/WSOP")

# 제외 키워드
EXCLUDE_KEYWORDS = ['clip', 'highlight', 'paradise', 'circuit']

# 크기/시간 제한
MAX_SIZE_GB = 1.0
MAX_DURATION_HOURS = 1.0


def get_video_duration(file_path: str) -> float:
    """ffprobe로 비디오 재생시간(초) 가져오기"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            duration = float(data.get('format', {}).get('duration', 0))
            return duration
    except Exception:
        pass
    return 0


def should_exclude(path: str) -> bool:
    """제외 키워드 포함 여부"""
    path_lower = path.lower()
    for kw in EXCLUDE_KEYWORDS:
        if kw in path_lower:
            return True
    return False


def scan_and_filter():
    """NAS 스캔 및 필터링"""
    all_files = []

    print("[1/3] Scanning NAS files...")

    # 재귀 스캔
    for file in NAS_BASE.rglob('*'):
        if file.is_file() and file.suffix.lower() in ['.mp4', '.mov', '.mxf']:
            all_files.append(file)

    print(f"  Total files found: {len(all_files)}")

    # 제외 키워드 필터
    print("\n[2/3] Applying keyword exclusion filter...")
    after_keyword = []
    excluded_keyword = 0

    for f in all_files:
        if should_exclude(str(f)):
            excluded_keyword += 1
        else:
            after_keyword.append(f)

    print(f"  Excluded by keywords (clip/highlight/paradise): {excluded_keyword}")
    print(f"  Remaining: {len(after_keyword)}")

    # 크기 필터
    print("\n[3/3] Checking file size and duration...")
    size_filtered = []
    excluded_size = 0

    for f in after_keyword:
        size_gb = f.stat().st_size / (1024**3)
        if size_gb > MAX_SIZE_GB:
            excluded_size += 1
        else:
            size_filtered.append({
                'path': f,
                'size_gb': size_gb,
            })

    print(f"  Excluded by size (>{MAX_SIZE_GB}GB): {excluded_size}")
    print(f"  Remaining for duration check: {len(size_filtered)}")

    # 재생시간 필터 (병렬 처리)
    print("\n  Checking duration (this may take a while)...")

    final_results = []
    excluded_duration = 0
    processed = 0

    def check_duration(item):
        duration = get_video_duration(str(item['path']))
        return {
            'path': item['path'],
            'size_gb': item['size_gb'],
            'duration_sec': duration,
            'duration_hours': duration / 3600,
        }

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(check_duration, item): item for item in size_filtered}

        for future in as_completed(futures):
            processed += 1
            if processed % 50 == 0:
                print(f"    Processed: {processed}/{len(size_filtered)}")

            result = future.result()
            if result['duration_hours'] <= MAX_DURATION_HOURS:
                final_results.append(result)
            else:
                excluded_duration += 1

    print(f"\n  Excluded by duration (>{MAX_DURATION_HOURS}h): {excluded_duration}")
    print(f"  Final count: {len(final_results)}")

    return final_results, {
        'total': len(all_files),
        'excluded_keyword': excluded_keyword,
        'excluded_size': excluded_size,
        'excluded_duration': excluded_duration,
        'final': len(final_results),
    }


def main():
    print("=" * 60)
    print("NAS File Filter")
    print("=" * 60)
    print("\nFilter criteria:")
    print(f"  - Size: <= {MAX_SIZE_GB} GB")
    print(f"  - Duration: <= {MAX_DURATION_HOURS} hour")
    print(f"  - Exclude keywords: {', '.join(EXCLUDE_KEYWORDS)}")
    print()

    results, stats = scan_and_filter()

    # 결과 출력
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    print("\n[Statistics]")
    print(f"  Total scanned: {stats['total']}")
    print(f"  Excluded (keywords): {stats['excluded_keyword']}")
    print(f"  Excluded (size>1GB): {stats['excluded_size']}")
    print(f"  Excluded (duration>1h): {stats['excluded_duration']}")
    print("  ─────────────────────")
    print(f"  Final count: {stats['final']}")

    # 연도별 통계
    by_year = {}
    for r in results:
        # 연도 추출
        year = None
        for y in range(1973, 2026):
            if str(y) in str(r['path']):
                year = y
                break
        year = year or 'unknown'
        by_year[year] = by_year.get(year, 0) + 1

    print("\n[By Year]")
    for y in sorted([k for k in by_year.keys() if k != 'unknown'], reverse=True):
        print(f"  {y}: {by_year[y]}")
    if 'unknown' in by_year:
        print(f"  unknown: {by_year['unknown']}")

    # 파일 목록 저장
    output_file = Path(__file__).parent.parent / 'data' / 'nas_filtered_files.json'
    output_data = []
    for r in results:
        output_data.append({
            'filename': r['path'].name,
            'path': str(r['path']),
            'size_gb': round(r['size_gb'], 3),
            'duration_sec': round(r['duration_sec'], 1),
            'duration_min': round(r['duration_sec'] / 60, 1),
        })

    # 정렬 (연도 내림, 파일명)
    def get_year(item):
        for y in range(2025, 1972, -1):
            if str(y) in item['path']:
                return y
        return 0
    output_data.sort(key=lambda x: (-get_year(x), x['filename']))

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'filter_criteria': {
                'max_size_gb': MAX_SIZE_GB,
                'max_duration_hours': MAX_DURATION_HOURS,
                'excluded_keywords': EXCLUDE_KEYWORDS,
            },
            'stats': stats,
            'files': output_data,
        }, f, ensure_ascii=False, indent=2)

    print("\n[Output]")
    print(f"  Saved to: {output_file}")

    # 샘플 출력
    print("\n[Sample files (first 10)]")
    for r in output_data[:10]:
        print(f"  {r['filename']}")
        print(f"    Size: {r['size_gb']:.2f}GB, Duration: {r['duration_min']:.0f}min")


if __name__ == "__main__":
    main()
