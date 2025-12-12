/**
 * UDM Schema Definition for Field Matrix Visualization
 * 전체 UDM 스키마 구조와 필드 메타데이터 정의
 */

export interface UdmFieldMeta {
  key: string
  label: string
  type: 'string' | 'number' | 'boolean' | 'date' | 'array' | 'object' | 'enum'
  required: boolean
  source: 'nas_path' | 'nas_filename' | 'sheet' | 'manual' | 'computed'
  description?: string
  enumValues?: string[]
  children?: UdmFieldMeta[]
}

// =============================================================================
// Asset Schema Definition
// =============================================================================

export const ASSET_SCHEMA: UdmFieldMeta[] = [
  // === 식별자 ===
  {
    key: 'asset_uuid',
    label: 'Asset UUID',
    type: 'string',
    required: true,
    source: 'computed',
    description: '파일 해시 기반 UUID',
  },

  // === 파일 정보 ===
  {
    key: 'file_name',
    label: '파일명',
    type: 'string',
    required: true,
    source: 'nas_filename',
    description: '확장자 포함 파일명',
  },
  {
    key: 'file_path_rel',
    label: '상대 경로',
    type: 'string',
    required: false,
    source: 'nas_path',
    description: 'NAS 상대 경로',
  },
  {
    key: 'file_path_nas',
    label: 'NAS 전체 경로',
    type: 'string',
    required: false,
    source: 'nas_path',
    description: '전체 NAS 경로',
  },

  // === Asset 유형 ===
  {
    key: 'asset_type',
    label: 'Asset Type',
    type: 'enum',
    required: false,
    source: 'nas_path',
    description: 'Asset 유형 (폴더 구조 기반)',
    enumValues: ['STREAM', 'SUBCLIP', 'HAND_CLIP', 'MASTER', 'CLEAN', 'NO_COMMENTARY', 'RAW', 'GENERIC', 'MOV', 'MXF'],
  },

  // === Event Context (중첩) ===
  {
    key: 'event_context',
    label: 'Event Context',
    type: 'object',
    required: true,
    source: 'nas_path',
    description: '이벤트 컨텍스트 정보',
    children: [
      { key: 'year', label: '연도', type: 'number', required: true, source: 'nas_path', description: '개최 연도' },
      {
        key: 'brand',
        label: '브랜드',
        type: 'enum',
        required: true,
        source: 'nas_path',
        description: '브랜드 (WSOP, HCL, PAD 등)',
        enumValues: ['WSOP', 'WSOPC', 'WSOPE', 'WSOPP', 'HCL', 'PAD', 'GGMillions', 'MPP', 'GOG', 'WPT', 'EPT', 'OTHER'],
      },
      {
        key: 'event_type',
        label: '이벤트 타입',
        type: 'enum',
        required: false,
        source: 'nas_path',
        enumValues: ['BRACELET', 'CIRCUIT', 'CASH_GAME_SHOW', 'SUPER_MAIN', 'ARCHIVE', 'SIDE_EVENT'],
      },
      { key: 'location', label: '장소', type: 'string', required: false, source: 'nas_path' },
      { key: 'venue', label: '상세 장소', type: 'string', required: false, source: 'manual' },
      { key: 'event_number', label: '이벤트 번호', type: 'number', required: false, source: 'nas_filename' },
      { key: 'buyin_usd', label: '바이인 (USD)', type: 'number', required: false, source: 'nas_filename' },
      {
        key: 'game_variant',
        label: '게임 종류',
        type: 'enum',
        required: false,
        source: 'nas_filename',
        enumValues: ['NLH', 'PLO', 'STUD', 'RAZZ', 'HORSE', 'MIXED', 'OMAHA_HI_LO', '2-7_TD', 'OTHER'],
      },
      { key: 'is_high_roller', label: '하이롤러', type: 'boolean', required: false, source: 'nas_filename' },
      { key: 'is_super_high_roller', label: '슈퍼 하이롤러', type: 'boolean', required: false, source: 'nas_filename' },
      { key: 'is_final_table', label: '파이널 테이블', type: 'boolean', required: false, source: 'nas_filename' },
      { key: 'season', label: '시즌', type: 'number', required: false, source: 'nas_filename' },
      { key: 'episode', label: '에피소드', type: 'number', required: false, source: 'nas_filename' },
      { key: 'episode_title', label: '에피소드 제목', type: 'string', required: false, source: 'sheet' },
    ],
  },

  // === Tech Spec (중첩) ===
  {
    key: 'tech_spec',
    label: 'Tech Spec',
    type: 'object',
    required: false,
    source: 'nas_filename',
    description: '기술 사양',
    children: [
      { key: 'fps', label: 'FPS', type: 'number', required: false, source: 'manual' },
      { key: 'resolution', label: '해상도', type: 'string', required: false, source: 'manual' },
      { key: 'duration_sec', label: '재생 시간 (초)', type: 'number', required: false, source: 'computed' },
      { key: 'file_size_mb', label: '파일 크기 (MB)', type: 'number', required: false, source: 'nas_path' },
      { key: 'codec', label: '코덱', type: 'string', required: false, source: 'manual' },
    ],
  },

  // === File Name Meta (중첩) ===
  {
    key: 'file_name_meta',
    label: 'File Name Meta',
    type: 'object',
    required: false,
    source: 'nas_filename',
    description: '파일명에서 추출된 메타데이터',
    children: [
      { key: 'code_prefix', label: '코드 접두사', type: 'string', required: false, source: 'nas_filename' },
      { key: 'year_code', label: '연도 코드', type: 'string', required: false, source: 'nas_filename' },
      { key: 'sequence_num', label: '시퀀스 번호', type: 'number', required: false, source: 'nas_filename' },
      { key: 'clip_type', label: '클립 타입', type: 'string', required: false, source: 'nas_filename' },
      { key: 'raw_description', label: '설명', type: 'string', required: false, source: 'nas_filename' },
    ],
  },

  // === Google Sheets 필드 ===
  { key: 'file_number', label: '파일 순번', type: 'number', required: false, source: 'sheet' },
  { key: 'tournament_name', label: '토너먼트명', type: 'string', required: false, source: 'sheet' },
  { key: 'project_name_tag', label: '프로젝트 태그', type: 'string', required: false, source: 'sheet' },
  { key: 'nas_folder_link', label: 'NAS 폴더 링크', type: 'string', required: false, source: 'sheet' },

  // === 메타 ===
  { key: 'source_origin', label: '데이터 출처', type: 'string', required: true, source: 'computed' },
  { key: 'created_at', label: '생성 시간', type: 'date', required: false, source: 'nas_path' },
  { key: 'last_modified', label: '최종 수정', type: 'date', required: false, source: 'nas_path' },

  // === Segments ===
  {
    key: 'segments',
    label: 'Segments',
    type: 'array',
    required: false,
    source: 'sheet',
    description: '포함된 Segment 목록',
  },
]

// =============================================================================
// Segment Schema Definition
// =============================================================================

export const SEGMENT_SCHEMA: UdmFieldMeta[] = [
  { key: 'segment_uuid', label: 'Segment UUID', type: 'string', required: true, source: 'computed' },
  { key: 'parent_asset_uuid', label: 'Parent Asset UUID', type: 'string', required: true, source: 'computed' },
  {
    key: 'segment_type',
    label: 'Segment Type',
    type: 'enum',
    required: false,
    source: 'sheet',
    enumValues: ['HAND', 'HIGHLIGHT', 'PE', 'INTRO', 'COMMENTARY'],
  },
  { key: 'time_in_sec', label: '시작 시간 (초)', type: 'number', required: true, source: 'sheet' },
  { key: 'time_out_sec', label: '종료 시간 (초)', type: 'number', required: true, source: 'sheet' },
  { key: 'title', label: '제목', type: 'string', required: false, source: 'sheet' },
  {
    key: 'game_type',
    label: '게임 타입',
    type: 'enum',
    required: false,
    source: 'sheet',
    enumValues: ['TOURNAMENT', 'CASH_GAME'],
  },
  { key: 'rating', label: '별점', type: 'number', required: false, source: 'sheet' },
  { key: 'winner', label: '승자', type: 'string', required: false, source: 'sheet' },
  { key: 'winning_hand', label: '승리 패', type: 'string', required: false, source: 'sheet' },
  { key: 'losing_hand', label: '패배 패', type: 'string', required: false, source: 'sheet' },
  { key: 'players', label: '플레이어', type: 'array', required: false, source: 'sheet' },
  { key: 'tags_action', label: '액션 태그', type: 'array', required: false, source: 'sheet' },
  { key: 'tags_emotion', label: '감정 태그', type: 'array', required: false, source: 'sheet' },
  { key: 'tags_content', label: '콘텐츠 태그', type: 'array', required: false, source: 'sheet' },
  {
    key: 'situation_flags',
    label: '상황 플래그',
    type: 'object',
    required: false,
    source: 'sheet',
    children: [
      { key: 'is_cooler', label: '쿨러', type: 'boolean', required: false, source: 'sheet' },
      { key: 'is_badbeat', label: '배드비트', type: 'boolean', required: false, source: 'sheet' },
      { key: 'is_suckout', label: '석아웃', type: 'boolean', required: false, source: 'sheet' },
      { key: 'is_bluff', label: '블러프', type: 'boolean', required: false, source: 'sheet' },
      { key: 'is_hero_call', label: '히어로 콜', type: 'boolean', required: false, source: 'sheet' },
      { key: 'is_hero_fold', label: '히어로 폴드', type: 'boolean', required: false, source: 'sheet' },
      { key: 'is_river_killer', label: '리버 킬러', type: 'boolean', required: false, source: 'sheet' },
    ],
  },
  {
    key: 'all_in_stage',
    label: '올인 스테이지',
    type: 'enum',
    required: false,
    source: 'sheet',
    enumValues: ['preflop', 'flop', 'turn', 'river', 'none'],
  },
  { key: 'board', label: '보드', type: 'string', required: false, source: 'sheet' },
  { key: 'hand_tag', label: '핸드 태그', type: 'string', required: false, source: 'sheet' },
  { key: 'is_epic_hand', label: '에픽 핸드', type: 'boolean', required: false, source: 'sheet' },
  { key: 'description', label: '설명', type: 'string', required: false, source: 'sheet' },
]

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * 전체 필드 개수 계산 (중첩 포함)
 */
export function countTotalFields(schema: UdmFieldMeta[]): number {
  let count = 0
  for (const field of schema) {
    count += 1
    if (field.children) {
      count += countTotalFields(field.children)
    }
  }
  return count
}

/**
 * 데이터에서 파싱된 필드 개수 계산
 */
export function countParsedFields(schema: UdmFieldMeta[], data: Record<string, unknown>): number {
  let count = 0
  for (const field of schema) {
    const value = data[field.key]
    if (hasValue(value)) {
      if (field.children && typeof value === 'object' && value !== null) {
        count += countParsedFields(field.children, value as Record<string, unknown>)
      } else {
        count += 1
      }
    }
  }
  return count
}

/**
 * 값이 있는지 확인 (null, undefined, 빈 문자열, 빈 배열 제외)
 */
export function hasValue(value: unknown): boolean {
  if (value === null || value === undefined) return false
  if (typeof value === 'string' && value.trim() === '') return false
  if (Array.isArray(value) && value.length === 0) return false
  return true
}

/**
 * 소스별 색상
 */
export const SOURCE_COLORS: Record<string, string> = {
  nas_path: 'bg-blue-100 text-blue-700',
  nas_filename: 'bg-green-100 text-green-700',
  sheet: 'bg-purple-100 text-purple-700',
  manual: 'bg-orange-100 text-orange-700',
  computed: 'bg-gray-100 text-gray-700',
}

/**
 * 소스별 라벨
 */
export const SOURCE_LABELS: Record<string, string> = {
  nas_path: 'NAS 경로',
  nas_filename: 'NAS 파일명',
  sheet: 'Sheet',
  manual: '수동',
  computed: '자동',
}

// =============================================================================
// Column Groups for Matrix View
// =============================================================================

export interface ColumnGroup {
  id: string
  label: string
  icon: string
  fields: string[]
  defaultExpanded: boolean
}

/**
 * 매트릭스 뷰 열 그룹 정의
 * PRD-0012 기반 - 전체 UDM 필드 포함
 */
export const COLUMN_GROUPS: ColumnGroup[] = [
  {
    id: 'basic',
    label: '기본정보',
    icon: '📁',
    fields: [
      'asset_uuid',
      'file_name',
      'file_path_rel',
      'file_path_nas',
      'asset_type',
      'source_origin',
    ],
    defaultExpanded: true,
  },
  {
    id: 'event',
    label: '이벤트',
    icon: '🎬',
    fields: [
      'event_context.brand',
      'event_context.year',
      'event_context.event_type',
      'event_context.location',
      'event_context.venue',
      'event_context.event_number',
      'event_context.buyin_usd',
      'event_context.game_variant',
    ],
    defaultExpanded: true,
  },
  {
    id: 'season',
    label: '시즌',
    icon: '📺',
    fields: [
      'event_context.season',
      'event_context.episode',
      'event_context.episode_title',
    ],
    defaultExpanded: false,
  },
  {
    id: 'flags',
    label: '플래그',
    icon: '🎯',
    fields: [
      'event_context.is_final_table',
      'event_context.is_high_roller',
      'event_context.is_super_high_roller',
    ],
    defaultExpanded: false,
  },
  {
    id: 'tech',
    label: '기술사양',
    icon: '⚙️',
    fields: [
      'tech_spec.fps',
      'tech_spec.resolution',
      'tech_spec.duration_sec',
      'tech_spec.file_size_mb',
      'tech_spec.codec',
    ],
    defaultExpanded: false,
  },
  {
    id: 'filename_meta',
    label: '파일명 메타',
    icon: '📄',
    fields: [
      'file_name_meta.code_prefix',
      'file_name_meta.year_code',
      'file_name_meta.sequence_num',
      'file_name_meta.clip_type',
      'file_name_meta.raw_description',
    ],
    defaultExpanded: false,
  },
  {
    id: 'sheet',
    label: '시트연동',
    icon: '📝',
    fields: [
      'file_number',
      'tournament_name',
      'project_name_tag',
      'nas_folder_link',
      'segments',
    ],
    defaultExpanded: false,
  },
  {
    id: 'meta',
    label: '메타',
    icon: '🕐',
    fields: [
      'created_at',
      'last_modified',
    ],
    defaultExpanded: false,
  },
]

/**
 * 중첩 경로에서 값 추출 (예: 'event_context.brand')
 */
export function getNestedValue(obj: Record<string, unknown>, path: string): unknown {
  const parts = path.split('.')
  let current: unknown = obj
  for (const part of parts) {
    if (current === null || current === undefined) return undefined
    if (typeof current !== 'object') return undefined
    current = (current as Record<string, unknown>)[part]
  }
  return current
}

/**
 * 필드 라벨 가져오기
 */
export function getFieldLabel(fieldPath: string): string {
  // 중첩 경로 처리
  const parts = fieldPath.split('.')
  const lastPart = parts[parts.length - 1]

  // ASSET_SCHEMA에서 찾기
  const findLabel = (schema: UdmFieldMeta[], path: string[]): string | null => {
    for (const field of schema) {
      if (field.key === path[0]) {
        if (path.length === 1) return field.label
        if (field.children && path.length > 1) {
          return findLabel(field.children, path.slice(1))
        }
      }
    }
    return null
  }

  return findLabel(ASSET_SCHEMA, parts) || lastPart
}

/**
 * 필드 소스 가져오기
 */
export function getFieldSource(fieldPath: string): string {
  const parts = fieldPath.split('.')

  const findSource = (schema: UdmFieldMeta[], path: string[]): string | null => {
    for (const field of schema) {
      if (field.key === path[0]) {
        if (path.length === 1) return field.source
        if (field.children && path.length > 1) {
          return findSource(field.children, path.slice(1))
        }
      }
    }
    return null
  }

  return findSource(ASSET_SCHEMA, parts) || 'computed'
}
