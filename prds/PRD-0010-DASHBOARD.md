# PRD-0010: Archive Converter Dashboard

**Version**: 1.2.0
**Status**: Draft
**Created**: 2025-12-11
**Updated**: 2025-12-11
**Parent**: PRD-0001-MASTER-ORCHESTRATOR

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.2.0 | 2025-12-11 | **3원 매트릭스 뷰**: NAS-Archive-Iconik-UDM 컬럼 분리, Orphan 경고 처리 |
| 1.1.0 | 2025-12-11 | **1:N 관계 모델 반영**: API 응답, DB 스키마, Frontend State 전면 수정 |
| 1.0.0 | 2025-12-11 | 초기 버전 |

---

## 1. Executive Summary

### 1.1 목적

NAS 저장소, Google Sheets 메타데이터, UDM 변환 결과를 **한눈에 확인**하고 **검증/수정**할 수 있는 통합 대시보드

### 1.2 핵심 가치

| 문제 | 해결책 |
|------|--------|
| 데이터 파편화 | 3개 소스(NAS, Sheets, UDM) 통합 뷰 |
| 매칭 상태 불명확 | 실시간 매칭 현황 시각화 |
| 검증 어려움 | 인터랙티브 데이터 탐색/수정 |
| 변환 모니터링 부재 | 파이프라인 실행 상태 대시보드 |

### 1.3 데이터 관계 모델 (1:N)

> **핵심**: 데이터 매칭은 1:1이 아닌 **1:N 관계**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      DATA RELATIONSHIP MODEL                             │
│                                                                         │
│   NAS File (1)              Sheet Records (N)           UDM (N)         │
│   ═══════════              ═════════════════          ═══════          │
│                                                                         │
│   ┌─────────────┐          ┌─────────────┐           ┌─────────┐       │
│   │ video.mp4   │◄────────┤│ Segment 1   │──────────▶│ UDM #1  │       │
│   │             │          │ 00:00-02:30 │           │ (Hand1) │       │
│   │  (물리 파일) │          └─────────────┘           └─────────┘       │
│   │             │          ┌─────────────┐           ┌─────────┐       │
│   │             │◄────────┤│ Segment 2   │──────────▶│ UDM #2  │       │
│   │             │          │ 02:30-05:15 │           │ (Hand2) │       │
│   │             │          └─────────────┘           └─────────┘       │
│   │             │          ┌─────────────┐           ┌─────────┐       │
│   │             │◄────────┤│ Segment 3   │──────────▶│ UDM #3  │       │
│   │             │          │ 05:15-08:00 │           │ (Hand3) │       │
│   └─────────────┘          └─────────────┘           └─────────┘       │
│                                                                         │
│   관계:                                                                 │
│   • 1 NAS File : N Sheet Records (여러 핸드/세그먼트)                    │
│   • 1 NAS File : N UDM Segments (각 핸드별 메타데이터)                   │
│   • 1 Sheet Record : 1 UDM Segment (1:1 변환)                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**관계 예시**:

| NAS File | Sheet Records | UDM Segments | 설명 |
|----------|---------------|--------------|------|
| `STREAM_01.mp4` | 15개 행 | 15개 Segment | 1시간 영상, 15개 핸드 |
| `WCLA24-01.mp4` | 1개 행 | 1개 Segment | 클립 파일, 1개 핸드 |
| `PAD_S13_EP01.mp4` | 8개 행 | 8개 Segment | 에피소드, 8개 핸드 |

### 1.4 사용자

- **Primary**: 내부 편집팀 (메타데이터 입력/검증)
- **Use Cases**:
  - 매칭 상태 확인
  - 누락 데이터 발견
  - 오류 수정
  - 변환 실행/모니터링

---

## 2. System Architecture

### 2.1 전체 구조

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DOCKER COMPOSE STACK                             │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    FRONTEND (React + TypeScript)                 │   │
│  │                                                                  │   │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │   │
│  │   │ Overview │  │ Matching │  │  Data    │  │ Pipeline │       │   │
│  │   │   Page   │  │  Matrix  │  │ Explorer │  │  Monitor │       │   │
│  │   └──────────┘  └──────────┘  └──────────┘  └──────────┘       │   │
│  │                                                                  │   │
│  │   Vite + TailwindCSS + React Query + Recharts                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│                                    │ REST API                            │
│                                    ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    BACKEND (FastAPI + Python)                    │   │
│  │                                                                  │   │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │   │
│  │   │   NAS    │  │  Sheets  │  │   UDM    │  │ Pipeline │       │   │
│  │   │ Scanner  │  │  Client  │  │  Service │  │  Runner  │       │   │
│  │   └──────────┘  └──────────┘  └──────────┘  └──────────┘       │   │
│  │                                                                  │   │
│  │   Pydantic V2 + httpx + google-api-client                       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│            ┌───────────────────────┼───────────────────────┐            │
│            │                       │                       │            │
│            ▼                       ▼                       ▼            │
│  ┌──────────────┐       ┌──────────────┐       ┌──────────────┐        │
│  │  PostgreSQL  │       │    Redis     │       │   Volumes    │        │
│  │   Database   │       │    Cache     │       │  (NAS Mount) │        │
│  └──────────────┘       └──────────────┘       └──────────────┘        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
                ▼                   ▼                   ▼
        ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
        │     NAS      │   │   Archive    │   │    Iconik    │
        │   Storage    │   │   Metadata   │   │   Metadata   │
        │  (194 폴더)  │   │   (Sheet)    │   │   (Sheet)    │
        └──────────────┘   └──────────────┘   └──────────────┘
```

### 2.2 Docker Compose 구성

```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/archive
      - REDIS_URL=redis://redis:6379
      - NAS_MOUNT_PATH=/mnt/nas
      - GOOGLE_SHEETS_CREDENTIALS=/app/credentials.json
    volumes:
      - //10.10.100.122/docker/GGPNAs:/mnt/nas:ro
      - ./credentials:/app/credentials:ro
    depends_on:
      - db
      - redis

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=archive
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

---

## 3. Features

### 3.1 Overview Page (홈 대시보드)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ARCHIVE CONVERTER DASHBOARD                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │   1,400+    │  │     238     │  │     54      │  │    98%      │   │
│  │  NAS Files  │  │Sheet Records│  │  UDM Docs   │  │ Mapping Rate│   │
│  │    ████     │  │    ████     │  │    ████     │  │    ████     │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                                         │
│  ┌────────────────────────────────┐  ┌────────────────────────────┐   │
│  │      DATA SOURCE STATUS        │  │     MATCHING OVERVIEW      │   │
│  │                                │  │                            │   │
│  │  NAS         ████████████ 100% │  │    ┌─────┐                 │   │
│  │  Archive MD  ████████████ 100% │  │    │ NAS │◄──┐             │   │
│  │  Iconik MD   ████████████ 100% │  │    └──┬──┘   │             │   │
│  │  UDM Cache   ████████░░░░  67% │  │       │      │             │   │
│  │                                │  │    ┌──▼──┐   │             │   │
│  │  Last Sync: 2 mins ago         │  │    │Sheet│───┤             │   │
│  └────────────────────────────────┘  │    └──┬──┘   │             │   │
│                                      │       │      │             │   │
│  ┌────────────────────────────────┐  │    ┌──▼──┐   │             │   │
│  │     RECENT ACTIVITIES          │  │    │ UDM │◄──┘             │   │
│  │                                │  │    └─────┘                 │   │
│  │  ● Archive MD synced (38 rows) │  │                            │   │
│  │  ● 12 new NAS files detected   │  │  Matched: 238 (98%)       │   │
│  │  ● UDM export completed        │  │  Orphan:  5 (2%)          │   │
│  │  ● 3 validation warnings       │  │                            │   │
│  └────────────────────────────────┘  └────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**KPI 카드**:
- NAS Files: 전체 파일 수
- Sheet Records: Archive + Iconik 레코드 수
- UDM Documents: 변환 완료된 UDM 수
- Mapping Rate: 매칭 성공률

### 3.2 Three-Way Matrix (3원 매트릭스) - v1.2.0 신규

> **핵심**: NAS, Archive Sheet, Iconik Sheet, UDM 4개 소스를 동시에 표시하여 매칭 관계를 명확히 파악

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                         THREE-WAY MATCHING MATRIX                                   │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│  Filter: [All Status ▼]  Brand: [All ▼]  Search: [________________]               │
│                                                                                    │
│  ═══════════════════════════════════════════════════════════════════════════════  │
│  │ NAS File            │ Archive │ Iconik │ Total │ UDM    │ Status      │ Actions││
│  │                     │ Sheet   │ Sheet  │ Segs  │ 변환   │             │        ││
│  ├─────────────────────┼─────────┼────────┼───────┼────────┼─────────────┼────────┤│
│  │ ▶ STREAM_01.mp4     │    12   │    3   │   15  │ 15/15  │ ● Complete  │ [▶][📤]││
│  │ ▶ PAD_S13_EP01.mp4  │     0   │    8   │    8  │  6/8   │ ○ Partial   │ [▶][📤]││
│  │   WCLA24-01.mp4     │     1   │    0   │    1  │  1/1   │ ● Complete  │ [▶][📤]││
│  │   WCLA24-02.mp4     │     1   │    0   │    1  │  1/1   │ ● Complete  │ [▶][📤]││
│  │ ▶ HCL_2024_EP01.mp4 │     0   │    5   │    5  │  3/5   │ △ Warning   │ [▶][📤]││
│  │   UNKNOWN_FILE.mp4  │     0   │    0   │    0  │   -    │ ✗ No Meta   │ [+]    ││
│  └─────────────────────┴─────────┴────────┴───────┴────────┴─────────────┴────────┘│
│                                                                                    │
│  Legend: Archive Sheet = 🟦 Blue | Iconik Sheet = 🟩 Green                         │
│  ▶ = 확장 가능 (클릭하여 세그먼트 목록 표시)                                          │
│                                                                                    │
│  ═══════════════════════════════════════════════════════════════════════════════  │
│  │ ▼ EXPANDED: STREAM_01.mp4 (15 Segments from 2 Sources)                        ││
│  ├────────────────────────────────────────────────────────────────────────────────┤│
│  │                                                                                ││
│  │  ┌─────┬────────────┬───────────┬───────────┬────────┬────────┬──────┬──────┐││
│  │  │ #   │ Source     │ Time In   │ Time Out  │ Rating │ Winner │ UDM  │Status│││
│  │  ├─────┼────────────┼───────────┼───────────┼────────┼────────┼──────┼──────┤││
│  │  │ 1   │ 🟦 Archive │ 00:02:15  │ 00:05:30  │ ★★★★  │ P.Ivey │  ✅  │  ●   │││
│  │  │ 2   │ 🟦 Archive │ 00:08:45  │ 00:12:20  │ ★★★   │ D.Neg  │  ✅  │  ●   │││
│  │  │ 3   │ 🟩 Iconik  │ 00:15:00  │ 00:18:45  │ ★★★★★ │ Hellmu │  ✅  │  ●   │││
│  │  │ 4   │ 🟦 Archive │ 00:22:10  │ 00:25:55  │ ★★★   │ -      │  ✅  │  ●   │││
│  │  │ ... │ ...        │ ...       │ ...       │ ...    │ ...    │ ...  │ ...  │││
│  │  │ 14  │ 🟩 Iconik  │ 00:52:15  │ 00:56:45  │ ★★★★  │ Ivey   │  ✅  │  ●   │││
│  │  │ 15  │ 🟩 Iconik  │ 00:58:00  │ 01:02:30  │ ★★★   │ Dwan   │  ✅  │  ●   │││
│  │  └─────┴────────────┴───────────┴───────────┴────────┴────────┴──────┴──────┘││
│  │                                                                                ││
│  │  [Transform All] [Export Segments] [View UDM JSON]                            ││
│  └────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2.1 Orphan Records 경고 섹션

> **규칙**: NAS에 없는 Sheet 행은 존재하면 안됨 → 경고 표시 후 수동 정리

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│  ⚠️ ORPHAN RECORDS (NAS 파일 없음) - 정리 필요: 3건                                  │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│  ┌─────┬────────────┬──────────────────┬───────────┬───────────┬────────────────┐ │
│  │ #   │ Source     │ File Name        │ Time In   │ Time Out  │ Actions        │ │
│  ├─────┼────────────┼──────────────────┼───────────┼───────────┼────────────────┤ │
│  │ 1   │ 🟦 Archive │ OLD_DELETED.mp4  │ 00:05:00  │ 00:08:30  │ [🗑 Delete]    │ │
│  │ 2   │ 🟩 Iconik  │ TYPO_NAME.mp4    │ 00:02:15  │ 00:04:45  │ [✎ Edit Name] │ │
│  │ 3   │ 🟩 Iconik  │ MOVED_FILE.mp4   │ 00:10:00  │ 00:13:20  │ [🔗 Re-link]  │ │
│  └─────┴────────────┴──────────────────┴───────────┴───────────┴────────────────┘ │
│                                                                                    │
│  [Delete All Orphans] [Export for Review]                                          │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2.2 Source Coverage Summary (소스별 커버리지)

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                         SOURCE COVERAGE SUMMARY                                     │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│  ┌─────────────────────┬─────────────────────┬─────────────────────┐              │
│  │ NAS Files           │ Archive Metadata    │ Iconik Metadata     │              │
│  ├─────────────────────┼─────────────────────┼─────────────────────┤              │
│  │ Total: 1,438 files  │ Records: 38         │ Records: 200        │              │
│  │ With Metadata: 86   │ Matched: 38 (100%)  │ Matched: 197 (98.5%)│              │
│  │ No Metadata: 1,352  │ Orphan: 0           │ Orphan: 3 ⚠️        │              │
│  │ Size: 2.45 TB       │ Unique Files: 38    │ Unique Files: 45    │              │
│  └─────────────────────┴─────────────────────┴─────────────────────┘              │
│                                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                           UDM CONVERSION STATUS                              │  │
│  │                                                                               │  │
│  │  Total Segments: 238    Converted: 230 (96.6%)    Pending: 5    Warning: 3   │  │
│  │                                                                               │  │
│  │  [████████████████████████████████████████████░░] 96.6%                      │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2.3 세그먼트 상세 패널 (선택 시)

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                    SELECTED: STREAM_01.mp4 - Segment #3                             │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│  ┌──────────────────────────┐ ┌──────────────────────────┐ ┌──────────────────────┐│
│  │ NAS File Info            │ │ Sheet Record (🟩 Iconik) │ │ UDM Preview          ││
│  │ ─────────────            │ │ ──────────────────────── │ │ ───────────          ││
│  │ Path: /ARCHIVE/WSOP/...  │ │ Row: 45                  │ │ UUID: a1b2c3d4-...   ││
│  │ Size: 2.45 GB            │ │ Time In: 00:15:00        │ │ Status: ✅ Complete  ││
│  │ Duration: 1h 02m 30s     │ │ Time Out: 00:18:45       │ │                      ││
│  │ Total Segments: 15       │ │ Rating: ★★★★★ (5)       │ │ time_in_sec: 900.0   ││
│  │ Archive: 12 | Iconik: 3  │ │ Winner: Phil Hellmuth    │ │ time_out_sec: 1125.0 ││
│  │                          │ │ Hands: KK vs AA          │ │ rating: 5            ││
│  │                          │ │ Tags: cooler, bad-beat   │ │                      ││
│  └──────────────────────────┘ └──────────────────────────┘ └──────────────────────┘│
│                                                                                    │
│  [View Full UDM JSON] [Edit Sheet Record] [Re-transform] [Export]                 │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2.4 매칭 상태 분류

| Status | 설명 | 액션 |
|--------|------|------|
| ● Complete | 모든 세그먼트가 UDM 변환 완료 | 없음 |
| ○ Partial | 일부 세그먼트만 변환됨 | 나머지 변환 실행 |
| △ Warning | 일부 세그먼트에 검증 오류 | 검토 및 수정 |
| ✗ No Metadata | NAS 파일만 존재, Sheet 레코드 없음 | 메타데이터 입력 필요 |
| ⚠️ Orphan | Sheet 레코드만 존재, NAS 파일 없음 | **경고 표시 → 수동 정리** |

> **Orphan 규칙**: NAS에 없는 Sheet 행은 존재하면 안됨. Orphan 섹션에 경고로 표시 후 사용자가 수동 정리

### 3.3 Data Explorer (데이터 탐색기)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          DATA EXPLORER                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Source: [NAS ▼] [Archive Metadata ▼] [Iconik Metadata ▼] [UDM ▼]      │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ TAB: NAS Browser                                                 │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │                                                                  │   │
│  │  📁 ARCHIVE/                                                     │   │
│  │  ├── 📁 WSOP/ (170 folders)                                     │   │
│  │  │   ├── 📁 WSOP ARCHIVE (PRE-2016)/                            │   │
│  │  │   ├── 📁 WSOP Bracelet Event/                                │   │
│  │  │   │   ├── 📁 WSOP-EUROPE/                                    │   │
│  │  │   │   ├── 📁 WSOP-LAS VEGAS/                                 │   │
│  │  │   │   └── 📁 WSOP-PARADISE/                                  │   │
│  │  │   └── 📁 WSOP Circuit Event/                                 │   │
│  │  │       └── 📁 2024 WSOP Circuit LA/                           │   │
│  │  │           ├── 📁 STREAM/ (12 files)                          │   │
│  │  │           └── 📁 SUBCLIP/ (38 files) ← Archive Metadata      │   │
│  │  ├── 📁 HCL/ (6 folders)                                        │   │
│  │  ├── 📁 PAD/ (3 folders)                                        │   │
│  │  ├── 📁 GGMillions/                                             │   │
│  │  ├── 📁 MPP/                                                    │   │
│  │  └── 📁 GOG 최종/                                               │   │
│  │                                                                  │   │
│  │  Selected: SUBCLIP/ (38 files)                                  │   │
│  │  ┌───────────────────────────────────────────────────────────┐  │   │
│  │  │ WCLA24-01.mp4  │ 245 MB │ 2024-11-15 │ ● Has Metadata    │  │   │
│  │  │ WCLA24-02.mp4  │ 312 MB │ 2024-11-15 │ ● Has Metadata    │  │   │
│  │  │ WCLA24-03.mp4  │ 198 MB │ 2024-11-15 │ ● Has Metadata    │  │   │
│  │  │ ...                                                       │  │   │
│  │  └───────────────────────────────────────────────────────────┘  │   │
│  │                                                                  │   │
│  │  [Scan Folder] [Export File List] [Match with Sheet]            │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ TAB: Sheet Viewer                                                │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │                                                                  │   │
│  │  Sheet: [Archive Metadata ▼]  Tab: [WSOP Circuit 2024 ▼]        │   │
│  │                                                                  │   │
│  │  ┌─────┬───────────┬─────────┬─────────┬───────┬───────┬─────┐ │   │
│  │  │ No. │ File Name │   In    │   Out   │ Grade │Winner │Hands│ │   │
│  │  ├─────┼───────────┼─────────┼─────────┼───────┼───────┼─────┤ │   │
│  │  │  1  │WCLA24-01  │00:02:05 │00:03:45 │ ★★★★ │P.Ivey │AA/KK│ │   │
│  │  │  2  │WCLA24-02  │00:01:30 │00:02:45 │ ★★★  │D.Neg  │QQ/JJ│ │   │
│  │  │  3  │WCLA24-03  │00:00:45 │00:01:55 │ ★★★★★│Hellmu │KK/AA│ │   │
│  │  │ ... │   ...     │  ...    │  ...    │ ...   │ ...   │ ... │ │   │
│  │  └─────┴───────────┴─────────┴─────────┴───────┴───────┴─────┘ │   │
│  │                                                                  │   │
│  │  Total: 38 rows | Last Sync: 5 mins ago                         │   │
│  │  [Sync Now] [Download CSV] [Transform to UDM]                   │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.4 Pipeline Monitor (파이프라인 모니터)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PIPELINE MONITOR                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    TRANSFORMATION PIPELINE                       │   │
│  │                                                                  │   │
│  │   ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐         │   │
│  │   │ INGEST │───▶│TRANSFORM│───▶│VALIDATE│───▶│ EXPORT │         │   │
│  │   │   ✅   │    │   ✅   │    │   ⏳   │    │   ○    │         │   │
│  │   │ 38/38  │    │ 38/38  │    │ 25/38  │    │  0/38  │         │   │
│  │   └────────┘    └────────┘    └────────┘    └────────┘         │   │
│  │                                                                  │   │
│  │   Progress: ████████████████░░░░░░░░ 65%                        │   │
│  │   Elapsed: 2m 34s | ETA: 1m 20s                                 │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      EXECUTION LOG                               │   │
│  │                                                                  │   │
│  │  14:32:15 [INFO]  Starting pipeline: Archive Metadata → UDM     │   │
│  │  14:32:16 [INFO]  Ingest: Loading 38 rows from Sheet            │   │
│  │  14:32:18 [INFO]  Ingest: Complete (38 records)                 │   │
│  │  14:32:18 [INFO]  Transform: Starting UDM conversion            │   │
│  │  14:32:45 [INFO]  Transform: Complete (38 documents)            │   │
│  │  14:32:45 [INFO]  Validate: Starting schema validation          │   │
│  │  14:33:12 [WARN]  Validate: Row 15 - time_out < time_in         │   │
│  │  14:33:15 [WARN]  Validate: Row 23 - missing winner field       │   │
│  │  14:34:49 [INFO]  Validate: 25/38 passed, 13 warnings           │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    QUICK ACTIONS                                 │   │
│  │                                                                  │   │
│  │  [▶ Run Full Pipeline]  [⟳ Sync All Sources]  [⬇ Export UDM]   │   │
│  │                                                                  │   │
│  │  Source Selection:                                               │   │
│  │  ☑ Archive Metadata (38 rows)                                   │   │
│  │  ☑ Iconik Metadata (200+ rows)                                  │   │
│  │  ☐ NAS Scan Only (no metadata)                                  │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.5 Validation & Edit (검증 및 수정)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      VALIDATION & EDIT                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Filter: [⚠️ Warnings Only ▼]  [All Sources ▼]                         │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ VALIDATION ISSUES (13)                                          │   │
│  │                                                                  │   │
│  │ ⚠️ WCLA24-15.mp4 - time_out_sec < time_in_sec                  │   │
│  │    Sheet: In=00:03:45, Out=00:02:05                             │   │
│  │    [Fix: Swap In/Out] [Edit Manually] [Ignore]                  │   │
│  │                                                                  │   │
│  │ ⚠️ WCLA24-23.mp4 - Missing winner field                        │   │
│  │    Sheet: Winner column is empty                                │   │
│  │    [Edit Manually] [Mark as N/A] [Ignore]                       │   │
│  │                                                                  │   │
│  │ ⚠️ HCL_2024_001.mp4 - Rating out of range (6)                  │   │
│  │    Sheet: Hand Grade = ★★★★★★                                   │   │
│  │    [Fix: Set to 5] [Edit Manually] [Ignore]                     │   │
│  │                                                                  │   │
│  │ ✗ OLD_RECORD_01 - Orphan record (no NAS file)                  │   │
│  │    Sheet exists but file not found in NAS                       │   │
│  │    [Delete Record] [Update File Path] [Ignore]                  │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ EDIT FORM: WCLA24-15.mp4                                        │   │
│  │                                                                  │   │
│  │  Time In:     [00:02:05    ] → 125.0 sec                        │   │
│  │  Time Out:    [00:03:45    ] → 225.0 sec                        │   │
│  │  Hand Grade:  [★★★★☆      ] → 4                                 │   │
│  │  Winner:      [Phil Ivey   ]                                    │   │
│  │  Hands:       [AA vs KK    ]                                    │   │
│  │                                                                  │   │
│  │  Tags (Player):  [Phil Ivey] [x] [Add +]                        │   │
│  │  Tags (Action):  [cooler] [hero-call] [x] [Add +]               │   │
│  │  Tags (Emotion): [brutal] [x] [Add +]                           │   │
│  │                                                                  │   │
│  │  [Cancel] [Save & Re-validate] [Save & Transform]               │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. API Design

### 4.1 Endpoints

```yaml
# NAS Operations
GET  /api/nas/folders              # 폴더 트리 조회
GET  /api/nas/files?path=...       # 특정 폴더 파일 목록
GET  /api/nas/scan                 # 전체 스캔 (캐시 갱신)
GET  /api/nas/file/{path}          # 파일 상세 정보

# Sheet Operations
GET  /api/sheets                   # 시트 목록
GET  /api/sheets/{id}/sync         # 시트 동기화
GET  /api/sheets/{id}/rows         # 행 데이터 조회
PUT  /api/sheets/{id}/rows/{row}   # 행 수정 (캐시만)

# Matching Operations
GET  /api/matching/matrix          # 매칭 매트릭스 조회
GET  /api/matching/stats           # 매칭 통계
GET  /api/matching/orphans         # Orphan 레코드 조회
GET  /api/matching/unmatched       # 미매칭 NAS 파일

# UDM Operations
GET  /api/udm                      # UDM 문서 목록
GET  /api/udm/{uuid}               # UDM 문서 상세
POST /api/udm/transform            # 변환 실행
GET  /api/udm/export?format=json   # 내보내기

# Pipeline Operations
POST /api/pipeline/run             # 파이프라인 실행
GET  /api/pipeline/status/{id}     # 실행 상태 조회
GET  /api/pipeline/logs/{id}       # 실행 로그
POST /api/pipeline/cancel/{id}     # 실행 취소

# Validation Operations
GET  /api/validation/issues        # 검증 이슈 목록
POST /api/validation/fix/{id}      # 자동 수정 적용
POST /api/validation/ignore/{id}   # 이슈 무시
```

### 4.2 Response Examples (1:N 관계 지원)

```json
// GET /api/matching/matrix
// 1:N 관계: 하나의 NAS 파일에 여러 Sheet 레코드와 UDM 세그먼트가 연결됨
{
  "total_files": 1438,
  "total_segments": 2850,
  "matched_files": 238,
  "matched_segments": 2340,
  "orphan_records": 5,
  "unmatched_nas": 1195,
  "items": [
    {
      "file_name": "STREAM_01.mp4",
      "nas": {
        "exists": true,
        "path": "/ARCHIVE/WSOP/.../STREAM/STREAM_01.mp4",
        "size_mb": 2450,
        "duration_sec": 3600,
        "modified": "2024-11-15T10:30:00Z"
      },
      "segment_count": 15,
      "udm_count": 15,
      "status": "complete",
      "status_detail": "15/15",
      "segments": [
        {
          "row_number": 1,
          "source": "archive_metadata",
          "time_in": "00:02:15",
          "time_out": "00:05:30",
          "time_in_sec": 135.0,
          "time_out_sec": 330.0,
          "rating": 4,
          "winner": "Phil Ivey",
          "hands": "AA vs KK",
          "udm_uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
          "udm_status": "complete"
        },
        {
          "row_number": 2,
          "source": "archive_metadata",
          "time_in": "00:08:45",
          "time_out": "00:12:20",
          "time_in_sec": 525.0,
          "time_out_sec": 740.0,
          "rating": 3,
          "winner": "Daniel Negreanu",
          "hands": "QQ vs JJ",
          "udm_uuid": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
          "udm_status": "complete"
        }
        // ... 13 more segments
      ],
      "warnings": []
    },
    {
      "file_name": "PAD_S13_EP01.mp4",
      "nas": {
        "exists": true,
        "path": "/ARCHIVE/PAD/S13/PAD_S13_EP01.mp4",
        "size_mb": 1200,
        "duration_sec": 3510,
        "modified": "2024-10-20T14:00:00Z"
      },
      "segment_count": 8,
      "udm_count": 6,
      "status": "partial",
      "status_detail": "6/8",
      "segments": [
        {
          "row_number": 45,
          "source": "iconik_metadata",
          "time_in": "00:15:00",
          "time_out": "00:18:45",
          "time_in_sec": 900.0,
          "time_out_sec": 1125.0,
          "rating": 5,
          "winner": "Phil Hellmuth",
          "hands": "KK vs AA",
          "udm_uuid": "c3d4e5f6-a7b8-9012-cdef-123456789012",
          "udm_status": "complete"
        },
        {
          "row_number": 52,
          "source": "iconik_metadata",
          "time_in": "00:45:30",
          "time_out": "00:49:00",
          "time_in_sec": 2730.0,
          "time_out_sec": 2940.0,
          "rating": 2,
          "winner": null,
          "hands": null,
          "udm_uuid": null,
          "udm_status": "pending"
        }
        // ... 6 more segments
      ],
      "warnings": [
        {"segment_row": 52, "type": "missing_hands", "message": "핸드 정보 누락"}
      ]
    },
    {
      "file_name": "WCLA24-01.mp4",
      "nas": {
        "exists": true,
        "path": "/ARCHIVE/WSOP/.../SUBCLIP/WCLA24-01.mp4",
        "size_mb": 245,
        "duration_sec": 120,
        "modified": "2024-11-15T10:30:00Z"
      },
      "segment_count": 1,
      "udm_count": 1,
      "status": "complete",
      "status_detail": "1/1",
      "segments": [
        {
          "row_number": 1,
          "source": "archive_metadata",
          "time_in": "00:02:05",
          "time_out": "00:03:45",
          "time_in_sec": 125.0,
          "time_out_sec": 225.0,
          "rating": 4,
          "winner": "Phil Ivey",
          "hands": "AA vs KK",
          "udm_uuid": "550e8400-e29b-41d4-a716-446655440000",
          "udm_status": "complete"
        }
      ],
      "warnings": []
    }
  ]
}

// GET /api/matching/stats
// 1:N 관계를 고려한 통계: 파일 수 vs 세그먼트 수 구분
{
  "sources": {
    "nas": {
      "total_files": 1438,
      "total_size_gb": 2450,
      "scanned_at": "2025-12-11T14:30:00Z"
    },
    "archive_metadata": {
      "total_records": 38,
      "unique_files": 38,
      "synced_at": "2025-12-11T14:25:00Z"
    },
    "iconik_metadata": {
      "total_records": 200,
      "unique_files": 45,
      "synced_at": "2025-12-11T14:20:00Z"
    }
  },
  "matching": {
    "files": {
      "complete": 78,
      "partial": 5,
      "warning": 3,
      "unmatched": 1195,
      "total_with_metadata": 86
    },
    "segments": {
      "complete": 2340,
      "pending": 45,
      "warning": 15,
      "total": 2400
    },
    "orphan_records": 5
  },
  "coverage": {
    "archive_to_nas": 1.0,
    "iconik_to_nas": 0.97,
    "nas_to_any_sheet": 0.06,
    "segment_conversion_rate": 0.975
  },
  "summary": {
    "avg_segments_per_file": 28,
    "max_segments_per_file": 156,
    "min_segments_per_file": 1
  }
}

// GET /api/matching/file/{file_name}/segments
// 특정 파일의 모든 세그먼트 조회
{
  "file_name": "STREAM_01.mp4",
  "nas": {
    "path": "/ARCHIVE/WSOP/.../STREAM/STREAM_01.mp4",
    "size_mb": 2450,
    "duration_sec": 3600
  },
  "total_segments": 15,
  "converted_segments": 15,
  "segments": [
    {
      "index": 1,
      "source": "archive_metadata",
      "row_number": 1,
      "time_range": {
        "in_tc": "00:02:15",
        "out_tc": "00:05:30",
        "in_sec": 135.0,
        "out_sec": 330.0,
        "duration_sec": 195.0
      },
      "metadata": {
        "rating": 4,
        "winner": "Phil Ivey",
        "hands": "AA vs KK",
        "tags": ["hero-call", "cooler"]
      },
      "udm": {
        "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "status": "complete",
        "created_at": "2025-12-11T14:35:00Z"
      }
    }
    // ... more segments
  ]
}
```

---

## 5. Data Models

### 5.1 Database Schema (1:N 관계 지원)

> **핵심 관계**: `nas_files (1) → sheet_records (N) → udm_segments (N)`

```sql
-- ================================================================
-- 1. NAS 파일 (물리 파일 - Asset Level)
-- ================================================================
CREATE TABLE nas_files (
    id SERIAL PRIMARY KEY,
    file_path VARCHAR(1024) UNIQUE NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    folder_path VARCHAR(1024) NOT NULL,
    size_bytes BIGINT,
    duration_sec FLOAT,                    -- 영상 길이 (초)
    modified_at TIMESTAMP,
    scanned_at TIMESTAMP DEFAULT NOW(),

    -- 추론된 메타데이터
    inferred_brand VARCHAR(50),
    inferred_asset_type VARCHAR(50),
    inferred_year INTEGER,

    -- 1:N 집계 캐시 (성능 최적화)
    segment_count INTEGER DEFAULT 0,       -- 연결된 세그먼트 수
    udm_count INTEGER DEFAULT 0            -- 변환 완료된 UDM 수
);

CREATE INDEX idx_nas_files_file_name ON nas_files(file_name);
CREATE INDEX idx_nas_files_brand ON nas_files(inferred_brand);

-- ================================================================
-- 2. Sheet 레코드 (세그먼트 - Segment Level)
-- 하나의 NAS 파일에 여러 Sheet 레코드가 연결됨 (1:N)
-- ================================================================
CREATE TABLE sheet_records (
    id SERIAL PRIMARY KEY,
    sheet_id VARCHAR(100) NOT NULL,        -- Google Sheet ID
    sheet_name VARCHAR(100) NOT NULL,      -- 'archive_metadata' or 'iconik_metadata'
    row_number INTEGER NOT NULL,

    -- NAS 파일 연결 (1:N 관계의 N 측)
    nas_file_id INTEGER REFERENCES nas_files(id),
    file_name VARCHAR(255),                -- 매칭 키

    -- 시간 정보
    time_in_tc VARCHAR(20),                -- 원본 타임코드
    time_out_tc VARCHAR(20),
    time_in_sec FLOAT,                     -- 파싱된 초
    time_out_sec FLOAT,
    duration_sec FLOAT GENERATED ALWAYS AS (time_out_sec - time_in_sec) STORED,

    -- 메타데이터
    rating INTEGER,
    winner VARCHAR(255),
    hands VARCHAR(255),
    tags JSONB DEFAULT '[]',

    -- 원본 데이터
    raw_data JSONB NOT NULL,
    parsed_data JSONB,
    synced_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(sheet_id, row_number)
);

CREATE INDEX idx_sheet_records_nas_file_id ON sheet_records(nas_file_id);
CREATE INDEX idx_sheet_records_file_name ON sheet_records(file_name);
CREATE INDEX idx_sheet_records_time ON sheet_records(time_in_sec, time_out_sec);

-- ================================================================
-- 3. UDM 세그먼트 (변환된 메타데이터)
-- Sheet 레코드와 1:1 관계, NAS 파일과 N:1 관계
-- ================================================================
CREATE TABLE udm_segments (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 관계 (1:N 구조)
    nas_file_id INTEGER REFERENCES nas_files(id),      -- Asset (1)
    sheet_record_id INTEGER REFERENCES sheet_records(id) UNIQUE,  -- Source (1:1)
    parent_asset_uuid UUID,                -- UDM Asset UUID

    -- 시간 정보
    time_in_sec FLOAT NOT NULL,
    time_out_sec FLOAT NOT NULL,
    duration_sec FLOAT GENERATED ALWAYS AS (time_out_sec - time_in_sec) STORED,

    -- 세그먼트 데이터
    segment_data JSONB NOT NULL,           -- 전체 UDM Segment 데이터

    -- 상태
    status VARCHAR(20) DEFAULT 'complete', -- complete, warning, error
    warnings JSONB DEFAULT '[]',

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_udm_segments_nas_file_id ON udm_segments(nas_file_id);
CREATE INDEX idx_udm_segments_parent_asset ON udm_segments(parent_asset_uuid);

-- ================================================================
-- 4. UDM Asset (파일 레벨 메타데이터)
-- NAS 파일과 1:1 관계
-- ================================================================
CREATE TABLE udm_assets (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nas_file_id INTEGER REFERENCES nas_files(id) UNIQUE,

    -- Asset 데이터
    asset_data JSONB NOT NULL,

    -- 집계 정보
    segment_count INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ================================================================
-- 5. 매칭 상태 뷰 (1:N 관계 시각화용)
-- ================================================================
CREATE VIEW matching_status AS
SELECT
    nf.id AS nas_file_id,
    nf.file_name,
    nf.file_path,
    nf.size_bytes,
    nf.duration_sec,
    nf.inferred_brand,

    -- 세그먼트 집계
    COUNT(sr.id) AS sheet_record_count,
    COUNT(us.uuid) AS udm_segment_count,

    -- 상태 계산
    CASE
        WHEN COUNT(sr.id) = 0 THEN 'no_metadata'
        WHEN COUNT(us.uuid) = COUNT(sr.id) THEN 'complete'
        WHEN COUNT(us.uuid) > 0 THEN 'partial'
        ELSE 'pending'
    END AS status,

    -- 상태 상세
    CONCAT(COUNT(us.uuid), '/', COUNT(sr.id)) AS status_detail,

    -- 경고 수
    COUNT(CASE WHEN us.status = 'warning' THEN 1 END) AS warning_count

FROM nas_files nf
LEFT JOIN sheet_records sr ON sr.nas_file_id = nf.id
LEFT JOIN udm_segments us ON us.sheet_record_id = sr.id
GROUP BY nf.id, nf.file_name, nf.file_path, nf.size_bytes,
         nf.duration_sec, nf.inferred_brand;

-- ================================================================
-- 6. Orphan 레코드 뷰 (NAS 파일 없는 Sheet 레코드)
-- ================================================================
CREATE VIEW orphan_records AS
SELECT
    sr.id,
    sr.sheet_name,
    sr.row_number,
    sr.file_name,
    sr.time_in_tc,
    sr.time_out_tc,
    sr.raw_data
FROM sheet_records sr
WHERE sr.nas_file_id IS NULL;

-- ================================================================
-- 7. 파이프라인 실행 기록
-- ================================================================
CREATE TABLE pipeline_runs (
    id SERIAL PRIMARY KEY,
    source_type VARCHAR(50) NOT NULL,      -- 'archive_metadata', 'iconik_metadata', 'full'
    status VARCHAR(20) NOT NULL,           -- running, completed, failed, cancelled
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,

    -- 1:N 통계
    stats JSONB,                           -- {files_processed, segments_created, ...}
    logs TEXT[]
);

-- ================================================================
-- 8. 검증 이슈
-- ================================================================
CREATE TABLE validation_issues (
    id SERIAL PRIMARY KEY,

    -- 세그먼트 레벨 이슈
    sheet_record_id INTEGER REFERENCES sheet_records(id),
    udm_segment_id UUID REFERENCES udm_segments(uuid),

    issue_type VARCHAR(50) NOT NULL,       -- time_invalid, missing_field, etc.
    severity VARCHAR(20) NOT NULL,         -- error, warning, info
    message TEXT NOT NULL,
    suggested_fix JSONB,
    status VARCHAR(20) DEFAULT 'open',     -- open, fixed, ignored
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_validation_issues_sheet_record ON validation_issues(sheet_record_id);
```

### 5.1.1 관계 다이어그램

```
┌─────────────────┐
│   nas_files     │ ◄─────────────── 물리 파일 (1)
│   (Asset)       │
└────────┬────────┘
         │ 1:N
         │
┌────────▼────────┐
│  sheet_records  │ ◄─────────────── Sheet 레코드 (N)
│   (Segment)     │                  - Archive Metadata
└────────┬────────┘                  - Iconik Metadata
         │ 1:1
         │
┌────────▼────────┐
│  udm_segments   │ ◄─────────────── UDM 변환 결과 (N)
│   (UDM)         │
└─────────────────┘

┌─────────────────┐
│   udm_assets    │ ◄─────────────── 파일 레벨 UDM (1)
│ (Asset 메타)    │
└─────────────────┘
```

### 5.2 Frontend State (1:N 관계 지원)

```typescript
// types/segment.ts
// 세그먼트 레벨 (1:N 관계의 N)
interface SegmentRecord {
  id: number;
  rowNumber: number;
  source: 'archive_metadata' | 'iconik_metadata';

  // 시간 정보
  timeIn: string;           // 타임코드 "00:02:15"
  timeOut: string;
  timeInSec: number;        // 초 단위
  timeOutSec: number;
  durationSec: number;

  // 메타데이터
  rating: number | null;
  winner: string | null;
  hands: string | null;
  tags: string[];

  // UDM 변환 상태
  udm: {
    uuid: string | null;
    status: 'complete' | 'pending' | 'warning' | 'error';
  };
}

// types/matching.ts
// 파일 레벨 (1:N 관계의 1)
interface MatchingItem {
  fileName: string;

  // NAS 정보 (Asset Level)
  nas: {
    exists: boolean;
    path: string;
    sizeMb: number;
    durationSec: number;
    modifiedAt: string;
    inferredBrand: string | null;
  } | null;

  // 1:N 관계: 세그먼트 목록
  segmentCount: number;       // Sheet 레코드 수
  udmCount: number;           // 변환 완료 UDM 수
  segments: SegmentRecord[];  // 세그먼트 상세 (확장 시 로드)

  // 상태
  status: 'complete' | 'partial' | 'pending' | 'warning' | 'no_metadata' | 'orphan';
  statusDetail: string;       // "15/15", "6/8" 등
  warnings: ValidationWarning[];

  // UI 상태
  isExpanded: boolean;        // 세그먼트 목록 펼침 여부
}

interface ValidationWarning {
  segmentRow: number;
  type: string;
  message: string;
  suggestedFix?: Record<string, unknown>;
}

// types/stats.ts
interface MatchingStats {
  sources: {
    nas: {
      totalFiles: number;
      totalSizeGb: number;
      scannedAt: string;
    };
    archiveMetadata: {
      totalRecords: number;   // Sheet 행 수 (세그먼트)
      uniqueFiles: number;    // 고유 파일 수
      syncedAt: string;
    };
    iconikMetadata: {
      totalRecords: number;
      uniqueFiles: number;
      syncedAt: string;
    };
  };
  matching: {
    files: {
      complete: number;       // 모든 세그먼트 변환 완료
      partial: number;        // 일부만 변환
      warning: number;        // 경고 있음
      unmatched: number;      // 메타데이터 없음
      totalWithMetadata: number;
    };
    segments: {
      complete: number;
      pending: number;
      warning: number;
      total: number;
    };
    orphanRecords: number;    // NAS 없는 Sheet 레코드
  };
  coverage: {
    archiveToNas: number;     // Archive Sheet → NAS 매칭률
    iconikToNas: number;      // Iconik Sheet → NAS 매칭률
    nasToAnySheet: number;    // NAS → 어떤 Sheet든 매칭률
    segmentConversionRate: number;  // 세그먼트 UDM 변환율
  };
  summary: {
    avgSegmentsPerFile: number;
    maxSegmentsPerFile: number;
    minSegmentsPerFile: number;
  };
}

// stores/matchingStore.ts
interface MatchingState {
  // 데이터
  items: MatchingItem[];
  stats: MatchingStats | null;

  // 선택 상태
  selectedFile: MatchingItem | null;      // 선택된 파일
  selectedSegment: SegmentRecord | null;  // 선택된 세그먼트

  // 필터
  filters: {
    source: 'all' | 'archive_metadata' | 'iconik_metadata';
    status: 'all' | 'complete' | 'partial' | 'pending' | 'warning' | 'no_metadata' | 'orphan';
    search: string;
    brand: string | null;
  };

  // 뷰 모드
  viewMode: 'asset_centric' | 'segment_centric';

  // 로딩 상태
  loading: boolean;
  loadingSegments: boolean;   // 세그먼트 로딩 중
  error: string | null;
}

// stores/matchingStore.ts - Actions
interface MatchingActions {
  // 데이터 로드
  fetchItems: () => Promise<void>;
  fetchStats: () => Promise<void>;

  // 1:N 관계 - 세그먼트 로드
  fetchSegments: (fileName: string) => Promise<void>;
  toggleExpand: (fileName: string) => void;

  // 선택
  selectFile: (item: MatchingItem | null) => void;
  selectSegment: (segment: SegmentRecord | null) => void;

  // 필터
  setFilter: (key: keyof MatchingState['filters'], value: string) => void;
  resetFilters: () => void;

  // 뷰 모드
  setViewMode: (mode: 'asset_centric' | 'segment_centric') => void;

  // 액션
  transformSegment: (segmentId: number) => Promise<void>;
  transformAllSegments: (fileName: string) => Promise<void>;
}
```

---

## 6. Tech Stack

### 6.1 Frontend

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Framework** | React 18 + TypeScript | UI Framework |
| **Build** | Vite 5 | Fast bundler |
| **Styling** | TailwindCSS 3 | Utility-first CSS |
| **State** | Zustand | Global state |
| **Data Fetching** | TanStack Query v5 | Server state |
| **Charts** | Recharts | 데이터 시각화 |
| **Table** | TanStack Table v8 | 데이터 테이블 |
| **Icons** | Lucide React | 아이콘 |
| **Forms** | React Hook Form + Zod | 폼 관리 |

### 6.2 Backend

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Framework** | FastAPI | REST API |
| **Validation** | Pydantic V2 | 데이터 검증 |
| **Database** | PostgreSQL 16 | 메인 DB |
| **ORM** | SQLAlchemy 2.0 | DB 접근 |
| **Cache** | Redis 7 | 캐시/세션 |
| **Sheets API** | google-api-python-client | Google Sheets |
| **HTTP Client** | httpx | 비동기 HTTP |
| **Task Queue** | Celery (optional) | 백그라운드 작업 |

### 6.3 Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Container** | Docker + Compose | 컨테이너화 |
| **Reverse Proxy** | Traefik (optional) | 라우팅 |
| **Volumes** | Docker Volumes | 데이터 영속성 |
| **NAS Mount** | CIFS/SMB | NAS 접근 |

---

## 7. Implementation Plan

### Phase 1: Foundation (Week 1-2)

```
┌─────────────────────────────────────────────┐
│ Phase 1: Foundation                         │
├─────────────────────────────────────────────┤
│                                             │
│ Backend:                                    │
│ ├── Docker Compose 구성                     │
│ ├── FastAPI 프로젝트 구조                    │
│ ├── PostgreSQL 스키마                       │
│ ├── NAS 스캐너 (기존 코드 활용)              │
│ └── Google Sheets 클라이언트                 │
│                                             │
│ Frontend:                                   │
│ ├── Vite + React + TypeScript 설정          │
│ ├── TailwindCSS 구성                        │
│ ├── 라우팅 구조                             │
│ └── API 클라이언트 (React Query)            │
│                                             │
│ Deliverable:                                │
│ └── 기본 대시보드 구조 + 데이터 로딩         │
│                                             │
└─────────────────────────────────────────────┘
```

### Phase 2: Core Features (Week 3-4)

```
┌─────────────────────────────────────────────┐
│ Phase 2: Core Features                      │
├─────────────────────────────────────────────┤
│                                             │
│ Matching Matrix:                            │
│ ├── 매칭 알고리즘 구현                       │
│ ├── 매트릭스 뷰 UI                          │
│ ├── 필터링/검색                             │
│ └── 상세 패널                               │
│                                             │
│ Data Explorer:                              │
│ ├── NAS 브라우저                            │
│ ├── Sheet 뷰어                              │
│ └── UDM 프리뷰                              │
│                                             │
│ Deliverable:                                │
│ └── 매칭 현황 확인 가능                      │
│                                             │
└─────────────────────────────────────────────┘
```

### Phase 3: Pipeline & Validation (Week 5-6)

```
┌─────────────────────────────────────────────┐
│ Phase 3: Pipeline & Validation              │
├─────────────────────────────────────────────┤
│                                             │
│ Pipeline Monitor:                           │
│ ├── 변환 파이프라인 실행                     │
│ ├── 실시간 진행 상태                        │
│ └── 로그 뷰어                               │
│                                             │
│ Validation:                                 │
│ ├── 검증 규칙 적용                          │
│ ├── 이슈 리스트                             │
│ ├── 자동 수정 제안                          │
│ └── 수동 편집 폼                            │
│                                             │
│ Deliverable:                                │
│ └── 전체 워크플로우 완성                     │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 8. Directory Structure

```
Archive_Converter/
├── dashboard/                    # 대시보드 (신규)
│   ├── docker-compose.yml
│   ├── .env.example
│   │
│   ├── frontend/
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   ├── tailwind.config.js
│   │   ├── tsconfig.json
│   │   │
│   │   └── src/
│   │       ├── main.tsx
│   │       ├── App.tsx
│   │       ├── api/              # API 클라이언트
│   │       │   ├── client.ts
│   │       │   ├── nas.ts
│   │       │   ├── sheets.ts
│   │       │   ├── matching.ts
│   │       │   └── pipeline.ts
│   │       ├── components/       # UI 컴포넌트
│   │       │   ├── layout/
│   │       │   ├── matching/
│   │       │   ├── explorer/
│   │       │   └── pipeline/
│   │       ├── pages/            # 페이지
│   │       │   ├── Overview.tsx
│   │       │   ├── MatchingMatrix.tsx
│   │       │   ├── DataExplorer.tsx
│   │       │   ├── PipelineMonitor.tsx
│   │       │   └── Validation.tsx
│   │       ├── stores/           # Zustand stores
│   │       ├── hooks/            # Custom hooks
│   │       └── types/            # TypeScript types
│   │
│   └── backend/
│       ├── Dockerfile
│       ├── pyproject.toml
│       │
│       └── app/
│           ├── main.py
│           ├── config.py
│           ├── database.py
│           │
│           ├── routers/          # API 라우터
│           │   ├── nas.py
│           │   ├── sheets.py
│           │   ├── matching.py
│           │   ├── udm.py
│           │   └── pipeline.py
│           │
│           ├── services/         # 비즈니스 로직
│           │   ├── nas_scanner.py
│           │   ├── sheets_client.py
│           │   ├── matching_engine.py
│           │   ├── transformer.py
│           │   └── validator.py
│           │
│           ├── models/           # SQLAlchemy models
│           │   ├── nas_file.py
│           │   ├── sheet_record.py
│           │   ├── matching.py
│           │   └── pipeline.py
│           │
│           └── schemas/          # Pydantic schemas
│               ├── nas.py
│               ├── sheets.py
│               ├── matching.py
│               └── pipeline.py
│
├── src/models/                   # 기존 UDM 스키마
│   ├── __init__.py
│   └── udm.py
│
├── profiles/                     # 기존 프로파일
├── prds/                         # PRD 문서
└── docs/                         # 문서
```

---

## 9. Success Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| **매칭 정확도** | 100% | File Name 매칭 성공률 |
| **데이터 로딩** | < 3s | 초기 대시보드 로딩 |
| **검색 응답** | < 500ms | 필터/검색 응답 시간 |
| **동기화** | < 30s | Sheet 전체 동기화 |
| **변환 처리** | 100 rows/s | UDM 변환 속도 |

---

## 10. Related PRDs

| PRD | 연관성 |
|-----|--------|
| PRD-0001 | Master Orchestrator - 파이프라인 구조 |
| PRD-0002 | Ingest Agent - NAS/Sheet 데이터 수집 |
| PRD-0003 | Transform Agent - UDM 변환 |
| PRD-0004 | Validate Agent - 검증 규칙 |
| PRD-0008 | UDM Schema v3.1 - 데이터 모델 |
| PRD-0009 | Source Data Spec - 소스 데이터 명세 |

---

## Appendix A: Google Sheets 연동

### 인증 설정

```python
# Service Account 방식 (권장)
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

credentials = service_account.Credentials.from_service_account_file(
    'credentials.json', scopes=SCOPES
)
service = build('sheets', 'v4', credentials=credentials)

# Sheet ID 상수
ARCHIVE_METADATA_ID = "1_RN_W_ZQclSZA0Iez6XniCXVtjkkd5HNZwiT6l-z6d4"
ICONIK_METADATA_ID = "1pUMPKe-OsKc-Xd8lH1cP9ctJO4hj3keXY5RwNFp2Mtk"
```

### 데이터 동기화

```python
async def sync_sheet(sheet_id: str, tab_name: str) -> list[dict]:
    """Google Sheet 데이터 동기화"""
    range_name = f"'{tab_name}'!A:ZZ"
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=range_name
    ).execute()

    rows = result.get('values', [])
    headers = rows[0] if rows else []

    return [
        dict(zip(headers, row + [''] * (len(headers) - len(row))))
        for row in rows[1:]
    ]
```

---

## Appendix B: NAS 마운트 설정

### Docker Volume 설정

```yaml
# docker-compose.yml
services:
  backend:
    volumes:
      # Windows 호스트에서 SMB 마운트된 드라이브 사용
      - type: bind
        source: //10.10.100.122/docker/GGPNAs
        target: /mnt/nas
        read_only: true
```

### Linux 호스트 마운트

```bash
# /etc/fstab
//10.10.100.122/docker/GGPNAs /mnt/nas cifs credentials=/root/.smbcredentials,ro 0 0

# credentials 파일
username=user
password=pass
```
