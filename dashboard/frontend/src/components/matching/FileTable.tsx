import { ChevronUp, ChevronDown } from 'lucide-react'
import type { MatchingItem, FilterOptions } from '@/types/matching'
import FileTableRow from './FileTableRow'

interface FileTableProps {
  items: MatchingItem[]
  expandedFiles: Set<string>
  onToggle: (fileName: string) => void
  loading?: boolean
  filters: FilterOptions
  onSort: (sortBy: FilterOptions['sortBy']) => void
}

export default function FileTable({
  items,
  expandedFiles,
  onToggle,
  loading,
  filters,
  onSort,
}: FileTableProps) {
  const columns = [
    { key: 'expand', label: '', width: 'w-10', sortable: false },
    { key: 'file_name', label: 'File Name', width: 'flex-1', sortable: true },
    { key: 'nas', label: 'NAS', width: 'w-16', sortable: false },
    { key: 'sheet', label: 'Sheet', width: 'w-16', sortable: false },
    { key: 'udm', label: 'UDM', width: 'w-16', sortable: false },
    { key: 'match', label: 'Match', width: 'w-24', sortable: false },
    { key: 'size', label: 'Size', width: 'w-20', sortable: false },
    { key: 'brand', label: 'Brand', width: 'w-24', sortable: false },
  ]

  const SortIcon = ({ columnKey }: { columnKey: string }) => {
    if (filters.sortBy !== columnKey) return null
    return filters.sortOrder === 'asc' ? (
      <ChevronUp className="w-4 h-4" />
    ) : (
      <ChevronDown className="w-4 h-4" />
    )
  }

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="divide-y divide-gray-100">
          {[...Array(10)].map((_, i) => (
            <div key={i} className="px-4 py-3 animate-pulse">
              <div className="flex items-center space-x-4">
                <div className="w-5 h-5 bg-gray-200 rounded" />
                <div className="flex-1 h-4 bg-gray-200 rounded" />
                <div className="w-12 h-4 bg-gray-200 rounded" />
                <div className="w-12 h-4 bg-gray-200 rounded" />
                <div className="w-12 h-4 bg-gray-200 rounded" />
                <div className="w-20 h-4 bg-gray-200 rounded" />
                <div className="w-16 h-4 bg-gray-200 rounded" />
                <div className="w-20 h-4 bg-gray-200 rounded" />
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
        <p className="text-gray-500">No files found</p>
      </div>
    )
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      {/* Table Header */}
      <div className="bg-gray-50 border-b border-gray-200 px-4 py-3">
        <div className="flex items-center text-xs font-medium text-gray-500 uppercase tracking-wider">
          {columns.map((col) => (
            <div
              key={col.key}
              className={`${col.width} ${col.sortable ? 'cursor-pointer hover:text-gray-700' : ''} flex items-center space-x-1`}
              onClick={() => col.sortable && onSort(col.key as FilterOptions['sortBy'])}
            >
              <span>{col.label}</span>
              {col.sortable && <SortIcon columnKey={col.key} />}
            </div>
          ))}
        </div>
      </div>

      {/* Table Body */}
      <div className="divide-y divide-gray-100">
        {items.map((item) => (
          <FileTableRow
            key={item.file_name}
            item={item}
            isExpanded={expandedFiles.has(item.file_name)}
            onToggle={() => onToggle(item.file_name)}
          />
        ))}
      </div>
    </div>
  )
}
