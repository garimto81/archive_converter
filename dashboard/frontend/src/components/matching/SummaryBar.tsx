import type { MatchingStats } from '@/types/matching'

interface SummaryBarProps {
  stats: MatchingStats | null
  loading?: boolean
}

export default function SummaryBar({ stats, loading }: SummaryBarProps) {
  if (loading) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 animate-pulse">
        <div className="flex items-center justify-between">
          <div className="flex space-x-8">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-5 bg-gray-200 rounded w-24" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (!stats) return null

  const nasFiles = stats.sources?.nas?.total_files || 0
  const sheetRecords = stats.matching?.segments?.total || 0
  const udmSegments = stats.matching?.segments?.complete || 0
  const matched = stats.matching?.files?.total_with_metadata || 0
  const unmatched = stats.matching?.files?.unmatched || 0
  const orphan = stats.matching?.orphan_records || 0

  const items = [
    { label: 'NAS', value: nasFiles, color: 'text-blue-600' },
    { label: 'Sheet', value: sheetRecords, color: 'text-purple-600' },
    { label: 'UDM', value: udmSegments, color: 'text-green-600' },
    { label: 'Matched', value: matched, color: 'text-emerald-600' },
    { label: 'Unmatched', value: unmatched, color: 'text-gray-500' },
    { label: 'Orphan', value: orphan, color: orphan > 0 ? 'text-red-600' : 'text-gray-400' },
  ]

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center space-x-6 md:space-x-8">
          {items.map((item) => (
            <div key={item.label} className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">{item.label}:</span>
              <span className={`text-sm font-semibold ${item.color}`}>
                {item.value.toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
