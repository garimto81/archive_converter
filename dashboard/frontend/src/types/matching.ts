// Backend API 응답에 맞춘 타입 정의

// UDM 정보
export interface UdmInfo {
  uuid: string | null
  status: 'complete' | 'pending' | 'warning' | 'error'
}

// 세그먼트 레코드 (1:N 관계의 N)
export interface SegmentRecord {
  row_number: number
  source: 'archive_metadata' | 'iconik_metadata'
  time_in: string
  time_out: string
  time_in_sec: number
  time_out_sec: number
  duration_sec: number
  rating: number | null
  winner: string | null
  hands: string | null
  tags: string[]
  udm: UdmInfo
}

// NAS 파일 정보
export interface NasFileInfo {
  exists: boolean
  path: string
  size_mb: number
  duration_sec: number
  modified_at: string
  inferred_brand: string | null
}

// 검증 경고
export interface ValidationWarning {
  segment_row: number
  type: string
  message: string
}

// 매칭 아이템 (파일 레벨)
export interface MatchingItem {
  file_name: string
  nas: NasFileInfo | null
  segment_count: number
  udm_count: number
  segments: SegmentRecord[]
  status: 'complete' | 'partial' | 'warning' | 'pending' | 'no_metadata' | 'orphan'
  status_detail: string
  warnings: ValidationWarning[]
  is_expanded: boolean
}

// 소스별 통계
export interface SourceStats {
  total_files?: number
  total_records?: number
  unique_files?: number
  total_size_gb?: number
  scanned_at?: string
  synced_at?: string
}

// 매칭 통계
export interface MatchingStats {
  sources: {
    nas: SourceStats
    archive_metadata: SourceStats
    iconik_metadata: SourceStats
  }
  matching: {
    files: {
      complete: number
      partial: number
      warning: number
      unmatched: number
      total_with_metadata: number
    }
    segments: {
      complete: number
      pending: number
      warning: number
      total: number
    }
    orphan_records: number
  }
  coverage: {
    archive_to_nas: number
    iconik_to_nas: number
    nas_to_any_sheet: number
    segment_conversion_rate: number
  }
  summary: {
    avg_segments_per_file: number
    max_segments_per_file: number
    min_segments_per_file: number
  }
}

// 필터 옵션
export interface FilterOptions {
  status?: 'all' | 'complete' | 'partial' | 'warning' | 'pending' | 'no_metadata'
  searchQuery?: string
  sortBy?: 'file_name' | 'segment_count' | 'status'
  sortOrder?: 'asc' | 'desc'
}
