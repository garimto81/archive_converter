import type { SegmentRecord } from '@/types/matching'

interface ExpandedSegmentsProps {
  segments: SegmentRecord[]
}

export default function ExpandedSegments({ segments }: ExpandedSegmentsProps) {
  if (segments.length === 0) {
    return null
  }

  // Status indicator
  const StatusCheck = ({ hasData }: { hasData: boolean }) => (
    hasData ? (
      <span className="text-green-600">✓</span>
    ) : (
      <span className="text-gray-300">·</span>
    )
  )

  return (
    <div className="ml-10 mr-4 mb-4 bg-white border border-gray-200 rounded-lg overflow-hidden">
      {/* Segment Header */}
      <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
        <div className="flex items-center text-xs font-medium text-gray-500 uppercase tracking-wider">
          <div className="w-8">#</div>
          <div className="w-28">Time In</div>
          <div className="w-28">Time Out</div>
          <div className="flex-1">Player</div>
          <div className="w-32">Tags</div>
          <div className="w-14 text-center">Sheet</div>
          <div className="w-14 text-center">UDM</div>
        </div>
      </div>

      {/* Segment Rows */}
      <div className="divide-y divide-gray-100">
        {segments.map((segment, index) => {
          const hasSheet = true // Sheet 레코드에서 왔으므로 항상 true
          const hasUdm = segment.udm?.status === 'complete'

          return (
            <div
              key={segment.row_number || index}
              className="px-4 py-2 hover:bg-gray-50 flex items-center text-sm"
            >
              {/* Index */}
              <div className="w-8 text-gray-400 text-xs">
                {index + 1}
              </div>

              {/* Time In */}
              <div className="w-28 font-mono text-xs text-gray-600">
                {segment.time_in || '-'}
              </div>

              {/* Time Out */}
              <div className="w-28 font-mono text-xs text-gray-600">
                {segment.time_out || '-'}
              </div>

              {/* Player */}
              <div className="flex-1 text-gray-700 truncate">
                {segment.winner || '-'}
              </div>

              {/* Tags */}
              <div className="w-32">
                {segment.tags && segment.tags.length > 0 ? (
                  <div className="flex flex-wrap gap-1">
                    {segment.tags.slice(0, 2).map((tag, i) => (
                      <span
                        key={i}
                        className="text-xs bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded"
                      >
                        {tag}
                      </span>
                    ))}
                    {segment.tags.length > 2 && (
                      <span className="text-xs text-gray-400">
                        +{segment.tags.length - 2}
                      </span>
                    )}
                  </div>
                ) : (
                  <span className="text-gray-300">-</span>
                )}
              </div>

              {/* Sheet Status */}
              <div className="w-14 text-center">
                <StatusCheck hasData={hasSheet} />
              </div>

              {/* UDM Status */}
              <div className="w-14 text-center">
                <StatusCheck hasData={hasUdm} />
              </div>
            </div>
          )
        })}
      </div>

      {/* Footer Actions */}
      {segments.length > 0 && (
        <div className="bg-gray-50 px-4 py-2 border-t border-gray-200 flex items-center justify-between">
          <span className="text-xs text-gray-500">
            {segments.length} segment{segments.length !== 1 ? 's' : ''}
          </span>
          <div className="flex space-x-2">
            <button className="text-xs text-blue-600 hover:text-blue-800">
              View Details
            </button>
            <button className="text-xs text-blue-600 hover:text-blue-800">
              Export
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
