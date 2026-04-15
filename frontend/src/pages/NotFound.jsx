import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-6">
      <div className="max-w-sm text-center">
        <div className="text-[96px] font-black text-black leading-none mb-4">404</div>
        <h1 className="text-2xl font-bold text-black mb-2">Page not found</h1>
        <p className="text-as-body text-sm mb-8">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="flex gap-3 justify-center">
          <Link to="/app" className="btn-primary">
            Go to Dashboard
          </Link>
          <Link to="/" className="btn-secondary">
            Home
          </Link>
        </div>
      </div>
    </div>
  )
}
