/**
 * Dashboard Version Info
 * 버전 변경 시 이 파일만 수정하면 됨
 */

export const VERSION = '0.5.1'

// Vite에서 주입하는 빌드 타임스탬프
declare const __BUILD_TIMESTAMP__: number
export const BUILD_TIMESTAMP = typeof __BUILD_TIMESTAMP__ !== 'undefined'
  ? __BUILD_TIMESTAMP__
  : Date.now()

export const BUILD_DATE = new Date(BUILD_TIMESTAMP).toISOString().split('T')[0]
export const BUILD_TIME = new Date(BUILD_TIMESTAMP).toLocaleTimeString('ko-KR')

export const CHANGELOG: Array<{
  version: string
  date: string
  changes: string[]
}> = [
  {
    version: '0.5.1',
    date: '2024-12-12',
    changes: [
      'NAS 스캔 → UDM 변환 API 연동',
      '/api/udm/from-nas 엔드포인트 추가',
      '/api/udm/assets/full 전체 데이터 API',
      '8개 열 그룹 (기본정보/이벤트/시즌/플래그/기술사양/파일명메타/시트연동/메타)',
      'NAS 스캔 버튼으로 실시간 데이터 로드',
      '전체 UDM 필드 파싱 (경로/파일명 기반)',
    ],
  },
  {
    version: '0.5.0',
    date: '2024-12-12',
    changes: [
      'UDM Matrix View 구현 (PRD-0012)',
      '행=파일, 열=UDM 필드 매트릭스 테이블',
      '6개 열 그룹 (기본정보/이벤트/시즌/플래그/기술사양/시트연동)',
      '열 그룹 접기/펼치기',
      '파일별 완성도 % 시각화',
      '필터링 (브랜드/연도/타입/Segments)',
      '행 클릭 시 상세 모달',
    ],
  },
  {
    version: '0.4.0',
    date: '2024-12-12',
    changes: [
      'UDM Viewer 재설계 (Split View)',
      'NAS 파일 → UDM 필드 파싱 현황 시각화',
      'UDM 스키마 전체 필드 매트릭스',
      '데이터 소스별 색상 구분',
      '파싱 완성도 % 표시',
    ],
  },
  {
    version: '0.3.0',
    date: '2024-12-12',
    changes: [
      'NAS 스캔 기능 추가 (Full/Incremental)',
      '통합 트리 뷰 (폴더+파일 하나로)',
      '버전 표시 추가',
    ],
  },
  {
    version: '0.2.0',
    date: '2024-12-12',
    changes: [
      'Split View 레이아웃 (폴더 트리 + 파일 테이블)',
      '폴더별 필터링',
      'SummaryBar 컴팩트 디자인',
    ],
  },
  {
    version: '0.1.0',
    date: '2024-12-11',
    changes: [
      '초기 대시보드 구현',
      'Matching Matrix 페이지',
      'NAS 실시간 연동',
    ],
  },
]

export const LATEST_CHANGES = CHANGELOG[0]?.changes || []
