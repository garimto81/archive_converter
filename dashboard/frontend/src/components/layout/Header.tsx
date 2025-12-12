import { useState, useRef, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Database, Activity, FileJson, Info } from 'lucide-react'
import { VERSION, CHANGELOG, BUILD_TIME } from '@/version'

export default function Header() {
  const location = useLocation()
  const [showChangelog, setShowChangelog] = useState(false)
  const changelogRef = useRef<HTMLDivElement>(null)

  // Close changelog when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (changelogRef.current && !changelogRef.current.contains(event.target as Node)) {
        setShowChangelog(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const navItems = [
    { path: '/matching', label: '매칭 매트릭스', icon: Activity },
    { path: '/udm', label: 'UDM Viewer', icon: FileJson },
  ]

  return (
    <header className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* 로고 및 타이틀 */}
          <div className="flex items-center space-x-3">
            <Database className="w-8 h-8 text-primary-600" />
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-gray-900">
                  Archive Converter Dashboard
                </h1>
                {/* Version Badge */}
                <div className="relative" ref={changelogRef}>
                  <button
                    onClick={() => setShowChangelog(!showChangelog)}
                    className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs font-medium rounded-full hover:bg-blue-200 transition-colors"
                    title="Click to see changelog"
                  >
                    v{VERSION}
                    <Info className="w-3 h-3" />
                  </button>

                  {/* Changelog Popover */}
                  {showChangelog && (
                    <div className="absolute left-0 top-full mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-xl z-50">
                      <div className="p-3 border-b border-gray-100">
                        <h3 className="font-semibold text-gray-900">Changelog</h3>
                        <p className="text-xs text-gray-400 mt-0.5">Build: {BUILD_TIME}</p>
                      </div>
                      <div className="max-h-64 overflow-y-auto p-2">
                        {CHANGELOG.map((release, idx) => (
                          <div
                            key={release.version}
                            className={`p-2 ${idx > 0 ? 'border-t border-gray-100' : ''}`}
                          >
                            <div className="flex items-center gap-2 mb-1">
                              <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${
                                idx === 0 ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                              }`}>
                                v{release.version}
                              </span>
                              <span className="text-xs text-gray-400">{release.date}</span>
                            </div>
                            <ul className="text-xs text-gray-600 space-y-0.5">
                              {release.changes.map((change, i) => (
                                <li key={i} className="flex items-start gap-1">
                                  <span className="text-gray-400 mt-0.5">-</span>
                                  <span>{change}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
              <p className="text-xs text-gray-500">
                {CHANGELOG[0]?.changes[0] || '분할 아카이브 매칭 관리 시스템'}
              </p>
            </div>
          </div>

          {/* 네비게이션 */}
          <nav className="flex space-x-2">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path

              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </nav>
        </div>
      </div>
    </header>
  )
}
