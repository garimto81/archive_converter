import { apiGet } from './client'
import type { MatchingItem, MatchingStats, SegmentRecord } from '@/types/matching'

// 매칭 매트릭스 응답 타입
interface MatchingMatrixResponse {
  total_files: number
  total_segments: number
  matched_files: number
  matched_segments: number
  orphan_records: number
  unmatched_nas: number
  items: MatchingItem[]
}

// 매칭 매트릭스 조회
export async function fetchMatchingMatrix(): Promise<MatchingItem[]> {
  const response = await apiGet<MatchingMatrixResponse>('/api/matching/matrix')
  return response.items || []
}

// 매칭 통계 조회
export async function fetchMatchingStats(): Promise<MatchingStats> {
  return apiGet<MatchingStats>('/api/matching/stats')
}

// 특정 파일의 세그먼트 목록 조회
export async function fetchFileSegments(fileId: number): Promise<SegmentRecord[]> {
  return apiGet<SegmentRecord[]>(`/api/matching/files/${fileId}/segments`)
}

// 세그먼트 상태별 필터링
export async function fetchSegmentsByStatus(
  fileId: number,
  status: 'matched' | 'pending' | 'failed'
): Promise<SegmentRecord[]> {
  return apiGet<SegmentRecord[]>(`/api/matching/files/${fileId}/segments?status=${status}`)
}
