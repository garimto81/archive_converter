# PRD-0013: PokerGO Downloader Web App

## 개요

| 항목 | 내용 |
|------|------|
| **제목** | PokerGO Downloader - Local Network Web App |
| **버전** | 2.0.0 |
| **작성일** | 2025-12-16 |
| **상태** | Draft |
| **우선순위** | High |
| **기반** | PRD-0012 (Desktop GUI) |

## 배경

현재 PyQt6 기반 데스크톱 앱을 **웹 기반**으로 전환하여:
- 독립적인 장비(NAS, 서버, Raspberry Pi 등)에서 실행
- 로컬 네트워크 내 모든 기기에서 접근 가능
- 24/7 백그라운드 다운로드 지원

### 현재 상황 (v1.0 Desktop)

| 항목 | 상태 |
|------|------|
| 영상 목록 | 557개 WSOP (2011-2025) |
| 다운로드 | yt-dlp + JWPlayer HLS |
| 품질 | 1080p/720p/480p 선택 가능 |
| 인증 | Playwright 로그인 → HLS URL 추출 |

### 전환 이유

| Desktop (현재) | Web App (목표) |
|---------------|---------------|
| PC 실행 필요 | 서버에서 독립 실행 |
| PC 종료 시 중단 | 24/7 다운로드 |
| 단일 접근 | 다중 기기 접근 |
| PyQt6 의존성 | 브라우저만 필요 |

## 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                    Local Network (192.168.x.x)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐     HTTP      ┌──────────────────────────┐   │
│   │   Client     │──────────────▶│   PokerGO Web Server     │   │
│   │  (Browser)   │◀──────────────│   (FastAPI + React)      │   │
│   │              │   WebSocket   │                          │   │
│   │  - PC        │               │   Port: 8080             │   │
│   │  - Mobile    │               │   Host: 0.0.0.0          │   │
│   │  - Tablet    │               │                          │   │
│   └──────────────┘               └────────────┬─────────────┘   │
│                                               │                  │
│                                               │                  │
│                                  ┌────────────▼─────────────┐   │
│                                  │   Download Worker        │   │
│                                  │   (Background Process)   │   │
│                                  │                          │   │
│                                  │   - yt-dlp               │   │
│                                  │   - Playwright (HLS)     │   │
│                                  │   - Queue Manager        │   │
│                                  └────────────┬─────────────┘   │
│                                               │                  │
│                                               ▼                  │
│                                  ┌──────────────────────────┐   │
│                                  │   Storage (NAS/Local)    │   │
│                                  │   /downloads/            │   │
│                                  └──────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 기술 스택

### Backend

| 구성요소 | 기술 | 이유 |
|---------|------|------|
| Framework | **FastAPI** | 비동기, WebSocket, 자동 API 문서 |
| Database | **SQLite** | 경량, 서버리스 (기존 호환) |
| Task Queue | **asyncio + Queue** | 다운로드 작업 관리 |
| Scraper | **Playwright** | HLS URL 추출 (기존 코드 재사용) |
| Downloader | **yt-dlp** | HLS 다운로드 (기존 코드 재사용) |

### Frontend

| 구성요소 | 기술 | 이유 |
|---------|------|------|
| Framework | **React 18** | 컴포넌트 기반, 풍부한 생태계 |
| Build | **Vite** | 빠른 빌드, HMR |
| State | **Zustand** | 경량 상태관리 |
| UI | **Tailwind CSS** | 유틸리티 기반, 빠른 개발 |
| WebSocket | **socket.io-client** | 실시간 진행률 |

### 배포

| 구성요소 | 기술 | 이유 |
|---------|------|------|
| Container | **Docker** | 플랫폼 독립적 배포 |
| Compose | **docker-compose** | 멀티 서비스 관리 |
| Reverse Proxy | **Nginx** (Optional) | HTTPS, 로드밸런싱 |

## 요구사항

### 기능 요구사항 (FR)

#### FR-1: 영상 목록 조회 (Web UI)

```
┌─────────────────────────────────────────────────────────────────┐
│  🎰 PokerGO Downloader                    [Settings] [Account]  │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 🔍 Search...           │ Year [All ▼] │ Status [All ▼] │    │
│  └─────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│  □ Select All                                    557 videos     │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ □ │ WSOP 2024 Main Event Episode 1   │ 2024 │ 1080p │ ⬇️  │    │
│  │ □ │ WSOP 2024 Main Event Episode 2   │ 2024 │ 1080p │ ⬇️  │    │
│  │ ☑ │ WSOP 2023 Main Event Episode 1   │ 2023 │ 720p  │ ✅  │    │
│  │ □ │ WSOP 2017 Main Event Episode 1   │ 2017 │ 720p  │ ⏳  │    │
│  └─────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│  Selected: 3 videos (~2.1 GB)     [Fetch HLS] [Download]        │
└─────────────────────────────────────────────────────────────────┘
```

#### FR-2: 다운로드 큐 관리

```
┌─────────────────────────────────────────────────────────────────┐
│  📥 Download Queue                                    3 active  │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 🔄 WSOP 2017 Episode 1                                  │    │
│  │    ████████████████░░░░░░░░  65% │ 18.5 MB/s │ 2:30    │    │
│  │    [Pause] [Cancel]                                     │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │ ⏳ WSOP 2017 Episode 2                      Queued (1)  │    │
│  │ ⏳ WSOP 2017 Episode 3                      Queued (2)  │    │
│  └─────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│  Total: 3 videos │ ~2.1 GB │ ETA: 15:30                         │
│  [Pause All] [Cancel All] [Clear Completed]                     │
└─────────────────────────────────────────────────────────────────┘
```

#### FR-3: 실시간 진행률 (WebSocket)

```python
# WebSocket 메시지 형식
{
    "type": "progress",
    "video_id": "im_70009",
    "progress": 65.5,
    "speed": "18.5 MB/s",
    "eta": "2:30",
    "status": "downloading"
}

{
    "type": "completed",
    "video_id": "im_70009",
    "file_path": "/downloads/WSOP 2017 Main Event - Episode 1.mp4",
    "file_size": 731185152
}
```

#### FR-4: 설정 페이지

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚙️ Settings                                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📧 PokerGO Account                                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Email:    [_______________________________]             │    │
│  │ Password: [_______________________________]             │    │
│  │           [Test Login]  ✅ Connected                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  📁 Download Settings                                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Download Path: [/mnt/nas/pokergo/________] [Browse]     │    │
│  │ Quality:       [1080p ▼]                                │    │
│  │ Concurrent:    [2 ▼] downloads                          │    │
│  │ Auto-fetch HLS: [✓] Automatically fetch before download │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  🌐 Network                                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Server Port:   [8080]                                   │    │
│  │ Bind Address:  [0.0.0.0] (All interfaces)               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│                                         [Cancel] [Save]          │
└─────────────────────────────────────────────────────────────────┘
```

#### FR-5: 다운로드 히스토리

```
┌─────────────────────────────────────────────────────────────────┐
│  📜 Download History                              [Export CSV]   │
├─────────────────────────────────────────────────────────────────┤
│  │ Date       │ Title                    │ Size   │ Status │    │
│  ├────────────┼──────────────────────────┼────────┼────────┤    │
│  │ 2025-12-16 │ WSOP 2017 Episode 1      │ 697 MB │ ✅     │    │
│  │ 2025-12-16 │ WSOP 2024 Episode 1      │ 1.1 GB │ ✅     │    │
│  │ 2025-12-15 │ WSOP 2023 Episode 1      │ 1.3 GB │ ✅     │    │
│  │ 2025-12-15 │ WSOP 2023 Episode 2      │ 1.3 GB │ ❌     │    │
│  └────────────┴──────────────────────────┴────────┴────────┘    │
│                                                                  │
│  Total: 156 videos │ 198.5 GB │ Success: 154 │ Failed: 2        │
└─────────────────────────────────────────────────────────────────┘
```

### 비기능 요구사항 (NFR)

#### NFR-1: 성능

| 항목 | 요구사항 |
|------|---------|
| 동시 다운로드 | 1-3개 (설정 가능) |
| 웹 응답 시간 | < 200ms (목록 조회) |
| WebSocket 지연 | < 100ms (진행률 업데이트) |
| 메모리 사용 | < 512MB (기본 상태) |

#### NFR-2: 가용성

| 항목 | 요구사항 |
|------|---------|
| 다운로드 재개 | 네트워크 끊김 후 자동 재개 |
| 서버 재시작 | 큐 상태 유지 |
| 오류 복구 | 3회 자동 재시도 |

#### NFR-3: 보안

| 항목 | 요구사항 |
|------|---------|
| 인증 | 기본 인증 (설정 가능) |
| 네트워크 | 로컬 네트워크 전용 (기본) |
| 자격증명 | 암호화 저장 |

## API 설계

### REST API

```yaml
# 영상 관리
GET    /api/videos              # 목록 조회 (필터, 페이징)
GET    /api/videos/{id}         # 상세 조회
POST   /api/videos/import       # JSON 임포트
GET    /api/videos/export       # JSON 내보내기

# 다운로드 관리
GET    /api/downloads           # 큐 조회
POST   /api/downloads           # 다운로드 추가 (video_ids)
DELETE /api/downloads/{id}      # 다운로드 취소
PATCH  /api/downloads/{id}      # 일시정지/재개

# HLS URL
POST   /api/hls/fetch           # HLS URL 추출 (video_ids)
GET    /api/hls/status          # 추출 상태

# 설정
GET    /api/settings            # 설정 조회
PUT    /api/settings            # 설정 저장
POST   /api/settings/test-login # 로그인 테스트

# 통계
GET    /api/stats               # 다운로드 통계
GET    /api/stats/history       # 히스토리
```

### WebSocket

```yaml
# 연결
WS /ws/downloads

# 메시지 타입
- progress: 진행률 업데이트
- completed: 다운로드 완료
- failed: 다운로드 실패
- queue_update: 큐 상태 변경
```

## 파일 구조

```
pokergo_downloader/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI 앱
│   │   ├── config.py            # 설정
│   │   ├── database.py          # DB (기존 코드 재사용)
│   │   ├── models/
│   │   │   ├── video.py         # 비디오 모델
│   │   │   └── download.py      # 다운로드 모델
│   │   ├── routers/
│   │   │   ├── videos.py        # 영상 API
│   │   │   ├── downloads.py     # 다운로드 API
│   │   │   ├── settings.py      # 설정 API
│   │   │   └── websocket.py     # WebSocket
│   │   ├── services/
│   │   │   ├── scraper.py       # HLS 추출 (기존 코드)
│   │   │   ├── downloader.py    # 다운로드 (기존 코드)
│   │   │   └── queue.py         # 큐 관리
│   │   └── utils/
│   │       └── filename.py      # 파일명 처리
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── VideoList.tsx
│   │   │   ├── DownloadQueue.tsx
│   │   │   ├── Settings.tsx
│   │   │   └── Progress.tsx
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts
│   │   ├── stores/
│   │   │   └── downloadStore.ts
│   │   └── api/
│   │       └── client.ts
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Docker 배포

### docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
      - /path/to/downloads:/downloads
    environment:
      - DOWNLOAD_PATH=/downloads
      - DATABASE_PATH=/app/data/pokergo.db
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped
```

### 실행

```bash
# 빌드 및 실행
docker-compose up -d

# 접속
http://192.168.x.x:3000
```

## 마이그레이션 계획

### Phase 1: Backend 전환 (1주)

1. FastAPI 앱 구조 생성
2. 기존 `database.py` 재사용
3. 기존 `scraper.py` 재사용
4. 기존 다운로드 로직 재사용
5. REST API 구현
6. WebSocket 구현

### Phase 2: Frontend 개발 (1주)

1. React + Vite 프로젝트 생성
2. VideoList 컴포넌트
3. DownloadQueue 컴포넌트
4. Settings 컴포넌트
5. WebSocket 연동

### Phase 3: Docker 패키징 (2-3일)

1. Backend Dockerfile
2. Frontend Dockerfile
3. docker-compose.yml
4. 문서화

### Phase 4: 테스트 및 배포 (2-3일)

1. 로컬 테스트
2. NAS/서버 배포 테스트
3. 문서 완성

## 예상 이점

| 항목 | Desktop (현재) | Web App (목표) |
|------|---------------|---------------|
| 접근성 | PC만 | 모든 기기 (브라우저) |
| 24/7 운영 | 불가 | 가능 (서버) |
| 다중 사용자 | 불가 | 가능 |
| 원격 모니터링 | 불가 | 가능 |
| 배포 | 수동 설치 | Docker 원클릭 |

## 관련 문서

- [PRD-0012: PokerGO Downloader GUI](PRD-0012-POKERGO-DOWNLOADER-GUI.md) - 기존 Desktop 버전
- [PRD-0010: Dashboard](PRD-0010-DASHBOARD.md) - 유사 웹 아키텍처 참조
