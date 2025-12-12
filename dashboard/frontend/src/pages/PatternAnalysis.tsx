/**
 * Pattern Analysis Page
 *
 * 파일명 패턴 매칭 분석 및 통계 페이지
 */

import { useState, useEffect } from 'react'
import { Search, RefreshCw, CheckCircle, XCircle, AlertTriangle, BarChart3, List, FileQuestion } from 'lucide-react'
import {
  fetchPatternStats,
  fetchPatternList,
  fetchUnmatchedFiles,
  testPattern,
  refreshPatternCache,
  type PatternStats,
  type PatternInfo,
  type UnmatchedFile,
} from '../api/pattern'

// =============================================================================
// Components
// =============================================================================

function StatsCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color,
}: {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ElementType
  color: 'blue' | 'green' | 'red' | 'yellow'
}) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
    green: 'bg-green-50 text-green-600 border-green-200',
    red: 'bg-red-50 text-red-600 border-red-200',
    yellow: 'bg-yellow-50 text-yellow-600 border-yellow-200',
  }

  return (
    <div className={`p-4 rounded-lg border ${colorClasses[color]}`}>
      <div className="flex items-center gap-3">
        <Icon className="w-8 h-8" />
        <div>
          <div className="text-2xl font-bold">{value}</div>
          <div className="text-sm font-medium">{title}</div>
          {subtitle && <div className="text-xs opacity-75">{subtitle}</div>}
        </div>
      </div>
    </div>
  )
}

function PatternTable({ patterns }: { patterns: PatternInfo[] }) {
  const categoryColors: Record<string, string> = {
    'WSOP Archive': 'bg-blue-100 text-blue-800',
    'WSOP Modern': 'bg-indigo-100 text-indigo-800',
    'WSOP Short Code': 'bg-purple-100 text-purple-800',
    'WSOP Europe': 'bg-pink-100 text-pink-800',
    'Circuit/Paradise': 'bg-green-100 text-green-800',
    'PAD': 'bg-yellow-100 text-yellow-800',
    'GGMillions': 'bg-orange-100 text-orange-800',
    'GOG': 'bg-red-100 text-red-800',
    'HCL': 'bg-cyan-100 text-cyan-800',
    'Hand Clip': 'bg-teal-100 text-teal-800',
    'ESPN': 'bg-gray-100 text-gray-800',
    'Generic': 'bg-slate-100 text-slate-800',
    'Other': 'bg-zinc-100 text-zinc-800',
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              패턴명
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              카테고리
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              정규식
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              매칭 수
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {patterns.map((pattern) => (
            <tr key={pattern.name} className="hover:bg-gray-50">
              <td className="px-4 py-3 text-sm font-mono text-gray-900">
                {pattern.name}
              </td>
              <td className="px-4 py-3">
                <span
                  className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                    categoryColors[pattern.category] || categoryColors['Other']
                  }`}
                >
                  {pattern.category}
                </span>
              </td>
              <td className="px-4 py-3 text-xs font-mono text-gray-500 max-w-xs truncate">
                {pattern.regex}
              </td>
              <td className="px-4 py-3 text-sm text-right font-medium text-gray-900">
                {pattern.match_count}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function UnmatchedTable({ files }: { files: UnmatchedFile[] }) {
  const categoryColors: Record<string, string> = {
    'en-dash char': 'bg-orange-100 text-orange-800',
    'special symbol': 'bg-red-100 text-red-800',
    'non-standard': 'bg-gray-100 text-gray-800',
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              파일명
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              추정 원인
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              이유
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {files.map((file, idx) => (
            <tr key={idx} className="hover:bg-gray-50">
              <td className="px-4 py-3 text-sm font-mono text-gray-900">
                {file.file_name}
              </td>
              <td className="px-4 py-3">
                {file.suggested_category && (
                  <span
                    className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                      categoryColors[file.suggested_category] || categoryColors['non-standard']
                    }`}
                  >
                    {file.suggested_category}
                  </span>
                )}
              </td>
              <td className="px-4 py-3 text-sm text-gray-500">
                {file.reason}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function PatternTester() {
  const [testFileName, setTestFileName] = useState('')
  const [testResult, setTestResult] = useState<{
    matched: boolean
    pattern_name: string | null
    extracted_groups: Record<string, string | number | null>
  } | null>(null)
  const [testing, setTesting] = useState(false)

  const handleTest = async () => {
    if (!testFileName.trim()) return
    setTesting(true)
    try {
      const result = await testPattern({ file_name: testFileName })
      setTestResult({
        matched: result.matched,
        pattern_name: result.pattern_name,
        extracted_groups: result.extracted_groups,
      })
    } catch {
      setTestResult(null)
    } finally {
      setTesting(false)
    }
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <Search className="w-5 h-5" />
        패턴 테스트
      </h3>
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={testFileName}
          onChange={(e) => setTestFileName(e.target.value)}
          placeholder="파일명을 입력하세요 (예: WCLA24-15.mp4)"
          className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          onKeyDown={(e) => e.key === 'Enter' && handleTest()}
        />
        <button
          onClick={handleTest}
          disabled={testing || !testFileName.trim()}
          className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {testing ? '테스트 중...' : '테스트'}
        </button>
      </div>

      {testResult && (
        <div
          className={`p-3 rounded-md ${
            testResult.matched ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
          }`}
        >
          <div className="flex items-center gap-2 mb-2">
            {testResult.matched ? (
              <CheckCircle className="w-5 h-5 text-green-600" />
            ) : (
              <XCircle className="w-5 h-5 text-red-600" />
            )}
            <span className={`font-medium ${testResult.matched ? 'text-green-800' : 'text-red-800'}`}>
              {testResult.matched ? '매칭됨' : '미매칭'}
            </span>
            {testResult.pattern_name && (
              <span className="text-sm text-gray-600">
                패턴: <code className="bg-gray-100 px-1 rounded">{testResult.pattern_name}</code>
              </span>
            )}
          </div>
          {testResult.matched && Object.keys(testResult.extracted_groups).length > 0 && (
            <div className="mt-2 text-sm">
              <span className="text-gray-600">추출된 필드:</span>
              <div className="mt-1 flex flex-wrap gap-2">
                {Object.entries(testResult.extracted_groups).map(([key, value]) => (
                  <span key={key} className="bg-white px-2 py-1 rounded border border-gray-200">
                    <span className="text-gray-500">{key}:</span>{' '}
                    <span className="font-mono">{String(value)}</span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// =============================================================================
// Main Page Component
// =============================================================================

export default function PatternAnalysis() {
  const [stats, setStats] = useState<PatternStats | null>(null)
  const [patterns, setPatterns] = useState<PatternInfo[]>([])
  const [unmatchedFiles, setUnmatchedFiles] = useState<UnmatchedFile[]>([])
  const [activeTab, setActiveTab] = useState<'patterns' | 'unmatched'>('patterns')
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [statsData, patternsData, unmatchedData] = await Promise.all([
        fetchPatternStats(),
        fetchPatternList(100),
        fetchUnmatchedFiles(100),
      ])
      setStats(statsData)
      setPatterns(patternsData.patterns)
      setUnmatchedFiles(unmatchedData.files)
    } catch (error) {
      console.error('Failed to load pattern data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      await refreshPatternCache()
      await loadData()
    } catch (error) {
      console.error('Failed to refresh:', error)
    } finally {
      setRefreshing(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">패턴 분석</h1>
          <p className="text-sm text-gray-500 mt-1">
            파일명 패턴 매칭 통계 및 분석
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          새로고침
        </button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatsCard
            title="전체 파일"
            value={stats.total_files.toLocaleString()}
            icon={BarChart3}
            color="blue"
          />
          <StatsCard
            title="매칭된 파일"
            value={stats.matched_files.toLocaleString()}
            subtitle={`${stats.match_rate}%`}
            icon={CheckCircle}
            color="green"
          />
          <StatsCard
            title="미매칭 파일"
            value={stats.unmatched_files.toLocaleString()}
            subtitle={`${(100 - stats.match_rate).toFixed(1)}%`}
            icon={AlertTriangle}
            color="yellow"
          />
          <StatsCard
            title="등록 패턴"
            value={stats.total_patterns}
            subtitle={`신뢰도 ${stats.avg_confidence}%`}
            icon={List}
            color="blue"
          />
        </div>
      )}

      {/* Pattern Tester */}
      <PatternTester />

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('patterns')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'patterns'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <List className="w-4 h-4 inline-block mr-2" />
            패턴 목록 ({patterns.length})
          </button>
          <button
            onClick={() => setActiveTab('unmatched')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'unmatched'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <FileQuestion className="w-4 h-4 inline-block mr-2" />
            미매칭 파일 ({unmatchedFiles.length})
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-lg border border-gray-200">
        {activeTab === 'patterns' ? (
          <PatternTable patterns={patterns} />
        ) : (
          <UnmatchedTable files={unmatchedFiles} />
        )}
      </div>
    </div>
  )
}
