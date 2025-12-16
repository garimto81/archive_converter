"""
Build script for PokerGO Downloader
Creates standalone executable using PyInstaller
"""

import subprocess
import sys
import shutil
from pathlib import Path


def main():
    print("=" * 60)
    print("PokerGO Downloader - Build Script")
    print("=" * 60)

    # Get script directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Check if PyInstaller is installed
    print("\n[1/5] Checking PyInstaller...")
    try:
        import PyInstaller
        print(f"  PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("  PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller>=6.3.0"], check=True)

    # Install dependencies
    print("\n[2/5] Installing dependencies...")
    requirements_file = script_dir / "requirements.txt"
    if requirements_file.exists():
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)], check=True)
    else:
        print("  Warning: requirements.txt not found")

    # Create data directory if not exists
    print("\n[3/5] Preparing data directory...")
    data_dir = script_dir / "data"
    data_dir.mkdir(exist_ok=True)
    (data_dir / "pokergo").mkdir(exist_ok=True)

    # Create placeholder file to ensure directory is included
    placeholder = data_dir / "pokergo" / ".gitkeep"
    placeholder.touch()

    # Clean previous build
    print("\n[4/5] Cleaning previous build...")
    dist_dir = script_dir / "dist"
    build_dir = script_dir / "build"

    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print("  Removed dist/")
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print("  Removed build/")

    # Run PyInstaller
    print("\n[5/5] Building executable...")
    spec_file = script_dir / "pokergo_downloader.spec"

    if not spec_file.exists():
        print("  Error: spec file not found!")
        return 1

    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", str(spec_file), "--clean", "--noconfirm"],
        cwd=str(script_dir)
    )

    if result.returncode != 0:
        print("\n[ERROR] Build failed!")
        return 1

    # Copy additional files
    print("\n[POST] Copying additional files...")
    output_dir = script_dir / "dist" / "PokerGO_Downloader_v1.0.1"

    if output_dir.exists():
        # Create data directory in output
        data_dest = output_dir / "data" / "pokergo"
        data_dest.mkdir(parents=True, exist_ok=True)

        # Source data directory
        src_data = project_root / "data" / "pokergo"

        # Copy database
        src_db = src_data / "pokergo.db"
        if src_db.exists():
            shutil.copy(src_db, data_dest / "pokergo.db")
            print("  Copied pokergo.db")

        # Copy important JSON files for import
        json_files = [
            "wsop_for_app_20251216_155853.json",
            "pokergo_merged_all.json",
            "wsop_final_20251216_154021.json",
        ]
        for json_file in json_files:
            src_json = src_data / json_file
            if src_json.exists():
                shutil.copy(src_json, data_dest / json_file)
                print(f"  Copied {json_file}")

    print("\n" + "=" * 60)
    print("[SUCCESS] Build complete!")
    print("=" * 60)
    print(f"\nOutput: {output_dir}")
    print("\nTo distribute:")
    print("  1. Copy the entire 'dist/PokerGO_Downloader' folder")
    print("  2. Run 'PokerGO_Downloader.exe' on target machine")
    print("\nNote: For HLS URL fetching, install Playwright browsers:")
    print("  playwright install chromium")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
