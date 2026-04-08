import { useState, useEffect } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from 'recharts'
import { carsApi, analyticsApi } from '../api/client'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#ec4899']

function KpiCard({ label, value, sub, accent }) {
  const accents = {
    blue: 'border-l-blue-500 bg-blue-50',
    green: 'border-l-green-500 bg-green-50',
    amber: 'border-l-amber-500 bg-amber-50',
    purple: 'border-l-purple-500 bg-purple-50',
  }
  return (
    <div className={`card border-l-4 ${accents[accent]} py-4`}>
      <div className="text-xs text-slate-500 uppercase tracking-wider font-semibold mb-1">{label}</div>
      <div className="text-3xl font-bold text-slate-800">{value}</div>
      {sub && <div className="text-xs text-slate-400 mt-1">{sub}</div>}
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [priceDist, setPriceDist] = useState([])
  const [gearbox, setGearbox] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      carsApi.stats(),
      analyticsApi.priceDistribution(),
      analyticsApi.gearboxDistribution(),
    ])
      .then(([s, pd, gb]) => {
        setStats(s.data)
        setPriceDist(pd.data.data || [])
        setGearbox(gb.data.data || [])
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400 animate-pulse">
        Loading dashboard…
      </div>
    )
  }

  const fmt = (n) => (n != null ? Number(n).toLocaleString() : '—')

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>
        <p className="text-slate-500 text-sm mt-1">Overview of the used car market dataset</p>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <KpiCard
          label="Total Listings"
          value={fmt(stats?.total_cars)}
          sub="Cars in database"
          accent="blue"
        />
        <KpiCard
          label="Average Price"
          value={`€${fmt(Math.round(stats?.avg_price ?? 0))}`}
          sub={`€${fmt(Math.round(stats?.min_price ?? 0))} – €${fmt(Math.round(stats?.max_price ?? 0))}`}
          accent="green"
        />
        <KpiCard
          label="Car Brands"
          value={stats?.total_makes ?? '—'}
          sub="Unique manufacturers"
          accent="amber"
        />
        <KpiCard
          label="Avg Mileage"
          value={`${fmt(Math.round(stats?.avg_mileage ?? 0))} km`}
          sub="Across all listings"
          accent="purple"
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Price Distribution */}
        <div className="card">
          <h2 className="font-semibold text-slate-700 mb-4">Price Distribution</h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={priceDist} margin={{ top: 4, right: 8, left: 0, bottom: 48 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
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
          <h2 className="font-semibold text-slate-700 mb-4">Gearbox Distribution</h2>
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
      <div className="card border-l-4 border-l-blue-500 flex items-start gap-4 py-4">
        <div className="text-3xl">🤖</div>
        <div className="flex-1">
          <div className="font-semibold text-slate-700">ML Model: XGBoost Price Predictor</div>
          <div className="text-sm text-slate-500 mt-1">
            Trained on 1,893 listings · R² = 0.895 · MAE = €3,037 · 12 features (year, mileage, make, model, fuel type…)
          </div>
          <a href="/predict" className="inline-block mt-2 text-sm text-blue-600 hover:underline font-medium">
            Try the prediction tool →
          </a>
        </div>
      </div>
    </div>
  )
}
