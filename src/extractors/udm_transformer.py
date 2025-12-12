"""
UDM 변환기

NAS 파일 정보 → UDM Asset 변환
"""

import uuid
import hashlib
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path

from ..models.udm import (
    Asset,
    Segment,
    Brand,
    AssetType,
    TechSpec,
    FileNameMeta,
    EventContext,
    parse_filename,
    infer_brand_from_path,
    infer_asset_type_from_path,
)
from .nas_scanner import NasFileInfo


@dataclass
class TransformResult:
    """변환 결과"""

    success: int = 0
    failed: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.success + self.failed + self.skipped


class UdmTransformer:
    """NAS 파일 → UDM Asset 변환기"""

    def __init__(
        self,
        default_brand: str | None = None,
        default_asset_type: str = "SUBCLIP",
        include_tech_spec: bool = False,
    ):
        """
        Args:
            default_brand: 기본 브랜드 (추론 실패 시)
            default_asset_type: 기본 Asset Type
            include_tech_spec: FFprobe로 기술 메타데이터 추출 여부
        """
        self.default_brand = default_brand
        self.default_asset_type = default_asset_type
        self.include_tech_spec = include_tech_spec

    def transform(self, file_info: NasFileInfo) -> Asset | None:
        """
        NAS 파일 정보를 UDM Asset으로 변환

        Args:
            file_info: NAS 파일 정보

        Returns:
            Asset 객체 또는 None (변환 실패 시)
        """
        try:
            # 1. UUID 생성 (파일 경로 기반 deterministic)
            asset_uuid = self._generate_uuid(file_info.path)

            # 2. 파일명 파싱
            filename_meta = self._parse_filename(file_info.filename)

            # 3. 브랜드 결정
            brand = self._determine_brand(file_info, filename_meta)

            # 4. Asset Type 결정
            asset_type = self._determine_asset_type(file_info, filename_meta)

            # 5. Tech Spec 생성 (선택적)
            tech_spec = None
            if self.include_tech_spec:
                tech_spec = self._extract_tech_spec(file_info)

            # 6. Event Context 생성 (필수)
            event_context = self._create_event_context(filename_meta, brand)

            # 7. Source Origin 생성 (문자열)
            source_origin = self._create_source_origin_str(file_info, brand)

            # 8. Asset 생성
            asset = Asset(
                asset_uuid=asset_uuid,
                file_name=file_info.filename,
                file_path_rel=file_info.relative_path,
                file_path_nas=file_info.path,
                asset_type=asset_type,
                event_context=event_context,
                tech_spec=tech_spec,
                file_name_meta=filename_meta,
                source_origin=source_origin,
                segments=[],  # Segment는 별도 처리
            )

            return asset

        except Exception:
            return None

    def transform_batch(
        self,
        files: list[NasFileInfo],
    ) -> tuple[list[Asset], TransformResult]:
        """
        배치 변환

        Args:
            files: NAS 파일 목록

        Returns:
            (Asset 목록, 변환 결과)
        """
        assets: list[Asset] = []
        result = TransformResult()

        for file_info in files:
            asset = self.transform(file_info)

            if asset:
                assets.append(asset)
                result.success += 1
            else:
                result.failed += 1
                result.errors.append(f"Failed to transform: {file_info.filename}")

        return assets, result

    def _generate_uuid(self, path: str) -> str:
        """경로 기반 deterministic UUID 생성"""
        # 경로를 정규화하여 일관된 UUID 생성
        normalized = path.replace("\\", "/").lower()
        hash_bytes = hashlib.sha256(normalized.encode()).digest()[:16]
        return str(uuid.UUID(bytes=hash_bytes))

    def _parse_filename(self, filename: str) -> FileNameMeta | None:
        """파일명 파싱"""
        try:
            result = parse_filename(filename)
            if result:
                return result
        except Exception:
            pass

        # 파싱 실패 시 기본 메타데이터
        return FileNameMeta(
            raw_description=filename,
        )

    def _determine_brand(
        self,
        file_info: NasFileInfo,
        filename_meta: FileNameMeta | None,
    ) -> Brand:
        """브랜드 결정"""
        # 1. NAS 경로에서 추론된 브랜드
        if file_info.inferred_brand:
            try:
                return Brand(file_info.inferred_brand)
            except ValueError:
                pass

        # 2. 파일명에서 추론 (FileNameMeta의 code_prefix 사용)
        if filename_meta and filename_meta.code_prefix:
            code = filename_meta.code_prefix
            brand_map = {
                "WSOP": Brand.WSOP,
                "WSOPE": Brand.WSOP,
                "WCLA": Brand.WSOP,
                "WP": Brand.WSOP,
                "HCL": Brand.HCL,
                "PAD": Brand.PAD,
                "GGM": Brand.GG_MILLIONS,
                "GGMILLIONS": Brand.GG_MILLIONS,
                "MPP": Brand.MPP,
                "GOG": Brand.GOG,
                "STREAM": Brand.WSOP,
            }
            if code.upper() in brand_map:
                return brand_map[code.upper()]

        # 3. 경로에서 직접 추론
        try:
            inferred = infer_brand_from_path(file_info.path)
            if inferred:
                return Brand(inferred)
        except Exception:
            pass

        # 4. 기본값
        if self.default_brand:
            try:
                return Brand(self.default_brand)
            except ValueError:
                pass

        return Brand.WSOP  # 최종 기본값

    def _determine_asset_type(
        self,
        file_info: NasFileInfo,
        filename_meta: FileNameMeta | None,
    ) -> AssetType:
        """Asset Type 결정"""
        # 1. NAS 경로에서 추론된 타입
        if file_info.inferred_asset_type:
            try:
                return AssetType(file_info.inferred_asset_type)
            except ValueError:
                pass

        # 2. 경로에서 직접 추론
        try:
            inferred = infer_asset_type_from_path(file_info.path)
            if inferred:
                return AssetType(inferred)
        except Exception:
            pass

        # 3. 기본값
        try:
            return AssetType(self.default_asset_type)
        except ValueError:
            return AssetType.SUBCLIP

    def _create_source_origin_str(self, file_info: NasFileInfo, brand: Brand) -> str:
        """Source Origin 문자열 생성"""
        year = datetime.now().year
        brand_str = brand.value if hasattr(brand, 'value') else str(brand)
        return f"NAS_{brand_str}_{year}"

    def _extract_tech_spec(self, file_info: NasFileInfo) -> TechSpec | None:
        """기술 메타데이터 추출 (FFprobe)"""
        try:
            import subprocess
            import json

            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_format",
                    "-show_streams",
                    file_info.path,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return None

            data = json.loads(result.stdout)

            # 비디오 스트림 찾기
            video_stream = None
            audio_stream = None

            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video" and not video_stream:
                    video_stream = stream
                elif stream.get("codec_type") == "audio" and not audio_stream:
                    audio_stream = stream

            if not video_stream:
                return None

            # TechSpec 생성
            duration = float(data.get("format", {}).get("duration", 0))

            return TechSpec(
                duration_sec=duration,
                fps=eval(video_stream.get("r_frame_rate", "30/1")),
                width=video_stream.get("width", 0),
                height=video_stream.get("height", 0),
                codec=video_stream.get("codec_name", "unknown"),
                audio_codec=audio_stream.get("codec_name") if audio_stream else None,
                bitrate_kbps=int(data.get("format", {}).get("bit_rate", 0)) // 1000,
            )

        except Exception:
            return None

    def _create_event_context(
        self,
        filename_meta: FileNameMeta | None,
        brand: Brand,
    ) -> EventContext:
        """Event Context 생성 (year, brand 필수)"""
        year = datetime.now().year  # 기본값: 현재 연도
        episode = None
        season = None

        if filename_meta:
            # 연도 추출 (year_code 속성에서)
            if filename_meta.year_code:
                try:
                    year_code = str(filename_meta.year_code)
                    # 2자리 연도 처리 (예: 24 -> 2024)
                    if len(year_code) == 2:
                        year = 2000 + int(year_code)
                    else:
                        year = int(year_code)
                except (ValueError, TypeError):
                    pass

            # 에피소드 추출
            if filename_meta.episode:
                episode = filename_meta.episode

            # 시즌 추출
            if filename_meta.season:
                season = filename_meta.season

        return EventContext(
            year=year,
            brand=brand,
            season=season,
            episode=episode,
        )
