import { ChevronDown, ChevronRight, FileArchive } from 'lucide-react'
import clsx from 'clsx'
import type { MatchingItem } from '@/types/matching'
import SegmentList from './SegmentList'

interface FileRowProps {
  item: MatchingItem
  isExpanded: boolean
  onToggle: () => void
  loading?: boolean
}

export default function FileRow({ item, isExpanded, onToggle, loading }: FileRowProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'complete':
        return 'bg-green-50 border-green-200'
      case 'partial':
        return 'bg-yellow-50 border-yellow-200'
      case 'warning':
        return 'bg-orange-50 border-orange-200'
      case 'no_metadata':
        return 'bg-gray-50 border-gray-200'
      case 'orphan':
        return 'bg-red-50 border-red-200'
      default:
        return 'bg-gray-50 border-gray-200'
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'complete':
        return <span className="badge-success">완료</span>
      case 'partial':
        return <span className="badge-warning">부분</span>
      case 'warning':
        return <span className="badge-error">경고</span>
      case 'no_metadata':
        return <span className="badge-info">메타데이터 없음</span>
      case 'orphan':
        return <span className="badge-error">고아 레코드</span>
      default:
        return <span className="badge-info">대기</span>
    }
  }

  // UDM 변환율 계산 (udm_count / segment_count * 100)
  const conversionRate = item.segment_count > 0
    ? (item.udm_count / item.segment_count) * 100
    : 0

  // NAS 파일 크기 포맷
  const formatSize = (sizeMb: number | undefined) => {
    if (!sizeMb) return '-'
    if (sizeMb >= 1024) {
      return `${(sizeMb / 1024).toFixed(1)} GB`
    }
    return `${sizeMb.toFixed(1)} MB`
  }

  return (
    <div className={clsx('card overflow-hidden', getStatusColor(item.status))}>
      {/* 파일 정보 행 */}
      <div
        className="px-6 py-4 cursor-pointer hover:bg-white/50 transition-colors"
        onClick={onToggle}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3 flex-1 min-w-0">
            <button className="text-gray-400 hover:text-gray-600 transition-colors">
              {isExpanded ? (
                <ChevronDown className="w-5 h-5" />
              ) : (
                <ChevronRight className="w-5 h-5" />
              )}
            </button>

            <FileArchive className="w-5 h-5 text-gray-400 flex-shrink-0" />

            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-medium text-gray-900 truncate">
                {item.file_name}
              </h3>
              <p className="text-xs text-gray-500 mt-1">
                {item.nas?.exists
                  ? `${formatSize(item.nas.size_mb)} | ${item.nas.inferred_brand || 'Unknown Brand'}`
                  : 'NAS 파일 없음'
                }
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-6 ml-4">
            {/* 세그먼트 정보 */}
            <div className="text-right">
              <p className="text-sm font-medium text-gray-900">
                {item.udm_count} / {item.segment_count}
              </p>
              <p className="text-xs text-gray-500">UDM 변환</p>
            </div>

            {/* 변환율 */}
            <div className="text-right min-w-[80px]">
              <p className="text-sm font-bold text-gray-900">
                {conversionRate.toFixed(1)}%
              </p>
              <div className="w-20 bg-gray-200 rounded-full h-1.5 mt-1">
                <div
                  className={clsx(
                    'h-1.5 rounded-full transition-all',
                    item.status === 'complete' && 'bg-green-600',
                    item.status === 'partial' && 'bg-yellow-600',
                    item.status === 'warning' && 'bg-orange-600',
                    item.status === 'pending' && 'bg-gray-400',
                    item.status === 'no_metadata' && 'bg-gray-400',
                    item.status === 'orphan' && 'bg-red-600'
                  )}
                  style={{ width: `${conversionRate}%` }}
                />
              </div>
            </div>

            {/* 상태 배지 */}
            <div className="min-w-[100px] text-right">
              {getStatusBadge(item.status)}
            </div>
          </div>
        </div>

        {/* 상세 정보 - 경고 표시 */}
        {item.warnings && item.warnings.length > 0 && (
          <div className="flex items-center space-x-4 mt-2 ml-8 text-xs text-orange-600">
            <span>경고: {item.warnings.length}개</span>
          </div>
        )}

        {/* 상태 상세 */}
        {item.status_detail && (
          <div className="mt-2 ml-8 text-xs text-gray-500">
            {item.status_detail}
          </div>
        )}
      </div>

      {/* 세그먼트 목록 (확장 시) */}
      {isExpanded && <SegmentList segments={item.segments} loading={loading} />}
    </div>
  )
}
