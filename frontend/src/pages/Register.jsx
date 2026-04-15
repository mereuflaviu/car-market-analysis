import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({ display_name: '', email: '', phone: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const set = (k, v) => setForm((p) => ({ ...p, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await register(form)
      navigate('/app', { replace: true })
    } catch (err) {
      setError(err.message || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <Link to="/" className="text-2xl font-black tracking-tight text-black">AutoScope</Link>
          <p className="text-as-muted text-sm mt-1">Create your account</p>
        </div>

        <div className="card">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-as-body mb-1">Full Name *</label>
              <input
                type="text" className="input-field" value={form.display_name} autoFocus required
                onChange={(e) => set('display_name', e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-as-body mb-1">Email *</label>
              <input
                type="email" className="input-field" value={form.email} required
                onChange={(e) => set('email', e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-as-body mb-1">
                Phone <span className="text-as-muted font-normal">(optional)</span>
              </label>
              <input
                type="tel" className="input-field" value={form.phone}
                onChange={(e) => set('phone', e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-as-body mb-1">Password *</label>
              <input
                type="password" className="input-field" value={form.password} required minLength={8}
                onChange={(e) => set('password', e.target.value)}
              />
              <p className="text-xs text-as-muted mt-1">Minimum 8 characters</p>
            </div>
            {error && <p className="text-red-600 text-xs">{error}</p>}
            <button type="submit" className="btn-primary w-full py-2.5" disabled={loading}>
              {loading ? 'Creating account…' : 'Create account'}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-as-muted mt-4">
          Already have an account?{' '}
          <Link to="/login" className="text-black font-medium underline">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
