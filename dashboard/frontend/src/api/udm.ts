// UDM Viewer API
import { apiGet, apiPost } from './client'
import type {
  UdmDocumentResponse,
  UdmStats,
  UdmAssetDetail,
  UdmFilters,
} from '@/types/udm'

const API_PREFIX = '/api/v1/udm'

export async function fetchUdmDocument(
  filters?: UdmFilters
): Promise<UdmDocumentResponse> {
  const params = new URLSearchParams()

  if (filters?.brand) params.append('brand', filters.brand)
  if (filters?.asset_type) params.append('asset_type', filters.asset_type)
  if (filters?.year) params.append('year', String(filters.year))
  if (filters?.search) params.append('search', filters.search)

  const queryString = params.toString()
  const url = queryString ? `${API_PREFIX}?${queryString}` : API_PREFIX

  return apiGet<UdmDocumentResponse>(url)
}

export async function fetchUdmStats(): Promise<UdmStats> {
  return apiGet<UdmStats>(`${API_PREFIX}/stats`)
}

export async function fetchAssetDetail(
  assetUuid: string
): Promise<UdmAssetDetail> {
  return apiGet<UdmAssetDetail>(`${API_PREFIX}/assets/${assetUuid}`)
}

export async function fetchBrands(): Promise<{ brands: string[] }> {
  return apiGet<{ brands: string[] }>(`${API_PREFIX}/brands`)
}

export async function fetchAssetTypes(): Promise<{ asset_types: string[] }> {
  return apiGet<{ asset_types: string[] }>(`${API_PREFIX}/asset-types`)
}

export async function loadDemoData(): Promise<{
  success: boolean
  message: string
  total_assets: number
}> {
  return apiPost(`${API_PREFIX}/demo`)
}

export async function loadUdmFile(
  filePath: string
): Promise<{
  success: boolean
  message: string
  total_assets: number
}> {
  return apiPost(`${API_PREFIX}/load?file_path=${encodeURIComponent(filePath)}`)
}
