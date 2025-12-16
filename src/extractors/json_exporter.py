"""
JSON Exporter

UDM Asset → JSON 파일 내보내기
"""

import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Literal


from ..models.udm import Asset, generate_json_schema


@dataclass
class ExportConfig:
    """내보내기 설정"""

    # 출력 형식
    format: Literal["json", "jsonl"] = "json"

    # JSON 옵션
    indent: int | None = 2
    ensure_ascii: bool = False

    # 파일 옵션
    output_dir: str = "./output"
    filename_prefix: str = "udm_export"
    include_timestamp: bool = True

    # 청킹 옵션 (대용량)
    chunk_size: int = 1000  # JSONL 청크 크기
    max_file_size_mb: int = 100  # 단일 파일 최대 크기


@dataclass
class ExportResult:
    """내보내기 결과"""

    success: bool = False
    output_files: list[str] = field(default_factory=list)
    total_assets: int = 0
    total_segments: int = 0
    file_size_bytes: int = 0
    export_duration_sec: float = 0.0
    errors: list[str] = field(default_factory=list)


class JsonExporter:
    """UDM JSON Exporter"""

    def __init__(self, config: ExportConfig | None = None):
        """
        Args:
            config: 내보내기 설정
        """
        self.config = config or ExportConfig()

    def export(
        self,
        assets: list[Asset],
        metadata: dict | None = None,
    ) -> ExportResult:
        """
        Asset 목록을 JSON으로 내보내기

        Args:
            assets: Asset 목록
            metadata: 추가 메타데이터

        Returns:
            ExportResult
        """
        import time
        start_time = time.time()

        result = ExportResult()
        result.total_assets = len(assets)
        result.total_segments = sum(len(a.segments) for a in assets)

        try:
            # 출력 디렉토리 생성
            output_dir = Path(self.config.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # 파일명 생성
            filename = self._generate_filename()

            if self.config.format == "json":
                output_file = self._export_json(assets, metadata, output_dir, filename)
            else:
                output_file = self._export_jsonl(assets, output_dir, filename)

            result.output_files.append(str(output_file))
            result.file_size_bytes = output_file.stat().st_size
            result.success = True

        except Exception as e:
            result.errors.append(str(e))
            result.success = False

        result.export_duration_sec = time.time() - start_time

        return result

    def _generate_filename(self) -> str:
        """파일명 생성"""
        parts = [self.config.filename_prefix]

        if self.config.include_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            parts.append(timestamp)

        return "_".join(parts)

    def _export_json(
        self,
        assets: list[Asset],
        metadata: dict | None,
        output_dir: Path,
        filename: str,
    ) -> Path:
        """단일 JSON 파일로 내보내기 (배치 형식)"""
        # 배치 내보내기용 구조 (UDMDocument는 단일 Asset용)
        export_data = {
            "_metadata": {
                "version": "3.1.0",
                "generated_at": datetime.now().isoformat(),
                "source": "nas_extractor",
                "total_assets": len(assets),
                "total_segments": sum(len(a.segments) for a in assets),
                "custom": metadata or {},
            },
            "assets": [
                asset.model_dump(mode="json", exclude_none=True)
                for asset in assets
            ],
        }

        # JSON 직렬화
        output_file = output_dir / f"{filename}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(
                export_data,
                f,
                indent=self.config.indent,
                ensure_ascii=self.config.ensure_ascii,
                default=str,
            )

        return output_file

    def _export_jsonl(
        self,
        assets: list[Asset],
        output_dir: Path,
        filename: str,
    ) -> Path:
        """JSONL (JSON Lines) 형식으로 내보내기"""
        output_file = output_dir / f"{filename}.jsonl"

        with open(output_file, "w", encoding="utf-8") as f:
            for asset in assets:
                line = json.dumps(
                    asset.model_dump(mode="json", exclude_none=True),
                    ensure_ascii=self.config.ensure_ascii,
                    default=str,
                )
                f.write(line + "\n")

        return output_file

    def export_schema(self, output_dir: str | None = None) -> Path:
        """JSON Schema 내보내기"""
        output_dir = Path(output_dir or self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        schema = generate_json_schema()

        output_file = output_dir / "udm_schema.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(
                schema,
                f,
                indent=2,
                ensure_ascii=False,
            )

        return output_file

    def export_summary(
        self,
        assets: list[Asset],
        output_dir: str | None = None,
    ) -> Path:
        """요약 통계 내보내기"""
        output_dir = Path(output_dir or self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 통계 계산
        brand_counts: dict[str, int] = {}
        asset_type_counts: dict[str, int] = {}
        total_segments = 0
        total_duration = 0.0

        for asset in assets:
            # 브랜드 카운트 (event_context에서 가져옴)
            brand = str(asset.event_context.brand) if asset.event_context else "unknown"
            brand_counts[brand] = brand_counts.get(brand, 0) + 1

            # Asset Type 카운트 (use_enum_values=True이므로 이미 문자열)
            asset_type = str(asset.asset_type) if asset.asset_type else "unknown"
            asset_type_counts[asset_type] = asset_type_counts.get(asset_type, 0) + 1

            # Segment 카운트
            total_segments += len(asset.segments)

            # Duration
            if asset.tech_spec and asset.tech_spec.duration_sec:
                total_duration += asset.tech_spec.duration_sec

        summary = {
            "generated_at": datetime.now().isoformat(),
            "total_assets": len(assets),
            "total_segments": total_segments,
            "total_duration_hours": round(total_duration / 3600, 2),
            "brand_distribution": brand_counts,
            "asset_type_distribution": asset_type_counts,
        }

        output_file = output_dir / "export_summary.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        return output_file


class NasToUdmPipeline:
    """NAS → UDM 변환 파이프라인 (편의 클래스)"""

    def __init__(
        self,
        nas_root: str,
        output_dir: str = "./output",
        include_tech_spec: bool = False,
        export_format: Literal["json", "jsonl"] = "json",
    ):
        """
        Args:
            nas_root: NAS 루트 경로
            output_dir: 출력 디렉토리
            include_tech_spec: FFprobe로 기술 메타데이터 추출 여부
            export_format: 출력 형식
        """
        from .nas_scanner import NasScanner
        from .udm_transformer import UdmTransformer

        self.scanner = NasScanner(nas_root)
        self.transformer = UdmTransformer(include_tech_spec=include_tech_spec)
        self.exporter = JsonExporter(
            ExportConfig(
                output_dir=output_dir,
                format=export_format,
            )
        )

    def run(
        self,
        video_only: bool = True,
        max_files: int | None = None,
    ) -> dict:
        """
        전체 파이프라인 실행

        Returns:
            실행 결과 요약
        """
        # 1. 스캔
        files, scan_result = self.scanner.scan_with_stats(
            video_only=video_only,
            max_files=max_files,
        )

        # 2. 변환
        assets, transform_result = self.transformer.transform_batch(files)

        # 3. 내보내기
        export_result = self.exporter.export(
            assets,
            metadata={
                "scan": {
                    "total_files": scan_result.total_files,
                    "video_files": scan_result.video_files,
                    "folders_scanned": scan_result.folders_scanned,
                },
            },
        )

        # 4. 스키마 & 요약 내보내기
        schema_file = self.exporter.export_schema()
        summary_file = self.exporter.export_summary(assets)

        return {
            "scan": {
                "total_files": scan_result.total_files,
                "video_files": scan_result.video_files,
                "total_size_gb": round(scan_result.total_size_gb, 2),
                "duration_sec": round(scan_result.scan_duration_sec, 2),
            },
            "transform": {
                "success": transform_result.success,
                "failed": transform_result.failed,
                "total": transform_result.total,
            },
            "export": {
                "success": export_result.success,
                "files": export_result.output_files + [str(schema_file), str(summary_file)],
                "size_bytes": export_result.file_size_bytes,
                "duration_sec": round(export_result.export_duration_sec, 2),
            },
        }
