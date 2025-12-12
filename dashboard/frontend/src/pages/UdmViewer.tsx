import { useState, useMemo, useCallback, useRef, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  ChevronDown,
  ChevronRight,
  Check,
  Minus,
  AlertCircle,
  RefreshCw,
  Search,
  Filter,
  Download,
  Layers,
} from 'lucide-react'
import { fetchUdmAssets, fetchUdmStats, loadFromNas } from '@/api/udm'
import {
  COLUMN_GROUPS,
  getNestedValue,
  getFieldLabel,
  getFieldSource,
  hasValue,
  SOURCE_COLORS,
  type ColumnGroup,
} from '@/types/udm-schema'
import type { Asset, UdmFilters } from '@/types/udm'

// =============================================================================
// Types
// =============================================================================

interface ExpandedGroups {
  [groupId: string]: boolean
}

// =============================================================================
// FilterBar Component
// =============================================================================

interface FilterBarProps {
  filters: UdmFilters
  onFilterChange: (filters: UdmFilters) => void
  onRefresh: () => void
  brands: string[]
  assetTypes: string[]
  years: number[]
}

function FilterBar({ filters, onFilterChange, onRefresh, brands, assetTypes, years }: FilterBarProps) {
  return (
    <div className="flex items-center gap-3 px-4 py-2 bg-white border-b border-gray-200">
      <Filter className="w-4 h-4 text-gray-400" />

      {/* Brand Filter */}
      <select
        className="px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        value={filters.brand || ''}
        onChange={(e) => onFilterChange({ ...filters, brand: e.target.value || undefined })}
      >
        <option value="">All Brands</option>
        {brands.map((b) => (
          <option key={b} value={b}>
            {b}
          </option>
        ))}
      </select>

      {/* Year Filter */}
      <select
        className="px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        value={filters.year || ''}
        onChange={(e) => onFilterChange({ ...filters, year: e.target.value ? Number(e.target.value) : undefined })}
      >
        <option value="">All Years</option>
        {years.map((y) => (
          <option key={y} value={y}>
            {y}
          </option>
        ))}
      </select>

      {/* Asset Type Filter */}
      <select
        className="px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        value={filters.asset_type || ''}
        onChange={(e) => onFilterChange({ ...filters, asset_type: e.target.value || undefined })}
      >
        <option value="">All Types</option>
        {assetTypes.map((t) => (
          <option key={t} value={t}>
            {t}
          </option>
        ))}
      </select>

      {/* Segments Filter */}
      <label className="flex items-center gap-1 text-sm text-gray-600 cursor-pointer">
        <input
          type="checkbox"
          className="rounded border-gray-300"
          checked={filters.hasSegments || false}
          onChange={(e) => onFilterChange({ ...filters, hasSegments: e.target.checked || undefined })}
        />
        Segments
      </label>

      {/* Search */}
      <div className="relative flex-1 max-w-xs ml-auto">
        <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="검색..."
          className="w-full pl-8 pr-3 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={filters.search || ''}
          onChange={(e) => onFilterChange({ ...filters, search: e.target.value || undefined })}
        />
      </div>

      {/* Refresh */}
      <button
        onClick={onRefresh}
        className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md"
        title="새로고침"
      >
        <RefreshCw className="w-4 h-4" />
      </button>
    </div>
  )
}

// =============================================================================
// StatsBar Component
// =============================================================================

interface StatsBarProps {
  totalFiles: number
  avgCompletion: number
  totalBrands: number
  segmentFiles: number
}

function StatsBar({ totalFiles, avgCompletion, totalBrands, segmentFiles }: StatsBarProps) {
  return (
    <div className="flex items-center gap-6 px-4 py-2 bg-gray-50 border-b border-gray-200 text-sm">
      <div className="flex items-center gap-2">
        <span className="text-gray-500">총 파일:</span>
        <span className="font-semibold text-gray-900">{totalFiles}개</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-gray-500">평균 완성도:</span>
        <span
          className={`font-semibold ${
            avgCompletion >= 67 ? 'text-green-600' : avgCompletion >= 34 ? 'text-yellow-600' : 'text-red-600'
          }`}
        >
          {avgCompletion}%
        </span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-gray-500">브랜드:</span>
        <span className="font-semibold text-gray-900">{totalBrands}개</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-gray-500">Segments 있음:</span>
        <span className="font-semibold text-gray-900">{segmentFiles}개</span>
      </div>
    </div>
  )
}

// =============================================================================
// CompletionBar Component
// =============================================================================

interface CompletionBarProps {
  percentage: number
  compact?: boolean
}

function CompletionBar({ percentage, compact = false }: CompletionBarProps) {
  const color = percentage >= 67 ? 'bg-green-500' : percentage >= 34 ? 'bg-yellow-500' : 'bg-red-500'
  const textColor = percentage >= 67 ? 'text-green-600' : percentage >= 34 ? 'text-yellow-600' : 'text-red-600'

  if (compact) {
    return (
      <div className="flex items-center gap-1">
        <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
          <div className={`h-full ${color}`} style={{ width: `${percentage}%` }} />
        </div>
        <span className={`text-xs font-medium ${textColor} w-8 text-right`}>{percentage}%</span>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2">
      <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${percentage}%` }} />
      </div>
      <span className={`text-sm font-medium ${textColor}`}>{percentage}%</span>
    </div>
  )
}

// =============================================================================
// FieldCell Component
// =============================================================================

interface FieldCellProps {
  value: unknown
  fieldPath: string
  required?: boolean
}

function FieldCell({ value, fieldPath, required = false }: FieldCellProps) {
  const isParsed = hasValue(value)
  const source = getFieldSource(fieldPath)

  // Format value for display
  const formatValue = (val: unknown): string => {
    if (val === null || val === undefined) return '-'
    if (typeof val === 'boolean') return val ? 'Y' : 'N'
    if (typeof val === 'number') return val.toLocaleString()
    if (Array.isArray(val)) return val.length > 0 ? `[${val.length}]` : '-'
    if (typeof val === 'object') return '{...}'
    const str = String(val)
    return str.length > 15 ? str.slice(0, 15) + '...' : str
  }

  // Cell styling based on state
  const bgClass = isParsed
    ? 'bg-green-50'
    : required
      ? 'bg-red-50'
      : 'bg-gray-50'

  const borderClass = isParsed
    ? 'border-green-100'
    : required
      ? 'border-red-200'
      : 'border-gray-100'

  return (
    <td
      className={`px-2 py-1 border-r ${borderClass} ${bgClass} text-center min-w-[80px] max-w-[120px]`}
      title={isParsed ? String(value) : undefined}
    >
      <div className="flex flex-col items-center gap-0.5">
        {/* Status Icon */}
        {isParsed ? (
          <Check className="w-3.5 h-3.5 text-green-500" />
        ) : required ? (
          <AlertCircle className="w-3.5 h-3.5 text-red-400" />
        ) : (
          <Minus className="w-3.5 h-3.5 text-gray-300" />
        )}
        {/* Value Preview */}
        <span
          className={`text-xs font-mono truncate max-w-full ${
            isParsed ? 'text-gray-700' : 'text-gray-300'
          }`}
        >
          {formatValue(value)}
        </span>
        {/* Source indicator (tiny dot) */}
        <span className={`w-1.5 h-1.5 rounded-full ${SOURCE_COLORS[source]?.split(' ')[0] || 'bg-gray-300'}`} />
      </div>
    </td>
  )
}

// =============================================================================
// ColumnGroupHeader Component
// =============================================================================

interface ColumnGroupHeaderProps {
  group: ColumnGroup
  isExpanded: boolean
  onToggle: () => void
  colSpan: number
}

function ColumnGroupHeader({ group, isExpanded, onToggle, colSpan }: ColumnGroupHeaderProps) {
  return (
    <th
      className="px-2 py-2 bg-gray-100 border-r border-gray-300 cursor-pointer hover:bg-gray-200"
      colSpan={colSpan}
      onClick={onToggle}
    >
      <div className="flex items-center justify-center gap-1">
        {isExpanded ? (
          <ChevronDown className="w-3.5 h-3.5 text-gray-500" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5 text-gray-500" />
        )}
        <span className="text-sm font-medium text-gray-700">
          {group.icon} {group.label}
        </span>
        {!isExpanded && (
          <span className="text-xs text-gray-400 ml-1">({group.fields.length})</span>
        )}
      </div>
    </th>
  )
}

// =============================================================================
// MatrixTable Component
// =============================================================================

interface MatrixTableProps {
  assets: Asset[]
  expandedGroups: ExpandedGroups
  onToggleGroup: (groupId: string) => void
  onRowClick?: (asset: Asset) => void
  selectedAssetId?: string | null
}

function MatrixTable({ assets, expandedGroups, onToggleGroup, onRowClick, selectedAssetId }: MatrixTableProps) {
  // Refs for dual scrollbar synchronization
  const topScrollRef = useRef<HTMLDivElement>(null)
  const tableScrollRef = useRef<HTMLDivElement>(null)
  const [tableWidth, setTableWidth] = useState(2000)

  // Calculate completion for an asset
  const calculateCompletion = useCallback((asset: Asset): number => {
    let total = 0
    let filled = 0

    for (const group of COLUMN_GROUPS) {
      for (const fieldPath of group.fields) {
        total++
        const value = getNestedValue(asset as unknown as Record<string, unknown>, fieldPath)
        if (hasValue(value)) filled++
      }
    }

    return total > 0 ? Math.round((filled / total) * 100) : 0
  }, [])

  // Sync top scrollbar with table scroll
  const handleTopScroll = useCallback(() => {
    if (tableScrollRef.current && topScrollRef.current) {
      tableScrollRef.current.scrollLeft = topScrollRef.current.scrollLeft
    }
  }, [])

  // Sync table scroll with top scrollbar
  const handleTableScroll = useCallback(() => {
    if (topScrollRef.current && tableScrollRef.current) {
      topScrollRef.current.scrollLeft = tableScrollRef.current.scrollLeft
    }
  }, [])

  // Update table width when content changes
  useEffect(() => {
    if (tableScrollRef.current) {
      const table = tableScrollRef.current.querySelector('table')
      if (table) {
        setTableWidth(table.scrollWidth)
      }
    }
  }, [assets, expandedGroups])

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {/* Top Scrollbar */}
      <div
        ref={topScrollRef}
        className="overflow-x-auto overflow-y-hidden h-3 border-b border-gray-200 bg-gray-50 flex-shrink-0"
        onScroll={handleTopScroll}
      >
        <div style={{ width: tableWidth, height: 1 }} />
      </div>

      {/* Table Container */}
      <div
        ref={tableScrollRef}
        className="overflow-auto flex-1"
        onScroll={handleTableScroll}
      >
        <table className="w-full border-collapse text-sm">
        {/* Header Row 1: Group Headers */}
        <thead className="sticky top-0 z-10">
          <tr className="bg-gray-50 border-b border-gray-200">
            {/* File Name Header */}
            <th className="px-3 py-2 text-left bg-gray-100 border-r border-gray-300 sticky left-0 z-20 min-w-[200px]">
              <span className="font-semibold text-gray-700">파일명</span>
            </th>

            {/* Column Group Headers */}
            {COLUMN_GROUPS.map((group) => (
              <ColumnGroupHeader
                key={group.id}
                group={group}
                isExpanded={expandedGroups[group.id]}
                onToggle={() => onToggleGroup(group.id)}
                colSpan={expandedGroups[group.id] ? group.fields.length : 1}
              />
            ))}

            {/* Completion Header */}
            <th className="px-3 py-2 bg-gray-100 border-r border-gray-300 min-w-[100px]">
              <span className="font-semibold text-gray-700">완성도</span>
            </th>
          </tr>

          {/* Header Row 2: Field Names (only for expanded groups) */}
          <tr className="bg-gray-50 border-b border-gray-200">
            <th className="px-3 py-1 bg-gray-50 border-r border-gray-200 sticky left-0 z-20" />

            {COLUMN_GROUPS.map((group) => {
              if (expandedGroups[group.id]) {
                return group.fields.map((fieldPath) => (
                  <th
                    key={fieldPath}
                    className="px-1 py-1 text-xs text-gray-500 font-normal border-r border-gray-200 min-w-[80px] max-w-[120px]"
                    title={getFieldLabel(fieldPath)}
                  >
                    <span className="truncate block">{getFieldLabel(fieldPath)}</span>
                  </th>
                ))
              } else {
                return (
                  <th
                    key={group.id}
                    className="px-1 py-1 text-xs text-gray-400 font-normal border-r border-gray-200"
                  >
                    ...
                  </th>
                )
              }
            })}

            <th className="px-1 py-1 border-r border-gray-200" />
          </tr>
        </thead>

        {/* Data Rows */}
        <tbody>
          {assets.map((asset) => {
            const completion = calculateCompletion(asset)
            const isSelected = selectedAssetId === asset.asset_uuid

            return (
              <tr
                key={asset.asset_uuid}
                className={`border-b border-gray-100 hover:bg-blue-50 cursor-pointer ${
                  isSelected ? 'bg-blue-100' : ''
                }`}
                onClick={() => onRowClick?.(asset)}
              >
                {/* File Name */}
                <td className="px-3 py-2 bg-white border-r border-gray-200 sticky left-0 z-10">
                  <div className="flex flex-col">
                    <span className="font-medium text-gray-900 truncate max-w-[180px]" title={asset.file_name}>
                      {asset.file_name}
                    </span>
                    {asset.segments.length > 0 && (
                      <span className="text-xs text-purple-600 flex items-center gap-1">
                        <Layers className="w-3 h-3" />
                        {asset.segments.length} segments
                      </span>
                    )}
                  </div>
                </td>

                {/* Field Cells */}
                {COLUMN_GROUPS.map((group) => {
                  if (expandedGroups[group.id]) {
                    return group.fields.map((fieldPath) => (
                      <FieldCell
                        key={fieldPath}
                        value={getNestedValue(asset as unknown as Record<string, unknown>, fieldPath)}
                        fieldPath={fieldPath}
                      />
                    ))
                  } else {
                    // Collapsed: show summary (count of filled fields)
                    const filledCount = group.fields.filter((fp) =>
                      hasValue(getNestedValue(asset as unknown as Record<string, unknown>, fp))
                    ).length
                    const bgClass =
                      filledCount === group.fields.length
                        ? 'bg-green-50'
                        : filledCount > 0
                          ? 'bg-yellow-50'
                          : 'bg-gray-50'
                    const textClass =
                      filledCount === group.fields.length
                        ? 'text-green-600'
                        : filledCount > 0
                          ? 'text-yellow-600'
                          : 'text-gray-400'

                    return (
                      <td
                        key={group.id}
                        className={`px-2 py-2 border-r border-gray-200 text-center ${bgClass}`}
                      >
                        <span className={`text-xs font-medium ${textClass}`}>
                          {filledCount}/{group.fields.length}
                        </span>
                      </td>
                    )
                  }
                })}

                {/* Completion Bar */}
                <td className="px-2 py-2 border-r border-gray-200">
                  <CompletionBar percentage={completion} compact />
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
      </div>
    </div>
  )
}

// =============================================================================
// Asset Detail Modal Component
// =============================================================================

interface AssetDetailModalProps {
  asset: Asset | null
  onClose: () => void
}

function AssetDetailModal({ asset, onClose }: AssetDetailModalProps) {
  if (!asset) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div
        className="bg-white rounded-lg shadow-xl max-w-4xl max-h-[80vh] overflow-auto w-full mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between sticky top-0 bg-white">
          <div>
            <h2 className="text-lg font-bold text-gray-900">{asset.file_name}</h2>
            <p className="text-sm text-gray-500">{asset.file_path_rel}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            &times;
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* All Fields by Group */}
          {COLUMN_GROUPS.map((group) => (
            <div key={group.id}>
              <h3 className="font-semibold text-gray-700 mb-2">
                {group.icon} {group.label}
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {group.fields.map((fieldPath) => {
                  const value = getNestedValue(asset as unknown as Record<string, unknown>, fieldPath)
                  const isParsed = hasValue(value)

                  return (
                    <div
                      key={fieldPath}
                      className={`p-2 rounded border ${isParsed ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}
                    >
                      <div className="text-xs text-gray-500">{getFieldLabel(fieldPath)}</div>
                      <div className={`text-sm font-medium ${isParsed ? 'text-gray-900' : 'text-gray-400'}`}>
                        {isParsed ? String(value) : '-'}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          ))}

          {/* Segments */}
          {asset.segments.length > 0 && (
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">
                <Layers className="w-4 h-4 inline mr-1" />
                Segments ({asset.segments.length})
              </h3>
              <div className="space-y-2">
                {asset.segments.map((seg, idx) => (
                  <div key={seg.segment_uuid} className="p-3 bg-purple-50 border border-purple-200 rounded">
                    <div className="font-medium text-purple-900">
                      Segment {idx + 1}: {seg.title || 'Untitled'}
                    </div>
                    <div className="text-sm text-purple-700 mt-1">
                      {seg.time_in_sec}s - {seg.time_out_sec}s | {seg.segment_type} | {seg.game_type}
                    </div>
                    {seg.players && seg.players.length > 0 && (
                      <div className="text-xs text-purple-600 mt-1">
                        Players: {seg.players.map((p) => p.name).join(', ')}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// Main UDM Matrix View Component
// =============================================================================

export default function UdmViewer() {
  // State
  const [filters, setFilters] = useState<UdmFilters>({})
  const [expandedGroups, setExpandedGroups] = useState<ExpandedGroups>(() => {
    const initial: ExpandedGroups = {}
    for (const group of COLUMN_GROUPS) {
      initial[group.id] = group.defaultExpanded
    }
    return initial
  })
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null)

  // State for loading from NAS
  const [isLoadingNas, setIsLoadingNas] = useState(false)
  const [nasLoadMessage, setNasLoadMessage] = useState<string | null>(null)

  // Queries
  const {
    data: assets = [],
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ['udm-assets', filters],
    queryFn: () => fetchUdmAssets(filters),
  })

  const { data: stats, refetch: refetchStats } = useQuery({
    queryKey: ['udm-stats'],
    queryFn: fetchUdmStats,
  })

  // Handler for loading from NAS
  const handleLoadFromNas = useCallback(async () => {
    setIsLoadingNas(true)
    setNasLoadMessage(null)
    try {
      const result = await loadFromNas()
      setNasLoadMessage(`${result.total_assets}개 파일 로드 완료`)
      // Refetch data after loading
      refetch()
      refetchStats()
    } catch (error) {
      setNasLoadMessage('NAS 로드 실패')
      console.error('Failed to load from NAS:', error)
    } finally {
      setIsLoadingNas(false)
    }
  }, [refetch, refetchStats])

  // Computed values
  const brands = useMemo(() => {
    return stats ? Object.keys(stats.by_brand).sort() : []
  }, [stats])

  const assetTypes = useMemo(() => {
    return stats ? Object.keys(stats.by_asset_type).sort() : []
  }, [stats])

  const years = useMemo(() => {
    return stats ? Object.keys(stats.by_year).map(Number).sort((a, b) => b - a) : []
  }, [stats])

  const avgCompletion = useMemo(() => {
    if (assets.length === 0) return 0

    let totalCompletion = 0
    for (const asset of assets) {
      let total = 0
      let filled = 0
      for (const group of COLUMN_GROUPS) {
        for (const fieldPath of group.fields) {
          total++
          const value = getNestedValue(asset as unknown as Record<string, unknown>, fieldPath)
          if (hasValue(value)) filled++
        }
      }
      totalCompletion += total > 0 ? (filled / total) * 100 : 0
    }

    return Math.round(totalCompletion / assets.length)
  }, [assets])

  const segmentFiles = useMemo(() => {
    return assets.filter((a) => a.segments.length > 0).length
  }, [assets])

  // Handlers
  const handleToggleGroup = useCallback((groupId: string) => {
    setExpandedGroups((prev) => ({
      ...prev,
      [groupId]: !prev[groupId],
    }))
  }, [])

  const handleRowClick = useCallback((asset: Asset) => {
    setSelectedAsset(asset)
  }, [])

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-white">
        <div>
          <h1 className="text-lg font-bold text-gray-900">UDM Matrix View</h1>
          <p className="text-xs text-gray-500">NAS 파일별 UDM 파싱 현황 매트릭스</p>
        </div>
        <div className="flex items-center gap-3">
          {nasLoadMessage && (
            <span className="text-sm text-green-600">{nasLoadMessage}</span>
          )}
          <button
            onClick={handleLoadFromNas}
            disabled={isLoadingNas}
            className="flex items-center gap-1 px-3 py-1.5 text-sm bg-green-500 text-white rounded-md hover:bg-green-600 disabled:opacity-50"
          >
            {isLoadingNas ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
            NAS 스캔
          </button>
          <button className="flex items-center gap-1 px-3 py-1.5 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600">
            <Download className="w-4 h-4" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <FilterBar
        filters={filters}
        onFilterChange={setFilters}
        onRefresh={() => refetch()}
        brands={brands}
        assetTypes={assetTypes}
        years={years}
      />

      {/* Stats Bar */}
      <StatsBar
        totalFiles={assets.length}
        avgCompletion={avgCompletion}
        totalBrands={brands.length}
        segmentFiles={segmentFiles}
      />

      {/* Matrix Table */}
      {isLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
        </div>
      ) : assets.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-gray-400">
          <div className="text-center">
            <Search className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>데이터가 없습니다</p>
            <p className="text-sm">필터를 조정하거나 데이터를 로드해주세요</p>
          </div>
        </div>
      ) : (
        <MatrixTable
          assets={assets}
          expandedGroups={expandedGroups}
          onToggleGroup={handleToggleGroup}
          onRowClick={handleRowClick}
          selectedAssetId={selectedAsset?.asset_uuid}
        />
      )}

      {/* Asset Detail Modal */}
      <AssetDetailModal asset={selectedAsset} onClose={() => setSelectedAsset(null)} />
    </div>
  )
}
