import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const NAV = [
  { to: '/app',            label: 'Dashboard' },
  { to: '/app/listings',   label: 'Listings' },
  { to: '/app/predict',    label: 'Predict Price' },
  { to: '/app/analytics',  label: 'Analytics' },
]

export default function AppLayout({ children }) {
  const { pathname } = useLocation()
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/')
  }

  return (
    <div className="min-h-screen bg-white">
      <header className="sticky top-0 z-50 bg-white border-b border-black">
        <div className="max-w-[1136px] mx-auto px-6 h-14 flex items-center gap-6">
          <Link to="/" className="font-bold text-lg text-black tracking-tight mr-4">
            AutoScope
          </Link>

          <nav className="flex items-center gap-2 flex-1">
            {NAV.map(({ to, label }) => {
              const active = pathname === to || (to !== '/app' && pathname.startsWith(to))
              return (
                <Link
                  key={to}
                  to={to}
                  className={`px-4 py-1.5 rounded-pill text-sm font-medium transition-colors ${
                    active ? 'bg-black text-white' : 'bg-as-chip text-black hover:bg-as-hover'
                  }`}
                >
                  {label}
                </Link>
              )
            })}
          </nav>

          <div className="flex items-center gap-2 ml-auto flex-shrink-0">
            {user ? (
              <>
                {user.role === 'admin' && (
                  <Link
                    to="/admin/users"
                    className={`px-3 py-1.5 rounded-pill text-xs font-semibold transition-colors ${
                      pathname.startsWith('/admin')
                        ? 'bg-black text-white'
                        : 'bg-as-chip text-black hover:bg-as-hover'
                    }`}
                  >
                    Admin
                  </Link>
                )}
                <span className="text-sm text-as-body font-medium hidden sm:block">
                  {user.display_name}
                </span>
                <button
                  onClick={handleLogout}
                  className="px-4 py-1.5 rounded-pill text-sm font-medium bg-as-chip text-black hover:bg-as-hover transition-colors"
                >
                  Log out
                </button>
              </>
            ) : (
              <>
                <Link to="/login"
                  className="px-4 py-1.5 rounded-pill text-sm font-medium bg-as-chip text-black hover:bg-as-hover transition-colors">
                  Log in
                </Link>
                <Link to="/register"
                  className="px-4 py-1.5 rounded-pill text-sm font-medium bg-black text-white hover:bg-as-body transition-colors">
                  Sign up
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-[1136px] mx-auto px-6 py-8">{children}</main>
    </div>
  )
}
