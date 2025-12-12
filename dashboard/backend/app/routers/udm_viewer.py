"""
UDM JSON Viewer API Router

NAS에서 추출된 UDM JSON 데이터를 대시보드에서 조회하기 위한 API
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/udm", tags=["UDM Viewer"])


# =============================================================================
# Schemas
# =============================================================================


class UdmAssetSummary(BaseModel):
    """Asset 요약 정보"""
    asset_uuid: str
    file_name: str
    file_path_nas: Optional[str] = None
    asset_type: str
    brand: str
    year: int
    season: Optional[int] = None
    episode: Optional[int] = None
    source_origin: str
    segment_count: int = 0


class UdmMetadata(BaseModel):
    """UDM 문서 메타데이터"""
    version: str
    generated_at: str
    source: str
    total_assets: int
    total_segments: int


class UdmDocumentResponse(BaseModel):
    """UDM 문서 응답"""
    metadata: UdmMetadata
    assets: list[UdmAssetSummary]


class UdmStatsResponse(BaseModel):
    """UDM 통계 응답"""
    total_assets: int
    total_segments: int
    brand_distribution: dict[str, int]
    asset_type_distribution: dict[str, int]
    year_distribution: dict[str, int]


class UdmAssetDetail(BaseModel):
    """Asset 상세 정보"""
    asset_uuid: str
    file_name: str
    file_path_rel: Optional[str] = None
    file_path_nas: Optional[str] = None
    asset_type: str
    event_context: dict
    tech_spec: Optional[dict] = None
    file_name_meta: Optional[dict] = None
    source_origin: str
    segments: list[dict] = []
    created_at: Optional[str] = None


# =============================================================================
# In-Memory Storage (Demo)
# =============================================================================


class UdmDataStore:
    """UDM 데이터 저장소 (인메모리)"""

    def __init__(self):
        self._data: dict | None = None
        self._loaded_at: datetime | None = None
        self._file_path: str | None = None

    def load_from_file(self, file_path: str) -> bool:
        """JSON 파일에서 로드"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
            self._loaded_at = datetime.now()
            self._file_path = file_path
            return True
        except Exception as e:
            print(f"Error loading UDM file: {e}")
            return False

    def load_from_dict(self, data: dict) -> bool:
        """딕셔너리에서 로드"""
        self._data = data
        self._loaded_at = datetime.now()
        self._file_path = None
        return True

    @property
    def is_loaded(self) -> bool:
        return self._data is not None

    @property
    def metadata(self) -> dict | None:
        if not self._data:
            return None
        return self._data.get("_metadata", {})

    @property
    def assets(self) -> list[dict]:
        if not self._data:
            return []
        return self._data.get("assets", [])

    def get_asset(self, asset_uuid: str) -> dict | None:
        for asset in self.assets:
            if asset.get("asset_uuid") == asset_uuid:
                return asset
        return None

    def search_assets(
        self,
        brand: str | None = None,
        asset_type: str | None = None,
        year: int | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """Asset 검색"""
        results = []

        for asset in self.assets:
            # 브랜드 필터
            if brand:
                asset_brand = asset.get("event_context", {}).get("brand", "")
                if asset_brand.upper() != brand.upper():
                    continue

            # Asset Type 필터
            if asset_type:
                if asset.get("asset_type", "").upper() != asset_type.upper():
                    continue

            # 연도 필터
            if year:
                asset_year = asset.get("event_context", {}).get("year")
                if asset_year != year:
                    continue

            # 검색어 필터
            if search:
                file_name = asset.get("file_name", "").lower()
                if search.lower() not in file_name:
                    continue

            results.append(asset)

        # 페이징
        return results[offset:offset + limit]

    def get_stats(self) -> dict:
        """통계 계산"""
        if not self.assets:
            return {
                "total_assets": 0,
                "total_segments": 0,
                "brand_distribution": {},
                "asset_type_distribution": {},
                "year_distribution": {},
            }

        brand_counts: dict[str, int] = {}
        asset_type_counts: dict[str, int] = {}
        year_counts: dict[str, int] = {}
        total_segments = 0

        for asset in self.assets:
            # 브랜드
            brand = asset.get("event_context", {}).get("brand", "unknown")
            brand_counts[brand] = brand_counts.get(brand, 0) + 1

            # Asset Type
            asset_type = asset.get("asset_type", "unknown")
            asset_type_counts[asset_type] = asset_type_counts.get(asset_type, 0) + 1

            # 연도
            year = str(asset.get("event_context", {}).get("year", "unknown"))
            year_counts[year] = year_counts.get(year, 0) + 1

            # Segment
            total_segments += len(asset.get("segments", []))

        return {
            "total_assets": len(self.assets),
            "total_segments": total_segments,
            "brand_distribution": brand_counts,
            "asset_type_distribution": asset_type_counts,
            "year_distribution": year_counts,
        }


# Global data store
_data_store = UdmDataStore()


def get_data_store() -> UdmDataStore:
    """데이터 저장소 인스턴스 반환"""
    return _data_store


# =============================================================================
# Demo Data Generator
# =============================================================================


def generate_demo_data() -> dict:
    """데모 데이터 생성"""
    from uuid import uuid4
    import random

    brands = ["WSOP", "HCL", "PAD", "GGMillions", "MPP", "GOG"]
    asset_types = ["STREAM", "SUBCLIP", "EPISODE", "HAND_CLIP"]

    assets = []
    for i in range(50):
        brand = random.choice(brands)
        asset_type = random.choice(asset_types)
        year = random.choice([2022, 2023, 2024])

        # 파일명 생성
        if brand == "WSOP":
            file_name = f"WCLA{str(year)[2:]}-{i+1:02d}.mp4"
        elif brand == "HCL":
            file_name = f"HCL_{year}_EP{random.randint(1, 20):02d}.mp4"
        elif brand == "PAD":
            file_name = f"PAD_S{random.randint(10, 15)}_EP{random.randint(1, 10):02d}.mp4"
        else:
            file_name = f"{brand}_{year}_{i+1:02d}.mp4"

        asset = {
            "asset_uuid": str(uuid4()),
            "file_name": file_name,
            "file_path_rel": f"{brand}/{asset_type}/{file_name}",
            "file_path_nas": f"\\\\10.10.100.122\\docker\\GGPNAs\\ARCHIVE\\{brand}\\{asset_type}\\{file_name}",
            "asset_type": asset_type,
            "event_context": {
                "year": year,
                "brand": brand,
                "season": random.randint(1, 15) if brand in ["PAD", "HCL"] else None,
                "episode": random.randint(1, 20) if asset_type == "EPISODE" else None,
            },
            "source_origin": f"NAS_{brand}_{year}",
            "segments": [],
        }
        assets.append(asset)

    return {
        "_metadata": {
            "version": "3.1.0",
            "generated_at": datetime.now().isoformat(),
            "source": "demo_generator",
            "total_assets": len(assets),
            "total_segments": 0,
        },
        "assets": assets,
    }


# =============================================================================
# API Endpoints
# =============================================================================


@router.get("/", response_model=UdmDocumentResponse)
async def get_udm_document(
    brand: Optional[str] = Query(None, description="브랜드 필터"),
    asset_type: Optional[str] = Query(None, description="Asset Type 필터"),
    year: Optional[int] = Query(None, description="연도 필터"),
    search: Optional[str] = Query(None, description="파일명 검색"),
    limit: int = Query(100, ge=1, le=500, description="결과 수 제한"),
    offset: int = Query(0, ge=0, description="오프셋"),
):
    """UDM 문서 조회"""
    store = get_data_store()

    # 데이터가 없으면 데모 데이터 로드
    if not store.is_loaded:
        store.load_from_dict(generate_demo_data())

    metadata = store.metadata or {}
    assets = store.search_assets(
        brand=brand,
        asset_type=asset_type,
        year=year,
        search=search,
        limit=limit,
        offset=offset,
    )

    # Asset 요약 변환
    asset_summaries = []
    for asset in assets:
        ctx = asset.get("event_context", {})
        summary = UdmAssetSummary(
            asset_uuid=asset.get("asset_uuid", ""),
            file_name=asset.get("file_name", ""),
            file_path_nas=asset.get("file_path_nas"),
            asset_type=asset.get("asset_type", ""),
            brand=ctx.get("brand", ""),
            year=ctx.get("year", 0),
            season=ctx.get("season"),
            episode=ctx.get("episode"),
            source_origin=asset.get("source_origin", ""),
            segment_count=len(asset.get("segments", [])),
        )
        asset_summaries.append(summary)

    return UdmDocumentResponse(
        metadata=UdmMetadata(
            version=metadata.get("version", ""),
            generated_at=metadata.get("generated_at", ""),
            source=metadata.get("source", ""),
            total_assets=metadata.get("total_assets", 0),
            total_segments=metadata.get("total_segments", 0),
        ),
        assets=asset_summaries,
    )


@router.get("/assets/full")
async def get_full_assets(
    brand: Optional[str] = Query(None, description="브랜드 필터"),
    asset_type: Optional[str] = Query(None, description="Asset Type 필터"),
    year: Optional[int] = Query(None, description="연도 필터"),
    search: Optional[str] = Query(None, description="파일명 검색"),
    limit: int = Query(500, ge=1, le=1000, description="결과 수 제한"),
    offset: int = Query(0, ge=0, description="오프셋"),
):
    """
    전체 Asset 데이터 조회 (매트릭스 뷰용)
    모든 중첩 필드 포함
    """
    store = get_data_store()

    # 데이터가 없으면 데모 데이터 로드
    if not store.is_loaded:
        store.load_from_dict(generate_demo_data())

    assets = store.search_assets(
        brand=brand,
        asset_type=asset_type,
        year=year,
        search=search,
        limit=limit,
        offset=offset,
    )

    # 전체 데이터 반환 (중첩 필드 포함)
    return {
        "total": len(store.assets),
        "filtered": len(assets),
        "assets": assets,
    }


@router.get("/stats", response_model=UdmStatsResponse)
async def get_udm_stats():
    """UDM 통계 조회"""
    store = get_data_store()

    if not store.is_loaded:
        store.load_from_dict(generate_demo_data())

    stats = store.get_stats()

    return UdmStatsResponse(
        total_assets=stats["total_assets"],
        total_segments=stats["total_segments"],
        brand_distribution=stats["brand_distribution"],
        asset_type_distribution=stats["asset_type_distribution"],
        year_distribution=stats["year_distribution"],
    )


@router.get("/assets/{asset_uuid}", response_model=UdmAssetDetail)
async def get_asset_detail(asset_uuid: str):
    """Asset 상세 조회"""
    store = get_data_store()

    if not store.is_loaded:
        store.load_from_dict(generate_demo_data())

    asset = store.get_asset(asset_uuid)

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    return UdmAssetDetail(
        asset_uuid=asset.get("asset_uuid", ""),
        file_name=asset.get("file_name", ""),
        file_path_rel=asset.get("file_path_rel"),
        file_path_nas=asset.get("file_path_nas"),
        asset_type=asset.get("asset_type", ""),
        event_context=asset.get("event_context", {}),
        tech_spec=asset.get("tech_spec"),
        file_name_meta=asset.get("file_name_meta"),
        source_origin=asset.get("source_origin", ""),
        segments=asset.get("segments", []),
        created_at=asset.get("created_at"),
    )


@router.post("/load")
async def load_udm_file(file_path: str):
    """UDM JSON 파일 로드"""
    store = get_data_store()

    if not Path(file_path).exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    if not store.load_from_file(file_path):
        raise HTTPException(status_code=500, detail="Failed to load file")

    return {
        "success": True,
        "message": f"Loaded {len(store.assets)} assets from {file_path}",
        "total_assets": len(store.assets),
    }


@router.post("/demo")
async def load_demo_data():
    """데모 데이터 로드"""
    store = get_data_store()
    store.load_from_dict(generate_demo_data())

    return {
        "success": True,
        "message": f"Loaded {len(store.assets)} demo assets",
        "total_assets": len(store.assets),
    }


@router.post("/from-nas")
async def load_from_nas():
    """
    NAS 파일을 스캔하여 UDM으로 변환
    실제 NAS 데이터 기반 UDM 생성
    """
    from ..config import settings

    # NAS 서비스 가져오기
    if settings.nas_use_real_data:
        from ..services.nas_service import get_nas_service
        nas_service = get_nas_service(settings.nas_mount_path)
    else:
        from ..services.mock_data import MockDataService
        nas_service = MockDataService()

    # NAS 스캔 실행
    try:
        if hasattr(nas_service, 'refresh_scan'):
            nas_service.refresh_scan(force=True)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"NAS scan failed: {e}")

    # NAS 파일 목록 가져오기
    matching_items = nas_service.get_matching_items()

    # UDM 변환
    assets = []
    for item in matching_items:
        asset = _parse_nas_file_to_udm(item)
        assets.append(asset)

    # 데이터 저장
    store = get_data_store()
    udm_data = {
        "_metadata": {
            "version": "3.1.0",
            "generated_at": datetime.now().isoformat(),
            "source": "nas_scan",
            "total_assets": len(assets),
            "total_segments": sum(len(a.get("segments", [])) for a in assets),
        },
        "assets": assets,
    }
    store.load_from_dict(udm_data)

    return {
        "success": True,
        "message": f"Loaded {len(assets)} assets from NAS",
        "total_assets": len(assets),
    }


def _parse_nas_file_to_udm(item) -> dict:
    """NAS 파일 정보를 UDM Asset으로 변환"""
    import re
    import hashlib

    file_name = item.file_name
    nas_info = item.nas

    # UUID 생성 (경로 기반)
    path_hash = hashlib.md5(nas_info.path.encode()).hexdigest()
    asset_uuid = f"{path_hash[:8]}-{path_hash[8:12]}-4{path_hash[13:16]}-8{path_hash[17:20]}-{path_hash[20:32]}"

    # 경로에서 메타데이터 추출
    path_parts = nas_info.path.replace("\\", "/").split("/")
    file_name_upper = file_name.upper()
    path_upper = nas_info.path.upper()

    # 브랜드 추출 (경로 또는 파일명에서)
    brand = nas_info.inferred_brand or _extract_brand(path_upper, file_name_upper)

    # 연도 추출
    year = _extract_year(nas_info.path, file_name)

    # Asset Type 추출 (경로에서)
    asset_type = _extract_asset_type(path_upper)

    # 시즌/에피소드 추출 (파일명에서)
    season, episode = _extract_season_episode(file_name)

    # 이벤트 번호 추출
    event_number = _extract_event_number(file_name)

    # 바이인 추출
    buyin_usd = _extract_buyin(file_name)

    # 게임 종류 추출
    game_variant = _extract_game_variant(file_name_upper)

    # 플래그 추출
    is_final_table = "FINAL" in file_name_upper or "FT" in file_name_upper
    is_high_roller = "HIGH" in file_name_upper and "ROLLER" in file_name_upper
    is_super_high_roller = "SUPER" in file_name_upper and "HIGH" in file_name_upper

    # 장소 추출
    location = _extract_location(path_upper, file_name_upper)

    return {
        "asset_uuid": asset_uuid,
        "file_name": file_name,
        "file_path_rel": "/".join(path_parts[-3:]) if len(path_parts) >= 3 else file_name,
        "file_path_nas": nas_info.path,
        "asset_type": asset_type,
        "event_context": {
            "year": year,
            "brand": brand,
            "event_type": _infer_event_type(brand, file_name_upper),
            "location": location,
            "venue": None,
            "event_number": event_number,
            "buyin_usd": buyin_usd,
            "game_variant": game_variant,
            "is_final_table": is_final_table if is_final_table else None,
            "is_high_roller": is_high_roller if is_high_roller else None,
            "is_super_high_roller": is_super_high_roller if is_super_high_roller else None,
            "season": season,
            "episode": episode,
            "episode_title": None,
        },
        "tech_spec": {
            "fps": None,
            "resolution": None,
            "duration_sec": nas_info.duration_sec,
            "file_size_mb": nas_info.size_mb,
            "codec": None,
        },
        "file_name_meta": _parse_file_name_meta(file_name),
        "source_origin": f"NAS_{brand or 'UNKNOWN'}_{year or 'UNKNOWN'}",
        "created_at": nas_info.modified_at.isoformat() if nas_info.modified_at else None,
        "segments": [],
    }


def _extract_brand(path_upper: str, file_name_upper: str) -> Optional[str]:
    """브랜드 추출"""
    brands = {
        "WSOP": ["WSOP", "WSOPC", "WSOPE", "WSOPP"],
        "HCL": ["HCL", "HUSTLER"],
        "PAD": ["PAD", "POKERAFTERDARK"],
        "GGMillions": ["GGMILLIONS", "GGM"],
        "MPP": ["MPP", "MAJOR"],
        "GOG": ["GOG", "GAMEOFGOLD"],
        "WPT": ["WPT"],
        "EPT": ["EPT"],
    }

    # 파일명에서 먼저 확인
    for brand, keywords in brands.items():
        for kw in keywords:
            if kw in file_name_upper:
                return brand

    # 경로에서 확인
    for brand, keywords in brands.items():
        for kw in keywords:
            if kw in path_upper:
                return brand

    return None


def _extract_year(path: str, file_name: str) -> Optional[int]:
    """연도 추출"""
    import re

    # 4자리 연도 (2020-2029)
    match = re.search(r"20[2-3]\d", path + file_name)
    if match:
        return int(match.group())

    # 2자리 연도 (예: 24 -> 2024)
    match = re.search(r"[_-](\d{2})[_-]", file_name)
    if match:
        year_short = int(match.group(1))
        if 20 <= year_short <= 30:
            return 2000 + year_short

    return None


def _extract_asset_type(path_upper: str) -> str:
    """Asset Type 추출"""
    if "STREAM" in path_upper:
        return "STREAM"
    elif "SUBCLIP" in path_upper or "SUB" in path_upper:
        return "SUBCLIP"
    elif "HAND" in path_upper:
        return "HAND_CLIP"
    elif "MASTER" in path_upper:
        return "MASTER"
    elif "CLEAN" in path_upper:
        return "CLEAN"
    elif "RAW" in path_upper:
        return "RAW"
    elif "MOV" in path_upper:
        return "MOV"
    elif "MXF" in path_upper:
        return "MXF"
    return "GENERIC"


def _extract_season_episode(file_name: str) -> tuple[Optional[int], Optional[int]]:
    """시즌/에피소드 추출"""
    import re

    season = None
    episode = None

    # S15_EP01 형식
    s_match = re.search(r"S(\d+)", file_name, re.IGNORECASE)
    if s_match:
        season = int(s_match.group(1))

    # EP01, E01 형식
    ep_match = re.search(r"E(?:P)?(\d+)", file_name, re.IGNORECASE)
    if ep_match:
        episode = int(ep_match.group(1))

    return season, episode


def _extract_event_number(file_name: str) -> Optional[int]:
    """이벤트 번호 추출"""
    import re

    # EV-21, EVENT-21 형식
    match = re.search(r"(?:EV|EVENT)[_-]?(\d+)", file_name, re.IGNORECASE)
    if match:
        return int(match.group(1))

    return None


def _extract_buyin(file_name: str) -> Optional[int]:
    """바이인 추출"""
    import re

    # 50K, 250K 형식
    match = re.search(r"(\d+)K", file_name, re.IGNORECASE)
    if match:
        return int(match.group(1)) * 1000

    # $10,000 형식
    match = re.search(r"\$?([\d,]+)", file_name)
    if match:
        val = int(match.group(1).replace(",", ""))
        if val >= 1000:  # 바이인으로 보이는 값
            return val

    return None


def _extract_game_variant(file_name_upper: str) -> Optional[str]:
    """게임 종류 추출"""
    if "NLH" in file_name_upper or "NLHE" in file_name_upper:
        return "NLH"
    elif "PLO" in file_name_upper:
        return "PLO"
    elif "STUD" in file_name_upper:
        return "STUD"
    elif "RAZZ" in file_name_upper:
        return "RAZZ"
    elif "HORSE" in file_name_upper:
        return "HORSE"
    elif "MIXED" in file_name_upper:
        return "MIXED"
    return None


def _extract_location(path_upper: str, file_name_upper: str) -> Optional[str]:
    """장소 추출"""
    combined = path_upper + " " + file_name_upper

    if "VEGAS" in combined or "LV" in combined:
        return "Las Vegas"
    elif "BARCELONA" in combined:
        return "Barcelona"
    elif "PARADISE" in combined:
        return "Paradise"
    elif "CYPRUS" in combined:
        return "Cyprus"
    elif "MONTE" in combined and "CARLO" in combined:
        return "Monte Carlo"
    elif "LONDON" in combined:
        return "London"
    elif "LA" in combined or "LOS ANGELES" in combined:
        return "Los Angeles"

    return None


def _infer_event_type(brand: Optional[str], file_name_upper: str) -> Optional[str]:
    """이벤트 타입 추론"""
    if not brand:
        return None

    if brand in ["HCL", "PAD"]:
        return "CASH_GAME_SHOW"
    elif "CIRCUIT" in file_name_upper or "WCLA" in file_name_upper:
        return "CIRCUIT"
    elif "MAIN" in file_name_upper and "EVENT" in file_name_upper:
        return "BRACELET"
    elif brand == "WSOP":
        return "BRACELET"

    return None


def _parse_file_name_meta(file_name: str) -> dict:
    """파일명 메타데이터 파싱"""
    import re

    # 확장자 제거
    name_without_ext = file_name.rsplit(".", 1)[0] if "." in file_name else file_name

    # 코드 접두사 (예: WCLA, HCL)
    code_match = re.match(r"^([A-Z]+)", name_without_ext)
    code_prefix = code_match.group(1) if code_match else None

    # 시퀀스 번호
    seq_match = re.search(r"-(\d+)(?:\.|$)", file_name)
    sequence_num = int(seq_match.group(1)) if seq_match else None

    return {
        "code_prefix": code_prefix,
        "year_code": None,
        "sequence_num": sequence_num,
        "clip_type": None,
        "raw_description": name_without_ext,
    }


@router.get("/brands")
async def get_brands():
    """사용 가능한 브랜드 목록"""
    store = get_data_store()

    if not store.is_loaded:
        store.load_from_dict(generate_demo_data())

    stats = store.get_stats()
    brands = list(stats["brand_distribution"].keys())

    return {"brands": sorted(brands)}


@router.get("/asset-types")
async def get_asset_types():
    """사용 가능한 Asset Type 목록"""
    store = get_data_store()

    if not store.is_loaded:
        store.load_from_dict(generate_demo_data())

    stats = store.get_stats()
    asset_types = list(stats["asset_type_distribution"].keys())

    return {"asset_types": sorted(asset_types)}
