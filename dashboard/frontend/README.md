# Archive Converter Dashboard Frontend

React + Vite + TailwindCSS 기반의 분할 아카이브 매칭 대시보드 프론트엔드

## 기술 스택

- **React 18** - UI 라이브러리
- **TypeScript** - 타입 안정성
- **Vite** - 빌드 도구
- **TailwindCSS** - 유틸리티 CSS
- **React Query** - 서버 상태 관리
- **Zustand** - 클라이언트 상태 관리
- **React Router** - 라우팅
- **Lucide React** - 아이콘

## 주요 기능

### 1. 매칭 매트릭스 (메인 화면)
- 파일별 세그먼트 매칭 현황 테이블
- 파일 클릭 시 1:N 세그먼트 목록 확장
- 상태별 색상 표시
  - Complete: 녹색
  - Partial: 노란색
  - Warning: 주황색
  - Pending: 회색

### 2. 통계 카드
- 총 파일 수
- 완료된 파일
- 부분 매칭
- 대기 중
- 전체 매칭률 프로그레스 바

### 3. 필터 및 검색
- 파일명 검색
- 상태별 필터
- 정렬 (파일명, 매칭률, 등록일시)

### 4. 자동 새로고침
- 10초마다 자동 데이터 갱신
- 수동 새로고침 버튼

## 디렉토리 구조

```
src/
├── api/              # API 클라이언트
│   ├── client.ts     # fetch 기반 HTTP 클라이언트
│   └── matching.ts   # 매칭 API 함수
├── components/       # React 컴포넌트
│   ├── layout/       # 레이아웃 컴포넌트
│   │   ├── Header.tsx
│   │   └── Layout.tsx
│   └── matching/     # 매칭 관련 컴포넌트
│       ├── FileRow.tsx      # 파일 행 (확장 가능)
│       ├── SegmentList.tsx  # 세그먼트 목록
│       └── StatsCards.tsx   # 통계 카드
├── pages/            # 페이지 컴포넌트
│   └── MatchingMatrix.tsx
├── stores/           # Zustand 스토어
│   └── matchingStore.ts
├── types/            # TypeScript 타입
│   └── matching.ts
├── App.tsx           # 라우터 설정
├── main.tsx          # 진입점
└── index.css         # TailwindCSS
```

## 설치 및 실행

### 개발 환경

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# http://localhost:3000 접속
```

### 프로덕션 빌드

```bash
# 빌드
npm run build

# 미리보기
npm run preview
```

### Docker 실행

```bash
# 이미지 빌드
docker build -t archive-dashboard-frontend .

# 컨테이너 실행
docker run -p 3000:3000 archive-dashboard-frontend
```

## 환경 변수

`.env` 파일 생성 (`.env.example` 참고):

```env
VITE_API_URL=http://localhost:8000
VITE_PORT=3000
```

## API 엔드포인트

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/api/matching/matrix` | 매칭 매트릭스 조회 |
| GET | `/api/matching/stats` | 통계 조회 |
| GET | `/api/matching/files/:id/segments` | 파일별 세그먼트 조회 |

## 컴포넌트 사용 예시

### FileRow 컴포넌트

```tsx
// 파일 행 컴포넌트 - 클릭 시 세그먼트 확장
<FileRow
  item={matchingItem}
  isExpanded={expandedFiles.has(item.original_file_id)}
  onToggle={() => toggleFileExpansion(item.original_file_id)}
/>
```

### SegmentList 컴포넌트

```tsx
// 세그먼트 목록 - 파일 확장 시 표시
<SegmentList
  segments={item.segments}
  loading={false}
/>
```

### StatsCards 컴포넌트

```tsx
// 통계 카드 - 대시보드 상단
<StatsCards
  stats={matchingStats}
  loading={statsLoading}
/>
```

## 상태 관리 (Zustand)

```tsx
// Zustand 스토어 사용
const {
  items,           // 매칭 아이템 목록
  stats,           // 통계 데이터
  expandedFiles,   // 확장된 파일 ID Set
  filters,         // 필터 옵션
  toggleFileExpansion, // 파일 확장 토글
  setFilters,      // 필터 설정
} = useMatchingStore()
```

## 성능 최적화

1. **React Query 캐싱**
   - 5초 stale time
   - 10초 자동 갱신

2. **컴포넌트 메모이제이션**
   - 불필요한 리렌더링 방지

3. **코드 스플리팅**
   - React Router lazy loading 준비

4. **Tailwind JIT**
   - 사용된 클래스만 빌드

## 접근성 (A11y)

- 시맨틱 HTML 사용
- ARIA 레이블 적용
- 키보드 네비게이션 지원
- 색상 대비 WCAG AA 준수

## 브라우저 지원

- Chrome (최신)
- Firefox (최신)
- Safari (최신)
- Edge (최신)

## 라이센스

MIT
