import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8001/api',
  headers: { 'Content-Type': 'application/json' },
})

// ── Cars ──────────────────────────────────────────────────────────────────────
export const carsApi = {
  list: (params = {}) => api.get('/cars', { params }),
  get: (id) => api.get(`/cars/${id}`),
  create: (data) => api.post('/cars', data),
  update: (id, data) => api.put(`/cars/${id}`, data),
  delete: (id) => api.delete(`/cars/${id}`),
  stats: () => api.get('/cars/stats'),
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
