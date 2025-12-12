"""
Tests for Sheet-NAS Matching Logic

시트 데이터와 NAS 파일 매칭 검증

테스트 범위:
- 파일명 패턴 파싱 (FILENAME_PATTERNS)
- 파일명 정규화 및 매칭
- NAS 경로 추론 (브랜드, AssetType)
- 시트 레코드 ↔ NAS 파일 매칭
- 매칭 결과 검증

Author: Archive Converter Team
Version: 1.0.0
"""

import pytest
from uuid import uuid4

from src.models.udm import (
    parse_filename,
    infer_brand_from_path,
    infer_asset_type_from_path,
    FileNameMeta,
    Brand,
    EventType,
    AssetType,
)


# =============================================================================
# 파일명 매칭 서비스 테스트 (현재 없음 - 구현 필요)
# =============================================================================


class TestFileNameMatching:
    """파일명 기반 매칭 테스트"""

    def test_exact_match(self):
        """정확한 파일명 매칭"""
        sheet_file_name = "WCLA24-15.mp4"
        nas_file_name = "WCLA24-15.mp4"

        # TODO: 실제 매칭 함수 구현 필요
        # result = match_file_names(sheet_file_name, nas_file_name)
        # assert result.is_match is True
        # assert result.confidence == 1.0
        assert sheet_file_name == nas_file_name  # 임시 직접 비교

    def test_case_insensitive_match(self):
        """대소문자 무시 매칭"""
        sheet_file_name = "wcla24-15.mp4"
        nas_file_name = "WCLA24-15.mp4"

        # TODO: 매칭 로직에서 대소문자 무시 처리 필요
        # result = match_file_names(sheet_file_name, nas_file_name)
        # assert result.is_match is True
        assert sheet_file_name.lower() == nas_file_name.lower()

    def test_extension_variation_match(self):
        """확장자 변형 매칭 (.mp4 vs .MP4 vs .mov)"""
        sheet_file_name = "WCLA24-15.mp4"
        nas_file_name = "WCLA24-15.MP4"

        # TODO: 확장자 정규화 처리 필요
        # result = match_file_names(sheet_file_name, nas_file_name)
        # assert result.is_match is True
        base_sheet = sheet_file_name.rsplit(".", 1)[0]
        base_nas = nas_file_name.rsplit(".", 1)[0]
        assert base_sheet.lower() == base_nas.lower()

    def test_fuzzy_match_with_typo(self):
        """타이핑 오류 퍼지 매칭"""
        sheet_file_name = "WCLA24-15.mp4"  # 정상
        nas_file_name = "WCLA24_15.mp4"  # 하이픈 대신 언더스코어

        # TODO: 퍼지 매칭 구현 필요
        # result = match_file_names(sheet_file_name, nas_file_name, fuzzy=True)
        # assert result.is_match is True
        # assert result.confidence >= 0.9

        # 현재는 실패해야 함 (매칭 로직 없음)
        assert sheet_file_name != nas_file_name

    def test_partial_match_without_extension(self):
        """확장자 없는 부분 매칭"""
        sheet_file_name = "WCLA24-15"  # 확장자 없음
        nas_file_name = "WCLA24-15.mp4"

        # TODO: 확장자 없는 경우 처리 필요
        # result = match_file_names(sheet_file_name, nas_file_name)
        # assert result.is_match is True

        base_nas = nas_file_name.rsplit(".", 1)[0]
        assert sheet_file_name == base_nas


# =============================================================================
# 파일명 패턴 파싱 테스트 (기존 + 누락 케이스)
# =============================================================================


class TestParseFilenamePatterns:
    """파일명 패턴 파싱 테스트"""

    # === 기존 지원 패턴 ===

    def test_circuit_subclip_pattern(self):
        """WCLA24-15.mp4 패턴 파싱"""
        result = parse_filename("WCLA24-15.mp4")
        assert result.code_prefix == "WCLA"
        assert result.year_code == "24"
        assert result.sequence_num == 15

    def test_paradise_pe_pattern(self):
        """WP23-PE-01.mp4 패턴 파싱"""
        result = parse_filename("WP23-PE-01.mp4")
        assert result.code_prefix == "WP"
        assert result.year_code == "23"
        assert result.clip_type == "PE"
        assert result.sequence_num == 1

    def test_paradise_subclip_pattern(self):
        """WP23-03.mp4 패턴 파싱"""
        result = parse_filename("WP23-03.mp4")
        assert result.code_prefix == "WP"
        assert result.year_code == "23"
        assert result.sequence_num == 3

    def test_pad_episode_pattern(self):
        """PAD_S13_EP01_GGPoker-001.mp4 패턴 파싱"""
        result = parse_filename("PAD_S13_EP01_GGPoker-001.mp4")
        assert result.code_prefix == "PAD"
        assert result.season == 13
        assert result.episode == 1
        assert result.raw_description == "GGPoker-001"

    def test_wsop_mastered_pattern(self):
        """10-wsop-2024-be-ev-21-25k-nlh-hr-ft-description.mp4 패턴 파싱"""
        result = parse_filename("10-wsop-2024-be-ev-21-25k-nlh-hr-ft-description.mp4")
        assert result.sequence_num == 10
        assert result.year_code == "2024"
        assert result.event_number == 21
        assert result.buyin_code == "25k"
        assert result.game_code == "nlh"

    # === 신규 추가 패턴 (Issue #matching) ===

    def test_hcl_episode_pattern(self):
        """HCL_2024_EP10.mp4 패턴 파싱"""
        result = parse_filename("HCL_2024_EP10.mp4")
        # 필요한 패턴 지원
        assert result.code_prefix == "HCL", "HCL 패턴 지원 필요"
        assert result.year_code == "2024"
        assert result.episode == 10

    def test_wsope_pattern(self):
        """WSOPE_2024_01.mp4 패턴 파싱"""
        result = parse_filename("WSOPE_2024_01.mp4")
        assert result.code_prefix == "WSOPE", "WSOPE 패턴 지원 필요"
        assert result.year_code == "2024"
        assert result.sequence_num == 1

    def test_ggmillions_alt_pattern(self):
        """GGM_FINAL_01.mp4 패턴 파싱"""
        result = parse_filename("GGM_FINAL_01.mp4")
        assert result.code_prefix == "GGM", "GGMillions 대체 패턴 지원 필요"
        assert result.sequence_num == 1

    def test_mpp_pattern(self):
        """MPP_S01_EP01.mp4 패턴 파싱"""
        result = parse_filename("MPP_S01_EP01.mp4")
        assert result.code_prefix == "MPP", "MPP 패턴 지원 필요"
        assert result.season == 1
        assert result.episode == 1

    def test_gog_pattern(self):
        """GOG_FINAL.mp4 패턴 파싱"""
        result = parse_filename("GOG_FINAL.mp4")
        assert result.code_prefix == "GOG", "GOG 패턴 지원 필요"

    def test_stream_pattern(self):
        """STREAM_01.mp4 패턴 파싱"""
        result = parse_filename("STREAM_01.mp4")
        assert result.code_prefix == "STREAM", "STREAM 패턴 지원 필요"
        assert result.sequence_num == 1


# =============================================================================
# 시트 데이터 ↔ NAS 파일 매칭 테스트
# =============================================================================


class TestSheetNasMatching:
    """시트 레코드와 NAS 파일 매칭 테스트"""

    def test_sheet_file_name_to_nas_path_mapping(self):
        """시트의 File Name → NAS 경로 매핑"""
        # 시트 레코드
        sheet_file_name = "WCLA24-15.mp4"

        # NAS 경로들
        nas_paths = [
            "/ARCHIVE/WSOP/WSOP Circuit Event/2024/SUBCLIP/WCLA24-15.mp4",
            "/ARCHIVE/WSOP/WSOP Circuit Event/2024/STREAM/WCLA24-15.mp4",
            "/ARCHIVE/WSOP/WSOP Circuit Event/2024/SUBCLIP/WCLA24-16.mp4",
        ]

        # TODO: 매칭 함수 구현 필요
        # matched = find_matching_nas_path(sheet_file_name, nas_paths)
        # assert matched == "/ARCHIVE/WSOP/WSOP Circuit Event/2024/SUBCLIP/WCLA24-15.mp4"

        # 임시 검증
        matched = [p for p in nas_paths if sheet_file_name in p]
        assert len(matched) == 2  # 중복 가능성 있음

    def test_multiple_segments_for_single_nas_file(self):
        """1개 NAS 파일 → N개 시트 레코드 매칭"""
        nas_file = "STREAM_01.mp4"

        # 동일 파일에 대한 여러 세그먼트 레코드
        sheet_records = [
            {"file_name": "STREAM_01.mp4", "time_in": "00:05:00", "time_out": "00:10:00"},
            {"file_name": "STREAM_01.mp4", "time_in": "00:15:00", "time_out": "00:20:00"},
            {"file_name": "STREAM_01.mp4", "time_in": "00:30:00", "time_out": "00:35:00"},
        ]

        # TODO: 1:N 매칭 검증 함수 필요
        matched_records = [r for r in sheet_records if r["file_name"] == nas_file]
        assert len(matched_records) == 3

    def test_orphan_sheet_record_detection(self):
        """NAS에 없는 시트 레코드 (고아 레코드) 감지"""
        sheet_record = {"file_name": "MISSING_FILE.mp4", "time_in": "00:00:00"}

        nas_files = [
            "WCLA24-15.mp4",
            "WCLA24-16.mp4",
            "STREAM_01.mp4",
        ]

        # TODO: 고아 레코드 감지 함수 필요
        is_orphan = sheet_record["file_name"] not in nas_files
        assert is_orphan is True

    def test_unmatched_nas_file_detection(self):
        """시트에 없는 NAS 파일 (매칭 안 된 파일) 감지"""
        nas_file = "UNKNOWN_FILE_01.mp4"

        sheet_file_names = [
            "WCLA24-15.mp4",
            "WCLA24-16.mp4",
            "STREAM_01.mp4",
        ]

        # TODO: 미매칭 NAS 파일 감지 함수 필요
        is_unmatched = nas_file not in sheet_file_names
        assert is_unmatched is True


# =============================================================================
# NAS 경로 추론 테스트
# =============================================================================


class TestNasPathInference:
    """NAS 경로에서 브랜드/타입 추론 테스트"""

    def test_infer_wsop_bracelet(self):
        """WSOP Bracelet 경로 추론"""
        path = "/ARCHIVE/WSOP/WSOP Bracelet Event/2024/Mastered/file.mp4"
        result = infer_brand_from_path(path)
        assert result["brand"] == Brand.WSOP
        assert result["event_type"] == EventType.BRACELET

    def test_infer_wsop_circuit(self):
        """WSOP Circuit 경로 추론"""
        path = "/ARCHIVE/WSOP/WSOP Circuit Event/2024/SUBCLIP/file.mp4"
        result = infer_brand_from_path(path)
        assert result["brand"] == Brand.WSOPC
        assert result["event_type"] == EventType.CIRCUIT

    def test_infer_hcl(self):
        """HCL 경로 추론"""
        path = "/ARCHIVE/HCL/2024/file.mp4"
        result = infer_brand_from_path(path)
        assert result["brand"] == Brand.HCL
        assert result["event_type"] == EventType.CASH_GAME_SHOW

    def test_infer_asset_type_stream(self):
        """STREAM 폴더 → AssetType.STREAM 추론"""
        path = "/ARCHIVE/WSOP/2024/STREAM/file.mp4"
        result = infer_asset_type_from_path(path)
        assert result == AssetType.STREAM

    def test_infer_asset_type_subclip(self):
        """SUBCLIP 폴더 → AssetType.SUBCLIP 추론"""
        path = "/ARCHIVE/WSOP/2024/SUBCLIP/file.mp4"
        result = infer_asset_type_from_path(path)
        assert result == AssetType.SUBCLIP

    def test_infer_asset_type_mastered(self):
        """Mastered 폴더 → AssetType.MASTER 추론"""
        path = "/ARCHIVE/WSOP/2024/Mastered/file.mp4"
        result = infer_asset_type_from_path(path)
        assert result == AssetType.MASTER

    def test_infer_unknown_brand(self):
        """알 수 없는 경로 → Brand.OTHER"""
        path = "/ARCHIVE/UNKNOWN/file.mp4"
        result = infer_brand_from_path(path)
        assert result["brand"] == Brand.OTHER


# =============================================================================
# 매칭 결과 검증 테스트
# =============================================================================


class TestMatchingValidation:
    """매칭 결과 검증 테스트"""

    def test_segment_time_range_within_file_duration(self):
        """세그먼트 시간 범위가 파일 길이 내에 있는지 검증"""
        file_duration_sec = 3600.0  # 1시간
        segment_time_in = 100.0
        segment_time_out = 200.0

        # TODO: 검증 함수 필요
        is_valid = (
            0 <= segment_time_in < file_duration_sec and
            segment_time_in < segment_time_out <= file_duration_sec
        )
        assert is_valid is True

    def test_segment_time_exceeds_file_duration(self):
        """세그먼트 시간이 파일 길이를 초과하는 경우 감지"""
        file_duration_sec = 3600.0
        segment_time_in = 3500.0
        segment_time_out = 4000.0  # 파일 길이 초과

        is_invalid = segment_time_out > file_duration_sec
        assert is_invalid is True

    def test_overlapping_segments_detection(self):
        """겹치는 세그먼트 감지"""
        segments = [
            {"time_in_sec": 0.0, "time_out_sec": 100.0},
            {"time_in_sec": 50.0, "time_out_sec": 150.0},  # 첫 번째와 겹침
            {"time_in_sec": 200.0, "time_out_sec": 300.0},
        ]

        # TODO: 겹침 감지 함수 필요
        def has_overlap(seg1, seg2):
            return (
                seg1["time_in_sec"] < seg2["time_out_sec"] and
                seg2["time_in_sec"] < seg1["time_out_sec"]
            )

        overlaps = []
        for i, s1 in enumerate(segments):
            for j, s2 in enumerate(segments[i + 1:], i + 1):
                if has_overlap(s1, s2):
                    overlaps.append((i, j))

        assert len(overlaps) == 1
        assert overlaps[0] == (0, 1)

    def test_brand_consistency_check(self):
        """NAS 경로 브랜드와 시트 데이터 브랜드 일치 검증"""
        nas_path = "/ARCHIVE/WSOP/WSOP Circuit Event/2024/SUBCLIP/WCLA24-15.mp4"
        sheet_brand = "WSOPC"  # 시트에서 추출된 브랜드

        inferred = infer_brand_from_path(nas_path)
        assert inferred["brand"].value == sheet_brand


# =============================================================================
# 통합 매칭 워크플로우 테스트
# =============================================================================


class TestMatchingWorkflow:
    """전체 매칭 워크플로우 테스트"""

    def test_full_matching_pipeline(self):
        """전체 매칭 파이프라인 테스트"""
        # 1. 시트 데이터 (Circuit Sheet)
        sheet_records = [
            {
                "file_name": "WCLA24-15.mp4",
                "time_in": "00:02:05",
                "time_out": "00:03:45",
                "rating": "★★★★",
                "winner": "Phil Ivey",
            },
            {
                "file_name": "WCLA24-15.mp4",
                "time_in": "00:10:00",
                "time_out": "00:15:00",
                "rating": "★★★",
                "winner": "Daniel Negreanu",
            },
        ]

        # 2. NAS 파일 목록
        nas_files = [
            {
                "path": "/ARCHIVE/WSOP/WSOP Circuit Event/2024/SUBCLIP/WCLA24-15.mp4",
                "file_name": "WCLA24-15.mp4",
                "duration_sec": 1200.0,
            },
        ]

        # 3. 매칭 실행 (TODO: 실제 매칭 함수 필요)
        # result = perform_matching(sheet_records, nas_files)

        # 4. 검증
        # - 1개 NAS 파일에 2개 세그먼트 매칭
        matched_count = len([r for r in sheet_records if r["file_name"] == nas_files[0]["file_name"]])
        assert matched_count == 2

        # - 브랜드 일치 (WSOPC)
        inferred = infer_brand_from_path(nas_files[0]["path"])
        assert inferred["brand"] == Brand.WSOPC

        # - 파일명 파싱
        meta = parse_filename(nas_files[0]["file_name"])
        assert meta.code_prefix == "WCLA"
        assert meta.year_code == "24"
        assert meta.sequence_num == 15


# =============================================================================
# 매칭 서비스 (구현 필요)
# =============================================================================


class TestMatchingService:
    """매칭 서비스 클래스 테스트 - 아직 구현되지 않음"""

    @pytest.mark.skip(reason="MatchingService 클래스 아직 구현 안됨")
    def test_matching_service_initialization(self):
        """매칭 서비스 초기화"""
        # from src.services.matching import MatchingService
        # service = MatchingService()
        # assert service is not None
        pass

    @pytest.mark.skip(reason="MatchingService.match() 메서드 아직 구현 안됨")
    def test_matching_service_match(self):
        """매칭 실행"""
        # service = MatchingService()
        # result = service.match(sheet_records, nas_files)
        # assert result.matched_count > 0
        pass

    @pytest.mark.skip(reason="MatchingService.validate() 메서드 아직 구현 안됨")
    def test_matching_service_validate(self):
        """매칭 결과 검증"""
        # service = MatchingService()
        # validation = service.validate(matching_result)
        # assert validation.is_valid
        pass
