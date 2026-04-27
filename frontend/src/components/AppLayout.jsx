import { useEffect, useRef } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { ThemeSwitcher } from './ui/theme-switcher'

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
  const headerRef = useRef(null)
  const spotlightRef = useRef(null)

  useEffect(() => {
    const onPointerMove = (e) => {
      if (!headerRef.current || !spotlightRef.current) return
      const rect = headerRef.current.getBoundingClientRect()
      const x = e.clientX - rect.left
      const y = e.clientY - rect.top
      const buffer = 80
      const nearNav = e.clientY <= rect.bottom + buffer
      spotlightRef.current.style.opacity = nearNav ? '1' : '0'
      spotlightRef.current.style.background = `radial-gradient(400px circle at ${x}px ${y}px, rgba(99,102,241,0.12), transparent 70%)`
    }
    document.addEventListener('pointermove', onPointerMove)
    return () => document.removeEventListener('pointermove', onPointerMove)
  }, [])

  const handleLogout = async () => {
    await logout()
    navigate('/')
  }

  return (
    <div className="min-h-screen page-bg transition-colors duration-200">
      <header ref={headerRef} data-dark-nav className="sticky top-0 z-50 bg-white border-b border-black overflow-hidden transition-colors duration-200">
        <div
          ref={spotlightRef}
          aria-hidden="true"
          style={{ opacity: 0, transition: 'opacity 0.3s ease' }}
          className="pointer-events-none absolute inset-0 z-0"
        />
        <div className="relative z-10 max-w-[1136px] mx-auto px-6 h-14 flex items-center gap-6">
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
                    active
                      ? 'bg-black text-white nav-pill-active'
                      : 'bg-as-chip text-black hover:bg-as-hover'
                  }`}
                >
                  {label}
                </Link>
              )
            })}
          </nav>

          <div className="flex items-center gap-3 ml-auto flex-shrink-0">
            <ThemeSwitcher />

            {user ? (
              <>
                {user.role === 'admin' && (
                  <>
                    <Link
                      to="/admin/users"
                      className={`px-3 py-1.5 rounded-pill text-xs font-semibold transition-colors ${
                        pathname === '/admin/users'
                          ? 'bg-black text-white nav-pill-active'
                          : 'bg-as-chip text-black hover:bg-as-hover'
                      }`}
                    >
                      Users
                    </Link>
                    <Link
                      to="/admin/pipeline"
                      className={`px-3 py-1.5 rounded-pill text-xs font-semibold transition-colors ${
                        pathname === '/admin/pipeline'
                          ? 'bg-black text-white nav-pill-active'
                          : 'bg-as-chip text-black hover:bg-as-hover'
                      }`}
                    >
                      Pipeline
                    </Link>
                  </>
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
