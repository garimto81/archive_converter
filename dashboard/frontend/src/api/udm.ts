// UDM Viewer API - Real NAS Data Connection
import { apiGet, apiPost } from './client'
import type { Asset, Segment, UdmStats, UdmFilters } from '@/types/udm'

const API_PREFIX = '/api/udm'

// =============================================================================
// Flag: Use Mock Data or Real API
// =============================================================================

const USE_MOCK = false  // Set to false to use real NAS data

// =============================================================================
// Mock Data - 실제 포커 데이터 기반 (fallback)
// =============================================================================

const MOCK_SEGMENTS: Segment[] = [
  {
    segment_uuid: 'seg-001-aaaa',
    parent_asset_uuid: 'asset-001',
    segment_type: 'HAND',
    time_in_sec: 120,
    time_out_sec: 245,
    duration_sec: 125,
    title: 'Phil Ivey vs Tom Dwan - Epic Bluff',
    game_type: 'CASH_GAME',
    rating: 5,
    winner: 'Phil Ivey',
    winning_hand: 'High Card',
    losing_hand: 'Ace High',
    players: [
      { name: 'Phil Ivey', hand: '72o', position: 'BTN', is_winner: true },
      { name: 'Tom Dwan', hand: 'AKs', position: 'BB', is_winner: false },
    ],
    tags_action: ['bluff', 'hero-fold'],
    tags_emotion: ['brutal', 'insane'],
    situation_flags: { is_bluff: true, is_hero_fold: true },
    all_in_stage: 'river',
    board: 'Qh 8d 3c 7s 2d',
    hand_tag: '72o vs AKs',
    is_epic_hand: true,
  },
  {
    segment_uuid: 'seg-002-bbbb',
    parent_asset_uuid: 'asset-001',
    segment_type: 'HAND',
    time_in_sec: 500,
    time_out_sec: 620,
    duration_sec: 120,
    title: 'Garrett Adelstein vs Andy Stack - Cooler',
    game_type: 'CASH_GAME',
    rating: 4,
    winner: 'Andy Stack',
    winning_hand: 'Four of a Kind',
    losing_hand: 'Full House',
    players: [
      { name: 'Garrett Adelstein', hand: 'KK', position: 'CO', is_winner: false },
      { name: 'Andy Stack', hand: 'KK', position: 'BB', is_winner: true, chips_won: 150000 },
    ],
    tags_action: ['cooler', 'all-in'],
    tags_emotion: ['brutal'],
    situation_flags: { is_cooler: true },
    all_in_stage: 'flop',
    board: 'Kh Kd 5c 2s Ac',
    hand_tag: 'KK vs KK Cooler',
    is_epic_hand: true,
  },
  {
    segment_uuid: 'seg-003-cccc',
    parent_asset_uuid: 'asset-002',
    segment_type: 'HAND',
    time_in_sec: 1800,
    time_out_sec: 1920,
    duration_sec: 120,
    title: 'Main Event Final Table - AA vs KK',
    game_type: 'TOURNAMENT',
    rating: 5,
    winner: 'Daniel Negreanu',
    winning_hand: 'Pair of Aces',
    losing_hand: 'Pair of Kings',
    players: [
      { name: 'Daniel Negreanu', hand: 'AA', position: 'SB', is_winner: true, chips_won: 2500000 },
      { name: 'Phil Hellmuth', hand: 'KK', position: 'BTN', is_winner: false },
    ],
    tags_action: ['preflop-allin', 'classic'],
    tags_emotion: ['incredible'],
    situation_flags: { is_cooler: true },
    all_in_stage: 'preflop',
    board: 'Qc 7d 2h 5s 9c',
    hand_tag: 'AA vs KK',
    is_epic_hand: true,
  },
]

const MOCK_ASSETS: Asset[] = [
  {
    asset_uuid: 'asset-001',
    file_name: 'HCL_S15_EP01_Full_Stream.mp4',
    file_path_rel: 'HCL/2024/Season15/Episode01',
    file_path_nas: 'Z:\\ARCHIVE\\HCL\\2024\\Season15\\HCL_S15_EP01_Full_Stream.mp4',
    asset_type: 'STREAM',
    event_context: {
      year: 2024,
      brand: 'HCL',
      event_type: 'CASH_GAME_SHOW',
      location: 'Los Angeles',
      venue: 'Hustler Casino',
      season: 15,
      episode: 1,
      episode_title: 'Season 15 Premiere',
    },
    tech_spec: {
      fps: 29.97,
      resolution: '1080p',
      duration_sec: 14400,
      file_size_mb: 8500,
      codec: 'H.264',
    },
    source_origin: 'NAS_HCL_2024',
    created_at: '2024-01-15T00:00:00Z',
    segments: MOCK_SEGMENTS.filter((s) => s.parent_asset_uuid === 'asset-001'),
  },
  {
    asset_uuid: 'asset-002',
    file_name: 'WSOP_2024_MainEvent_FinalTable_Day9.mp4',
    file_path_rel: 'WSOP/2024/MainEvent/FinalTable',
    file_path_nas: 'Z:\\ARCHIVE\\WSOP\\2024\\MainEvent\\WSOP_2024_MainEvent_FinalTable_Day9.mp4',
    asset_type: 'STREAM',
    event_context: {
      year: 2024,
      brand: 'WSOP',
      event_type: 'BRACELET',
      location: 'Las Vegas',
      venue: 'Horseshoe Casino',
      event_number: 76,
      buyin_usd: 10000,
      game_variant: 'NLH',
      is_final_table: true,
    },
    tech_spec: {
      fps: 59.94,
      resolution: '4K',
      duration_sec: 28800,
      file_size_mb: 45000,
      codec: 'H.265',
    },
    source_origin: 'NAS_WSOP_2024',
    created_at: '2024-07-17T00:00:00Z',
    segments: MOCK_SEGMENTS.filter((s) => s.parent_asset_uuid === 'asset-002'),
  },
  {
    asset_uuid: 'asset-003',
    file_name: 'PAD_S14_EP05_Phil_vs_Negreanu.mp4',
    file_path_rel: 'PAD/2024/Season14/Episode05',
    file_path_nas: 'Z:\\ARCHIVE\\PAD\\2024\\Season14\\PAD_S14_EP05_Phil_vs_Negreanu.mp4',
    asset_type: 'SUBCLIP',
    event_context: {
      year: 2024,
      brand: 'PAD',
      event_type: 'CASH_GAME_SHOW',
      location: 'Las Vegas',
      venue: 'PokerGO Studio',
      season: 14,
      episode: 5,
      episode_title: 'Legends Clash',
      game_variant: 'NLH',
    },
    tech_spec: {
      fps: 29.97,
      resolution: '1080p',
      duration_sec: 3600,
      file_size_mb: 2100,
    },
    source_origin: 'NAS_PAD_2024',
    created_at: '2024-03-20T00:00:00Z',
    segments: [],
  },
  {
    asset_uuid: 'asset-004',
    file_name: 'WSOPP_2024_50K_SHR_Day3.mp4',
    file_path_rel: 'WSOPP/2024/SuperHighRoller',
    file_path_nas: 'Z:\\ARCHIVE\\WSOPP\\2024\\50K_SHR\\WSOPP_2024_50K_SHR_Day3.mp4',
    asset_type: 'STREAM',
    event_context: {
      year: 2024,
      brand: 'WSOPP',
      event_type: 'BRACELET',
      location: 'Paradise',
      venue: 'Atlantis Resort',
      event_number: 5,
      buyin_usd: 50000,
      game_variant: 'NLH',
      is_super_high_roller: true,
      is_final_table: true,
    },
    tech_spec: {
      fps: 59.94,
      resolution: '4K',
      duration_sec: 18000,
      file_size_mb: 28000,
    },
    source_origin: 'NAS_WSOPP_2024',
    created_at: '2024-01-10T00:00:00Z',
    segments: [],
  },
  {
    asset_uuid: 'asset-005',
    file_name: 'GGMillions_2024_250K_Final.mp4',
    file_path_rel: 'GGMillions/2024/250K',
    file_path_nas: 'Z:\\ARCHIVE\\GGMillions\\2024\\250K\\GGMillions_2024_250K_Final.mp4',
    asset_type: 'MASTER',
    event_context: {
      year: 2024,
      brand: 'GGMillions',
      event_type: 'SUPER_MAIN',
      location: 'Cyprus',
      venue: 'Merit Royal',
      buyin_usd: 250000,
      game_variant: 'NLH',
      is_super_high_roller: true,
      is_final_table: true,
    },
    tech_spec: {
      fps: 59.94,
      resolution: '4K',
      duration_sec: 12000,
      file_size_mb: 18000,
    },
    source_origin: 'NAS_GG_2024',
    created_at: '2024-05-15T00:00:00Z',
    segments: [],
  },
  {
    asset_uuid: 'asset-006',
    file_name: 'MPP_2025_Mystery_Bounty_Day1A.mp4',
    file_path_rel: 'MPP/2025/MysteryBounty',
    file_path_nas: 'Z:\\ARCHIVE\\MPP\\2025\\MysteryBounty\\MPP_2025_Mystery_Bounty_Day1A.mp4',
    asset_type: 'SUBCLIP',
    event_context: {
      year: 2025,
      brand: 'MPP',
      event_type: 'CIRCUIT',
      location: 'Europe',
      buyin_usd: 1000,
      game_variant: 'NLH',
    },
    source_origin: 'NAS_MPP_2025',
    created_at: '2025-01-05T00:00:00Z',
    segments: [],
  },
  {
    asset_uuid: 'asset-007',
    file_name: 'WPT_2024_Championship_Final.mp4',
    file_path_rel: 'WPT/2024/Championship',
    file_path_nas: 'Z:\\ARCHIVE\\WPT\\2024\\Championship\\WPT_2024_Championship_Final.mp4',
    asset_type: 'STREAM',
    event_context: {
      year: 2024,
      brand: 'WPT',
      event_type: 'BRACELET',
      location: 'Las Vegas',
      venue: 'Wynn Las Vegas',
      buyin_usd: 10000,
      game_variant: 'NLH',
      is_final_table: true,
    },
    tech_spec: {
      fps: 59.94,
      resolution: '4K',
      duration_sec: 21600,
      file_size_mb: 32000,
    },
    source_origin: 'NAS_WPT_2024',
    created_at: '2024-12-20T00:00:00Z',
    segments: [],
  },
  {
    asset_uuid: 'asset-008',
    file_name: 'EPT_2024_Barcelona_Main_Day5.mp4',
    file_path_rel: 'EPT/2024/Barcelona',
    file_path_nas: 'Z:\\ARCHIVE\\EPT\\2024\\Barcelona\\EPT_2024_Barcelona_Main_Day5.mp4',
    asset_type: 'STREAM',
    event_context: {
      year: 2024,
      brand: 'EPT',
      event_type: 'BRACELET',
      location: 'Europe',
      venue: 'Casino Barcelona',
      buyin_usd: 5000,
      game_variant: 'NLH',
      is_final_table: true,
    },
    tech_spec: {
      fps: 50,
      resolution: '1080p',
      duration_sec: 25200,
      file_size_mb: 15000,
    },
    source_origin: 'NAS_EPT_2024',
    created_at: '2024-08-25T00:00:00Z',
    segments: [],
  },
]

function calculateMockStats(): UdmStats {
  const by_brand: Record<string, number> = {}
  const by_asset_type: Record<string, number> = {}
  const by_year: Record<string, number> = {}

  for (const asset of MOCK_ASSETS) {
    const brand = asset.event_context.brand
    by_brand[brand] = (by_brand[brand] || 0) + 1

    by_asset_type[asset.asset_type] = (by_asset_type[asset.asset_type] || 0) + 1

    const year = asset.event_context.year.toString()
    by_year[year] = (by_year[year] || 0) + 1
  }

  return {
    total_assets: MOCK_ASSETS.length,
    total_segments: MOCK_SEGMENTS.length,
    by_brand,
    by_asset_type,
    by_year,
  }
}

function filterMockAssets(filters?: UdmFilters): Asset[] {
  let filtered = [...MOCK_ASSETS]

  if (filters?.brand) {
    filtered = filtered.filter((a) => a.event_context.brand === filters.brand)
  }

  if (filters?.asset_type) {
    filtered = filtered.filter((a) => a.asset_type === filters.asset_type)
  }

  if (filters?.year) {
    filtered = filtered.filter((a) => a.event_context.year === filters.year)
  }

  if (filters?.search) {
    const query = filters.search.toLowerCase()
    filtered = filtered.filter(
      (a) =>
        a.file_name.toLowerCase().includes(query) ||
        a.event_context.brand.toLowerCase().includes(query) ||
        a.source_origin.toLowerCase().includes(query)
    )
  }

  if (filters?.hasSegments) {
    filtered = filtered.filter((a) => a.segments.length > 0)
  }

  return filtered
}

// =============================================================================
// API Functions with Mock Fallback
// =============================================================================

export interface UdmDocumentResponse {
  metadata: {
    version: string
    generated_at: string
    source: string
    total_assets: number
    total_segments: number
  }
  assets: Asset[]
}

export async function fetchUdmAssets(filters?: UdmFilters): Promise<Asset[]> {
  if (USE_MOCK) {
    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 300))
    return filterMockAssets(filters)
  }

  // Build query params
  const params = new URLSearchParams()
  if (filters?.brand) params.append('brand', filters.brand)
  if (filters?.asset_type) params.append('asset_type', filters.asset_type)
  if (filters?.year) params.append('year', String(filters.year))
  if (filters?.search) params.append('search', filters.search)
  if (filters?.hasSegments) params.append('has_segments', 'true')

  const queryString = params.toString()
  const url = queryString ? `${API_PREFIX}/assets/full?${queryString}` : `${API_PREFIX}/assets/full`

  // Fetch full asset data
  const response = await apiGet<{
    total: number
    filtered: number
    assets: Asset[]
  }>(url)

  return response.assets
}

export async function fetchUdmDocument(filters?: UdmFilters): Promise<UdmDocumentResponse> {
  if (USE_MOCK) {
    await new Promise((resolve) => setTimeout(resolve, 300))
    const assets = filterMockAssets(filters)
    return {
      metadata: {
        version: '3.0.0',
        generated_at: new Date().toISOString(),
        source: 'MOCK_DATA',
        total_assets: assets.length,
        total_segments: assets.reduce((sum, a) => sum + a.segments.length, 0),
      },
      assets,
    }
  }

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
  if (USE_MOCK) {
    await new Promise((resolve) => setTimeout(resolve, 200))
    return calculateMockStats()
  }

  // Get stats from real API
  const response = await apiGet<{
    total_assets: number
    total_segments: number
    brand_distribution: Record<string, number>
    asset_type_distribution: Record<string, number>
    year_distribution: Record<string, number>
  }>(`${API_PREFIX}/stats`)

  return {
    total_assets: response.total_assets,
    total_segments: response.total_segments,
    by_brand: response.brand_distribution,
    by_asset_type: response.asset_type_distribution,
    by_year: response.year_distribution,
  }
}

/**
 * NAS 파일을 스캔하여 UDM으로 로드
 */
export async function loadFromNas(): Promise<{
  success: boolean
  message: string
  total_assets: number
}> {
  return apiPost(`${API_PREFIX}/from-nas`)
}

export async function fetchAssetDetail(assetUuid: string): Promise<Asset | null> {
  if (USE_MOCK) {
    await new Promise((resolve) => setTimeout(resolve, 200))
    return MOCK_ASSETS.find((a) => a.asset_uuid === assetUuid) || null
  }

  return apiGet<Asset>(`${API_PREFIX}/assets/${assetUuid}`)
}

export async function fetchBrands(): Promise<{ brands: string[] }> {
  if (USE_MOCK) {
    const stats = calculateMockStats()
    return { brands: Object.keys(stats.by_brand).sort() }
  }

  return apiGet<{ brands: string[] }>(`${API_PREFIX}/brands`)
}

export async function fetchAssetTypes(): Promise<{ asset_types: string[] }> {
  if (USE_MOCK) {
    const stats = calculateMockStats()
    return { asset_types: Object.keys(stats.by_asset_type).sort() }
  }

  return apiGet<{ asset_types: string[] }>(`${API_PREFIX}/asset-types`)
}

export async function loadDemoData(): Promise<{
  success: boolean
  message: string
  total_assets: number
}> {
  return apiPost(`${API_PREFIX}/demo`)
}

export async function loadUdmFile(filePath: string): Promise<{
  success: boolean
  message: string
  total_assets: number
}> {
  return apiPost(`${API_PREFIX}/load?file_path=${encodeURIComponent(filePath)}`)
}

// Export mock data for testing
export { MOCK_ASSETS, MOCK_SEGMENTS }
