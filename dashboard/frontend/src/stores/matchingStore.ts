import { create } from 'zustand'
import type { MatchingItem, MatchingStats, FilterOptions } from '@/types/matching'

interface MatchingStore {
  // 상태
  items: MatchingItem[]
  stats: MatchingStats | null
  selectedFile: string | null
  expandedFiles: Set<string>
  filters: FilterOptions

  // 액션
  setItems: (items: MatchingItem[]) => void
  setStats: (stats: MatchingStats) => void
  setSelectedFile: (fileName: string | null) => void
  toggleFileExpansion: (fileName: string) => void
  setFilters: (filters: Partial<FilterOptions>) => void
  resetFilters: () => void

  // 계산된 값
  getFilteredItems: () => MatchingItem[]
}

const defaultFilters: FilterOptions = {
  status: 'all',
  searchQuery: '',
  sortBy: 'file_name',
  sortOrder: 'asc',
}

export const useMatchingStore = create<MatchingStore>((set, get) => ({
  // 초기 상태
  items: [],
  stats: null,
  selectedFile: null,
  expandedFiles: new Set(),
  filters: defaultFilters,

  // 액션
  setItems: (items) => set({ items: items || [] }),

  setStats: (stats) => set({ stats }),

  setSelectedFile: (fileName) => set({ selectedFile: fileName }),

  toggleFileExpansion: (fileName) =>
    set((state) => {
      const newExpanded = new Set(state.expandedFiles)
      if (newExpanded.has(fileName)) {
        newExpanded.delete(fileName)
      } else {
        newExpanded.add(fileName)
      }
      return { expandedFiles: newExpanded }
    }),

  setFilters: (filters) =>
    set((state) => ({
      filters: { ...state.filters, ...filters },
    })),

  resetFilters: () => set({ filters: defaultFilters }),

  // 계산된 값
  getFilteredItems: () => {
    const { items, filters } = get()

    // items가 배열이 아니면 빈 배열 반환
    if (!Array.isArray(items)) {
      return []
    }

    let filtered = [...items]

    // 상태 필터
    if (filters.status && filters.status !== 'all') {
      filtered = filtered.filter((item) => item.status === filters.status)
    }

    // 검색어 필터
    if (filters.searchQuery) {
      const query = filters.searchQuery.toLowerCase()
      filtered = filtered.filter((item) =>
        item.file_name.toLowerCase().includes(query)
      )
    }

    // 정렬
    if (filters.sortBy) {
      filtered.sort((a, b) => {
        let aVal: string | number
        let bVal: string | number

        switch (filters.sortBy) {
          case 'file_name':
            aVal = a.file_name
            bVal = b.file_name
            break
          case 'segment_count':
            aVal = a.segment_count
            bVal = b.segment_count
            break
          case 'status':
            aVal = a.status
            bVal = b.status
            break
          default:
            return 0
        }

        if (aVal < bVal) return filters.sortOrder === 'asc' ? -1 : 1
        if (aVal > bVal) return filters.sortOrder === 'asc' ? 1 : -1
        return 0
      })
    }

    return filtered
  },
}))
