import { useState, useEffect } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line,
  ScatterChart, Scatter,
  PieChart, Pie, Cell, Legend,
} from 'recharts'
import { analyticsApi } from '../api/client'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316']

function ChartCard({ title, subtitle, loading, children }) {
  return (
    <div className="card">
      <div className="mb-4">
        <h2 className="font-semibold text-slate-700">{title}</h2>
        {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
      </div>
      {loading ? (
        <div className="flex items-center justify-center text-slate-300 text-sm animate-pulse" style={{ height: 260 }}>
          Loading chart…
        </div>
      ) : (
        children
      )}
    </div>
  )
}

const euroFmt = (v) => `€${Number(v).toLocaleString()}`
const kFmt = (v) => `€${(v / 1000).toFixed(0)}k`

export default function Analytics() {
  const [data, setData] = useState({})
  const [loading, setLoading] = useState({})

  const load = async (key, fn) => {
    setLoading((p) => ({ ...p, [key]: true }))
    try {
      const r = await fn()
      setData((p) => ({ ...p, [key]: r.data.data || [] }))
    } catch (e) {
      console.error(`Failed to load ${key}:`, e)
    } finally {
      setLoading((p) => ({ ...p, [key]: false }))
    }
  }

  useEffect(() => {
    load('priceDist', analyticsApi.priceDistribution)
    load('priceByMake', analyticsApi.priceByMake)
    load('priceByFuel', analyticsApi.priceByFuel)
    load('priceByBody', analyticsApi.priceByBodyType)
    load('yearVsPrice', analyticsApi.yearVsPrice)
    load('scatter', analyticsApi.mileageVsPrice)
    load('gearbox', analyticsApi.gearboxDistribution)
  }, [])

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Market Analytics</h1>
        <p className="text-sm text-slate-500 mt-1">
          7 interactive charts derived from 2,000 used car listings
        </p>
      </div>

      {/* 1 — Price Distribution (full width) */}
      <ChartCard
        title="Price Distribution"
        subtitle="Number of listings per price range (20 bins)"
        loading={loading.priceDist}
      >
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={data.priceDist || []} margin={{ top: 4, right: 16, left: 8, bottom: 52 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="range" angle={-45} textAnchor="end" tick={{ fontSize: 10 }} interval={1} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v) => [v, 'Cars']} labelFormatter={(l) => `Starting at ${l}`} />
            <Bar dataKey="count" fill="#3b82f6" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* 2 — Price by Make + Gearbox Pie */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard
          title="Average Price by Make"
          subtitle="Top 15 brands · min 3 listings"
          loading={loading.priceByMake}
        >
          <ResponsiveContainer width="100%" height={320}>
            <BarChart
              layout="vertical"
              data={data.priceByMake || []}
              margin={{ top: 4, right: 64, left: 84, bottom: 4 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 10 }} tickFormatter={kFmt} />
              <YAxis type="category" dataKey="make" tick={{ fontSize: 11 }} width={80} />
              <Tooltip formatter={(v) => [euroFmt(Math.round(v)), 'Avg Price']} />
              <Bar dataKey="avg_price" fill="#10b981" radius={[0, 3, 3, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Gearbox Distribution"
          subtitle="Manual vs Automatic breakdown"
          loading={loading.gearbox}
        >
          <ResponsiveContainer width="100%" height={320}>
            <PieChart>
              <Pie
                data={data.gearbox || []}
                cx="50%"
                cy="44%"
                outerRadius={110}
                dataKey="count"
                nameKey="gearbox"
                label={({ gearbox: g, percent }) => `${g}: ${(percent * 100).toFixed(1)}%`}
                labelLine
              >
                {(data.gearbox || []).map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(v, _n, p) => [v.toLocaleString(), p.payload.gearbox]} />
              <Legend formatter={(_v, entry) => entry.payload.gearbox} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* 3 — Price by Fuel + Price by Body Type */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard
          title="Average Price by Fuel Type"
          subtitle="Mean listing price per fuel category"
          loading={loading.priceByFuel}
        >
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data.priceByFuel || []} margin={{ top: 4, right: 16, left: 8, bottom: 44 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="fuel_type" angle={-30} textAnchor="end" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 10 }} tickFormatter={kFmt} />
              <Tooltip formatter={(v) => [euroFmt(Math.round(v)), 'Avg Price']} />
              <Bar dataKey="avg_price" fill="#f59e0b" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Average Price by Body Type"
          subtitle="Mean listing price per body style"
          loading={loading.priceByBody}
        >
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data.priceByBody || []} margin={{ top: 4, right: 16, left: 8, bottom: 44 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="body_type" angle={-30} textAnchor="end" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 10 }} tickFormatter={kFmt} />
              <Tooltip formatter={(v) => [euroFmt(Math.round(v)), 'Avg Price']} />
              <Bar dataKey="avg_price" fill="#8b5cf6" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* 4 — Year vs Price (full width line) */}
      <ChartCard
        title="Average Price by Manufacturing Year"
        subtitle="How market price evolves with car age"
        loading={loading.yearVsPrice}
      >
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={data.yearVsPrice || []} margin={{ top: 4, right: 24, left: 24, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="year" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 10 }} tickFormatter={kFmt} />
            <Tooltip
              formatter={(v) => [euroFmt(Math.round(v)), 'Avg Price']}
              labelFormatter={(l) => `Year: ${l}`}
            />
            <Line
              type="monotone"
              dataKey="avg_price"
              stroke="#3b82f6"
              strokeWidth={2.5}
              dot={{ r: 3, fill: '#3b82f6' }}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* 5 — Mileage vs Price scatter (full width) */}
      <ChartCard
        title="Mileage vs Price"
        subtitle="Scatter plot of 500 sampled listings — negative correlation visible"
        loading={loading.scatter}
      >
        <ResponsiveContainer width="100%" height={300}>
          <ScatterChart margin={{ top: 4, right: 24, left: 24, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              type="number"
              dataKey="mileage"
              name="Mileage"
              tick={{ fontSize: 10 }}
              tickFormatter={(v) => `${(v / 1000).toFixed(0)}k km`}
            />
            <YAxis
              type="number"
              dataKey="price"
              name="Price"
              tick={{ fontSize: 10 }}
              tickFormatter={kFmt}
            />
            <Tooltip
              cursor={{ strokeDasharray: '3 3' }}
              content={({ payload }) => {
                if (!payload?.length) return null
                const d = payload[0].payload
                return (
                  <div className="bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs shadow">
                    <div className="font-semibold">{d.make}</div>
                    <div>Mileage: {Number(d.mileage).toLocaleString()} km</div>
                    <div>Price: €{Number(d.price).toLocaleString()}</div>
                  </div>
                )
              }}
            />
            <Scatter data={data.scatter || []} fill="#3b82f6" fillOpacity={0.45} />
          </ScatterChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  )
}
