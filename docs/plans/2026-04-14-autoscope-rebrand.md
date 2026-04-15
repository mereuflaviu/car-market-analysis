# AutoScope Rebrand Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the app to AutoScope, add a public landing page at `/`, move the app to `/app/*`, and replace the sidebar with a top pill-chip navigation bar — all using the Uber-inspired black/white design system.

**Architecture:** Two layout zones in `App.jsx` — `LandingLayout` (no chrome) for `/`, and `AppLayout` (sticky top nav) for `/app/*`. The landing page pulls live data from the existing API. All existing page logic stays untouched; only visual chrome and page headers change.

**Tech Stack:** React 18, React Router v6, Tailwind CSS v3, Recharts, Axios — no new dependencies.

**Spec:** `docs/specs/2026-04-14-autoscope-rebrand-design.md`

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `frontend/index.html` | Modify | Title + Inter font via Google Fonts |
| `frontend/tailwind.config.js` | Modify | Add `as-*` color tokens + `card` shadow + `pill` radius |
| `frontend/src/index.css` | Modify | Update `.card`, `.btn-primary`, `.btn-secondary`, `.input-field`, `.select-field` |
| `frontend/src/App.jsx` | Modify | Two layout zones, routes move to `/app/*` |
| `frontend/src/components/LandingLayout.jsx` | Create | Minimal wrapper — no nav chrome |
| `frontend/src/components/AppLayout.jsx` | Create | Sticky top nav with pill chips |
| `frontend/src/pages/Landing.jsx` | Create | Full 7-section landing page |
| `frontend/src/pages/Dashboard.jsx` | Modify | Remove colored KPI borders, restyle ML banner |
| `frontend/src/pages/Analytics.jsx` | Modify | Restyle page header only |
| `frontend/src/pages/Listings.jsx` | Modify | Restyle page header only |
| `frontend/src/pages/Prediction.jsx` | Modify | Restyle page header only |
| `frontend/src/components/CarForm.jsx` | Modify | Update modal header style |

---

## Task 1: Foundation — HTML, Tailwind, CSS

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/tailwind.config.js`
- Modify: `frontend/src/index.css`

- [ ] **Step 1.1 — Update `index.html`**

Replace the entire file:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AutoScope — Buy smart. Sell smart.</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
      rel="stylesheet"
    />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

- [ ] **Step 1.2 — Update `tailwind.config.js`**

Replace the entire file:

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      colors: {
        'as-black': '#000000',
        'as-white': '#ffffff',
        'as-body': '#4b4b4b',
        'as-muted': '#afafaf',
        'as-chip': '#efefef',
        'as-hover': '#e2e2e2',
      },
      boxShadow: {
        card: 'rgba(0,0,0,0.12) 0px 4px 16px 0px',
        'card-md': 'rgba(0,0,0,0.16) 0px 4px 16px 0px',
      },
      borderRadius: {
        pill: '999px',
      },
    },
  },
  plugins: [],
}
```

- [ ] **Step 1.3 — Update `frontend/src/index.css`**

Replace the entire file:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply text-as-black bg-white font-sans;
  }
}

@layer components {
  .card {
    @apply bg-white rounded-lg shadow-card p-6;
  }
  .btn-primary {
    @apply bg-black hover:bg-as-body text-white px-5 py-2 rounded-pill text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed;
  }
  .btn-secondary {
    @apply bg-white hover:bg-as-hover text-black border border-black px-5 py-2 rounded-pill text-sm font-medium transition-colors;
  }
  .btn-ghost {
    @apply bg-as-chip hover:bg-as-hover text-black px-4 py-2 rounded-pill text-sm font-medium transition-colors;
  }
  .input-field {
    @apply w-full border border-black rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent;
  }
  .select-field {
    @apply w-full border border-black rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent bg-white;
  }
}
```

- [ ] **Step 1.4 — Verify build passes**

```bash
cd frontend && npm run build
```

Expected: `✓ built in X.XXs` — zero errors, zero warnings.

---

## Task 2: Routing — Two Layout Zones

**Files:**
- Create: `frontend/src/components/LandingLayout.jsx`
- Create: `frontend/src/components/AppLayout.jsx` (placeholder — full implementation in Task 3)
- Modify: `frontend/src/App.jsx`

- [ ] **Step 2.1 — Create `LandingLayout.jsx`**

```jsx
export default function LandingLayout({ children }) {
  return <div className="min-h-screen bg-white">{children}</div>
}
```

- [ ] **Step 2.2 — Create `AppLayout.jsx` placeholder**

Create the file with just enough to not crash — full implementation in Task 3:

```jsx
import { Link, useLocation } from 'react-router-dom'

const NAV = [
  { to: '/app', label: 'Dashboard' },
  { to: '/app/listings', label: 'Listings' },
  { to: '/app/predict', label: 'Predict Price' },
  { to: '/app/analytics', label: 'Analytics' },
]

export default function AppLayout({ children }) {
  const { pathname } = useLocation()

  return (
    <div className="min-h-screen bg-white">
      <header className="sticky top-0 z-50 bg-white border-b border-black">
        <div className="max-w-[1136px] mx-auto px-6 h-14 flex items-center gap-6">
          <Link to="/" className="font-bold text-lg text-black tracking-tight mr-4">
            AutoScope
          </Link>
          <nav className="flex items-center gap-2">
            {NAV.map(({ to, label }) => {
              const active = pathname === to || (to !== '/app' && pathname.startsWith(to))
              return (
                <Link
                  key={to}
                  to={to}
                  className={`px-4 py-1.5 rounded-pill text-sm font-medium transition-colors ${
                    active
                      ? 'bg-black text-white'
                      : 'bg-as-chip text-black hover:bg-as-hover'
                  }`}
                >
                  {label}
                </Link>
              )
            })}
          </nav>
        </div>
      </header>
      <main className="max-w-[1136px] mx-auto px-6 py-8">{children}</main>
    </div>
  )
}
```

- [ ] **Step 2.3 — Update `App.jsx`**

Replace the entire file:

```jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LandingLayout from './components/LandingLayout'
import AppLayout from './components/AppLayout'
import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import Listings from './pages/Listings'
import Prediction from './pages/Prediction'
import Analytics from './pages/Analytics'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <LandingLayout>
              <Landing />
            </LandingLayout>
          }
        />
        <Route
          path="/app"
          element={
            <AppLayout>
              <Dashboard />
            </AppLayout>
          }
        />
        <Route
          path="/app/listings"
          element={
            <AppLayout>
              <Listings />
            </AppLayout>
          }
        />
        <Route
          path="/app/predict"
          element={
            <AppLayout>
              <Prediction />
            </AppLayout>
          }
        />
        <Route
          path="/app/analytics"
          element={
            <AppLayout>
              <Analytics />
            </AppLayout>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}
```

- [ ] **Step 2.4 — Create `Landing.jsx` placeholder**

Just enough to not crash — full implementation in Task 4:

```jsx
export default function Landing() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <h1 className="text-4xl font-bold">AutoScope — coming soon</h1>
    </div>
  )
}
```

- [ ] **Step 2.5 — Verify build passes**

```bash
cd frontend && npm run build
```

Expected: `✓ built in X.XXs` — zero errors.

---

## Task 3: AppLayout — Full Top Nav

**Files:**
- Modify: `frontend/src/components/AppLayout.jsx`

The placeholder from Task 2 is already the final implementation. No changes needed — the full AppLayout was written in Step 2.2.

- [ ] **Step 3.1 — Verify active state logic**

The active detection uses:
```js
const active = pathname === to || (to !== '/app' && pathname.startsWith(to))
```
This ensures `/app` only activates on exact match, while `/app/listings` activates on any path starting with it.

- [ ] **Step 3.2 — Verify build**

```bash
cd frontend && npm run build
```

Expected: `✓ built in X.XXs`

---

## Task 4: Landing Page

**Files:**
- Modify: `frontend/src/pages/Landing.jsx`

- [ ] **Step 4.1 — Replace `Landing.jsx` with full implementation**

```jsx
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
            <Link to="/app/analytics" className="bg-as-chip hover:bg-as-hover text-black px-4 py-1.5 rounded-pill text-sm font-medium transition-colors">
              Market
            </Link>
            <Link to="/app/predict" className="bg-as-chip hover:bg-as-hover text-black px-4 py-1.5 rounded-pill text-sm font-medium transition-colors">
              Predict
            </Link>
            <Link to="/app/listings" className="bg-as-chip hover:bg-as-hover text-black px-4 py-1.5 rounded-pill text-sm font-medium transition-colors">
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

        {/* Mobile menu */}
        {menuOpen && (
          <div className="md:hidden border-t border-black bg-white px-6 py-4 flex flex-col gap-2">
            <Link to="/app/analytics" className="bg-as-chip text-black px-4 py-2 rounded-pill text-sm font-medium" onClick={() => setMenuOpen(false)}>Market</Link>
            <Link to="/app/predict" className="bg-as-chip text-black px-4 py-2 rounded-pill text-sm font-medium" onClick={() => setMenuOpen(false)}>Predict</Link>
            <Link to="/app/listings" className="bg-as-chip text-black px-4 py-2 rounded-pill text-sm font-medium" onClick={() => setMenuOpen(false)}>Listings</Link>
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
            AutoScope gives you the real market price of any used car — before you buy, before you sell, before you negotiate.
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
        <div className="w-full md:w-72 bg-white rounded-xl shadow-card p-6 flex flex-col gap-4">
          <div className="text-xs font-medium text-as-muted uppercase tracking-wider">
            Live market data
          </div>
          <div className="grid grid-cols-2 gap-4">
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
        <div className="max-w-[1136px] mx-auto px-6 py-10 flex flex-col gap-6">
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
          <div className="text-xs font-medium text-as-muted uppercase tracking-widest">How it works</div>
          <h2 className="text-[36px] font-bold text-black leading-tight">Three steps to a fair deal</h2>
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
            <div className="text-xs font-medium text-as-muted uppercase tracking-widest">The model</div>
            <h2 className="text-[36px] font-bold text-white leading-tight">
              Serious accuracy.<br />Real data.
            </h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <TrustStat value="R² = 0.9343" label="Variance explained" caption="93% of price variation" />
            <TrustStat value="€1,921" label="Avg prediction error" caption="Mean absolute error" />
            <TrustStat value="5,444" label="Training listings" caption="Real Romanian market data" />
            <TrustStat value="32" label="Engineered features" caption="Per prediction" />
          </div>
          <p className="text-sm text-as-muted max-w-[560px]">
            Trained on real autovit.ro listings. Not synthetic data. Not estimated. XGBoost regression with smoothed target encoding for make and model.
          </p>
        </div>
      </section>

      {/* ── CTA Banner ─────────────────────────────────────────────────── */}
      <section className="max-w-[1136px] mx-auto px-6 py-20 flex flex-col items-center text-center gap-6">
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
          <nav className="flex flex-wrap gap-4">
            <Link to="/app" className="text-as-muted hover:text-white text-sm transition-colors">Dashboard</Link>
            <Link to="/app/listings" className="text-as-muted hover:text-white text-sm transition-colors">Listings</Link>
            <Link to="/app/predict" className="text-as-muted hover:text-white text-sm transition-colors">Predict</Link>
            <Link to="/app/analytics" className="text-as-muted hover:text-white text-sm transition-colors">Analytics</Link>
          </nav>
        </div>
        <div className="border-t border-white/10 max-w-[1136px] mx-auto px-6 py-4">
          <p className="text-as-muted text-xs">Master VD · 2025 · Data sourced from autovit.ro</p>
        </div>
      </footer>

    </div>
  )
}
```

- [ ] **Step 4.2 — Verify build**

```bash
cd frontend && npm run build
```

Expected: `✓ built in X.XXs` — zero errors.

---

## Task 5: Restyle Dashboard

**Files:**
- Modify: `frontend/src/pages/Dashboard.jsx`

The only changes are to `KpiCard` (remove colored borders) and the ML banner (remove `border-l-blue-500`). Chart logic stays completely unchanged.

- [ ] **Step 5.1 — Replace `KpiCard` component**

Find and replace the `KpiCard` function:

```jsx
function KpiCard({ label, value, sub }) {
  return (
    <div className="card py-4">
      <div className="text-xs text-as-muted uppercase tracking-wider font-semibold mb-1">{label}</div>
      <div className="text-3xl font-bold text-black">{value}</div>
      {sub && <div className="text-xs text-as-muted mt-1">{sub}</div>}
    </div>
  )
}
```

- [ ] **Step 5.2 — Remove `accents` map and `accent` prop usage**

The `accents` object and `accent` prop are no longer needed. Remove the entire `accents` object from inside `KpiCard` (already done in step above — the new `KpiCard` has no `accent` prop).

Update the 4 `KpiCard` usages to remove the `accent` prop:

```jsx
<KpiCard label="Total Listings" value={fmt(stats?.total_cars)} sub="Cars in database" />
<KpiCard label="Average Price" value={`€${fmt(Math.round(stats?.avg_price ?? 0))}`} sub={`€${fmt(Math.round(stats?.min_price ?? 0))} – €${fmt(Math.round(stats?.max_price ?? 0))}`} />
<KpiCard label="Car Brands" value={stats?.total_makes ?? '—'} sub="Unique manufacturers" />
<KpiCard label="Avg Mileage" value={`${fmt(Math.round(stats?.avg_mileage ?? 0))} km`} sub="Across all listings" />
```

- [ ] **Step 5.3 — Restyle ML banner**

Find the ML banner div and remove the colored border:

```jsx
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
```

- [ ] **Step 5.4 — Update page subtitle colour**

Find:
```jsx
<p className="text-slate-500 text-sm mt-1">Overview of the used car market dataset</p>
```
Replace with:
```jsx
<p className="text-as-body text-sm mt-1">Overview of the used car market dataset</p>
```

- [ ] **Step 5.5 — Verify build**

```bash
cd frontend && npm run build
```

Expected: `✓ built in X.XXs`

---

## Task 6: Restyle Page Headers

**Files:**
- Modify: `frontend/src/pages/Analytics.jsx`
- Modify: `frontend/src/pages/Listings.jsx`
- Modify: `frontend/src/pages/Prediction.jsx`

Only page titles and subtitles change. All logic, charts, filters, and forms are untouched.

- [ ] **Step 6.1 — Analytics.jsx page header**

Find:
```jsx
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Market Analytics</h1>
        <p className="text-sm text-slate-500 mt-1">
          8 interactive charts derived from 5,444 real used car listings
        </p>
      </div>
```
Replace with:
```jsx
      <div>
        <h1 className="text-[32px] font-bold text-black leading-tight">Market Analytics</h1>
        <p className="text-sm text-as-body mt-1">
          8 interactive charts derived from 5,444 real used car listings
        </p>
      </div>
```

- [ ] **Step 6.2 — Listings.jsx page header (line 166–170)**

```jsx
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-[32px] font-bold text-black leading-tight">Car Listings</h1>
          <p className="text-sm text-as-body mt-0.5">{total.toLocaleString()} results</p>
        </div>
        <button
          className="btn-primary"
          onClick={() => { setEditCar(null); setShowForm(true) }}
        >
```

- [ ] **Step 6.3 — Prediction.jsx page header (line 226–230)**

```jsx
      <div>
        <h1 className="text-[32px] font-bold text-black leading-tight">Price Prediction</h1>
        <p className="text-sm text-as-body mt-1">Enter car specifications to get an AI-powered price estimate</p>
      </div>
```

- [ ] **Step 6.4 — Prediction.jsx model info card (line 233)**

Remove colored left borders from the model status card:

Find:
```jsx
        <div className={`card py-3 border-l-4 ${modelInfo.status === 'ready' ? 'border-l-green-500 bg-green-50' : 'border-l-yellow-500 bg-yellow-50'}`}>
```
Replace with:
```jsx
        <div className="card py-3">
```

- [ ] **Step 6.5 — Verify build**

```bash
cd frontend && npm run build
```

Expected: `✓ built in X.XXs`

---

## Task 7: Restyle CarForm Modal

**Files:**
- Modify: `frontend/src/components/CarForm.jsx`

Only the modal header background and button classes change. All form fields and logic stay the same.

- [ ] **Step 7.1 — Update CarForm.jsx modal header (line 115–125)**

Find:
```jsx
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 sticky top-0 bg-white z-10">
          <h2 className="text-lg font-semibold text-slate-800">
            {car ? 'Edit Car Listing' : 'Add New Car Listing'}
          </h2>
          <button
            onClick={() => onClose(false)}
            className="text-slate-400 hover:text-slate-600 text-2xl font-light leading-none"
          >
            ×
          </button>
        </div>
```
Replace with:
```jsx
        <div className="flex items-center justify-between px-6 py-4 border-b border-black sticky top-0 bg-white z-10">
          <h2 className="text-lg font-bold text-black">
            {car ? 'Edit Car Listing' : 'Add New Car Listing'}
          </h2>
          <button
            onClick={() => onClose(false)}
            className="w-8 h-8 flex items-center justify-center rounded-full bg-as-chip hover:bg-as-hover text-black transition-colors"
          >
            ✕
          </button>
        </div>
```

- [ ] **Step 7.3 — Verify build**

```bash
cd frontend && npm run build
```

Expected: `✓ built in X.XXs`

---

## Task 8: Final Verification

- [ ] **Step 8.1 — Full production build**

```bash
cd frontend && npm run build
```

Expected output (exact chunk names will vary):
```
✓ 889 modules transformed.
dist/index.html              ~0.5 kB
dist/assets/index-*.css      ~21 kB
dist/assets/vendor-http-*.js ~37 kB
dist/assets/index-*.js       ~50 kB
dist/assets/vendor-react-*.js ~162 kB
dist/assets/vendor-charts-*.js ~423 kB
✓ built in X.XXs
```

Zero errors. Zero warnings.

- [ ] **Step 8.2 — Smoke test checklist (run `npm run dev` and verify manually)**

| Route | Check |
|---|---|
| `http://localhost:5173/` | Landing page loads, all 6 sections visible |
| Landing | Live stat card shows real numbers (requires backend running) |
| Landing | "Open App →" navigates to `/app` |
| Landing | "Check a price →" navigates to `/app/predict` |
| `http://localhost:5173/app` | Dashboard loads, KPI cards visible, no colored borders |
| `/app` | ML banner shows live model metrics |
| `/app` | Active nav chip is black, others are chip-gray |
| `/app/listings` | Listings table loads, filters work, CRUD works |
| `/app/predict` | Prediction form loads, 56 equipment checkboxes visible |
| `/app/analytics` | All 8 charts render |
| Any `/app/*` | AutoScope wordmark links back to `/` |
| Browser back/forward | Navigation works correctly |

---

## Self-Review Notes

- All Recharts chart logic is untouched — charts are the only color in the UI
- `.btn-primary`, `.btn-secondary`, `.card`, `.input-field`, `.select-field` are CSS utility classes — updating them in `index.css` applies the new design system to all pages automatically
- `Layout.jsx` is no longer imported anywhere after Task 2 — it can be deleted manually
- No backend changes needed at any step
