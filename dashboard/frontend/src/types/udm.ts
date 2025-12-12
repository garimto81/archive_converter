// UDM JSON Viewer Types

export interface UdmMetadata {
  version: string
  generated_at: string
  source: string
  total_assets: number
  total_segments: number
}

export interface UdmAssetSummary {
  asset_uuid: string
  file_name: string
  file_path_nas?: string
  asset_type: string
  brand: string
  year: number
  season?: number
  episode?: number
  source_origin: string
  segment_count: number
}

export interface UdmDocumentResponse {
  metadata: UdmMetadata
  assets: UdmAssetSummary[]
}

export interface UdmStats {
  total_assets: number
  total_segments: number
  brand_distribution: Record<string, number>
  asset_type_distribution: Record<string, number>
  year_distribution: Record<string, number>
}

export interface UdmAssetDetail {
  asset_uuid: string
  file_name: string
  file_path_rel?: string
  file_path_nas?: string
  asset_type: string
  event_context: Record<string, unknown>
  tech_spec?: Record<string, unknown>
  file_name_meta?: Record<string, unknown>
  source_origin: string
  segments: Record<string, unknown>[]
  created_at?: string
}

export interface UdmFilters {
  brand?: string
  asset_type?: string
  year?: number
  search?: string
}
