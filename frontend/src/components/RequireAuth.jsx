import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function Spinner() {
  return (
    <div className="flex items-center justify-center h-64 text-as-muted animate-pulse text-sm">
      Loading…
    </div>
  )
}

export function RequireAuth({ children }) {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <Spinner />
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />
  return children
}

export function RequireAdmin({ children }) {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <Spinner />
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />
  if (user.role !== 'admin') return <Navigate to="/app" replace />
  return children
}

export function RedirectIfAuth({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <Spinner />
  if (user) return <Navigate to="/app" replace />
  return children
}
