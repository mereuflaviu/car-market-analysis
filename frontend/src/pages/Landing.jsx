import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { carsApi } from '../api/client'

function StatBlock({ value, label }) {
  return (
    <div className="flex flex-col items-center gap-1">
      <div className="text-3xl font-bold text-black">{value}</div>
      <div className="text-xs text-as-muted uppercase tracking-wider">{label}</div>
    </div>
  )
}

function Step({ number, title, description }) {
  return (
    <div className="flex flex-col gap-3">
      <div className="text-xs font-medium text-as-muted uppercase tracking-widest">{number}</div>
      <h3 className="text-2xl font-bold text-black leading-tight">{title}</h3>
      <p className="text-as-body text-base leading-relaxed">{description}</p>
    </div>
  )
}

function TrustStat({ value, label, caption }) {
  return (
    <div className="flex flex-col gap-1">
      <div className="text-4xl font-bold text-white">{value}</div>
      <div className="text-sm font-medium text-white">{label}</div>
      {caption && <div className="text-xs text-as-muted">{caption}</div>}
    </div>
  )
}

const fmt = (n) => (n != null ? Number(n).toLocaleString() : '—')

export default function Landing() {
  const [stats, setStats] = useState(null)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    carsApi.stats().then((r) => setStats(r.data)).catch(() => {})
  }, [])

  return (
    <div className="font-sans text-black">

      {/* ── Navbar ─────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 bg-white border-b border-black">
        <div className="max-w-[1136px] mx-auto px-6 h-14 flex items-center justify-between">
          <span className="font-bold text-lg tracking-tight">AutoScope</span>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-2">
            <Link
              to="/app/analytics"
              className="bg-as-chip hover:bg-as-hover text-black px-4 py-1.5 rounded-pill text-sm font-medium transition-colors"
            >
              Market
            </Link>
            <Link
              to="/app/predict"
              className="bg-as-chip hover:bg-as-hover text-black px-4 py-1.5 rounded-pill text-sm font-medium transition-colors"
            >
              Predict
            </Link>
            <Link
              to="/app/listings"
              className="bg-as-chip hover:bg-as-hover text-black px-4 py-1.5 rounded-pill text-sm font-medium transition-colors"
            >
              Listings
            </Link>
          </nav>

          <div className="flex items-center gap-3">
            <Link
              to="/app"
              className="bg-black text-white px-5 py-1.5 rounded-pill text-sm font-medium hover:bg-as-body transition-colors"
            >
              Open App →
            </Link>
            {/* Mobile hamburger */}
            <button
              className="md:hidden w-9 h-9 flex items-center justify-center rounded-full bg-as-chip"
              onClick={() => setMenuOpen((v) => !v)}
              aria-label="Toggle menu"
            >
              <span className="text-base">{menuOpen ? '✕' : '☰'}</span>
            </button>
          </div>
        </div>

        {/* Mobile drawer */}
        {menuOpen && (
          <div className="md:hidden border-t border-black bg-white px-6 py-4 flex flex-col gap-2">
            <Link
              to="/app/analytics"
              className="bg-as-chip text-black px-4 py-2 rounded-pill text-sm font-medium"
              onClick={() => setMenuOpen(false)}
            >
              Market
            </Link>
            <Link
              to="/app/predict"
              className="bg-as-chip text-black px-4 py-2 rounded-pill text-sm font-medium"
              onClick={() => setMenuOpen(false)}
            >
              Predict
            </Link>
            <Link
              to="/app/listings"
              className="bg-as-chip text-black px-4 py-2 rounded-pill text-sm font-medium"
              onClick={() => setMenuOpen(false)}
            >
              Listings
            </Link>
          </div>
        )}
      </header>

      {/* ── Hero ───────────────────────────────────────────────────────── */}
      <section className="max-w-[1136px] mx-auto px-6 py-20 md:py-28 flex flex-col md:flex-row items-start md:items-center gap-12">
        <div className="flex-1 flex flex-col gap-6">
          <div className="text-xs font-medium text-as-muted uppercase tracking-widest">
            Romanian Used Car Market
          </div>
          <h1 className="text-5xl md:text-[52px] font-bold text-black leading-[1.23]">
            Buy smart.<br />Sell smart.
          </h1>
          <p className="text-lg text-as-body max-w-[520px] leading-relaxed">
            AutoScope gives you the real market price of any used car — before you buy,
            before you sell, before you negotiate.
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            <Link
              to="/app/predict"
              className="bg-black text-white px-6 py-3 rounded-pill text-sm font-medium hover:bg-as-body transition-colors"
            >
              Check a price →
            </Link>
            <Link
              to="/app/analytics"
              className="bg-white text-black border border-black px-6 py-3 rounded-pill text-sm font-medium hover:bg-as-chip transition-colors"
            >
              Explore the market
            </Link>
          </div>
        </div>

        {/* Live stat card */}
        <div className="w-full md:w-72 flex-shrink-0 bg-white rounded-xl shadow-card p-6 flex flex-col gap-4">
          <div className="text-xs font-medium text-as-muted uppercase tracking-wider">
            Live market data
          </div>
          <div className="grid grid-cols-2 gap-6">
            <StatBlock
              value={stats ? fmt(stats.total_cars) : '—'}
              label="Listings"
            />
            <StatBlock
              value={stats ? `€${fmt(Math.round(stats.avg_price ?? 0))}` : '—'}
              label="Avg price"
            />
            <StatBlock
              value={stats ? fmt(stats.total_makes) : '—'}
              label="Brands"
            />
            <StatBlock
              value={stats ? `${fmt(Math.round(stats.avg_mileage ?? 0))} km` : '—'}
              label="Avg mileage"
            />
          </div>
        </div>
      </section>

      {/* ── Market Snapshot Strip ──────────────────────────────────────── */}
      <section className="bg-[#f9f9f9] border-y border-black/10">
        <div className="max-w-[1136px] mx-auto px-6 py-12 flex flex-col gap-6">
          <div className="text-xs font-medium text-as-muted uppercase tracking-widest text-center">
            Live market snapshot
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <StatBlock
              value={stats ? fmt(stats.total_cars) : '—'}
              label="Total listings"
            />
            <StatBlock
              value={stats ? `€${fmt(Math.round(stats.avg_price ?? 0))}` : '—'}
              label="Average price"
            />
            <StatBlock
              value={stats ? fmt(stats.total_makes) : '—'}
              label="Car brands"
            />
            <StatBlock
              value={stats ? `${fmt(Math.round(stats.avg_mileage ?? 0))} km` : '—'}
              label="Average mileage"
            />
          </div>
        </div>
      </section>

      {/* ── How It Works ───────────────────────────────────────────────── */}
      <section className="max-w-[1136px] mx-auto px-6 py-20">
        <div className="mb-12 flex flex-col gap-2">
          <div className="text-xs font-medium text-as-muted uppercase tracking-widest">
            How it works
          </div>
          <h2 className="text-[36px] font-bold text-black leading-tight">
            Three steps to a fair deal
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
          <Step
            number="01"
            title="Browse real listings"
            description="Filter 5,444 real Romanian car listings by make, year, fuel type, price range, mileage, and more."
          />
          <Step
            number="02"
            title="Run a price check"
            description="Enter your car's details and get an ML-powered market price estimate in seconds, with a confidence range."
          />
          <Step
            number="03"
            title="Negotiate with confidence"
            description="Know the fair market price before you commit. Walk into any deal knowing whether you're getting a good price."
          />
        </div>
      </section>

      {/* ── Trust Signals ──────────────────────────────────────────────── */}
      <section className="bg-black">
        <div className="max-w-[1136px] mx-auto px-6 py-20 flex flex-col gap-10">
          <div className="flex flex-col gap-2">
            <div className="text-xs font-medium text-as-muted uppercase tracking-widest">
              The model
            </div>
            <h2 className="text-[36px] font-bold text-white leading-tight">
              Serious accuracy.<br />Real data.
            </h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <TrustStat
              value="R² = 0.9343"
              label="Variance explained"
              caption="93% of price variation"
            />
            <TrustStat
              value="€1,921"
              label="Avg prediction error"
              caption="Mean absolute error"
            />
            <TrustStat
              value="5,444"
              label="Training listings"
              caption="Real Romanian market data"
            />
            <TrustStat
              value="32"
              label="Engineered features"
              caption="Per prediction"
            />
          </div>
          <p className="text-sm text-as-muted max-w-[560px]">
            Trained on real autovit.ro listings. Not synthetic data. Not estimated.
            XGBoost regression with smoothed target encoding for make and model.
          </p>
        </div>
      </section>

      {/* ── CTA Banner ─────────────────────────────────────────────────── */}
      <section className="max-w-[1136px] mx-auto px-6 py-24 flex flex-col items-center text-center gap-6">
        <h2 className="text-[36px] font-bold text-black leading-tight">
          Ready to check your car's price?
        </h2>
        <p className="text-as-body text-lg">It takes less than 30 seconds.</p>
        <Link
          to="/app/predict"
          className="bg-black text-white px-8 py-3 rounded-pill text-sm font-medium hover:bg-as-body transition-colors"
        >
          Open AutoScope →
        </Link>
      </section>

      {/* ── Footer ─────────────────────────────────────────────────────── */}
      <footer className="bg-black">
        <div className="max-w-[1136px] mx-auto px-6 py-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="flex flex-col gap-1">
            <span className="font-bold text-white text-lg">AutoScope</span>
            <span className="text-as-muted text-sm">Buy smart. Sell smart.</span>
          </div>
          <nav className="flex flex-wrap gap-6">
            <Link to="/app" className="text-as-muted hover:text-white text-sm transition-colors">
              Dashboard
            </Link>
            <Link to="/app/listings" className="text-as-muted hover:text-white text-sm transition-colors">
              Listings
            </Link>
            <Link to="/app/predict" className="text-as-muted hover:text-white text-sm transition-colors">
              Predict
            </Link>
            <Link to="/app/analytics" className="text-as-muted hover:text-white text-sm transition-colors">
              Analytics
            </Link>
          </nav>
        </div>
        <div className="border-t border-white/10">
          <div className="max-w-[1136px] mx-auto px-6 py-4">
            <p className="text-as-muted text-xs">
              Master VD · 2025 · Data sourced from autovit.ro
            </p>
          </div>
        </div>
      </footer>

    </div>
  )
}
