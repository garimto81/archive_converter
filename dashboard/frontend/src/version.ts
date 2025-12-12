/**
 * Dashboard Version Info
 * 버전 변경 시 이 파일만 수정하면 됨
 */

export const VERSION = '0.3.0'

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
