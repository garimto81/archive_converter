/**
 * Pattern Matching API Client
 */

import { apiGet, apiPost } from './client'

// =============================================================================
// Types
// =============================================================================

export interface PatternInfo {
  name: string
  regex: string
  category: string
  match_count: number
  example_files: string[]
}

export interface PatternStats {
  total_files: number
  matched_files: number
  unmatched_files: number
  match_rate: number
  total_patterns: number
  avg_confidence: number
}

export interface PatternListResponse {
  patterns: PatternInfo[]
  total: number
}

export interface UnmatchedFile {
  file_name: string
  path: string | null
  reason: string
  suggested_category: string | null
}

export interface UnmatchedFilesResponse {
  total_unmatched: number
  percentage: number
  categories: Record<string, number>
  files: UnmatchedFile[]
}

export interface PatternMatchDetail {
  file_name: string
  matched: boolean
  pattern_name: string | null
  confidence: number
  extracted_fields: Record<string, string | number | null>
}

export interface PatternTestRequest {
  file_name: string
  regex?: string
}

export interface PatternTestResponse {
  success: boolean
  matched: boolean
  pattern_name: string | null
  extracted_groups: Record<string, string | number | null>
  error: string | null
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * 패턴 매칭 통계 조회
 */
export async function fetchPatternStats(): Promise<PatternStats> {
  return apiGet<PatternStats>('/api/pattern/stats')
}

/**
 * 전체 패턴 목록 조회
 */
export async function fetchPatternList(
  limit: number = 50,
  offset: number = 0
): Promise<PatternListResponse> {
  return apiGet<PatternListResponse>(`/api/pattern/list?limit=${limit}&offset=${offset}`)
}

/**
 * 미매칭 파일 목록 조회
 */
export async function fetchUnmatchedFiles(
  limit: number = 50,
  offset: number = 0
): Promise<UnmatchedFilesResponse> {
  return apiGet<UnmatchedFilesResponse>(`/api/pattern/unmatched?limit=${limit}&offset=${offset}`)
}

/**
 * 파일별 패턴 매칭 상세 조회
 */
export async function fetchFilePatternMatch(fileName: string): Promise<PatternMatchDetail> {
  return apiGet<PatternMatchDetail>(`/api/pattern/files/${encodeURIComponent(fileName)}/match`)
}

/**
 * 패턴 테스트
 */
export async function testPattern(request: PatternTestRequest): Promise<PatternTestResponse> {
  return apiPost<PatternTestResponse, PatternTestRequest>('/api/pattern/test', request)
}

/**
 * 패턴 캐시 갱신
 */
export async function refreshPatternCache(): Promise<{ status: string; message: string }> {
  return apiPost<{ status: string; message: string }>('/api/pattern/refresh')
}
