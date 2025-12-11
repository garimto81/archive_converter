"""
Mock data service for development.
Generates realistic 1:N relationship data (NAS File → Sheet Records → UDM Segments).
"""
import random
from datetime import datetime, timedelta
from typing import Literal

from ..schemas.matching import (
    NasFileInfo,
    SegmentRecord,
    ValidationWarning,
    MatchingItem,
    UdmInfo,
)
from ..schemas.nas import NasFolder, NasFile


class MockDataService:
    """Service for generating mock data"""

    # Brand names from PRD
    BRANDS = ["WSOP", "HCL", "PAD", "GGMillions", "MPP", "GOG"]

    # Asset types
    ASSET_TYPES = ["STREAM", "SUBCLIP", "EPISODE"]

    # Player names
    PLAYERS = [
        "Phil Ivey",
        "Daniel Negreanu",
        "Phil Hellmuth",
        "Tom Dwan",
        "Doug Polk",
        "Garrett Adelstein",
        "Robbi Jade Lew",
        "Eric Persson",
    ]

    # Poker hands
    HANDS = [
        "AA vs KK",
        "KK vs AA",
        "QQ vs AK",
        "JJ vs AQ",
        "TT vs 99",
        "AK vs AQ",
        "AA vs QQ",
    ]

    # Tags
    TAGS = [
        "cooler",
        "hero-call",
        "bluff",
        "all-in",
        "bad-beat",
        "sick-hand",
        "fold",
        "big-pot",
    ]

    def __init__(self):
        """Initialize mock data generator"""
        self._files: list[dict] = []
        self._generate_mock_files()

    def _generate_mock_files(self):
        """Generate mock NAS files with 1:N segments"""
        # Generate 20 files with varying segment counts
        file_configs = [
            # Complete files (all segments converted)
            ("STREAM_01.mp4", "WSOP", 15, 15, "complete"),
            ("PAD_S13_EP01.mp4", "PAD", 8, 8, "complete"),
            ("WCLA24-01.mp4", "WSOP", 1, 1, "complete"),
            ("WCLA24-02.mp4", "WSOP", 1, 1, "complete"),
            ("WCLA24-03.mp4", "WSOP", 1, 1, "complete"),
            ("HCL_2024_EP10.mp4", "HCL", 12, 12, "complete"),

            # Partial files (some segments not converted)
            ("STREAM_02.mp4", "WSOP", 10, 7, "partial"),
            ("PAD_S13_EP02.mp4", "PAD", 6, 4, "partial"),
            ("HCL_2024_EP11.mp4", "HCL", 9, 5, "partial"),

            # Warning files (validation issues)
            ("STREAM_03.mp4", "WSOP", 8, 6, "warning"),
            ("PAD_S13_EP03.mp4", "PAD", 5, 5, "warning"),

            # No metadata files
            ("UNKNOWN_FILE_01.mp4", "WSOP", 0, 0, "no_metadata"),
            ("UNKNOWN_FILE_02.mp4", "HCL", 0, 0, "no_metadata"),

            # More mixed cases
            ("GGM_FINAL_01.mp4", "GGMillions", 4, 4, "complete"),
            ("MPP_S01_EP01.mp4", "MPP", 7, 7, "complete"),
            ("GOG_FINAL.mp4", "GOG", 3, 3, "complete"),
            ("WSOPE_2024_01.mp4", "WSOP", 11, 9, "partial"),
            ("HCL_SPECIAL.mp4", "HCL", 6, 6, "complete"),
            ("PAD_BONUS.mp4", "PAD", 2, 2, "complete"),
            ("STREAM_04.mp4", "WSOP", 14, 10, "partial"),
        ]

        for file_name, brand, segment_count, udm_count, status in file_configs:
            self._files.append(
                self._create_file_with_segments(
                    file_name, brand, segment_count, udm_count, status
                )
            )

    def _create_file_with_segments(
        self,
        file_name: str,
        brand: str,
        segment_count: int,
        udm_count: int,
        status: str,
    ) -> dict:
        """Create a file entry with segments (1:N relationship)"""
        # NAS file info
        duration_sec = segment_count * 200 + random.randint(0, 300)  # ~3-4 min per segment
        size_mb = duration_sec * 1.2  # ~1.2 MB per second

        nas_info = NasFileInfo(
            exists=(status != "orphan"),
            path=f"/ARCHIVE/{brand}/{file_name}",
            size_mb=round(size_mb, 2),
            duration_sec=float(duration_sec),
            modified_at=datetime.now() - timedelta(days=random.randint(1, 90)),
            inferred_brand=brand,
        )

        # Generate segments
        segments: list[SegmentRecord] = []
        warnings: list[ValidationWarning] = []

        if segment_count > 0:
            current_time = 0.0
            for i in range(segment_count):
                # Time range
                segment_duration = random.randint(120, 300)  # 2-5 minutes
                time_in_sec = current_time
                time_out_sec = current_time + segment_duration
                current_time = time_out_sec + random.randint(5, 30)  # Gap between segments

                # UDM status
                if i < udm_count:
                    udm_status = "complete"
                    udm_uuid = f"uuid-{file_name}-seg{i+1}"
                else:
                    udm_status = "pending"
                    udm_uuid = None

                # Check for warnings
                if status == "warning" and i == segment_count - 1:
                    # Last segment has warning
                    udm_status = "warning"
                    warnings.append(
                        ValidationWarning(
                            segment_row=i + 1,
                            type="missing_hands",
                            message="Hands information missing",
                        )
                    )

                segment = SegmentRecord(
                    row_number=i + 1,
                    source="archive_metadata" if i % 2 == 0 else "iconik_metadata",
                    time_in=self._format_timecode(time_in_sec),
                    time_out=self._format_timecode(time_out_sec),
                    time_in_sec=time_in_sec,
                    time_out_sec=time_out_sec,
                    duration_sec=segment_duration,
                    rating=random.randint(2, 5) if udm_status != "warning" else None,
                    winner=random.choice(self.PLAYERS) if udm_status != "warning" else None,
                    hands=random.choice(self.HANDS) if udm_status != "warning" else None,
                    tags=random.sample(self.TAGS, k=random.randint(1, 3)),
                    udm=UdmInfo(uuid=udm_uuid, status=udm_status),
                )
                segments.append(segment)

        # Determine status detail
        if segment_count == 0:
            status_detail = "No metadata"
        else:
            status_detail = f"{udm_count}/{segment_count}"

        return {
            "file_name": file_name,
            "nas": nas_info,
            "segment_count": segment_count,
            "udm_count": udm_count,
            "segments": segments,
            "status": status,
            "status_detail": status_detail,
            "warnings": warnings,
            "is_expanded": False,
        }

    @staticmethod
    def _format_timecode(seconds: float) -> str:
        """Convert seconds to HH:MM:SS timecode"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def get_matching_items(
        self,
        status_filter: str | None = None,
        search: str | None = None,
    ) -> list[MatchingItem]:
        """Get matching matrix items with optional filters"""
        items = []

        for file_data in self._files:
            # Apply status filter
            if status_filter and status_filter != "all":
                if file_data["status"] != status_filter:
                    continue

            # Apply search filter
            if search:
                if search.lower() not in file_data["file_name"].lower():
                    continue

            # Convert to MatchingItem
            item = MatchingItem(**file_data)
            items.append(item)

        return items

    def get_file_segments(self, file_name: str) -> dict | None:
        """Get segments for a specific file"""
        for file_data in self._files:
            if file_data["file_name"] == file_name:
                return file_data
        return None

    def get_stats(self) -> dict:
        """Calculate matching statistics"""
        total_files = len(self._files)
        total_segments = sum(f["segment_count"] for f in self._files)
        matched_files = sum(1 for f in self._files if f["segment_count"] > 0)
        matched_segments = sum(f["udm_count"] for f in self._files)
        unmatched_nas = sum(1 for f in self._files if f["segment_count"] == 0)
        orphan_records = 5  # Mock orphan records

        # File-level stats
        complete_files = sum(
            1 for f in self._files
            if f["status"] == "complete" and f["segment_count"] > 0
        )
        partial_files = sum(1 for f in self._files if f["status"] == "partial")
        warning_files = sum(1 for f in self._files if f["status"] == "warning")

        # Segment-level stats
        complete_segments = matched_segments
        pending_segments = total_segments - matched_segments
        warning_segments = sum(len(f["warnings"]) for f in self._files)

        # Coverage metrics
        archive_to_nas = 1.0
        iconik_to_nas = 0.97
        nas_to_any_sheet = matched_files / total_files if total_files > 0 else 0
        segment_conversion_rate = (
            matched_segments / total_segments if total_segments > 0 else 0
        )

        # Summary
        files_with_segments = [f for f in self._files if f["segment_count"] > 0]
        avg_segments = (
            sum(f["segment_count"] for f in files_with_segments) / len(files_with_segments)
            if files_with_segments else 0
        )
        max_segments = max((f["segment_count"] for f in self._files), default=0)
        min_segments = min(
            (f["segment_count"] for f in self._files if f["segment_count"] > 0),
            default=0
        )

        return {
            "sources": {
                "nas": {
                    "total_files": total_files,
                    "total_size_gb": 2450.5,
                    "scanned_at": datetime.now(),
                },
                "archive_metadata": {
                    "total_records": 38,
                    "unique_files": 38,
                    "synced_at": datetime.now() - timedelta(minutes=5),
                },
                "iconik_metadata": {
                    "total_records": 200,
                    "unique_files": 45,
                    "synced_at": datetime.now() - timedelta(minutes=10),
                },
            },
            "matching": {
                "files": {
                    "complete": complete_files,
                    "partial": partial_files,
                    "warning": warning_files,
                    "unmatched": unmatched_nas,
                    "total_with_metadata": matched_files,
                },
                "segments": {
                    "complete": complete_segments,
                    "pending": pending_segments,
                    "warning": warning_segments,
                    "total": total_segments,
                },
                "orphan_records": orphan_records,
            },
            "coverage": {
                "archive_to_nas": archive_to_nas,
                "iconik_to_nas": iconik_to_nas,
                "nas_to_any_sheet": nas_to_any_sheet,
                "segment_conversion_rate": segment_conversion_rate,
            },
            "summary": {
                "avg_segments_per_file": avg_segments,
                "max_segments_per_file": max_segments,
                "min_segments_per_file": min_segments,
            },
        }

    def generate_nas_tree(self) -> NasFolder:
        """Generate mock NAS folder tree"""
        # Root folder
        root = NasFolder(
            name="ARCHIVE",
            path="/ARCHIVE",
            file_count=0,
            folder_count=4,
        )

        # WSOP folder
        wsop = NasFolder(
            name="WSOP",
            path="/ARCHIVE/WSOP",
            file_count=0,
            folder_count=2,
        )
        wsop.children = [
            NasFolder(
                name="STREAM",
                path="/ARCHIVE/WSOP/STREAM",
                file_count=12,
                folder_count=0,
            ),
            NasFolder(
                name="SUBCLIP",
                path="/ARCHIVE/WSOP/SUBCLIP",
                file_count=38,
                folder_count=0,
            ),
        ]

        # HCL folder
        hcl = NasFolder(
            name="HCL",
            path="/ARCHIVE/HCL",
            file_count=15,
            folder_count=0,
        )

        # PAD folder
        pad = NasFolder(
            name="PAD",
            path="/ARCHIVE/PAD",
            file_count=24,
            folder_count=0,
        )

        # Other folders
        other = NasFolder(
            name="OTHER",
            path="/ARCHIVE/OTHER",
            file_count=8,
            folder_count=0,
        )

        root.children = [wsop, hcl, pad, other]
        return root

    def get_files_in_folder(self, path: str) -> list[NasFile]:
        """Get files in a specific folder"""
        # Mock file list based on path
        files = []

        if "STREAM" in path:
            for i in range(1, 5):
                files.append(
                    NasFile(
                        name=f"STREAM_{i:02d}.mp4",
                        path=f"{path}/STREAM_{i:02d}.mp4",
                        size_mb=2450.5,
                        modified_at=datetime.now() - timedelta(days=i),
                        has_metadata=True,
                    )
                )
        elif "SUBCLIP" in path:
            for i in range(1, 4):
                files.append(
                    NasFile(
                        name=f"WCLA24-{i:02d}.mp4",
                        path=f"{path}/WCLA24-{i:02d}.mp4",
                        size_mb=245.8,
                        modified_at=datetime.now() - timedelta(days=i),
                        has_metadata=True,
                    )
                )
        else:
            # Generic files
            for i in range(1, 6):
                files.append(
                    NasFile(
                        name=f"FILE_{i:02d}.mp4",
                        path=f"{path}/FILE_{i:02d}.mp4",
                        size_mb=random.uniform(100, 3000),
                        modified_at=datetime.now() - timedelta(days=i * 5),
                        has_metadata=random.choice([True, False]),
                    )
                )

        return files
