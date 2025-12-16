# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Archive Converter는 다양한 MAM(Media Asset Management) 솔루션과 Google Sheets 데이터를 **UDM(Universal Data Model)** 스키마로 변환하는 데이터 파이프라인입니다. 포커 비디오 아카이빙 시스템으로, 핵심 질문은 "이 영상의 **어디**에 **뭐**가 있는가?"입니다.

## Commands

### Backend (Dashboard)

```bash
cd D:\AI\claude01\Archive_Converter\dashboard\backend
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

### Frontend (Dashboard)

**기술 스택**: React 18, Vite 5, TypeScript, TanStack Query, Zustand, Tailwind CSS

```bash
cd D:\AI\claude01\Archive_Converter\dashboard\frontend
npm install
npm run dev          # 개발 서버 (localhost:5173)
npm run build        # 프로덕션 빌드 (tsc && vite build)
```

### Docker (전체 스택)

```bash
cd D:\AI\claude01\Archive_Converter\dashboard
docker-compose up --build
```
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Tests

```bash
cd D:\AI\claude01\Archive_Converter

# UDM 모델 테스트
pytest tests/test_udm.py -v

# 커버리지 리포트
pytest tests/test_udm.py --cov=src.models.udm --cov-report=term-missing

# 특정 테스트 클래스/함수
pytest tests/test_udm.py::TestEnums -v
pytest tests/test_udm.py::TestEnums::test_brand_enum_values -v

# Dashboard backend 테스트
cd D:\AI\claude01\Archive_Converter\dashboard\backend
pytest -v
```

### Lint

```bash
cd D:\AI\claude01\Archive_Converter
ruff check src/ --fix
ruff format src/
```

### Scripts (PokerGO)

```bash
cd D:\AI\claude01\Archive_Converter

# PokerGO 스크래핑 (6개 스크립트)
python scripts/pokergo_scraper.py          # 기본 스크래퍼
python scripts/pokergo_api_scraper.py      # API 기반 스크래퍼
python scripts/pokergo_full_scraper.py     # 전체 데이터 스크래핑
python scripts/pokergo_detail_scraper.py   # 상세 정보 스크래핑
python scripts/merge_pokergo_batches.py    # 배치 병합

# UDM 변환
python scripts/pokergo_to_udm.py           # PokerGO → UDM 변환
```

**출력 위치**: `data/pokergo/`

## Architecture

### 2-Level UDM Schema

```
Level 1: Asset (물리적 파일)
  └── Level 2: Segment (논리적 구간 - 포커 핸드)
```

**Asset** - 비디오 파일 메타데이터 (file_name, event_context, tech_spec, source_origin)
**Segment** - 포커 핸드 구간 정보 (time_in_sec, time_out_sec, players, tags, situation_flags)

### 5-Block Pipeline Architecture

```
ORCHESTRATOR (PRD-0001)
    │
    ├── INGEST (PRD-0002) → 소스 데이터 수집 (NAS, Sheets, PokerGO API)
    ├── TRANSFORM (PRD-0003) → UDM 변환
    ├── VALIDATE (PRD-0004) → 유효성 검증
    ├── EXPORT (PRD-0005) → JSON/CSV 출력
    └── PROFILE MANAGER (PRD-0006) → YAML 프로파일 관리
```

### Dashboard Architecture

```
┌─────────────────────┐     ┌─────────────────────┐
│     Frontend        │     │     Backend         │
│ React + Vite + TS   │────▶│     FastAPI         │
│  localhost:5173     │     │   localhost:8000    │
└─────────────────────┘     └─────────────────────┘
        │                           │
        ▼                           ▼
┌─────────────────────┐     ┌─────────────────────┐
│     Pages           │     │     Routers         │
│ - MatchingMatrix    │     │ - /api/matching     │
│ - UdmViewer         │     │ - /api/nas          │
│ - PatternAnalysis   │     │ - /api/udm-viewer   │
└─────────────────────┘     │ - /api/pattern      │
                            └─────────────────────┘
```

데이터 관계: `NAS File (1) → Sheet Records (N) → UDM Segments (N)`

## Key Files

| Path | Description |
|------|-------------|
| `src/models/udm.py` | UDM Pydantic 스키마 (8 Enums, 10 Models, parse_filename, FILENAME_PATTERNS) |
| `src/api/main.py` | Core API 진입점 |
| `src/extractors/nas_scanner.py` | NAS 파일 시스템 스캔 |
| `src/extractors/udm_transformer.py` | UDM 변환 로직 |
| `dashboard/backend/app/main.py` | Dashboard API 진입점 |
| `dashboard/backend/app/routers/pattern.py` | 파일명 패턴 매칭 API |
| `dashboard/frontend/src/pages/` | React 페이지 컴포넌트 |
| `scripts/pokergo_*.py` | PokerGO 스크래퍼 및 UDM 변환 |
| `tests/conftest.py` | pytest 공통 픽스처 |
| `profiles/*.yaml` | 소스별 변환 프로파일 |

## API Endpoints

### Core API (`src/api/`)

- `/api/v1/assets` - Asset CRUD
- `/api/v1/segments` - Segment CRUD
- `/api/v1/search` - 복합 검색
- `/api/v1/export` - JSON/CSV 내보내기
- `/api/v1/stats` - 통계

### Dashboard API (`dashboard/backend/`)

| Router | Endpoints |
|--------|-----------|
| `/api/matching` | `GET /matrix`, `GET /stats`, `GET /file/{name}/segments` |
| `/api/nas` | `GET /folders`, `GET /files` |
| `/api/udm-viewer` | `GET /files`, `GET /files/{id}` |
| `/api/pattern` | `GET /stats`, `GET /list`, `GET /unmatched`, `POST /test` |

## Domain Knowledge

### Enums (UDM)

- **Brand**: WSOP, WSOPC, WSOPE, WSOPP, HCL, PAD, GGMillions, MPP, GOG, WPT, EPT, OTHER
- **EventType**: BRACELET, CIRCUIT, CASH_GAME_SHOW, SUPER_MAIN, ARCHIVE, SIDE_EVENT
- **AssetType**: STREAM, SUBCLIP, HAND_CLIP, MASTER, CLEAN, NO_COMMENTARY, RAW, GENERIC, MOV, MXF
- **GameVariant**: NLH, PLO, STUD, RAZZ, HORSE, MIXED, OMAHA_HI_LO, TD_27, OTHER

### File Naming Patterns (FILENAME_PATTERNS in udm.py)

| Pattern Category | Example |
|------------------|---------|
| WSOP Archive | `wsop-2018-ev-17-*.mp4`, `10-wsop-2024-be-ev-21-*` |
| WSOP Modern | `wsop_mastered_me_*`, `wsop_main_event_*` |
| Circuit/Paradise | `WCLA24-15.mp4`, `WP23-PE-01.mp4` |
| PAD/HCL | `PAD_S13_EP01_*.mp4`, `HCL_S3_EP45_*.mp4` |
| Other Brands | `GGMillions_*.mp4`, `GOG_S1_EP*.mp4` |

### Pattern Matching Flow

```
parse_filename(file_name) → FileNameMeta
  → pattern_matched: 매칭된 패턴 이름
  → code_prefix, year_code, sequence_num, clip_type 등 추출
```

## Agents

### UDM Engineer (전담 에이전트)

UDM 관련 모든 작업은 `udm-engineer` 에이전트를 사용합니다.

```
"Use the udm-engineer agent to [task]"
```

**에이전트 파일**: `.claude/agents/udm-engineer.md`

**사용 예시**:
- "NAS 파일을 UDM으로 변환해줘"
- "Google Sheets 데이터를 Segment로 매핑해줘"
- "UDM 검증 규칙 BR-001 확인해줘"
- "파일명 파싱 패턴 추가해줘"
- "PokerGO 데이터를 UDM으로 변환해줘"

## Data Sources

### NAS Storage (Primary)
- **경로**: `//10.10.100.122/docker/GGPNAs/ARCHIVE/` (마운트: `Z:`)
- **파일 수**: 1,753개 (WSOP)
- **브랜드**: WSOP(1,286), PAD(44), GOG(27), GGMillions(13), MPP(11)

### NAS File Filter Rules

NAS 파일 처리 및 PokerGO 매칭 시 다음 필터 규칙을 적용:

**크기/시간 필터:**
- [x] 1GB 초과 파일 제외
- [x] 1시간 초과 재생시간 제외

**제외 키워드** (폴더 경로 및 파일명):
- [x] clip
- [x] highlight
- [x] paradise
- [x] circuit

**PokerGO 매칭 규칙:**
- [x] 위 필터 조건에 해당하는 NAS 파일은 PokerGO 리스트 매칭에서 제외

```bash
# 필터링 스크립트 실행
python scripts/filter_nas_files.py

# 결과 파일
data/nas_filtered_files.json
```

**필터링 결과** (2025-12-16 기준):
- 전체: 1,753개 → 필터 후: 502개
- 키워드 제외: 484개, 크기 제외: 767개

### Google Sheets (Metadata)
| Sheet | ID |
|-------|-----|
| Archive Metadata | `1_RN_W_ZQclSZA0Iez6XniCXVtjkkd5HNZwiT6l-z6d4` |
| Iconik Metadata | `1pUMPKe-OsKc-Xd8lH1cP9ctJO4hj3keXY5RwNFp2Mtk` |

### PokerGO API (External)
- 스크래핑 데이터: `data/pokergo/`
- 변환된 UDM: `data/pokergo/pokergo_udm_*.json`

## Related Documents

- `docs/PROJECT_STATUS.md` - 프로젝트 현황
- `docs/API_ARCHITECTURE.md` - API 아키텍처 다이어그램
- `prds/PRD-0008-UDM-FINAL-SCHEMA.md` - UDM v3.1 스키마 명세
- `prds/PRD-0010-DASHBOARD.md` - Dashboard PRD
- `profiles/README.md` - 프로파일 가이드
- `.claude/agents/udm-engineer.md` - UDM 전담 에이전트
