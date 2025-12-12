# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Archive Converter는 다양한 MAM(Media Asset Management) 솔루션과 Google Sheets 데이터를 **UDM(Universal Data Model)** 스키마로 변환하는 데이터 파이프라인입니다. 포커 비디오 아카이빙 시스템으로, 핵심 질문은 "이 영상의 **어디**에 **뭐**가 있는가?"입니다.

## Commands

### Backend (Dashboard)

```bash
# 개발 서버 실행
cd D:\AI\claude01\Archive_Converter\dashboard\backend
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

### Frontend (Dashboard)

```bash
cd D:\AI\claude01\Archive_Converter\dashboard\frontend
npm install
npm run dev          # 개발 서버
npm run build        # 프로덕션 빌드
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

# 전체 테스트
pytest tests/test_udm.py -v

# 커버리지 리포트
pytest tests/test_udm.py --cov=src.models.udm --cov-report=term-missing

# 특정 테스트 클래스
pytest tests/test_udm.py::TestEnums -v

# 특정 테스트 함수
pytest tests/test_udm.py::TestEnums::test_brand_enum_values -v
```

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
    ├── INGEST (PRD-0002) → 소스 데이터 수집
    ├── TRANSFORM (PRD-0003) → UDM 변환
    ├── VALIDATE (PRD-0004) → 유효성 검증
    ├── EXPORT (PRD-0005) → JSON/CSV 출력
    └── PROFILE MANAGER (PRD-0006) → YAML 프로파일 관리
```

### Dashboard Architecture

```
Frontend (React + Vite + TailwindCSS)  →  Backend (FastAPI)
         localhost:3000                      localhost:8000
```

데이터 관계: `NAS File (1) → Sheet Records (N) → UDM Segments (N)`

## Key Files

| Path | Description |
|------|-------------|
| `src/models/udm.py` | UDM Pydantic 스키마 (8 Enums, 10 Models) |
| `src/api/main.py` | Core API 진입점 (19개 엔드포인트) |
| `dashboard/backend/app/main.py` | Dashboard API 진입점 |
| `dashboard/frontend/src/App.tsx` | Dashboard React 앱 |
| `tests/conftest.py` | pytest 공통 픽스처 (30개) |
| `profiles/*.yaml` | 소스별 변환 프로파일 |

## API Endpoints

### Core API (`src/api/`)

- `/api/v1/assets` - Asset CRUD
- `/api/v1/segments` - Segment CRUD
- `/api/v1/search` - 복합 검색
- `/api/v1/export` - JSON/CSV 내보내기
- `/api/v1/stats` - 통계

### Dashboard API (`dashboard/backend/`)

- `GET /api/matching/matrix` - 매칭 매트릭스
- `GET /api/matching/stats` - 통계
- `GET /api/nas/folders` - NAS 폴더 트리
- `GET /api/nas/files` - NAS 파일 목록

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, FastAPI, Pydantic V2 |
| Frontend | React 18, Vite 5, TailwindCSS 3.4, TypeScript 5.3 |
| State | Zustand, TanStack Query |
| Testing | pytest, httpx |
| Container | Docker, docker-compose |

## Domain Knowledge

### Enums (UDM)

- **Brand**: WSOP, WSOPC, WSOPE, WSOPP, HCL, PAD, GGMillions, MPP, GOG, WPT, EPT
- **EventType**: BRACELET, CIRCUIT, CASH_GAME_SHOW, SUPER_MAIN, ARCHIVE, SIDE_EVENT
- **AssetType**: STREAM, SUBCLIP, HAND_CLIP, MASTER, CLEAN, NO_COMMENTARY, RAW
- **GameVariant**: NLH, PLO, STUD, RAZZ, HORSE, MIXED

### File Naming Patterns

```
WCLA24-15.mp4           → Circuit Subclip
WP23-PE-01.mp4          → Paradise Player Emotion
PAD_S13_EP01_*.mp4      → PAD Episode
10-wsop-2024-be-ev-21-* → WSOP Mastered
```

## Agents

### UDM Engineer (전담 에이전트)

UDM 관련 모든 작업은 `udm-engineer` 에이전트를 사용합니다.

```
"Use the udm-engineer agent to [task]"
```

**에이전트 파일**: `.claude/agents/udm-engineer.md`

**책임 영역**:

| Block | 책임 | 에이전트 담당 |
|-------|------|-------------|
| INGEST | NAS 스캔, Sheets 로드 | O |
| TRANSFORM | UDM 변환 (★핵심) | O |
| VALIDATE | 스키마/BR 검증 | O |
| EXPORT | JSON/CSV 출력 | O |
| PROFILE | 매핑 프로파일 관리 | O |

**사용 예시**:
- "NAS 파일을 UDM으로 변환해줘"
- "Google Sheets 데이터를 Segment로 매핑해줘"
- "UDM 검증 규칙 BR-001 확인해줘"
- "파일명 파싱 패턴 추가해줘"

## Data Sources

### NAS Storage (Primary)
- **경로**: `//10.10.100.122/docker/GGPNAs/ARCHIVE/`
- **파일 수**: 1,381개
- **브랜드**: WSOP(1,286), PAD(44), GOG(27), GGMillions(13), MPP(11)

### Google Sheets (Metadata)
| Sheet | ID | Records |
|-------|-----|---------|
| Archive Metadata | `1_RN_W_ZQclSZA0Iez6XniCXVtjkkd5HNZwiT6l-z6d4` | 38 |
| Iconik Metadata | `1pUMPKe-OsKc-Xd8lH1cP9ctJO4hj3keXY5RwNFp2Mtk` | 200+ |

## Related Documents

- `docs/PROJECT_STATUS.md` - 프로젝트 현황
- `docs/API_ARCHITECTURE.md` - API 아키텍처 다이어그램
- `prds/PRD-0008-UDM-FINAL-SCHEMA.md` - UDM v3.1 스키마 명세
- `profiles/README.md` - 프로파일 가이드
- `.claude/agents/udm-engineer.md` - UDM 전담 에이전트
