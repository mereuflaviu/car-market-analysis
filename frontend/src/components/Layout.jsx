import { Link, useLocation } from 'react-router-dom'

const NAV = [
  { to: '/', label: 'Dashboard', icon: '📊' },
  { to: '/listings', label: 'Listings', icon: '🚗' },
  { to: '/predict', label: 'Predict Price', icon: '🤖' },
  { to: '/analytics', label: 'Analytics', icon: '📈' },
]

export default function Layout({ children }) {
  const { pathname } = useLocation()

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      {/* Sidebar */}
      <aside className="w-60 flex-shrink-0 bg-slate-900 flex flex-col">
        <div className="px-6 py-5 border-b border-slate-700">
          <div className="text-white font-bold text-lg leading-tight">CarMarket</div>
          <div className="text-slate-400 text-xs mt-0.5">Price Analysis Platform</div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {NAV.map(({ to, label, icon }) => {
            const active = pathname === to
            return (
              <Link
                key={to}
                to={to}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  active
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                }`}
              >
                <span className="text-base">{icon}</span>
                {label}
              </Link>
            )
          })}
        </nav>

        <div className="px-6 py-4 border-t border-slate-700 space-y-0.5">
          <div className="text-slate-500 text-xs">Master VD · 2024</div>
          <div className="text-slate-600 text-xs">2,000 listings · XGBoost R²=0.895</div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">{children}</main>
    </div>
  )
}
