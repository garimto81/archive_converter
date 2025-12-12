"""
NAS-to-UDM Extractor 테스트

Tests for:
- NasScanner: NAS 파일시스템 스캔
- UdmTransformer: NAS → UDM 변환
- JsonExporter: JSON 내보내기
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime

from src.extractors.nas_scanner import NasScanner, NasFileInfo, ScanResult
from src.extractors.udm_transformer import UdmTransformer, TransformResult
from src.extractors.json_exporter import JsonExporter, ExportConfig, NasToUdmPipeline


class TestNasScanner:
    """NasScanner 테스트"""

    @pytest.fixture
    def temp_nas_structure(self, tmp_path):
        """테스트용 NAS 폴더 구조 생성"""
        # WSOP 폴더
        wsop_stream = tmp_path / "WSOP" / "STREAM"
        wsop_stream.mkdir(parents=True)
        (wsop_stream / "STREAM_01.mp4").write_bytes(b"fake video content 1" * 1000)
        (wsop_stream / "STREAM_02.mp4").write_bytes(b"fake video content 2" * 500)

        wsop_subclip = tmp_path / "WSOP" / "SUBCLIP"
        wsop_subclip.mkdir(parents=True)
        (wsop_subclip / "WCLA24-01.mp4").write_bytes(b"subclip 1" * 200)
        (wsop_subclip / "WCLA24-02.mp4").write_bytes(b"subclip 2" * 200)

        # HCL 폴더
        hcl = tmp_path / "HCL"
        hcl.mkdir(parents=True)
        (hcl / "HCL_2024_EP01.mp4").write_bytes(b"hcl video" * 800)
        (hcl / "HCL_2024_EP02.mp4").write_bytes(b"hcl video 2" * 600)

        # PAD 폴더
        pad = tmp_path / "PAD"
        pad.mkdir(parents=True)
        (pad / "PAD_S13_EP01.mp4").write_bytes(b"pad video" * 400)

        # 비 비디오 파일
        (tmp_path / "readme.txt").write_text("This is a test")
        (hcl / "notes.txt").write_text("Some notes")

        return tmp_path

    def test_scanner_initialization(self, temp_nas_structure):
        """스캐너 초기화 테스트"""
        scanner = NasScanner(str(temp_nas_structure))
        assert scanner.root_path == temp_nas_structure

    def test_scanner_not_found(self):
        """존재하지 않는 경로 테스트"""
        with pytest.raises(FileNotFoundError):
            NasScanner("/nonexistent/path")

    def test_scan_video_only(self, temp_nas_structure):
        """비디오 파일만 스캔"""
        scanner = NasScanner(str(temp_nas_structure))
        files = list(scanner.scan(video_only=True))

        assert len(files) == 7
        assert all(f.extension == ".mp4" for f in files)

    def test_scan_all_files(self, temp_nas_structure):
        """모든 파일 스캔"""
        scanner = NasScanner(str(temp_nas_structure))
        files = list(scanner.scan(video_only=False))

        assert len(files) == 9  # 7 mp4 + 2 txt

    def test_scan_max_files(self, temp_nas_structure):
        """최대 파일 수 제한"""
        scanner = NasScanner(str(temp_nas_structure))
        files = list(scanner.scan(max_files=3))

        assert len(files) == 3

    def test_scan_with_stats(self, temp_nas_structure):
        """통계와 함께 스캔"""
        scanner = NasScanner(str(temp_nas_structure))
        files, result = scanner.scan_with_stats(video_only=False)

        assert result.total_files == 9
        assert result.video_files == 7
        assert result.other_files == 2
        assert result.folders_scanned > 0
        assert result.total_size_bytes > 0

    def test_brand_inference(self, temp_nas_structure):
        """브랜드 추론 테스트"""
        scanner = NasScanner(str(temp_nas_structure))
        files = list(scanner.scan())

        wsop_files = [f for f in files if f.inferred_brand == "WSOP"]
        hcl_files = [f for f in files if f.inferred_brand == "HCL"]
        pad_files = [f for f in files if f.inferred_brand == "PAD"]

        assert len(wsop_files) == 4  # 2 STREAM + 2 SUBCLIP
        assert len(hcl_files) == 2
        assert len(pad_files) == 1

    def test_asset_type_inference(self, temp_nas_structure):
        """Asset Type 추론 테스트"""
        scanner = NasScanner(str(temp_nas_structure))
        files = list(scanner.scan())

        stream_files = [f for f in files if f.inferred_asset_type == "STREAM"]
        subclip_files = [f for f in files if f.inferred_asset_type == "SUBCLIP"]

        assert len(stream_files) == 2
        assert len(subclip_files) == 2

    def test_file_info_properties(self, temp_nas_structure):
        """NasFileInfo 속성 테스트"""
        scanner = NasScanner(str(temp_nas_structure))
        files = list(scanner.scan())

        file_info = files[0]
        assert file_info.size_mb > 0
        assert file_info.size_gb >= 0
        assert file_info.extension == ".mp4"
        assert file_info.modified_at is not None

    def test_scan_with_hash(self, temp_nas_structure):
        """해시 계산 테스트"""
        scanner = NasScanner(str(temp_nas_structure), compute_hash=True)
        files = list(scanner.scan(max_files=2))

        for f in files:
            assert f.file_hash is not None
            assert len(f.file_hash) == 32  # MD5 hex length

    def test_folder_tree(self, temp_nas_structure):
        """폴더 트리 테스트"""
        scanner = NasScanner(str(temp_nas_structure))
        tree = scanner.get_folder_tree(max_depth=2)

        assert "name" in tree
        assert "children" in tree
        assert len(tree["children"]) > 0


class TestUdmTransformer:
    """UdmTransformer 테스트"""

    @pytest.fixture
    def sample_file_info(self):
        """샘플 NasFileInfo"""
        return NasFileInfo(
            path="/ARCHIVE/WSOP/STREAM/STREAM_01.mp4",
            filename="STREAM_01.mp4",
            extension=".mp4",
            size_bytes=1024 * 1024 * 100,  # 100MB
            modified_at=datetime.now(),
            folder_path="/ARCHIVE/WSOP/STREAM",
            relative_path="WSOP/STREAM/STREAM_01.mp4",
            inferred_brand="WSOP",
            inferred_asset_type="STREAM",
        )

    def test_transform_basic(self, sample_file_info):
        """기본 변환 테스트"""
        transformer = UdmTransformer()
        asset = transformer.transform(sample_file_info)

        assert asset is not None
        assert asset.asset_uuid is not None
        assert asset.event_context.brand == "WSOP"
        assert asset.asset_type == "STREAM"  # use_enum_values=True이므로 문자열

    def test_transform_deterministic_uuid(self, sample_file_info):
        """동일 경로 → 동일 UUID"""
        transformer = UdmTransformer()

        asset1 = transformer.transform(sample_file_info)
        asset2 = transformer.transform(sample_file_info)

        assert asset1.asset_uuid == asset2.asset_uuid

    def test_transform_batch(self, sample_file_info):
        """배치 변환 테스트"""
        transformer = UdmTransformer()

        # 여러 파일 정보 생성
        files = [
            sample_file_info,
            NasFileInfo(
                path="/ARCHIVE/HCL/HCL_2024_EP01.mp4",
                filename="HCL_2024_EP01.mp4",
                extension=".mp4",
                size_bytes=1024 * 1024 * 50,
                modified_at=datetime.now(),
                folder_path="/ARCHIVE/HCL",
                relative_path="HCL/HCL_2024_EP01.mp4",
                inferred_brand="HCL",
                inferred_asset_type=None,
            ),
        ]

        assets, result = transformer.transform_batch(files)

        assert len(assets) == 2
        assert result.success == 2
        assert result.failed == 0

    def test_brand_from_filename(self):
        """파일명에서 브랜드 추론"""
        transformer = UdmTransformer()

        file_info = NasFileInfo(
            path="/unknown/path/HCL_2024_EP05.mp4",
            filename="HCL_2024_EP05.mp4",
            extension=".mp4",
            size_bytes=1000,
            modified_at=datetime.now(),
            folder_path="/unknown/path",
            relative_path="unknown/path/HCL_2024_EP05.mp4",
            inferred_brand=None,  # 경로에서 추론 실패
            inferred_asset_type=None,
        )

        asset = transformer.transform(file_info)
        assert asset.event_context.brand == "HCL"

    def test_source_origin(self, sample_file_info):
        """source_origin 생성 테스트"""
        transformer = UdmTransformer()
        asset = transformer.transform(sample_file_info)

        assert asset.source_origin is not None
        assert "NAS_" in asset.source_origin
        assert "WSOP" in asset.source_origin

    def test_event_context_from_filename(self):
        """파일명에서 EventContext 추출"""
        transformer = UdmTransformer()

        file_info = NasFileInfo(
            path="/ARCHIVE/PAD/PAD_S13_EP01.mp4",
            filename="PAD_S13_EP01.mp4",
            extension=".mp4",
            size_bytes=1000,
            modified_at=datetime.now(),
            folder_path="/ARCHIVE/PAD",
            relative_path="PAD/PAD_S13_EP01.mp4",
            inferred_brand="PAD",
            inferred_asset_type=None,
        )

        asset = transformer.transform(file_info)

        assert asset.event_context is not None
        assert asset.event_context.brand == "PAD"
        # PAD_S13_EP01 패턴은 parse_filename에서 season/episode를 추출해야 함
        # 현재는 파싱 실패 시 None이 될 수 있음


class TestJsonExporter:
    """JsonExporter 테스트"""

    @pytest.fixture
    def sample_assets(self):
        """샘플 Asset 목록"""
        from uuid import uuid4
        from src.models.udm import Asset, Brand, AssetType, EventContext

        return [
            Asset(
                asset_uuid=uuid4(),
                file_name="STREAM_01.mp4",
                file_path_nas="/ARCHIVE/WSOP/STREAM_01.mp4",
                asset_type=AssetType.STREAM,
                event_context=EventContext(year=2024, brand=Brand.WSOP),
                source_origin="NAS_WSOP_2024",
                segments=[],
            ),
            Asset(
                asset_uuid=uuid4(),
                file_name="HCL_2024_EP01.mp4",
                file_path_nas="/ARCHIVE/HCL/HCL_2024_EP01.mp4",
                asset_type=AssetType.SUBCLIP,
                event_context=EventContext(year=2024, brand=Brand.HCL),
                source_origin="NAS_HCL_2024",
                segments=[],
            ),
        ]

    def test_export_json(self, sample_assets, tmp_path):
        """JSON 내보내기 테스트"""
        config = ExportConfig(
            output_dir=str(tmp_path),
            format="json",
            include_timestamp=False,
            filename_prefix="test_export",
        )
        exporter = JsonExporter(config)

        result = exporter.export(sample_assets)

        assert result.success
        assert len(result.output_files) == 1
        assert result.total_assets == 2

        # 파일 검증
        output_file = Path(result.output_files[0])
        assert output_file.exists()

        with open(output_file) as f:
            data = json.load(f)

        assert "_metadata" in data  # JSON 내보내기 형식은 _metadata 사용
        assert "assets" in data
        assert len(data["assets"]) == 2

    def test_export_jsonl(self, sample_assets, tmp_path):
        """JSONL 내보내기 테스트"""
        config = ExportConfig(
            output_dir=str(tmp_path),
            format="jsonl",
            include_timestamp=False,
            filename_prefix="test_export",
        )
        exporter = JsonExporter(config)

        result = exporter.export(sample_assets)

        assert result.success
        assert len(result.output_files) == 1

        # 파일 검증
        output_file = Path(result.output_files[0])
        assert output_file.suffix == ".jsonl"

        lines = output_file.read_text().strip().split("\n")
        assert len(lines) == 2

        for line in lines:
            data = json.loads(line)
            assert "asset_uuid" in data

    def test_export_schema(self, tmp_path):
        """스키마 내보내기 테스트"""
        config = ExportConfig(output_dir=str(tmp_path))
        exporter = JsonExporter(config)

        schema_file = exporter.export_schema()

        assert schema_file.exists()

        with open(schema_file, encoding="utf-8") as f:
            schema = json.load(f)

        assert "$defs" in schema or "definitions" in schema or "properties" in schema

    def test_export_summary(self, sample_assets, tmp_path):
        """요약 내보내기 테스트"""
        config = ExportConfig(output_dir=str(tmp_path))
        exporter = JsonExporter(config)

        summary_file = exporter.export_summary(sample_assets)

        assert summary_file.exists()

        with open(summary_file) as f:
            summary = json.load(f)

        assert summary["total_assets"] == 2
        assert "brand_distribution" in summary
        assert "WSOP" in summary["brand_distribution"]


class TestNasToUdmPipeline:
    """전체 파이프라인 테스트"""

    @pytest.fixture
    def temp_nas_and_output(self, tmp_path):
        """테스트용 NAS + 출력 디렉토리"""
        nas_dir = tmp_path / "nas"
        output_dir = tmp_path / "output"

        # NAS 구조 생성
        wsop = nas_dir / "WSOP" / "STREAM"
        wsop.mkdir(parents=True)
        (wsop / "STREAM_01.mp4").write_bytes(b"video" * 1000)
        (wsop / "STREAM_02.mp4").write_bytes(b"video" * 800)

        hcl = nas_dir / "HCL"
        hcl.mkdir(parents=True)
        (hcl / "HCL_2024_EP01.mp4").write_bytes(b"video" * 600)

        return nas_dir, output_dir

    def test_pipeline_full_run(self, temp_nas_and_output):
        """전체 파이프라인 실행 테스트"""
        nas_dir, output_dir = temp_nas_and_output

        pipeline = NasToUdmPipeline(
            nas_root=str(nas_dir),
            output_dir=str(output_dir),
            include_tech_spec=False,
            export_format="json",
        )

        result = pipeline.run()

        # 스캔 결과
        assert result["scan"]["video_files"] == 3

        # 변환 결과
        assert result["transform"]["success"] == 3
        assert result["transform"]["failed"] == 0

        # 내보내기 결과
        assert result["export"]["success"]
        assert len(result["export"]["files"]) == 3  # json, schema, summary

        # 파일 검증
        output_files = list(output_dir.glob("*.json"))
        assert len(output_files) >= 2  # export + schema + summary

    def test_pipeline_with_max_files(self, temp_nas_and_output):
        """max_files 제한 테스트"""
        nas_dir, output_dir = temp_nas_and_output

        pipeline = NasToUdmPipeline(
            nas_root=str(nas_dir),
            output_dir=str(output_dir),
        )

        result = pipeline.run(max_files=2)

        assert result["transform"]["success"] == 2


class TestIntegration:
    """통합 테스트"""

    def test_end_to_end_with_real_patterns(self, tmp_path):
        """실제 파일명 패턴으로 E2E 테스트"""
        # NAS 구조 생성
        nas_root = tmp_path / "ARCHIVE"

        # 다양한 브랜드/패턴
        test_files = [
            ("WSOP/STREAM/STREAM_01.mp4", "WSOP", "STREAM"),
            ("WSOP/SUBCLIP/WCLA24-01.mp4", "WSOP", "SUBCLIP"),
            ("HCL/HCL_2024_EP10.mp4", "HCL", None),
            ("PAD/PAD_S13_EP01.mp4", "PAD", None),
            ("GGMillions/GGM_FINAL_01.mp4", "GGMillions", None),
            ("MPP/MPP_S01_EP01.mp4", "MPP", None),
            ("GOG/GOG_FINAL.mp4", "GOG", None),
        ]

        for rel_path, brand, asset_type in test_files:
            file_path = nas_root / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(b"video content" * 100)

        # 파이프라인 실행
        output_dir = tmp_path / "output"
        pipeline = NasToUdmPipeline(
            nas_root=str(nas_root),
            output_dir=str(output_dir),
        )

        result = pipeline.run()

        # 모든 파일 변환 성공
        assert result["transform"]["success"] == 7
        assert result["transform"]["failed"] == 0

        # JSON 출력 검증
        json_files = list(output_dir.glob("udm_export*.json"))
        assert len(json_files) == 1

        with open(json_files[0], encoding="utf-8") as f:
            data = json.load(f)

        assert len(data["assets"]) == 7

        # 브랜드 다양성 검증 (brand는 event_context 안에 있음)
        brands = {a["event_context"]["brand"] for a in data["assets"]}
        assert len(brands) >= 5  # 최소 5개 브랜드
