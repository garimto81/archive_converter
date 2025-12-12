import { apiGet, apiPost } from './client'

// 폴더 타입
export interface NasFolder {
  name: string
  path: string
  file_count: number
  folder_count: number
  children: NasFolder[]
}

// 폴더 트리 응답
interface NasFolderTreeResponse {
  root: NasFolder
}

// 스캔 결과 타입
export interface ScanResult {
  message: string
  mode: 'full' | 'incremental'
  total_files: number
  total_size_gb: number
  scan_duration_sec: number
  new_files: number
  modified_files: number
  brand_counts: Record<string, number>
}

// 스캔 상태 타입
export interface ScanStatus {
  last_scan: string | null
  cached_files: number
  is_cached: boolean
  nas_path: string
  nas_accessible: boolean
}

// 폴더 트리 조회
export async function fetchFolderTree(): Promise<NasFolder> {
  const response = await apiGet<NasFolderTreeResponse>('/api/nas/folders')
  return response.root
}

// 특정 폴더의 파일 목록 조회
export async function fetchFilesInFolder(path: string): Promise<{
  path: string
  total: number
  files: Array<{
    name: string
    path: string
    size_mb: number
    modified_at: string
    has_metadata: boolean
  }>
}> {
  return apiGet(`/api/nas/files?path=${encodeURIComponent(path)}`)
}

// NAS 스캔 상태 조회
export async function fetchScanStatus(): Promise<ScanStatus> {
  return apiGet('/api/nas/status')
}

// NAS 스캔 실행
export async function refreshNasScan(mode: 'full' | 'incremental' = 'full'): Promise<ScanResult> {
  return apiPost(`/api/nas/refresh?mode=${mode}`)
}
