import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from?.pathname || '/app'

  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const set = (k, v) => setForm((p) => ({ ...p, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await login(form.email, form.password)
      navigate(from, { replace: true })
    } catch (err) {
      setError(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <Link to="/" className="text-2xl font-black tracking-tight text-black">AutoScope</Link>
          <p className="text-as-muted text-sm mt-1">Sign in to your account</p>
        </div>

        <div className="card">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-as-body mb-1">Email</label>
              <input
                type="email" className="input-field" value={form.email} autoFocus required
                onChange={(e) => set('email', e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-as-body mb-1">Password</label>
              <input
                type="password" className="input-field" value={form.password} required
                onChange={(e) => set('password', e.target.value)}
              />
            </div>
            {error && <p className="text-red-600 text-xs">{error}</p>}
            <button type="submit" className="btn-primary w-full py-2.5" disabled={loading}>
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-as-muted mt-4">
          No account?{' '}
          <Link to="/register" className="text-black font-medium underline">Create one</Link>
        </p>
      </div>
    </div>
  )
}
