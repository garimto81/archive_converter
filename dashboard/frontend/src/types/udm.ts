/**
 * UDM (Unified Data Model) TypeScript Types
 * Based on PRD-0008-UDM-FINAL-SCHEMA.md v3.0.0
 */

// =============================================================================
// Enums
// =============================================================================

export type Brand =
  | 'WSOP'
  | 'WSOPC'
  | 'WSOPE'
  | 'WSOPP'
  | 'HCL'
  | 'PAD'
  | 'GGMillions'
  | 'MPP'
  | 'GOG'
  | 'WPT'
  | 'EPT'
  | 'OTHER'

export type EventType =
  | 'BRACELET'
  | 'CIRCUIT'
  | 'CASH_GAME_SHOW'
  | 'SUPER_MAIN'
  | 'ARCHIVE'
  | 'SIDE_EVENT'

export type AssetType =
  | 'STREAM'
  | 'SUBCLIP'
  | 'HAND_CLIP'
  | 'MASTER'
  | 'CLEAN'
  | 'NO_COMMENTARY'
  | 'RAW'
  | 'GENERIC'
  | 'MOV'
  | 'MXF'

export type GameVariant =
  | 'NLH'
  | 'PLO'
  | 'STUD'
  | 'RAZZ'
  | 'HORSE'
  | 'MIXED'
  | 'OMAHA_HI_LO'
  | '2-7_TD'
  | 'OTHER'

export type GameType = 'TOURNAMENT' | 'CASH_GAME'

export type SegmentType = 'HAND' | 'HIGHLIGHT' | 'PE' | 'INTRO' | 'COMMENTARY'

export type AllInStage = 'preflop' | 'flop' | 'turn' | 'river' | 'none'

// =============================================================================
// Supporting Models
// =============================================================================

export interface EventContext {
  year: number
  brand: Brand
  event_type?: EventType | null
  location?: string | null
  venue?: string | null
  event_number?: number | null
  buyin_usd?: number | null
  game_variant?: GameVariant | null
  is_high_roller?: boolean
  is_super_high_roller?: boolean
  is_final_table?: boolean
  season?: number | null
  episode?: number | null
  episode_title?: string | null
}

export interface TechSpec {
  fps?: number
  resolution?: string | null
  duration_sec?: number | null
  file_size_mb?: number | null
  codec?: string | null
}

export interface FileNameMeta {
  code_prefix?: string | null
  year_code?: string | null
  sequence_num?: number | null
  clip_type?: string | null
  raw_description?: string | null
}

export interface SituationFlags {
  is_cooler?: boolean
  is_badbeat?: boolean
  is_suckout?: boolean
  is_bluff?: boolean
  is_hero_call?: boolean
  is_hero_fold?: boolean
  is_river_killer?: boolean
}

export interface PlayerInHand {
  name: string
  hand?: string | null
  position?: string | null
  is_winner?: boolean
  chips_won?: number | null
}

// =============================================================================
// Level 2: Segment
// =============================================================================

export interface Segment {
  segment_uuid: string
  parent_asset_uuid: string
  segment_type: SegmentType
  time_in_sec: number
  time_out_sec: number
  duration_sec?: number
  title?: string | null
  game_type?: GameType
  rating?: number | null
  winner?: string | null
  winning_hand?: string | null
  losing_hand?: string | null
  players?: PlayerInHand[] | null
  tags_action?: string[] | null
  tags_emotion?: string[] | null
  tags_content?: string[] | null
  situation_flags?: SituationFlags | null
  all_in_stage?: AllInStage | null
  board?: string | null
  hand_tag?: string | null
  is_epic_hand?: boolean
  description?: string | null
}

// =============================================================================
// Level 1: Asset
// =============================================================================

export interface Asset {
  asset_uuid: string
  file_name: string
  file_path_rel?: string | null
  file_path_nas?: string | null
  asset_type: AssetType
  event_context: EventContext
  tech_spec?: TechSpec | null
  file_name_meta?: FileNameMeta | null
  source_origin: string
  created_at?: string | null
  last_modified?: string | null
  segments: Segment[]
}

// =============================================================================
// API Response Types
// =============================================================================

export interface UdmStats {
  total_assets: number
  total_segments: number
  by_brand: Record<string, number>
  by_asset_type: Record<string, number>
  by_year: Record<string, number>
}

export interface UdmFilters {
  brand?: string
  asset_type?: string
  year?: number
  search?: string
  hasSegments?: boolean
}

// =============================================================================
// Mock Data Helper
// =============================================================================

export const BRAND_COLORS: Record<string, string> = {
  WSOP: 'bg-red-100 text-red-800',
  WSOPC: 'bg-orange-100 text-orange-800',
  WSOPE: 'bg-blue-100 text-blue-800',
  WSOPP: 'bg-purple-100 text-purple-800',
  HCL: 'bg-yellow-100 text-yellow-800',
  PAD: 'bg-green-100 text-green-800',
  GGMillions: 'bg-cyan-100 text-cyan-800',
  MPP: 'bg-pink-100 text-pink-800',
  GOG: 'bg-indigo-100 text-indigo-800',
  WPT: 'bg-teal-100 text-teal-800',
  EPT: 'bg-emerald-100 text-emerald-800',
  OTHER: 'bg-gray-100 text-gray-800',
}

export const ASSET_TYPE_COLORS: Record<string, string> = {
  STREAM: 'bg-blue-100 text-blue-700',
  SUBCLIP: 'bg-green-100 text-green-700',
  HAND_CLIP: 'bg-purple-100 text-purple-700',
  MASTER: 'bg-yellow-100 text-yellow-700',
  CLEAN: 'bg-cyan-100 text-cyan-700',
  NO_COMMENTARY: 'bg-orange-100 text-orange-700',
  RAW: 'bg-gray-100 text-gray-700',
  GENERIC: 'bg-slate-100 text-slate-700',
  MOV: 'bg-rose-100 text-rose-700',
  MXF: 'bg-amber-100 text-amber-700',
}
