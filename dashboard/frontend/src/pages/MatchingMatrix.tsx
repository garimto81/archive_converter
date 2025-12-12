import { useEffect, useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Search, RefreshCw, HardDrive, Plus } from 'lucide-react'
import { useMatchingStore } from '@/stores/matchingStore'
import { fetchMatchingMatrix, fetchMatchingStats } from '@/api/matching'
import { fetchFolderTree, refreshNasScan, type ScanResult } from '@/api/nas'
import SummaryBar from '@/components/matching/SummaryBar'
import UnifiedTree from '@/components/matching/UnifiedTree'
import type { FilterOptions } from '@/types/matching'

export default function MatchingMatrix() {
  const queryClient = useQueryClient()
  const [scanResult, setScanResult] = useState<ScanResult | null>(null)
  const [showScanMenu, setShowScanMenu] = useState(false)
  const scanMenuRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (scanMenuRef.current && !scanMenuRef.current.contains(event.target as Node)) {
        setShowScanMenu(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const {
    stats,
    items,
    expandedFiles,
    filters,
    setItems,
    setStats,
    toggleFileExpansion,
    setFilters,
  } = useMatchingStore()

  // NAS Scan mutation
  const scanMutation = useMutation({
    mutationFn: (mode: 'full' | 'incremental') => refreshNasScan(mode),
    onSuccess: (result) => {
      setScanResult(result)
      // 스캔 후 데이터 갱신
      queryClient.invalidateQueries({ queryKey: ['folder-tree'] })
      queryClient.invalidateQueries({ queryKey: ['matching-matrix'] })
      queryClient.invalidateQueries({ queryKey: ['matching-stats'] })
      // 3초 후 결과 메시지 숨기기
      setTimeout(() => setScanResult(null), 5000)
    },
  })

  // Load folder tree
  const {
    data: folderTree,
    isLoading: folderLoading,
  } = useQuery({
    queryKey: ['folder-tree'],
    queryFn: fetchFolderTree,
  })

  // Load matching matrix data
  const {
    data: matrixData,
    isLoading: matrixLoading,
    refetch: refetchMatrix,
  } = useQuery({
    queryKey: ['matching-matrix'],
    queryFn: fetchMatchingMatrix,
    refetchInterval: 60000, // 60초마다 자동 갱신
  })

  // Load stats data
  const {
    data: statsData,
    isLoading: statsLoading,
    refetch: refetchStats,
  } = useQuery({
    queryKey: ['matching-stats'],
    queryFn: fetchMatchingStats,
    refetchInterval: 60000,
  })

  // Sync data to store
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

  const handleRefresh = () => {
    refetchMatrix()
    refetchStats()
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-white">
        <div>
          <h1 className="text-lg font-bold text-gray-900">Matching Matrix</h1>
          <p className="text-xs text-gray-500">
            NAS files and segment matching status
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* Refresh Cache Button */}
          <button
            onClick={handleRefresh}
            className="inline-flex items-center px-3 py-1.5 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            disabled={matrixLoading || statsLoading}
            title="Refresh cached data"
          >
            <RefreshCw
              className={`w-4 h-4 mr-1.5 ${matrixLoading || statsLoading ? 'animate-spin' : ''}`}
            />
            Refresh
          </button>

          {/* Scan Dropdown */}
          <div className="relative" ref={scanMenuRef}>
            <button
              onClick={() => setShowScanMenu(!showScanMenu)}
              className="inline-flex items-center px-3 py-1.5 border border-blue-500 rounded-md text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100"
              disabled={scanMutation.isPending}
            >
              <HardDrive
                className={`w-4 h-4 mr-1.5 ${scanMutation.isPending ? 'animate-pulse' : ''}`}
              />
              {scanMutation.isPending ? 'Scanning...' : 'Scan NAS'}
            </button>

            {/* Dropdown Menu */}
            {showScanMenu && !scanMutation.isPending && (
              <div className="absolute right-0 mt-1 w-56 bg-white border border-gray-200 rounded-md shadow-lg z-10">
                <button
                  onClick={() => {
                    scanMutation.mutate('incremental')
                    setShowScanMenu(false)
                  }}
                  className="w-full flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  <Plus className="w-4 h-4 mr-2 text-green-500" />
                  <div className="text-left">
                    <div className="font-medium">Incremental Scan</div>
                    <div className="text-xs text-gray-500">New files only (fast)</div>
                  </div>
                </button>
                <button
                  onClick={() => {
                    scanMutation.mutate('full')
                    setShowScanMenu(false)
                  }}
                  className="w-full flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 border-t border-gray-100"
                >
                  <HardDrive className="w-4 h-4 mr-2 text-blue-500" />
                  <div className="text-left">
                    <div className="font-medium">Full Rescan</div>
                    <div className="text-xs text-gray-500">Scan all files</div>
                  </div>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Scan Result Toast */}
      {scanResult && (
        <div className="px-4 py-2 bg-green-50 border-b border-green-200 text-sm">
          <span className="text-green-700">
            {scanResult.mode === 'incremental' ? 'Incremental' : 'Full'} scan completed:
            {' '}{scanResult.total_files.toLocaleString()} files
            {scanResult.new_files > 0 && ` (+${scanResult.new_files} new)`}
            {scanResult.modified_files > 0 && ` (${scanResult.modified_files} modified)`}
            {' '}in {scanResult.scan_duration_sec.toFixed(1)}s
          </span>
        </div>
      )}

      {/* Summary Bar */}
      <div className="px-4 py-2 border-b border-gray-200 bg-gray-50">
        <SummaryBar stats={stats} loading={statsLoading} />
      </div>

      {/* Filters */}
      <div className="px-4 py-3 bg-white border-b border-gray-200">
        <div className="flex items-center space-x-3">
          {/* Search */}
          <div className="flex-1 max-w-md relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search files..."
              className="w-full pl-9 pr-4 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={filters.searchQuery || ''}
              onChange={(e) => setFilters({ searchQuery: e.target.value })}
            />
          </div>

          {/* Status Filter */}
          <select
            className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={filters.status || 'all'}
            onChange={(e) => setFilters({ status: e.target.value as FilterOptions['status'] })}
          >
            <option value="all">All Status</option>
            <option value="complete">Complete</option>
            <option value="partial">Partial</option>
            <option value="warning">Warning</option>
            <option value="pending">Pending</option>
            <option value="no_metadata">No Metadata</option>
          </select>
        </div>
      </div>

      {/* Unified Tree - Folders + Files */}
      <div className="flex-1 overflow-hidden">
        <UnifiedTree
          folderRoot={folderTree || null}
          items={items}
          expandedFiles={expandedFiles}
          onToggleFile={toggleFileExpansion}
          loading={folderLoading || matrixLoading}
          filters={filters}
        />
      </div>
    </div>
  )
}
