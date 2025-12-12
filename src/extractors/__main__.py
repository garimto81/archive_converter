"""
NAS-to-UDM Extractor CLI entry point

Usage:
    python -m src.extractors scan <nas_path>
    python -m src.extractors extract <nas_path> -o ./output
    python -m src.extractors schema -o ./output/schema.json
"""

from .cli import main

if __name__ == "__main__":
    main()
