import { useState } from 'react'
import { ChevronRight, ChevronDown, Folder, FolderOpen } from 'lucide-react'
import clsx from 'clsx'
import type { NasFolder } from '@/api/nas'

interface FolderTreeProps {
  root: NasFolder | null
  selectedPath: string | null
  onSelectFolder: (path: string | null) => void
  loading?: boolean
}

interface FolderNodeProps {
  folder: NasFolder
  depth: number
  selectedPath: string | null
  onSelect: (path: string | null) => void
  defaultExpanded?: boolean
}

function FolderNode({ folder, depth, selectedPath, onSelect, defaultExpanded = false }: FolderNodeProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)
  const hasChildren = folder.children && folder.children.length > 0
  const isSelected = selectedPath === folder.path
  const fileCount = folder.file_count
  const isEmpty = fileCount === 0 && !hasChildren

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (hasChildren) {
      setIsExpanded(!isExpanded)
    }
  }

  const handleSelect = () => {
    onSelect(isSelected ? null : folder.path)
  }

  return (
    <div>
      {/* Folder Row */}
      <div
        className={clsx(
          'flex items-center py-1.5 px-2 cursor-pointer rounded-md transition-colors',
          isSelected ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100',
          isEmpty && 'opacity-50'
        )}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
        onClick={handleSelect}
      >
        {/* Expand/Collapse Icon */}
        <span
          className={clsx(
            'w-4 h-4 flex items-center justify-center mr-1',
            hasChildren ? 'cursor-pointer' : 'invisible'
          )}
          onClick={handleToggle}
        >
          {hasChildren && (
            isExpanded ? (
              <ChevronDown className="w-3 h-3 text-gray-500" />
            ) : (
              <ChevronRight className="w-3 h-3 text-gray-500" />
            )
          )}
        </span>

        {/* Folder Icon */}
        {isExpanded ? (
          <FolderOpen className="w-4 h-4 text-amber-500 mr-2 flex-shrink-0" />
        ) : (
          <Folder className="w-4 h-4 text-amber-500 mr-2 flex-shrink-0" />
        )}

        {/* Folder Name */}
        <span className={clsx(
          'text-sm truncate flex-1',
          isSelected ? 'font-medium' : '',
          isEmpty ? 'text-gray-400' : ''
        )}>
          {folder.name}
        </span>

        {/* File Count */}
        <span className={clsx(
          'text-xs ml-2 flex-shrink-0',
          isSelected ? 'text-blue-600' : 'text-gray-400'
        )}>
          ({fileCount})
        </span>
      </div>

      {/* Children */}
      {isExpanded && hasChildren && (
        <div>
          {folder.children.map((child) => (
            <FolderNode
              key={child.path}
              folder={child}
              depth={depth + 1}
              selectedPath={selectedPath}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default function FolderTree({ root, selectedPath, onSelectFolder, loading }: FolderTreeProps) {
  if (loading) {
    return (
      <div className="p-4 space-y-2">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="flex items-center space-x-2 animate-pulse">
            <div className="w-4 h-4 bg-gray-200 rounded" />
            <div className="h-4 bg-gray-200 rounded flex-1" />
          </div>
        ))}
      </div>
    )
  }

  if (!root) {
    return (
      <div className="p-4 text-sm text-gray-500">
        No folder data
      </div>
    )
  }

  // Calculate total files recursively
  const getTotalFiles = (folder: NasFolder): number => {
    let total = folder.file_count
    for (const child of folder.children || []) {
      total += getTotalFiles(child)
    }
    return total
  }

  const totalFiles = getTotalFiles(root)

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="text-sm font-medium text-gray-700">Folders</h3>
        <p className="text-xs text-gray-500 mt-1">
          {totalFiles.toLocaleString()} files total
        </p>
      </div>

      {/* All Files Option */}
      <div
        className={clsx(
          'flex items-center py-2 px-4 cursor-pointer transition-colors border-b border-gray-100',
          selectedPath === null ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50'
        )}
        onClick={() => onSelectFolder(null)}
      >
        <Folder className="w-4 h-4 text-gray-400 mr-2" />
        <span className={clsx(
          'text-sm',
          selectedPath === null ? 'font-medium' : ''
        )}>
          All Files
        </span>
        <span className="text-xs text-gray-400 ml-auto">
          ({totalFiles})
        </span>
      </div>

      {/* Tree */}
      <div className="flex-1 overflow-y-auto py-2">
        <FolderNode
          folder={root}
          depth={0}
          selectedPath={selectedPath}
          onSelect={onSelectFolder}
          defaultExpanded={true}
        />
      </div>
    </div>
  )
}
