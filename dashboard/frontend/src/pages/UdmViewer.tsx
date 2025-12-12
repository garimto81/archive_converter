import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Search,
  Filter,
  RefreshCw,
  FileJson,
  ChevronDown,
  ChevronRight,
  Database,
  Copy,
  Check,
  Eye,
  X,
} from 'lucide-react'
import { fetchUdmDocument, fetchUdmStats, fetchAssetDetail } from '@/api/udm'
import type { UdmAssetSummary, UdmFilters } from '@/types/udm'

// 브랜드별 색상
const brandColors: Record<string, string> = {
  WSOP: 'bg-red-100 text-red-800',
  HCL: 'bg-purple-100 text-purple-800',
  PAD: 'bg-blue-100 text-blue-800',
  GGMillions: 'bg-green-100 text-green-800',
  MPP: 'bg-yellow-100 text-yellow-800',
  GOG: 'bg-orange-100 text-orange-800',
}

// Asset Type별 색상
const assetTypeColors: Record<string, string> = {
  STREAM: 'bg-indigo-100 text-indigo-800',
  SUBCLIP: 'bg-cyan-100 text-cyan-800',
  EPISODE: 'bg-pink-100 text-pink-800',
  HAND_CLIP: 'bg-teal-100 text-teal-800',
}

function JsonViewer({ data, title }: { data: unknown; title?: string }) {
  const [copied, setCopied] = useState(false)

  const jsonString = useMemo(
    () => JSON.stringify(data, null, 2),
    [data]
  )

  const handleCopy = async () => {
    await navigator.clipboard.writeText(jsonString)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="bg-gray-900 rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800">
        <span className="text-sm text-gray-300 font-mono">
          {title || 'JSON'}
        </span>
        <button
          onClick={handleCopy}
          className="flex items-center space-x-1 text-gray-400 hover:text-white transition-colors"
        >
          {copied ? (
            <>
              <Check className="w-4 h-4 text-green-400" />
              <span className="text-xs text-green-400">복사됨</span>
            </>
          ) : (
            <>
              <Copy className="w-4 h-4" />
              <span className="text-xs">복사</span>
            </>
          )}
        </button>
      </div>
      <pre className="p-4 text-sm text-green-400 font-mono overflow-x-auto max-h-96">
        {jsonString}
      </pre>
    </div>
  )
}

function AssetDetailModal({
  assetUuid,
  onClose,
}: {
  assetUuid: string
  onClose: () => void
}) {
  const { data, isLoading } = useQuery({
    queryKey: ['asset-detail', assetUuid],
    queryFn: () => fetchAssetDetail(assetUuid),
    enabled: !!assetUuid,
  })

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* 헤더 */}
        <div className="flex items-center justify-between px-6 py-4 border-b bg-gray-50">
          <div className="flex items-center space-x-3">
            <FileJson className="w-6 h-6 text-primary-600" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Asset 상세 정보
              </h3>
              {data && (
                <p className="text-sm text-gray-500">{data.file_name}</p>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* 콘텐츠 */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="w-8 h-8 text-gray-400 animate-spin" />
            </div>
          ) : data ? (
            <div className="space-y-6">
              {/* 기본 정보 */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs text-gray-500 uppercase">
                    UUID
                  </label>
                  <p className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
                    {data.asset_uuid}
                  </p>
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-gray-500 uppercase">
                    파일명
                  </label>
                  <p className="font-medium">{data.file_name}</p>
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-gray-500 uppercase">
                    Asset Type
                  </label>
                  <span
                    className={`inline-block px-2 py-1 rounded text-sm ${
                      assetTypeColors[data.asset_type] || 'bg-gray-100'
                    }`}
                  >
                    {data.asset_type}
                  </span>
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-gray-500 uppercase">
                    Source Origin
                  </label>
                  <p className="text-sm">{data.source_origin}</p>
                </div>
              </div>

              {/* NAS 경로 */}
              {data.file_path_nas && (
                <div className="space-y-1">
                  <label className="text-xs text-gray-500 uppercase">
                    NAS 경로
                  </label>
                  <p className="font-mono text-sm bg-gray-100 px-3 py-2 rounded break-all">
                    {data.file_path_nas}
                  </p>
                </div>
              )}

              {/* Event Context */}
              <div className="space-y-2">
                <label className="text-xs text-gray-500 uppercase">
                  Event Context
                </label>
                <JsonViewer
                  data={data.event_context}
                  title="event_context.json"
                />
              </div>

              {/* Tech Spec */}
              {data.tech_spec && (
                <div className="space-y-2">
                  <label className="text-xs text-gray-500 uppercase">
                    Tech Spec
                  </label>
                  <JsonViewer data={data.tech_spec} title="tech_spec.json" />
                </div>
              )}

              {/* 전체 JSON */}
              <div className="space-y-2">
                <label className="text-xs text-gray-500 uppercase">
                  전체 JSON
                </label>
                <JsonViewer data={data} title="asset.json" />
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              데이터를 불러올 수 없습니다.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function AssetRow({
  asset,
  onViewDetail,
}: {
  asset: UdmAssetSummary
  onViewDetail: (uuid: string) => void
}) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="card hover:shadow-md transition-shadow">
      {/* 메인 행 */}
      <div
        className="p-4 cursor-pointer flex items-center"
        onClick={() => setExpanded(!expanded)}
      >
        <button className="mr-3 text-gray-400">
          {expanded ? (
            <ChevronDown className="w-5 h-5" />
          ) : (
            <ChevronRight className="w-5 h-5" />
          )}
        </button>

        {/* 파일 아이콘 */}
        <FileJson className="w-5 h-5 text-gray-400 mr-3" />

        {/* 파일명 */}
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-gray-900 truncate">
            {asset.file_name}
          </h4>
          <p className="text-sm text-gray-500 font-mono truncate">
            {asset.asset_uuid.slice(0, 8)}...
          </p>
        </div>

        {/* 브랜드 */}
        <span
          className={`px-2 py-1 rounded text-xs font-medium mr-3 ${
            brandColors[asset.brand] || 'bg-gray-100 text-gray-800'
          }`}
        >
          {asset.brand}
        </span>

        {/* Asset Type */}
        <span
          className={`px-2 py-1 rounded text-xs font-medium mr-3 ${
            assetTypeColors[asset.asset_type] || 'bg-gray-100 text-gray-800'
          }`}
        >
          {asset.asset_type}
        </span>

        {/* 연도 */}
        <span className="text-sm text-gray-600 mr-3 w-12">{asset.year}</span>

        {/* 시즌/에피소드 */}
        <span className="text-sm text-gray-500 mr-3 w-20">
          {asset.season && `S${asset.season}`}
          {asset.episode && `E${asset.episode}`}
        </span>

        {/* 상세 보기 버튼 */}
        <button
          onClick={(e) => {
            e.stopPropagation()
            onViewDetail(asset.asset_uuid)
          }}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          title="상세 보기"
        >
          <Eye className="w-4 h-4 text-gray-500" />
        </button>
      </div>

      {/* 확장된 내용 */}
      {expanded && (
        <div className="px-4 pb-4 border-t bg-gray-50">
          <div className="pt-4">
            <JsonViewer
              data={{
                asset_uuid: asset.asset_uuid,
                file_name: asset.file_name,
                file_path_nas: asset.file_path_nas,
                asset_type: asset.asset_type,
                brand: asset.brand,
                year: asset.year,
                season: asset.season,
                episode: asset.episode,
                source_origin: asset.source_origin,
                segment_count: asset.segment_count,
              }}
              title="asset_summary.json"
            />
          </div>
        </div>
      )}
    </div>
  )
}

function StatsOverview({
  stats,
  loading,
}: {
  stats: {
    total_assets: number
    total_segments: number
    brand_distribution: Record<string, number>
    asset_type_distribution: Record<string, number>
  } | null
  loading: boolean
}) {
  if (loading) {
    return (
      <div className="grid grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="card p-4 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          </div>
        ))}
      </div>
    )
  }

  if (!stats) return null

  return (
    <div className="grid grid-cols-4 gap-4">
      {/* 총 Assets */}
      <div className="card p-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-primary-100 rounded-lg">
            <Database className="w-5 h-5 text-primary-600" />
          </div>
          <div>
            <p className="text-sm text-gray-500">총 Assets</p>
            <p className="text-2xl font-bold text-gray-900">
              {stats.total_assets.toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* 총 Segments */}
      <div className="card p-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-green-100 rounded-lg">
            <FileJson className="w-5 h-5 text-green-600" />
          </div>
          <div>
            <p className="text-sm text-gray-500">총 Segments</p>
            <p className="text-2xl font-bold text-gray-900">
              {stats.total_segments.toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* 브랜드 수 */}
      <div className="card p-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Filter className="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <p className="text-sm text-gray-500">브랜드</p>
            <p className="text-2xl font-bold text-gray-900">
              {Object.keys(stats.brand_distribution).length}
            </p>
          </div>
        </div>
      </div>

      {/* Asset Types */}
      <div className="card p-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-orange-100 rounded-lg">
            <FileJson className="w-5 h-5 text-orange-600" />
          </div>
          <div>
            <p className="text-sm text-gray-500">Asset Types</p>
            <p className="text-2xl font-bold text-gray-900">
              {Object.keys(stats.asset_type_distribution).length}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function UdmViewer() {
  const [filters, setFilters] = useState<UdmFilters>({})
  const [selectedAssetUuid, setSelectedAssetUuid] = useState<string | null>(
    null
  )

  // UDM 문서 로드
  const {
    data: documentData,
    isLoading: documentLoading,
    refetch: refetchDocument,
  } = useQuery({
    queryKey: ['udm-document', filters],
    queryFn: () => fetchUdmDocument(filters),
    refetchInterval: 30000, // 30초마다 갱신
  })

  // 통계 로드
  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ['udm-stats'],
    queryFn: fetchUdmStats,
    refetchInterval: 30000,
  })

  // 브랜드 목록 추출
  const brands = useMemo(() => {
    if (!statsData?.brand_distribution) return []
    return Object.keys(statsData.brand_distribution).sort()
  }, [statsData])

  // Asset Type 목록 추출
  const assetTypes = useMemo(() => {
    if (!statsData?.asset_type_distribution) return []
    return Object.keys(statsData.asset_type_distribution).sort()
  }, [statsData])

  const handleFilterChange = (newFilters: Partial<UdmFilters>) => {
    setFilters((prev) => ({ ...prev, ...newFilters }))
  }

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">UDM JSON Viewer</h2>
          <p className="text-sm text-gray-500 mt-1">
            NAS에서 추출된 UDM 데이터를 JSON 형식으로 조회합니다
          </p>
        </div>
        <button
          onClick={() => refetchDocument()}
          className="btn-secondary flex items-center space-x-2"
          disabled={documentLoading}
        >
          <RefreshCw
            className={`w-4 h-4 ${documentLoading ? 'animate-spin' : ''}`}
          />
          <span>새로고침</span>
        </button>
      </div>

      {/* 통계 카드 */}
      <StatsOverview stats={statsData || null} loading={statsLoading} />

      {/* 메타데이터 카드 */}
      {documentData?.metadata && (
        <div className="card p-4">
          <div className="flex items-center space-x-4 text-sm">
            <span className="text-gray-500">
              버전: <strong>{documentData.metadata.version}</strong>
            </span>
            <span className="text-gray-300">|</span>
            <span className="text-gray-500">
              소스: <strong>{documentData.metadata.source}</strong>
            </span>
            <span className="text-gray-300">|</span>
            <span className="text-gray-500">
              생성일:{' '}
              <strong>
                {new Date(documentData.metadata.generated_at).toLocaleString()}
              </strong>
            </span>
          </div>
        </div>
      )}

      {/* 필터 및 검색 */}
      <div className="card p-4">
        <div className="flex items-center space-x-4">
          {/* 검색 */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="파일명으로 검색..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              value={filters.search || ''}
              onChange={(e) => handleFilterChange({ search: e.target.value })}
            />
          </div>

          {/* 브랜드 필터 */}
          <select
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            value={filters.brand || ''}
            onChange={(e) =>
              handleFilterChange({ brand: e.target.value || undefined })
            }
          >
            <option value="">모든 브랜드</option>
            {brands.map((brand) => (
              <option key={brand} value={brand}>
                {brand}
              </option>
            ))}
          </select>

          {/* Asset Type 필터 */}
          <select
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            value={filters.asset_type || ''}
            onChange={(e) =>
              handleFilterChange({ asset_type: e.target.value || undefined })
            }
          >
            <option value="">모든 타입</option>
            {assetTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>

          {/* 연도 필터 */}
          <select
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            value={filters.year || ''}
            onChange={(e) =>
              handleFilterChange({
                year: e.target.value ? Number(e.target.value) : undefined,
              })
            }
          >
            <option value="">모든 연도</option>
            <option value="2024">2024</option>
            <option value="2023">2023</option>
            <option value="2022">2022</option>
          </select>
        </div>
      </div>

      {/* Asset 목록 */}
      <div className="space-y-3">
        {documentLoading ? (
          // 로딩 스켈레톤
          [...Array(5)].map((_, i) => (
            <div key={i} className="card p-6 animate-pulse">
              <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))
        ) : !documentData?.assets.length ? (
          <div className="card p-12 text-center">
            <FileJson className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">표시할 Asset이 없습니다.</p>
          </div>
        ) : (
          documentData.assets.map((asset) => (
            <AssetRow
              key={asset.asset_uuid}
              asset={asset}
              onViewDetail={setSelectedAssetUuid}
            />
          ))
        )}
      </div>

      {/* 결과 요약 */}
      {!documentLoading && documentData && documentData.assets.length > 0 && (
        <div className="text-sm text-gray-500 text-center">
          총 {documentData.assets.length}개의 Asset
        </div>
      )}

      {/* 상세 모달 */}
      {selectedAssetUuid && (
        <AssetDetailModal
          assetUuid={selectedAssetUuid}
          onClose={() => setSelectedAssetUuid(null)}
        />
      )}
    </div>
  )
}
