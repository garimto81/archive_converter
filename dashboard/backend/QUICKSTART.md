# Quick Start Guide

Archive Dashboard Backend를 빠르게 시작하는 가이드입니다.

## 1분 안에 시작하기

```bash
# 1. 의존성 설치
pip install -e .

# 2. 서버 실행
python -m app.main
```

서버가 실행되면 http://localhost:8000 에서 접근 가능합니다.

## API 문서 확인

서버 실행 후 아래 주소에서 자동 생성된 API 문서를 확인하세요:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API 테스트

### 간단한 curl 테스트

```bash
# Health check
curl http://localhost:8000/health

# Matching matrix
curl http://localhost:8000/api/matching/matrix

# Stats
curl http://localhost:8000/api/matching/stats

# File segments
curl http://localhost:8000/api/matching/file/STREAM_01.mp4/segments

# NAS folders
curl http://localhost:8000/api/nas/folders

# NAS files
curl "http://localhost:8000/api/nas/files?path=/ARCHIVE/WSOP/STREAM"
```

### Python 테스트 스크립트

```bash
python test_api.py
```

## Mock 데이터 구조

백엔드는 현재 Mock 데이터로 동작합니다:

- **20개의 NAS 파일** (다양한 브랜드: WSOP, HCL, PAD, etc.)
- **123개의 세그먼트** (1:N 관계 - 파일당 1~15개 세그먼트)
- **다양한 상태**:
  - Complete (11개): 모든 세그먼트 변환 완료
  - Partial (5개): 일부만 변환됨
  - Warning (2개): 검증 이슈 있음
  - No Metadata (2개): 메타데이터 없음

## 주요 엔드포인트

### 1. Matching Matrix
```http
GET /api/matching/matrix?status=partial&search=STREAM
```

1:N 관계 매칭 현황 조회. 파일별 세그먼트 수와 변환 상태 확인.

### 2. Matching Stats
```http
GET /api/matching/stats
```

전체 통계:
- 소스별 통계 (NAS, Archive Metadata, Iconik Metadata)
- 파일/세그먼트 레벨 통계
- 커버리지 메트릭

### 3. File Segments
```http
GET /api/matching/file/{file_name}/segments
```

특정 파일의 모든 세그먼트 상세 조회 (1:N 관계).

### 4. NAS Folders
```http
GET /api/nas/folders
```

NAS 폴더 트리 구조 조회.

### 5. NAS Files
```http
GET /api/nas/files?path=/ARCHIVE/WSOP/STREAM
```

특정 폴더의 파일 목록 조회.

## 다음 단계

1. **Frontend 연동**: React 프론트엔드와 연결
2. **Database 연동**: PostgreSQL 스키마 구현
3. **Real Data**: 실제 NAS 스캐너 및 Google Sheets 연동
4. **Authentication**: API 인증 추가

## 포트 변경

기본 포트(8000)를 변경하려면:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 9000
```

## 개발 모드

자동 재시작을 원하면:

```bash
uvicorn app.main:app --reload
```

## 문제 해결

### 포트가 이미 사용 중

다른 포트를 사용하거나 기존 프로세스를 종료하세요:

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### 의존성 오류

```bash
pip install --upgrade pip
pip install -e . --force-reinstall
```

## Support

문제가 발생하면 GitHub Issues에 등록해주세요.
