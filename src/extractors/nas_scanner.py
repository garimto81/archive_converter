"""
NAS 파일시스템 스캐너

비디오 파일 탐색 및 기본 메타데이터 수집
"""

import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Iterator, Literal
from dataclasses import dataclass, field

from pydantic import BaseModel, Field


@dataclass
class NasFileInfo:
    """NAS 파일 정보"""

    path: str
    filename: str
    extension: str
    size_bytes: int
    modified_at: datetime
    folder_path: str
    relative_path: str

    # 추론된 메타데이터
    inferred_brand: str | None = None
    inferred_asset_type: str | None = None

    # 해시 (선택적)
    file_hash: str | None = None

    @property
    def size_mb(self) -> float:
        """파일 크기 (MB)"""
        return self.size_bytes / (1024 * 1024)

    @property
    def size_gb(self) -> float:
        """파일 크기 (GB)"""
        return self.size_bytes / (1024 * 1024 * 1024)


@dataclass
class ScanResult:
    """스캔 결과 요약"""

    total_files: int = 0
    total_size_bytes: int = 0
    video_files: int = 0
    other_files: int = 0
    folders_scanned: int = 0
    errors: list[str] = field(default_factory=list)
    scan_duration_sec: float = 0.0

    # 브랜드별 카운트
    brand_counts: dict[str, int] = field(default_factory=dict)

    # 확장자별 카운트
    extension_counts: dict[str, int] = field(default_factory=dict)

    # 증분 스캔 정보
    new_files: int = 0
    modified_files: int = 0
    scan_mode: str = "full"  # "full" or "incremental"

    @property
    def total_size_gb(self) -> float:
        """총 크기 (GB)"""
        return self.total_size_bytes / (1024 * 1024 * 1024)


class NasScanner:
    """NAS 파일시스템 스캐너"""

    # 지원 비디오 확장자
    VIDEO_EXTENSIONS = {".mp4", ".mov", ".mxf", ".avi", ".mkv", ".wmv", ".m4v"}

    # 브랜드 폴더 매핑
    BRAND_FOLDERS = {
        "WSOP": ["WSOP", "WSOPE"],
        "HCL": ["HCL", "HustlerCasinoLive"],
        "PAD": ["PAD", "PokerAfterDark"],
        "GGMillions": ["GGMillions", "GGM"],
        "MPP": ["MPP", "MajorPokerParty"],
        "GOG": ["GOG", "GameOfGold"],
    }

    # Asset Type 폴더 매핑
    ASSET_TYPE_FOLDERS = {
        "STREAM": ["STREAM", "STREAMS", "stream"],
        "SUBCLIP": ["SUBCLIP", "SUBCLIPS", "subclip", "SUB"],
        "EPISODE": ["EPISODE", "EPISODES", "EP", "eps"],
    }

    def __init__(
        self,
        root_path: str,
        include_hidden: bool = False,
        compute_hash: bool = False,
    ):
        """
        Args:
            root_path: NAS 루트 경로 (예: \\\\10.10.100.122\\docker\\GGPNAs\\ARCHIVE)
            include_hidden: 숨김 파일 포함 여부
            compute_hash: 파일 해시 계산 여부 (느려짐)
        """
        self.root_path = Path(root_path)
        self.include_hidden = include_hidden
        self.compute_hash = compute_hash

        if not self.root_path.exists():
            raise FileNotFoundError(f"Root path not found: {root_path}")

    def scan(
        self,
        video_only: bool = True,
        max_files: int | None = None,
    ) -> Iterator[NasFileInfo]:
        """
        NAS 파일시스템 스캔

        Args:
            video_only: 비디오 파일만 반환
            max_files: 최대 파일 수 (테스트용)

        Yields:
            NasFileInfo 객체
        """
        count = 0

        for root, dirs, files in os.walk(self.root_path):
            # 숨김 폴더 제외
            if not self.include_hidden:
                dirs[:] = [d for d in dirs if not d.startswith(".")]

            for filename in files:
                # 숨김 파일 제외
                if not self.include_hidden and filename.startswith("."):
                    continue

                file_path = Path(root) / filename
                ext = file_path.suffix.lower()

                # 비디오 파일 필터링
                if video_only and ext not in self.VIDEO_EXTENSIONS:
                    continue

                try:
                    stat = file_path.stat()

                    # 상대 경로 계산
                    rel_path = file_path.relative_to(self.root_path)

                    # 브랜드/Asset Type 추론
                    inferred_brand = self._infer_brand(str(rel_path))
                    inferred_asset_type = self._infer_asset_type(str(rel_path))

                    # 파일 해시 (선택적)
                    file_hash = None
                    if self.compute_hash:
                        file_hash = self._compute_hash(file_path)

                    info = NasFileInfo(
                        path=str(file_path),
                        filename=filename,
                        extension=ext,
                        size_bytes=stat.st_size,
                        modified_at=datetime.fromtimestamp(stat.st_mtime),
                        folder_path=str(file_path.parent),
                        relative_path=str(rel_path),
                        inferred_brand=inferred_brand,
                        inferred_asset_type=inferred_asset_type,
                        file_hash=file_hash,
                    )

                    yield info

                    count += 1
                    if max_files and count >= max_files:
                        return

                except (OSError, PermissionError) as e:
                    # 접근 불가 파일 건너뛰기
                    continue

    def scan_with_stats(
        self,
        video_only: bool = True,
        max_files: int | None = None,
        since: datetime | None = None,
        known_files: set[str] | None = None,
    ) -> tuple[list[NasFileInfo], ScanResult]:
        """
        스캔 + 통계 수집

        Args:
            video_only: 비디오 파일만 반환
            max_files: 최대 파일 수 (테스트용)
            since: 이 시간 이후 수정된 파일만 반환 (증분 스캔)
            known_files: 이미 알려진 파일 경로 집합 (새 파일 감지용)

        Returns:
            (파일 목록, 스캔 결과)
        """
        import time
        start_time = time.time()

        files: list[NasFileInfo] = []
        result = ScanResult()
        result.scan_mode = "incremental" if since else "full"

        folders_seen = set()
        known_files = known_files or set()

        for file_info in self.scan(video_only=False, max_files=max_files):
            result.total_files += 1
            result.total_size_bytes += file_info.size_bytes

            # 폴더 카운트
            if file_info.folder_path not in folders_seen:
                folders_seen.add(file_info.folder_path)
                result.folders_scanned += 1

            # 확장자 카운트
            ext = file_info.extension.lower()
            result.extension_counts[ext] = result.extension_counts.get(ext, 0) + 1

            # 증분 스캔: 새 파일 또는 수정된 파일만
            is_new = file_info.path not in known_files
            is_modified = since and file_info.modified_at > since

            if is_new:
                result.new_files += 1
            if is_modified and not is_new:
                result.modified_files += 1

            # 증분 모드에서는 새 파일/수정된 파일만 포함
            include_file = True
            if since:
                include_file = is_new or is_modified

            # 비디오 파일 여부
            if ext in self.VIDEO_EXTENSIONS:
                result.video_files += 1

                # 브랜드 카운트
                if file_info.inferred_brand:
                    brand = file_info.inferred_brand
                    result.brand_counts[brand] = result.brand_counts.get(brand, 0) + 1

                if video_only and include_file:
                    files.append(file_info)
            else:
                result.other_files += 1
                if not video_only and include_file:
                    files.append(file_info)

        result.scan_duration_sec = time.time() - start_time

        return files, result

    def _infer_brand(self, relative_path: str) -> str | None:
        """경로에서 브랜드 추론"""
        path_upper = relative_path.upper()

        for brand, folders in self.BRAND_FOLDERS.items():
            for folder in folders:
                if folder.upper() in path_upper:
                    return brand

        return None

    def _infer_asset_type(self, relative_path: str) -> str | None:
        """경로에서 Asset Type 추론"""
        path_upper = relative_path.upper()

        for asset_type, folders in self.ASSET_TYPE_FOLDERS.items():
            for folder in folders:
                if folder.upper() in path_upper:
                    return asset_type

        return None

    def _compute_hash(self, file_path: Path, chunk_size: int = 8192) -> str:
        """파일 MD5 해시 계산 (첫 1MB만)"""
        hash_md5 = hashlib.md5()
        bytes_read = 0
        max_bytes = 1024 * 1024  # 1MB

        try:
            with open(file_path, "rb") as f:
                while bytes_read < max_bytes:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    hash_md5.update(chunk)
                    bytes_read += len(chunk)

            return hash_md5.hexdigest()
        except Exception:
            return None

    def get_folder_tree(self, max_depth: int = 3) -> dict:
        """폴더 트리 구조 반환"""
        tree = {"name": self.root_path.name, "path": str(self.root_path), "children": []}

        self._build_tree(self.root_path, tree, 0, max_depth)

        return tree

    def _build_tree(self, path: Path, node: dict, depth: int, max_depth: int):
        """재귀적으로 트리 구성"""
        if depth >= max_depth:
            return

        try:
            for item in sorted(path.iterdir()):
                if item.is_dir():
                    if not self.include_hidden and item.name.startswith("."):
                        continue

                    child = {
                        "name": item.name,
                        "path": str(item),
                        "children": [],
                    }
                    node["children"].append(child)
                    self._build_tree(item, child, depth + 1, max_depth)
        except PermissionError:
            pass
