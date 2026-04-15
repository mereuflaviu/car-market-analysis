import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ErrorBoundary from './components/ErrorBoundary'
import LandingLayout from './components/LandingLayout'
import AppLayout from './components/AppLayout'
import { RequireAdmin, RedirectIfAuth } from './components/RequireAuth'

const Landing    = lazy(() => import('./pages/Landing'))
const Dashboard  = lazy(() => import('./pages/Dashboard'))
const Listings   = lazy(() => import('./pages/Listings'))
const Prediction = lazy(() => import('./pages/Prediction'))
const Analytics  = lazy(() => import('./pages/Analytics'))
const Login      = lazy(() => import('./pages/Login'))
const Register   = lazy(() => import('./pages/Register'))
const AdminUsers = lazy(() => import('./pages/AdminUsers'))
const NotFound   = lazy(() => import('./pages/NotFound'))

function PageLoader() {
  return (
    <div className="flex items-center justify-center h-64 text-as-muted animate-pulse text-sm">
      Loading…
    </div>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <Suspense fallback={<PageLoader />}>
            <Routes>
              <Route path="/" element={<LandingLayout><Landing /></LandingLayout>} />

              <Route path="/login"    element={<RedirectIfAuth><Login /></RedirectIfAuth>} />
              <Route path="/register" element={<RedirectIfAuth><Register /></RedirectIfAuth>} />

              <Route path="/app"           element={<AppLayout><Dashboard /></AppLayout>} />
              <Route path="/app/listings"  element={<AppLayout><Listings /></AppLayout>} />
              <Route path="/app/predict"   element={<AppLayout><Prediction /></AppLayout>} />
              <Route path="/app/analytics" element={<AppLayout><Analytics /></AppLayout>} />

              <Route path="/admin/users" element={
                <RequireAdmin><AppLayout><AdminUsers /></AppLayout></RequireAdmin>
              } />

              <Route path="*" element={<NotFound />} />
            </Routes>
          </Suspense>
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  )
}
