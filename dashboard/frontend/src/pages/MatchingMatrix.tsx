import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, Filter, RefreshCw } from 'lucide-react'
import { useMatchingStore } from '@/stores/matchingStore'
import { fetchMatchingMatrix, fetchMatchingStats } from '@/api/matching'
import StatsCards from '@/components/matching/StatsCards'
import FileRow from '@/components/matching/FileRow'

export default function MatchingMatrix() {
  const {
    items,
    stats,
    expandedFiles,
    filters,
    setItems,
    setStats,
    toggleFileExpansion,
    setFilters,
    getFilteredItems,
  } = useMatchingStore()

  // 매칭 매트릭스 데이터 로드
  const {
    data: matrixData,
    isLoading: matrixLoading,
    refetch: refetchMatrix,
  } = useQuery({
    queryKey: ['matching-matrix'],
    queryFn: fetchMatchingMatrix,
    refetchInterval: 10000, // 10초마다 자동 갱신
  })

  // 통계 데이터 로드
  const {
    data: statsData,
    isLoading: statsLoading,
    refetch: refetchStats,
  } = useQuery({
    queryKey: ['matching-stats'],
    queryFn: fetchMatchingStats,
    refetchInterval: 10000,
  })

  // 데이터 동기화
  useEffect(() => {
    if (matrixData) {
      setItems(matrixData)
    }
  }, [matrixData, setItems])

  useEffect(() => {
    if (statsData) {
      setStats(statsData)
    }
  }, [statsData, setStats])

  const filteredItems = getFilteredItems()

  const handleRefresh = () => {
    refetchMatrix()
    refetchStats()
  }

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">매칭 매트릭스</h2>
          <p className="text-sm text-gray-500 mt-1">
            분할 아카이브 파일과 세그먼트 매칭 현황
          </p>
        </div>
        <button
          onClick={handleRefresh}
          className="btn-secondary flex items-center space-x-2"
          disabled={matrixLoading || statsLoading}
        >
          <RefreshCw
            className={`w-4 h-4 ${
              matrixLoading || statsLoading ? 'animate-spin' : ''
            }`}
          />
          <span>새로고침</span>
        </button>
      </div>

      {/* 통계 카드 */}
      <StatsCards stats={stats} loading={statsLoading} />

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
              value={filters.searchQuery || ''}
              onChange={(e) => setFilters({ searchQuery: e.target.value })}
            />
          </div>

          {/* 상태 필터 */}
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              value={filters.status || 'all'}
              onChange={(e) =>
                setFilters({
                  status: e.target.value as any,
                })
              }
            >
              <option value="all">전체</option>
              <option value="complete">완료</option>
              <option value="partial">부분</option>
              <option value="warning">경고</option>
              <option value="pending">대기</option>
            </select>
          </div>

          {/* 정렬 */}
          <select
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            value={filters.sortBy || 'file_name'}
            onChange={(e) =>
              setFilters({
                sortBy: e.target.value as any,
              })
            }
          >
            <option value="file_name">파일명</option>
            <option value="segment_count">세그먼트 수</option>
            <option value="status">상태</option>
          </select>

          <select
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            value={filters.sortOrder || 'desc'}
            onChange={(e) =>
              setFilters({
                sortOrder: e.target.value as any,
              })
            }
          >
            <option value="desc">내림차순</option>
            <option value="asc">오름차순</option>
          </select>
        </div>
      </div>

      {/* 파일 목록 */}
      <div className="space-y-3">
        {matrixLoading ? (
          // 로딩 스켈레톤
          [...Array(5)].map((_, i) => (
            <div key={i} className="card p-6 animate-pulse">
              <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))
        ) : filteredItems.length === 0 ? (
          // 데이터 없음
          <div className="card p-12 text-center">
            <p className="text-gray-500">표시할 파일이 없습니다.</p>
          </div>
        ) : (
          // 파일 목록
          filteredItems.map((item) => (
            <FileRow
              key={item.file_name}
              item={item}
              isExpanded={expandedFiles.has(item.file_name)}
              onToggle={() => toggleFileExpansion(item.file_name)}
            />
          ))
        )}
      </div>

      {/* 결과 요약 */}
      {!matrixLoading && filteredItems.length > 0 && (
        <div className="text-sm text-gray-500 text-center">
          총 {filteredItems.length}개의 파일
        </div>
      )}
    </div>
  )
}
