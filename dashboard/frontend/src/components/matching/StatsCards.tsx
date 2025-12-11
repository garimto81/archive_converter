import { FileArchive, CheckCircle2, AlertCircle, Clock, AlertTriangle } from 'lucide-react'
import type { MatchingStats } from '@/types/matching'

interface StatsCardsProps {
  stats: MatchingStats | null
  loading?: boolean
}

export default function StatsCards({ stats, loading }: StatsCardsProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="card p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-24 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-16"></div>
          </div>
        ))}
      </div>
    )
  }

  if (!stats) return null

  // Backend 응답에서 값 추출
  const fileStats = stats.matching?.files || { complete: 0, partial: 0, warning: 0, unmatched: 0, total_with_metadata: 0 }
  const segmentStats = stats.matching?.segments || { complete: 0, pending: 0, warning: 0, total: 0 }
  const coverage = stats.coverage || { segment_conversion_rate: 0 }

  const totalFiles = fileStats.complete + fileStats.partial + fileStats.warning + fileStats.unmatched
  const conversionRate = coverage.segment_conversion_rate || 0

  const cards = [
    {
      label: '총 파일 수',
      value: totalFiles,
      icon: FileArchive,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      showProgress: true,
    },
    {
      label: '완료된 파일',
      value: fileStats.complete,
      icon: CheckCircle2,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      showProgress: false,
    },
    {
      label: '부분/경고',
      value: fileStats.partial + fileStats.warning,
      icon: AlertTriangle,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
      showProgress: false,
    },
    {
      label: '대기 중',
      value: segmentStats.pending,
      icon: Clock,
      color: 'text-gray-600',
      bgColor: 'bg-gray-50',
      showProgress: false,
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {cards.map((card) => (
        <div key={card.label} className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">{card.label}</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {card.value?.toLocaleString() || 0}
              </p>
            </div>
            <div className={`${card.bgColor} p-3 rounded-lg`}>
              <card.icon className={`w-6 h-6 ${card.color}`} />
            </div>
          </div>

          {/* 전체 변환율 표시 (첫 번째 카드에만) */}
          {card.showProgress && (
            <div className="mt-4 pt-4 border-t border-gray-100">
              <p className="text-xs text-gray-500">UDM 변환율</p>
              <div className="flex items-center mt-1">
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-primary-600 h-2 rounded-full transition-all"
                    style={{ width: `${conversionRate}%` }}
                  />
                </div>
                <span className="ml-2 text-sm font-medium text-gray-900">
                  {conversionRate.toFixed(1)}%
                </span>
              </div>
            </div>
          )}
        </div>
      ))}

      {/* 추가 상세 통계 */}
      <div className="col-span-full mt-4">
        <div className="card p-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <p className="text-xs text-gray-500">총 세그먼트</p>
              <p className="text-lg font-semibold text-gray-900">
                {segmentStats.total.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">변환 완료</p>
              <p className="text-lg font-semibold text-green-600">
                {segmentStats.complete.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">경고</p>
              <p className="text-lg font-semibold text-orange-600">
                {segmentStats.warning.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">고아 레코드</p>
              <p className="text-lg font-semibold text-red-600">
                {(stats.matching?.orphan_records || 0).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
