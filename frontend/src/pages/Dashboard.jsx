import { useState, useEffect } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from 'recharts'
import { carsApi, analyticsApi, predictionsApi } from '../api/client'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#ec4899']

function KpiCard({ label, value, sub }) {
  return (
    <div className="card py-4">
      <div className="text-xs text-as-muted uppercase tracking-wider font-semibold mb-1">{label}</div>
      <div className="text-3xl font-bold text-black">{value}</div>
      {sub && <div className="text-xs text-as-muted mt-1">{sub}</div>}
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [priceDist, setPriceDist] = useState([])
  const [gearbox, setGearbox] = useState([])
  const [modelInfo, setModelInfo] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      carsApi.stats().catch(() => null),
      analyticsApi.priceDistribution().catch(() => null),
      analyticsApi.gearboxDistribution().catch(() => null),
      predictionsApi.modelInfo().catch(() => null),
    ])
      .then(([s, pd, gb, mi]) => {
        if (s) setStats(s.data)
        if (pd) setPriceDist(pd.data.data || [])
        if (gb) setGearbox(gb.data.data || [])
        if (mi) setModelInfo(mi.data)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-as-muted animate-pulse">
        Loading dashboard…
      </div>
    )
  }

  const fmt = (n) => (n != null ? Number(n).toLocaleString() : '—')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[32px] font-bold text-black leading-tight">Dashboard</h1>
        <p className="text-as-body text-sm mt-1">Overview of the used car market dataset</p>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <KpiCard label="Total Listings" value={fmt(stats?.total_cars)} sub="Cars in database" />
        <KpiCard
          label="Average Price"
          value={`€${fmt(Math.round(stats?.avg_price ?? 0))}`}
          sub={`€${fmt(Math.round(stats?.min_price ?? 0))} – €${fmt(Math.round(stats?.max_price ?? 0))}`}
        />
        <KpiCard label="Car Brands" value={stats?.total_makes ?? '—'} sub="Unique manufacturers" />
        <KpiCard label="Avg Mileage" value={`${fmt(Math.round(stats?.avg_mileage ?? 0))} km`} sub="Across all listings" />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Price Distribution */}
        <div className="card">
          <h2 className="font-semibold text-black mb-4">Price Distribution</h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={priceDist} margin={{ top: 4, right: 8, left: 0, bottom: 48 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="range"
                tick={{ fontSize: 10 }}
                angle={-45}
                textAnchor="end"
                interval={2}
              />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => [v, 'Cars']} labelFormatter={(l) => `Price from ${l}`} />
              <Bar dataKey="count" fill="#3b82f6" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Gearbox Pie */}
        <div className="card">
          <h2 className="font-semibold text-black mb-4">Gearbox Distribution</h2>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie
                data={gearbox}
                cx="50%"
                cy="45%"
                outerRadius={88}
                dataKey="count"
                nameKey="gearbox"
                label={({ gearbox: g, percent }) => `${g} (${(percent * 100).toFixed(0)}%)`}
                labelLine
              >
                {gearbox.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(v, _n, p) => [v, p.payload.gearbox]} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ML model banner */}
      <div className="card flex items-start gap-4 py-4">
        <div className="text-3xl">🤖</div>
        <div className="flex-1">
          <div className="font-semibold text-black">ML Model: XGBoost Price Predictor</div>
          {modelInfo ? (
            <div className="text-sm text-as-body mt-1">
              R² = <span className="font-medium text-black">{modelInfo.r2?.toFixed(4)}</span>
              {' · '}MAE = <span className="font-medium text-black">€{fmt(Math.round(modelInfo.mae))}</span>
              {' · '}RMSE = <span className="font-medium text-black">€{fmt(Math.round(modelInfo.rmse))}</span>
              {' · '}{modelInfo.n_features ?? 32} features
              {' · '}CV R² = <span className="font-medium text-black">{modelInfo.cv_r2?.toFixed(3)}</span>
            </div>
          ) : (
            <div className="text-sm text-as-body mt-1">
              Trained on 5,444 Romanian listings · R² = 0.9343 · MAE = €1,921 · 32 features
            </div>
          )}
          <a href="/app/predict" className="inline-block mt-2 text-sm text-black hover:underline font-medium">
            Try the prediction tool →
          </a>
        </div>
        {modelInfo && (
          <div className="hidden sm:flex flex-col items-end gap-1 text-xs text-as-muted">
            <span className={`px-2 py-0.5 rounded-full font-medium ${
              modelInfo.status === 'ready' ? 'bg-as-chip text-black' : 'bg-as-chip text-red-600'
            }`}>
              {modelInfo.status === 'ready' ? 'Model loaded' : 'Model offline'}
            </span>
            <span>{modelInfo.experiment ?? 'target_enc'}</span>
          </div>
        )}
      </div>
    </div>
  )
}
