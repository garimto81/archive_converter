import { ChevronRight, ChevronDown } from 'lucide-react'
import clsx from 'clsx'
import type { MatchingItem } from '@/types/matching'
import ExpandedSegments from './ExpandedSegments'

interface FileTableRowProps {
  item: MatchingItem
  isExpanded: boolean
  onToggle: () => void
}

export default function FileTableRow({ item, isExpanded, onToggle }: FileTableRowProps) {
  // Status indicator
  const getStatusStyle = (status: string) => {
    switch (status) {
      case 'complete':
        return 'text-green-600'
      case 'partial':
        return 'text-amber-600'
      case 'warning':
        return 'text-orange-600'
      case 'orphan':
        return 'text-red-600'
      default:
        return 'text-gray-400'
    }
  }

  // Format file size
  const formatSize = (sizeMb: number | undefined) => {
    if (!sizeMb) return '-'
    if (sizeMb >= 1024) {
      return `${(sizeMb / 1024).toFixed(1)}GB`
    }
    return `${sizeMb.toFixed(0)}MB`
  }

  // Calculate match ratio
  const matchRatio = item.segment_count > 0
    ? (item.udm_count / item.segment_count) * 100
    : 0

  // Match display
  const getMatchDisplay = () => {
    if (item.status === 'orphan') {
      return <span className="text-red-600 text-xs font-medium">orphan</span>
    }
    if (item.segment_count === 0) {
      return <span className="text-gray-400">-</span>
    }
    const isComplete = item.udm_count === item.segment_count && item.segment_count > 0
    return (
      <div className="flex items-center space-x-1">
        <span className={clsx(
          'text-sm',
          isComplete ? 'text-green-600 font-medium' : 'text-gray-700'
        )}>
          {item.udm_count}/{item.segment_count}
        </span>
        <span className={clsx(
          'text-xs',
          matchRatio === 100 ? 'text-green-600' :
          matchRatio >= 50 ? 'text-amber-600' : 'text-gray-500'
        )}>
          {matchRatio.toFixed(0)}%
        </span>
        {isComplete && <span className="text-green-600">✓</span>}
      </div>
    )
  }

  // Check mark or dot
  const StatusDot = ({ exists, count }: { exists?: boolean; count?: number }) => {
    if (count !== undefined) {
      return count > 0 ? (
        <span className="text-sm font-medium text-gray-700">{count}</span>
      ) : (
        <span className="text-gray-300">·</span>
      )
    }
    return exists ? (
      <span className="text-green-600">✓</span>
    ) : (
      <span className="text-gray-300">·</span>
    )
  }

  return (
    <div className={clsx(
      'transition-colors',
      isExpanded && 'bg-gray-50'
    )}>
      {/* Main Row */}
      <div
        className="px-4 py-3 cursor-pointer hover:bg-gray-50 flex items-center"
        onClick={onToggle}
      >
        {/* Expand Icon */}
        <div className="w-10 flex-shrink-0">
          {item.segment_count > 0 ? (
            isExpanded ? (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-gray-400" />
            )
          ) : (
            <span className="w-4" />
          )}
        </div>

        {/* File Name */}
        <div className="flex-1 min-w-0 pr-4">
          <span className={clsx(
            'text-sm truncate block',
            getStatusStyle(item.status)
          )}>
            {item.file_name}
          </span>
        </div>

        {/* NAS */}
        <div className="w-16 text-center flex-shrink-0">
          <StatusDot exists={item.nas?.exists} />
        </div>

        {/* Sheet */}
        <div className="w-16 text-center flex-shrink-0">
          <StatusDot count={item.segment_count} />
        </div>

        {/* UDM */}
        <div className="w-16 text-center flex-shrink-0">
          <StatusDot count={item.udm_count} />
        </div>

        {/* Match */}
        <div className="w-24 text-center flex-shrink-0">
          {getMatchDisplay()}
        </div>

        {/* Size */}
        <div className="w-20 text-right flex-shrink-0">
          <span className="text-sm text-gray-500">
            {formatSize(item.nas?.size_mb)}
          </span>
        </div>

        {/* Brand */}
        <div className="w-24 text-right flex-shrink-0">
          <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
            {item.nas?.inferred_brand || '-'}
          </span>
        </div>
      </div>

      {/* Expanded Segments */}
      {isExpanded && item.segments.length > 0 && (
        <ExpandedSegments segments={item.segments} />
      )}
    </div>
  )
}
