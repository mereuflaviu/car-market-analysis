import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8001/api',
  headers: { 'Content-Type': 'application/json' },
  timeout: 15_000,
  withCredentials: true,   // send cookies on every request
})

// Attach API key for legacy mutation guard (production)
api.interceptors.request.use((config) => {
  const apiKey = import.meta.env.VITE_API_KEY
  if (apiKey) config.headers['X-API-Key'] = apiKey
  return config
})

// 401 → attempt one silent refresh, then retry original request
let _refreshing = false
let _queue = []

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config
    if (
      err.response?.status === 401 &&
      !original._retry &&
      !original.url?.includes('/auth/refresh') &&
      !original.url?.includes('/auth/login') &&
      !original.url?.includes('/auth/me')
    ) {
      if (_refreshing) {
        return new Promise((resolve, reject) => {
          _queue.push({ resolve, reject })
        })
          .then(() => api(original))
          .catch((e) => Promise.reject(e))
      }
      original._retry = true
      _refreshing = true
      try {
        await api.post('/auth/refresh')
        _queue.forEach((p) => p.resolve())
        _queue = []
        return api(original)
      } catch {
        _queue.forEach((p) => p.reject())
        _queue = []
        window.location.href = '/login'
        return Promise.reject(new Error('Session expired'))
      } finally {
        _refreshing = false
      }
    }

    if (err.code === 'ECONNABORTED') return Promise.reject(new Error('Request timed out.'))
    if (!err.response) return Promise.reject(new Error('Cannot reach the server.'))
    const detail = err.response?.data?.detail
    const message =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((d) => d.msg || d).join(', ')
          : `Server error (${err.response.status})`
    const normalized = new Error(message)
    normalized.status = err.response.status
    normalized.raw = err
    return Promise.reject(normalized)
  },
)

// ── Cars ──────────────────────────────────────────────────────────────────────
export const carsApi = {
  list: (params = {}) => api.get('/cars', { params }),
  get: (id) => api.get(`/cars/${id}`),
  create: (data) => api.post('/cars', data),
  update: (id, data) => api.put(`/cars/${id}`, data),
  delete: (id) => api.delete(`/cars/${id}`),
  stats: () => api.get('/cars/stats'),
  recommendations: (params) => api.get('/cars/recommendations', { params }),
}

// ── Predictions ───────────────────────────────────────────────────────────────
export const predictionsApi = {
  predict: (data) => api.post('/predictions/predict', data),
  history: (params = {}) => api.get('/predictions/history', { params }),
  get: (id) => api.get(`/predictions/${id}`),
  delete: (id) => api.delete(`/predictions/${id}`),
  modelInfo: () => api.get('/predictions/model-info'),
}

// ── Analytics ─────────────────────────────────────────────────────────────────
export const analyticsApi = {
  priceDistribution: () => api.get('/analytics/price-distribution'),
  priceByMake: () => api.get('/analytics/price-by-make'),
  priceByFuel: () => api.get('/analytics/price-by-fuel'),
  priceByBodyType: () => api.get('/analytics/price-by-body-type'),
  mileageVsPrice: () => api.get('/analytics/mileage-vs-price'),
  yearVsPrice: () => api.get('/analytics/year-vs-price'),
  gearboxDistribution: () => api.get('/analytics/gearbox-distribution'),
  transmissionDistribution: () => api.get('/analytics/transmission-distribution'),
}

// ── Makes / Options ───────────────────────────────────────────────────────────
export const makesApi = {
  list: () => api.get('/makes'),
  models: (make) => api.get(`/makes/${encodeURIComponent(make)}/models`),
  options: () => api.get('/makes/options'),
}

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authApi = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  logout: () => api.post('/auth/logout'),
  me: () => api.get('/auth/me'),
  refresh: () => api.post('/auth/refresh'),
}

// ── Admin ─────────────────────────────────────────────────────────────────────
export const adminApi = {
  listUsers: (params = {}) => api.get('/admin/users', { params }),
  updateUser: (id, data) => api.patch(`/admin/users/${id}`, data),
  deleteUser: (id) => api.delete(`/admin/users/${id}`),
}
