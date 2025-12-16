"""
NAS-to-UDM Extractor CLI

Usage:
    python -m src.extractors.cli scan <nas_path> [options]
    python -m src.extractors.cli extract <nas_path> [options]
    python -m src.extractors.cli schema [options]
"""

import argparse
import json
import sys
from pathlib import Path


def cmd_scan(args):
    """NAS 스캔 명령"""
    from .nas_scanner import NasScanner

    print(f"🔍 Scanning: {args.path}")

    try:
        scanner = NasScanner(
            args.path,
            include_hidden=args.include_hidden,
            compute_hash=args.hash,
        )

        files, result = scanner.scan_with_stats(
            video_only=not args.all_files,
            max_files=args.max_files,
        )

        # 결과 출력
        print("\n📊 Scan Result:")
        print(f"  Total files:      {result.total_files:,}")
        print(f"  Video files:      {result.video_files:,}")
        print(f"  Other files:      {result.other_files:,}")
        print(f"  Folders scanned:  {result.folders_scanned:,}")
        print(f"  Total size:       {result.total_size_gb:.2f} GB")
        print(f"  Duration:         {result.scan_duration_sec:.2f} sec")

        if result.brand_counts:
            print("\n📁 Brand Distribution:")
            for brand, count in sorted(result.brand_counts.items()):
                print(f"  {brand}: {count}")

        if result.extension_counts:
            print("\n📄 Extension Distribution:")
            for ext, count in sorted(result.extension_counts.items(), key=lambda x: -x[1]):
                print(f"  {ext}: {count}")

        # 파일 목록 출력 (옵션)
        if args.list:
            print("\n📋 Files:")
            for f in files[:50]:  # 최대 50개
                print(f"  {f.relative_path}")
            if len(files) > 50:
                print(f"  ... and {len(files) - 50} more")

        # JSON 출력 (옵션)
        if args.output:
            output_path = Path(args.output)
            output_data = {
                "scan_result": {
                    "total_files": result.total_files,
                    "video_files": result.video_files,
                    "total_size_gb": result.total_size_gb,
                    "folders_scanned": result.folders_scanned,
                    "brand_counts": result.brand_counts,
                    "extension_counts": result.extension_counts,
                },
                "files": [
                    {
                        "path": f.path,
                        "filename": f.filename,
                        "size_mb": f.size_mb,
                        "brand": f.inferred_brand,
                        "asset_type": f.inferred_asset_type,
                    }
                    for f in files
                ],
            }
            with open(output_path, "w", encoding="utf-8") as fp:
                json.dump(output_data, fp, indent=2, ensure_ascii=False, default=str)
            print(f"\n✅ Saved to: {output_path}")

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def cmd_extract(args):
    """NAS → UDM 추출 명령"""
    from .json_exporter import NasToUdmPipeline

    print(f"🚀 Extracting UDM from: {args.path}")
    print(f"   Output: {args.output}")

    try:
        pipeline = NasToUdmPipeline(
            nas_root=args.path,
            output_dir=args.output,
            include_tech_spec=args.tech_spec,
            export_format=args.format,
        )

        result = pipeline.run(
            video_only=not args.all_files,
            max_files=args.max_files,
        )

        # 결과 출력
        print("\n📊 Extraction Result:")
        print("\n  Scan Phase:")
        print(f"    Files scanned:  {result['scan']['total_files']:,}")
        print(f"    Video files:    {result['scan']['video_files']:,}")
        print(f"    Total size:     {result['scan']['total_size_gb']:.2f} GB")

        print("\n  Transform Phase:")
        print(f"    Success:        {result['transform']['success']:,}")
        print(f"    Failed:         {result['transform']['failed']:,}")

        print("\n  Export Phase:")
        print("    Output files:")
        for f in result['export']['files']:
            print(f"      - {f}")

        print(f"\n✅ Done in {result['scan']['duration_sec'] + result['export']['duration_sec']:.2f} sec")

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def cmd_schema(args):
    """JSON Schema 생성 명령"""
    from ..models.udm import generate_json_schema

    schema = generate_json_schema()

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        print(f"✅ Schema saved to: {output_path}")
    else:
        print(json.dumps(schema, indent=2, ensure_ascii=False))


def main():
    """CLI 메인 엔트리포인트"""
    parser = argparse.ArgumentParser(
        description="NAS-to-UDM Extractor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # scan 명령
    scan_parser = subparsers.add_parser("scan", help="Scan NAS filesystem")
    scan_parser.add_argument("path", help="NAS root path")
    scan_parser.add_argument("--all-files", action="store_true", help="Include non-video files")
    scan_parser.add_argument("--include-hidden", action="store_true", help="Include hidden files")
    scan_parser.add_argument("--hash", action="store_true", help="Compute file hashes")
    scan_parser.add_argument("--max-files", type=int, help="Max files to scan (for testing)")
    scan_parser.add_argument("--list", action="store_true", help="List files")
    scan_parser.add_argument("-o", "--output", help="Output JSON file")

    # extract 명령
    extract_parser = subparsers.add_parser("extract", help="Extract UDM from NAS")
    extract_parser.add_argument("path", help="NAS root path")
    extract_parser.add_argument("-o", "--output", default="./output", help="Output directory")
    extract_parser.add_argument("--format", choices=["json", "jsonl"], default="json", help="Output format")
    extract_parser.add_argument("--tech-spec", action="store_true", help="Extract tech metadata (requires ffprobe)")
    extract_parser.add_argument("--all-files", action="store_true", help="Include non-video files")
    extract_parser.add_argument("--max-files", type=int, help="Max files to process (for testing)")

    # schema 명령
    schema_parser = subparsers.add_parser("schema", help="Generate JSON schema")
    schema_parser.add_argument("-o", "--output", help="Output file")

    args = parser.parse_args()

    if args.command == "scan":
        cmd_scan(args)
    elif args.command == "extract":
        cmd_extract(args)
    elif args.command == "schema":
        cmd_schema(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
