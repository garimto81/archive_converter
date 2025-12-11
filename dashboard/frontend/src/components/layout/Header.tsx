import { Link } from 'react-router-dom'
import { Database, Activity } from 'lucide-react'

export default function Header() {
  return (
    <header className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* 로고 및 타이틀 */}
          <div className="flex items-center space-x-3">
            <Database className="w-8 h-8 text-primary-600" />
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                Archive Converter Dashboard
              </h1>
              <p className="text-xs text-gray-500">
                분할 아카이브 매칭 관리 시스템
              </p>
            </div>
          </div>

          {/* 네비게이션 */}
          <nav className="flex space-x-4">
            <Link
              to="/matching"
              className="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50 transition-colors"
            >
              <Activity className="w-4 h-4" />
              <span>매칭 매트릭스</span>
            </Link>
          </nav>
        </div>
      </div>
    </header>
  )
}
