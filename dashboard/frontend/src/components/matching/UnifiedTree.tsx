import { useState, useMemo } from 'react'
import { ChevronRight, ChevronDown, Folder, FolderOpen, FileVideo, Clock, Check, Minus } from 'lucide-react'
import clsx from 'clsx'
import type { NasFolder } from '@/api/nas'
import type { MatchingItem, SegmentRecord, FilterOptions } from '@/types/matching'

interface UnifiedTreeProps {
  folderRoot: NasFolder | null
  items: MatchingItem[]
  expandedFiles: Set<string>
  onToggleFile: (fileName: string) => void
  loading?: boolean
  filters: FilterOptions
}

// 상태 인디케이터 컴포넌트
function StatusIndicator({ exists, count }: { exists: boolean; count?: number }) {
  if (!exists && (count === undefined || count === 0)) {
    return <span className="text-gray-300">·</span>
  }
  return (
    <span className="text-green-600 font-medium">
      {count !== undefined && count > 0 ? count : '✓'}
    </span>
  )
}

// 세그먼트 행 컴포넌트
function SegmentRow({ segment, index }: { segment: SegmentRecord; index: number }) {
  const formatTime = (sec: number) => {
    const h = Math.floor(sec / 3600)
    const m = Math.floor((sec % 3600) / 60)
    const s = Math.floor(sec % 60)
    return h > 0 ? `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}` : `${m}:${s.toString().padStart(2, '0')}`
  }

  return (
    <div className="flex items-center py-1.5 px-4 text-xs bg-gray-50 border-b border-gray-100 last:border-b-0">
      <span className="w-8 text-gray-400">#{index + 1}</span>
      <span className="w-24 flex items-center text-gray-600">
        <Clock className="w-3 h-3 mr-1" />
        {formatTime(segment.time_in_sec)}
      </span>
      <span className="w-24 text-gray-600">
        → {formatTime(segment.time_out_sec)}
      </span>
      <span className="flex-1 truncate text-gray-700">
        {segment.winner || segment.hands || '-'}
      </span>
      <span className="w-24 flex gap-1">
        {segment.tags?.slice(0, 3).map((tag, i) => (
          <span key={i} className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-[10px]">
            {tag}
          </span>
        ))}
      </span>
      <span className="w-16 text-center">
        {segment.udm?.uuid ? (
          <Check className="w-3.5 h-3.5 text-green-600 mx-auto" />
        ) : (
          <Minus className="w-3.5 h-3.5 text-gray-300 mx-auto" />
        )}
      </span>
    </div>
  )
}

// 파일 노드 컴포넌트
function FileNode({
  item,
  depth,
  isExpanded,
  onToggle,
}: {
  item: MatchingItem
  depth: number
  isExpanded: boolean
  onToggle: () => void
}) {
  const hasSegments = item.segments && item.segments.length > 0

  const statusColor = {
    complete: 'bg-green-100 text-green-700',
    partial: 'bg-yellow-100 text-yellow-700',
    warning: 'bg-orange-100 text-orange-700',
    pending: 'bg-gray-100 text-gray-600',
    no_metadata: 'bg-gray-100 text-gray-500',
    orphan: 'bg-red-100 text-red-700',
  }[item.status] || 'bg-gray-100 text-gray-600'

  return (
    <div>
      {/* 파일 행 */}
      <div
        className={clsx(
          'flex items-center py-1.5 px-2 cursor-pointer transition-colors hover:bg-blue-50',
          isExpanded && 'bg-blue-50'
        )}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
        onClick={onToggle}
      >
        {/* 확장 아이콘 */}
        <span className={clsx('w-4 h-4 flex items-center justify-center mr-1', !hasSegments && 'invisible')}>
          {hasSegments && (
            isExpanded ? (
              <ChevronDown className="w-3 h-3 text-gray-500" />
            ) : (
              <ChevronRight className="w-3 h-3 text-gray-500" />
            )
          )}
        </span>

        {/* 파일 아이콘 */}
        <FileVideo className="w-4 h-4 text-blue-500 mr-2 flex-shrink-0" />

        {/* 파일명 */}
        <span className="flex-1 text-sm truncate text-gray-700">
          {item.file_name}
        </span>

        {/* 상태 인디케이터들 */}
        <div className="flex items-center gap-4 text-xs ml-4">
          {/* NAS */}
          <span className="w-8 text-center" title="NAS">
            <StatusIndicator exists={item.nas?.exists ?? false} />
          </span>

          {/* Sheet */}
          <span className="w-8 text-center" title="Sheet">
            <StatusIndicator exists={item.segment_count > 0} count={item.segment_count} />
          </span>

          {/* UDM */}
          <span className="w-8 text-center" title="UDM">
            <StatusIndicator exists={item.udm_count > 0} count={item.udm_count} />
          </span>

          {/* Status Badge */}
          <span className={clsx('px-2 py-0.5 rounded text-[10px] font-medium', statusColor)}>
            {item.status === 'no_metadata' ? 'NO META' : item.status.toUpperCase()}
          </span>

          {/* Size */}
          <span className="w-16 text-right text-gray-500">
            {item.nas?.size_mb ? `${(item.nas.size_mb / 1024).toFixed(1)}GB` : '-'}
          </span>
        </div>
      </div>

      {/* 세그먼트 목록 (확장 시) */}
      {isExpanded && hasSegments && (
        <div className="border-l-2 border-blue-200" style={{ marginLeft: `${depth * 16 + 24}px` }}>
          <div className="flex items-center py-1 px-4 text-[10px] font-medium text-gray-500 bg-gray-100 uppercase">
            <span className="w-8">#</span>
            <span className="w-24">Time In</span>
            <span className="w-24">Time Out</span>
            <span className="flex-1">Player/Hands</span>
            <span className="w-24">Tags</span>
            <span className="w-16 text-center">UDM</span>
          </div>
          {item.segments.map((seg, idx) => (
            <SegmentRow key={seg.row_number || idx} segment={seg} index={idx} />
          ))}
        </div>
      )}
    </div>
  )
}

// 폴더 노드 컴포넌트
function FolderNode({
  folder,
  files,
  depth,
  expandedFiles,
  onToggleFile,
  defaultExpanded = false,
}: {
  folder: NasFolder
  files: MatchingItem[]
  depth: number
  expandedFiles: Set<string>
  onToggleFile: (fileName: string) => void
  defaultExpanded?: boolean
}) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)

  // 이 폴더에 속한 파일들 필터링
  const folderFiles = useMemo(() => {
    return files.filter((item) => {
      const itemPath = item.nas?.path || ''
      // 정확히 이 폴더에 있는 파일만 (하위 폴더 제외)
      if (!itemPath.startsWith(folder.path)) return false
      const relativePath = itemPath.substring(folder.path.length).replace(/^[/\\]/, '')
      return !relativePath.includes('/') && !relativePath.includes('\\')
    })
  }, [files, folder.path])

  const hasChildren = (folder.children && folder.children.length > 0) || folderFiles.length > 0
  const totalCount = folder.file_count

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation()
    setIsExpanded(!isExpanded)
  }

  return (
    <div>
      {/* 폴더 행 */}
      <div
        className="flex items-center py-1.5 px-2 cursor-pointer hover:bg-gray-100 transition-colors"
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
        onClick={handleToggle}
      >
        {/* 확장 아이콘 */}
        <span className={clsx('w-4 h-4 flex items-center justify-center mr-1', !hasChildren && 'invisible')}>
          {hasChildren && (
            isExpanded ? (
              <ChevronDown className="w-3 h-3 text-gray-500" />
            ) : (
              <ChevronRight className="w-3 h-3 text-gray-500" />
            )
          )}
        </span>

        {/* 폴더 아이콘 */}
        {isExpanded ? (
          <FolderOpen className="w-4 h-4 text-amber-500 mr-2 flex-shrink-0" />
        ) : (
          <Folder className="w-4 h-4 text-amber-500 mr-2 flex-shrink-0" />
        )}

        {/* 폴더명 */}
        <span className="flex-1 text-sm font-medium text-gray-700">
          {folder.name}
        </span>

        {/* 파일 수 */}
        <span className="text-xs text-gray-400 mr-4">
          {totalCount.toLocaleString()} files
        </span>
      </div>

      {/* 자식 노드들 (확장 시) */}
      {isExpanded && (
        <div>
          {/* 하위 폴더 */}
          {folder.children?.map((child) => (
            <FolderNode
              key={child.path}
              folder={child}
              files={files}
              depth={depth + 1}
              expandedFiles={expandedFiles}
              onToggleFile={onToggleFile}
            />
          ))}

          {/* 이 폴더의 파일들 */}
          {folderFiles.map((item) => (
            <FileNode
              key={item.file_name}
              item={item}
              depth={depth + 1}
              isExpanded={expandedFiles.has(item.file_name)}
              onToggle={() => onToggleFile(item.file_name)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// 메인 통합 트리 컴포넌트
export default function UnifiedTree({
  folderRoot,
  items,
  expandedFiles,
  onToggleFile,
  loading,
  filters,
}: UnifiedTreeProps) {
  // 필터링된 아이템
  const filteredItems = useMemo(() => {
    let result = items

    // 검색 필터
    if (filters.searchQuery) {
      const query = filters.searchQuery.toLowerCase()
      result = result.filter((item) => item.file_name.toLowerCase().includes(query))
    }

    // 상태 필터
    if (filters.status && filters.status !== 'all') {
      result = result.filter((item) => item.status === filters.status)
    }

    return result
  }, [items, filters])

  if (loading) {
    return (
      <div className="p-4 space-y-2">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="flex items-center space-x-2 animate-pulse">
            <div className="w-4 h-4 bg-gray-200 rounded" />
            <div className="h-4 bg-gray-200 rounded flex-1" />
          </div>
        ))}
      </div>
    )
  }

  if (!folderRoot) {
    return (
      <div className="p-4 text-sm text-gray-500">
        No folder data available
      </div>
    )
  }

  // 총 파일 수 계산
  const getTotalFiles = (folder: NasFolder): number => {
    let total = folder.file_count
    for (const child of folder.children || []) {
      total += getTotalFiles(child)
    }
    return total
  }

  const totalFiles = getTotalFiles(folderRoot)

  return (
    <div className="h-full flex flex-col bg-white">
      {/* 헤더 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50">
        <div>
          <h3 className="text-sm font-medium text-gray-700">File Browser</h3>
          <p className="text-xs text-gray-500">
            {filteredItems.length.toLocaleString()} / {totalFiles.toLocaleString()} files
          </p>
        </div>

        {/* 컬럼 헤더 */}
        <div className="flex items-center gap-4 text-[10px] font-medium text-gray-500 uppercase">
          <span className="w-8 text-center">NAS</span>
          <span className="w-8 text-center">Sheet</span>
          <span className="w-8 text-center">UDM</span>
          <span className="w-16 text-center">Status</span>
          <span className="w-16 text-right">Size</span>
        </div>
      </div>

      {/* 트리 영역 */}
      <div className="flex-1 overflow-y-auto">
        <FolderNode
          folder={folderRoot}
          files={filteredItems}
          depth={0}
          expandedFiles={expandedFiles}
          onToggleFile={onToggleFile}
          defaultExpanded={true}
        />
      </div>
    </div>
  )
}
