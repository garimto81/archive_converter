"""
NAS 실시간 스캐너 서비스

실제 NAS 파일시스템과 대시보드를 연결합니다.
기존 src/extractors/nas_scanner.py를 활용합니다.
"""
import sys
from datetime import datetime
from pathlib import Path
from typing import Literal

# src/extractors/nas_scanner.py 직접 import (패키지 __init__ 우회)
_nas_scanner_path = Path(__file__).parent.parent.parent.parent.parent / "src" / "extractors"
sys.path.insert(0, str(_nas_scanner_path))

# nas_scanner 모듈만 직접 import (extractors 패키지의 __init__.py 우회)
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "nas_scanner",
    _nas_scanner_path / "nas_scanner.py"
)
_nas_scanner_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_nas_scanner_module)

NasScanner = _nas_scanner_module.NasScanner
SrcNasFileInfo = _nas_scanner_module.NasFileInfo
ScanResult = _nas_scanner_module.ScanResult

from ..schemas.matching import (
    NasFileInfo,
    MatchingItem,
    SegmentRecord,
    UdmInfo,
)
from ..schemas.nas import NasFolder, NasFile


class NasRealTimeService:
    """실제 NAS 파일시스템 서비스"""

    def __init__(self, nas_path: str = "Z:\\ARCHIVE"):
        """
        Args:
            nas_path: NAS 마운트 경로 (기본값: Z:\\ARCHIVE)
        """
        self.nas_path = nas_path
        self._scanner: NasScanner | None = None
        self._cached_files: list[SrcNasFileInfo] = []
        self._cached_stats: ScanResult | None = None
        self._last_scan: datetime | None = None

    @property
    def scanner(self) -> NasScanner:
        """NasScanner 인스턴스 (지연 초기화)"""
        if self._scanner is None:
            self._scanner = NasScanner(
                root_path=self.nas_path,
                include_hidden=False,
                compute_hash=False,
            )
        return self._scanner

    def refresh_scan(
        self,
        force: bool = False,
        mode: Literal["full", "incremental"] = "full",
    ) -> ScanResult:
        """
        NAS 스캔 실행/갱신

        Args:
            force: 강제 갱신 여부
            mode: 스캔 모드
                - "full": 전체 재스캔
                - "incremental": 마지막 스캔 이후 변경된 파일만

        Returns:
            ScanResult: 스캔 결과
        """
        # 캐시가 있고 강제 갱신이 아니면 캐시 반환
        if not force and self._cached_stats is not None:
            return self._cached_stats

        # 증분 스캔 파라미터 준비
        since = None
        known_files: set[str] = set()

        if mode == "incremental" and self._last_scan is not None:
            since = self._last_scan
            known_files = {f.path for f in self._cached_files}

        # 스캔 실행
        new_files, stats = self.scanner.scan_with_stats(
            video_only=True,
            since=since,
            known_files=known_files,
        )

        # 증분 모드: 새 파일을 기존 캐시에 추가
        if mode == "incremental" and self._cached_files:
            # 기존 파일 + 새 파일 (중복 제거)
            existing_paths = {f.path for f in self._cached_files}
            for f in new_files:
                if f.path not in existing_paths:
                    self._cached_files.append(f)
        else:
            # 전체 스캔: 캐시 교체
            self._cached_files = new_files

        self._cached_stats = stats
        self._last_scan = datetime.now()
        return self._cached_stats

    def get_matching_items(
        self,
        status_filter: str | None = None,
        search: str | None = None,
    ) -> list[MatchingItem]:
        """매칭 매트릭스 항목 반환 (MockDataService 호환)"""
        # 스캔 실행 (캐시 사용)
        self.refresh_scan()

        items = []
        for src_file in self._cached_files:
            # 검색 필터
            if search and search.lower() not in src_file.filename.lower():
                continue

            # NasFileInfo 변환
            nas_info = NasFileInfo(
                exists=True,
                path=src_file.path,
                size_mb=round(src_file.size_mb, 2),
                duration_sec=None,  # 실제 duration은 ffprobe 필요
                modified_at=src_file.modified_at,
                inferred_brand=src_file.inferred_brand,
            )

            # 현재는 메타데이터 없이 Asset 정보만 표시
            # 향후 Sheet 연동 시 세그먼트 추가
            status: Literal["complete", "partial", "pending", "warning", "no_metadata", "orphan"] = "no_metadata"

            item = MatchingItem(
                file_name=src_file.filename,
                nas=nas_info,
                segment_count=0,
                udm_count=0,
                segments=[],
                status=status,
                status_detail="No metadata",
                warnings=[],
                is_expanded=False,
            )

            # 상태 필터
            if status_filter and status_filter != "all":
                if item.status != status_filter:
                    continue

            items.append(item)

        return items

    def get_file_segments(self, file_name: str) -> dict | None:
        """특정 파일의 세그먼트 정보 (현재는 메타데이터 없음)"""
        self.refresh_scan()

        for src_file in self._cached_files:
            if src_file.filename == file_name:
                return {
                    "file_name": src_file.filename,
                    "nas": {
                        "exists": True,
                        "path": src_file.path,
                        "size_mb": round(src_file.size_mb, 2),
                        "modified_at": src_file.modified_at,
                        "inferred_brand": src_file.inferred_brand,
                    },
                    "segment_count": 0,
                    "udm_count": 0,
                    "segments": [],
                    "status": "no_metadata",
                    "status_detail": "No metadata",
                    "warnings": [],
                }
        return None

    def get_stats(self) -> dict:
        """통계 데이터 반환 (MockDataService 호환)"""
        stats = self.refresh_scan()

        # 브랜드별 파일 수
        brand_counts = stats.brand_counts

        return {
            "sources": {
                "nas": {
                    "total_files": stats.video_files,
                    "total_size_gb": round(stats.total_size_gb, 2),
                    "scanned_at": self._last_scan,
                    "brand_counts": brand_counts,
                },
                "archive_metadata": {
                    "total_records": 0,  # 향후 Sheet 연동 시 업데이트
                    "unique_files": 0,
                    "synced_at": None,
                },
                "iconik_metadata": {
                    "total_records": 0,
                    "unique_files": 0,
                    "synced_at": None,
                },
            },
            "matching": {
                "files": {
                    "complete": 0,
                    "partial": 0,
                    "warning": 0,
                    "unmatched": stats.video_files,
                    "total_with_metadata": 0,
                },
                "segments": {
                    "complete": 0,
                    "pending": 0,
                    "warning": 0,
                    "total": 0,
                },
                "orphan_records": 0,
            },
            "coverage": {
                "archive_to_nas": 0.0,
                "iconik_to_nas": 0.0,
                "nas_to_any_sheet": 0.0,
                "segment_conversion_rate": 0.0,
            },
            "summary": {
                "avg_segments_per_file": 0.0,
                "max_segments_per_file": 0,
                "min_segments_per_file": 0,
                "scan_duration_sec": stats.scan_duration_sec,
                "folders_scanned": stats.folders_scanned,
                "extension_counts": stats.extension_counts,
            },
        }

    def generate_nas_tree(self) -> NasFolder:
        """NAS 폴더 트리 반환"""
        tree_dict = self.scanner.get_folder_tree(max_depth=4)
        return self._dict_to_nas_folder(tree_dict)

    def _dict_to_nas_folder(self, d: dict) -> NasFolder:
        """dict를 NasFolder로 변환"""
        children = [self._dict_to_nas_folder(c) for c in d.get("children", [])]

        # 파일 수 계산 (해당 폴더 내 비디오 파일)
        folder_path = Path(d["path"])
        file_count = 0
        try:
            if folder_path.exists():
                file_count = sum(
                    1
                    for f in folder_path.iterdir()
                    if f.is_file() and f.suffix.lower() in NasScanner.VIDEO_EXTENSIONS
                )
        except PermissionError:
            pass

        return NasFolder(
            name=d["name"],
            path=d["path"],
            file_count=file_count,
            folder_count=len(children),
            children=children,  # 빈 리스트도 허용
        )

    def get_files_in_folder(self, path: str) -> list[NasFile]:
        """특정 폴더의 파일 목록 반환"""
        folder_path = Path(path)
        files = []

        if not folder_path.exists():
            return files

        try:
            for item in folder_path.iterdir():
                if item.is_file() and item.suffix.lower() in NasScanner.VIDEO_EXTENSIONS:
                    stat = item.stat()

                    # 브랜드 추론
                    try:
                        rel_path = item.relative_to(self.nas_path)
                        inferred_brand = self.scanner._infer_brand(str(rel_path))
                    except ValueError:
                        inferred_brand = None

                    files.append(
                        NasFile(
                            name=item.name,
                            path=str(item),
                            size_mb=round(stat.st_size / (1024 * 1024), 2),
                            modified_at=datetime.fromtimestamp(stat.st_mtime),
                            has_metadata=False,  # 향후 Sheet 매칭 시 업데이트
                        )
                    )
        except PermissionError:
            pass

        return files

    def get_scan_status(self) -> dict:
        """스캔 상태 반환"""
        return {
            "last_scan": self._last_scan,
            "cached_files": len(self._cached_files),
            "is_cached": self._cached_stats is not None,
            "nas_path": self.nas_path,
            "nas_accessible": Path(self.nas_path).exists(),
        }


# 싱글톤 인스턴스
_nas_service: NasRealTimeService | None = None


def get_nas_service(nas_path: str = "Z:\\ARCHIVE") -> NasRealTimeService:
    """NasRealTimeService 싱글톤 반환"""
    global _nas_service
    if _nas_service is None:
        _nas_service = NasRealTimeService(nas_path=nas_path)
    return _nas_service
