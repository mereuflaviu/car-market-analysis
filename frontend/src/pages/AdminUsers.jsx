import { useState, useEffect, useCallback } from 'react'
import { adminApi } from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function AdminUsers() {
  const { user: currentUser } = useAuth()
  const [users, setUsers] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(false)
  const PAGE_SIZE = 20

  const fetchUsers = useCallback(async (p, s) => {
    setLoading(true)
    try {
      const r = await adminApi.listUsers({ page: p, page_size: PAGE_SIZE, search: s })
      setUsers(r.data.items)
      setTotal(r.data.total)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchUsers(page, search) }, [page, search, fetchUsers])

  const toggleRole = async (u) => {
    const newRole = u.role === 'admin' ? 'user' : 'admin'
    await adminApi.updateUser(u.id, { role: newRole })
    fetchUsers(page, search)
  }

  const toggleBan = async (u) => {
    await adminApi.updateUser(u.id, { is_active: !u.is_active })
    fetchUsers(page, search)
  }

  const handleDelete = async (u) => {
    if (!window.confirm(`Delete ${u.display_name}? This cannot be undone.`)) return
    await adminApi.deleteUser(u.id)
    fetchUsers(page, search)
  }

  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[32px] font-bold text-black leading-tight">User Management</h1>
        <p className="text-sm text-as-body mt-1">{total.toLocaleString()} registered users</p>
      </div>

      <div className="card p-4">
        <input
          type="search"
          className="input-field max-w-sm"
          placeholder="Search by name or email…"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1) }}
        />
      </div>

      {loading ? (
        <div className="card flex items-center justify-center h-40 text-as-muted animate-pulse">Loading…</div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-[#f9f9f9] border-b border-[#e8e8e8]">
                <tr>
                  {['Name', 'Email', 'Phone', 'Role', 'Status', 'Joined', 'Actions'].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-as-muted uppercase tracking-wider whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f0f0f0]">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-as-chip transition-colors">
                    <td className="px-4 py-3 font-medium whitespace-nowrap">{u.display_name}</td>
                    <td className="px-4 py-3 text-as-body">{u.email}</td>
                    <td className="px-4 py-3 text-as-muted">{u.phone || '—'}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                        u.role === 'admin' ? 'bg-black text-white' : 'bg-as-chip text-as-body'
                      }`}>
                        {u.role}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                        u.is_active ? 'bg-[#f0f0f0] text-as-body' : 'bg-red-50 text-red-600'
                      }`}>
                        {u.is_active ? 'Active' : 'Banned'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-as-muted text-xs whitespace-nowrap">
                      {u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}
                    </td>
                    <td className="px-4 py-3">
                      {u.id !== currentUser?.id && (
                        <div className="flex gap-1">
                          <button
                            className="text-xs px-2 py-1 rounded bg-as-chip hover:bg-as-hover text-black transition-colors"
                            onClick={() => toggleRole(u)}
                            title={u.role === 'admin' ? 'Demote to user' : 'Promote to admin'}
                          >
                            {u.role === 'admin' ? 'Demote' : 'Promote'}
                          </button>
                          <button
                            className={`text-xs px-2 py-1 rounded transition-colors ${
                              u.is_active
                                ? 'bg-red-50 text-red-600 hover:bg-red-100'
                                : 'bg-[#f0f0f0] text-as-body hover:bg-as-hover'
                            }`}
                            onClick={() => toggleBan(u)}
                          >
                            {u.is_active ? 'Ban' : 'Unban'}
                          </button>
                          <button
                            className="text-xs px-2 py-1 rounded text-as-muted hover:text-black transition-colors"
                            onClick={() => handleDelete(u)}
                          >
                            ×
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center gap-3 justify-center px-4 py-3 border-t border-[#f0f0f0] text-sm">
              <button className="btn-secondary py-1 px-3 disabled:opacity-40"
                disabled={page === 1} onClick={() => setPage(page - 1)}>← Prev</button>
              <span className="text-as-muted">Page {page} / {totalPages}</span>
              <button className="btn-secondary py-1 px-3 disabled:opacity-40"
                disabled={page === totalPages} onClick={() => setPage(page + 1)}>Next →</button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
