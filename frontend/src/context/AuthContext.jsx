import { createContext, useContext, useEffect, useReducer } from 'react'
import { authApi } from '../api/client'

const AuthContext = createContext(null)

function reducer(state, action) {
  switch (action.type) {
    case 'SET_USER':   return { user: action.user,  loading: false }
    case 'CLEAR_USER': return { user: null,          loading: false }
    default:           return state
  }
}

export function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, { user: null, loading: true })

  useEffect(() => {
    authApi.me()
      .then((r) => dispatch({ type: 'SET_USER', user: r.data }))
      .catch(() => dispatch({ type: 'CLEAR_USER' }))
  }, [])

  const login = async (email, password) => {
    const r = await authApi.login({ email, password })
    dispatch({ type: 'SET_USER', user: r.data })
    return r.data
  }

  const register = async (data) => {
    const r = await authApi.register(data)
    dispatch({ type: 'SET_USER', user: r.data })
    return r.data
  }

  const logout = async () => {
    await authApi.logout().catch(() => {})
    dispatch({ type: 'CLEAR_USER' })
  }

  return (
    <AuthContext.Provider value={{ ...state, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
