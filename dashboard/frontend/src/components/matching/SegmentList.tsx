import { CheckCircle2, XCircle, Clock, FileText, Tag } from 'lucide-react'
import type { SegmentRecord } from '@/types/matching'
import clsx from 'clsx'

interface SegmentListProps {
  segments: SegmentRecord[]
  loading?: boolean
}

export default function SegmentList({ segments, loading }: SegmentListProps) {
  if (loading) {
    return (
      <div className="bg-gray-50 px-6 py-4">
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-12 bg-gray-200 rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (!segments || segments.length === 0) {
    return (
      <div className="bg-gray-50 px-6 py-8 text-center">
        <p className="text-gray-500">세그먼트가 없습니다.</p>
      </div>
    )
  }

  const getStatusIcon = (segment: SegmentRecord) => {
    if (segment.udm?.status === 'complete') {
      return <CheckCircle2 className="w-4 h-4 text-green-600" />
    }
    if (segment.udm?.status === 'error') {
      return <XCircle className="w-4 h-4 text-red-600" />
    }
    if (segment.udm?.status === 'warning') {
      return <XCircle className="w-4 h-4 text-orange-600" />
    }
    return <Clock className="w-4 h-4 text-gray-400" />
  }

  const getStatusBadge = (segment: SegmentRecord) => {
    if (segment.udm?.status === 'complete') {
      return <span className="badge-success">UDM 완료</span>
    }
    if (segment.udm?.status === 'error') {
      return <span className="badge-error">오류</span>
    }
    if (segment.udm?.status === 'warning') {
      return <span className="badge-warning">경고</span>
    }
    return <span className="badge-info">대기 중</span>
  }

  const getSourceLabel = (source: string) => {
    switch (source) {
      case 'archive_metadata':
        return 'Archive'
      case 'iconik_metadata':
        return 'Iconik'
      default:
        return source
    }
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="bg-gray-50 border-t border-gray-200">
      <div className="px-6 py-3 bg-gray-100 border-b border-gray-200">
        <h4 className="text-sm font-semibold text-gray-700 flex items-center">
          <FileText className="w-4 h-4 mr-2" />
          세그먼트 목록 ({segments.length}개)
        </h4>
      </div>

      <div className="divide-y divide-gray-200">
        {segments.map((segment, index) => (
          <div
            key={`${segment.row_number}-${index}`}
            className={clsx(
              'px-6 py-4 hover:bg-gray-100 transition-colors',
              segment.udm?.status === 'error' && 'bg-red-50',
              segment.udm?.status === 'warning' && 'bg-orange-50'
            )}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3 flex-1">
                {getStatusIcon(segment)}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <p className="text-sm font-medium text-gray-900">
                      #{segment.row_number}
                    </p>
                    <span className="text-xs px-2 py-0.5 bg-gray-200 rounded">
                      {getSourceLabel(segment.source)}
                    </span>
                  </div>
                  <div className="flex items-center space-x-4 mt-1">
                    <span className="text-xs text-gray-500">
                      {segment.time_in} - {segment.time_out}
                    </span>
                    <span className="text-xs text-gray-500">
                      ({formatDuration(segment.duration_sec)})
                    </span>
                    {segment.rating !== null && (
                      <span className="text-xs text-yellow-600">
                        Rating: {segment.rating}
                      </span>
                    )}
                    {segment.winner && (
                      <span className="text-xs text-blue-600">
                        Winner: {segment.winner}
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {getStatusBadge(segment)}
              </div>
            </div>

            {/* 태그 표시 */}
            {segment.tags && segment.tags.length > 0 && (
              <div className="mt-2 ml-7 flex items-center space-x-2">
                <Tag className="w-3 h-3 text-gray-400" />
                <div className="flex flex-wrap gap-1">
                  {segment.tags.map((tag, tagIndex) => (
                    <span
                      key={tagIndex}
                      className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Hands 정보 */}
            {segment.hands && (
              <div className="mt-2 ml-7 text-xs text-gray-600">
                Hands: {segment.hands}
              </div>
            )}

            {/* UDM UUID */}
            {segment.udm?.uuid && (
              <div className="mt-1 ml-7 text-xs text-gray-400 font-mono truncate">
                UUID: {segment.udm.uuid}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
