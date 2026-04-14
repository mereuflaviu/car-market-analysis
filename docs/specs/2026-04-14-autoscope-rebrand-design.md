# AutoScope — Rebrand & Landing Page Design Spec

**Date:** 2026-04-14
**Project:** CarMarket → AutoScope
**Scope:** Rename, landing page, top navigation, app-wide visual rebrand

---

## 1. Product Identity

**Name:** AutoScope
**Tagline:** Buy smart. Sell smart.
**Value proposition:** AutoScope gives you the real market price of any used car — before you buy, before you sell, before you negotiate.
**Target users:** Car buyers (primary), car sellers (primary), dealers / analysts (secondary)
**Market:** Romanian used car market (autovit.ro data)

---

## 2. Design System

Based on `DESIGN.md` (Uber-inspired confident minimalism), adapted for an automotive market intelligence product.

### Colors
| Token | Value | Use |
|---|---|---|
| Black | `#000000` | Primary buttons, headlines, active nav, footer bg |
| White | `#ffffff` | Page backgrounds, card surfaces, text on black |
| Body Gray | `#4b4b4b` | Subtitles, secondary text |
| Muted Gray | `#afafaf` | Captions, labels, overlines |
| Chip Gray | `#efefef` | Inactive nav pills, filter chips |
| Hover Gray | `#e2e2e2` | Hover state on white buttons |
| Card Shadow | `rgba(0,0,0,0.12) 0px 4px 16px` | Card elevation |

**No color accent anywhere in the UI chrome.** Charts (Recharts) are the only source of color in the app.

### Typography
- **Font:** Inter (pinned via Google Fonts in `index.html`) — closest available substitute for UberMove
- **Headlines:** Inter 700, tight line-height (1.22–1.25)
- **Body / UI:** Inter 400–500, line-height 1.5
- **Scale:** 52px hero · 36px section · 32px page title · 24px card title · 16px body · 14px caption · 12px micro

### Components
- **Buttons:** 999px border-radius (full pill), black primary / white secondary
- **Nav chips:** 999px radius, Chip Gray inactive → Black active (inversion)
- **Cards:** `8px` radius, whisper shadow, no colored borders
- **Inputs:** `8px` radius, 1px solid black border
- **No gradients. No colored shadows. No decorative borders.**

---

## 3. Routing Architecture

### Current
```
/ → Dashboard
/listings → Listings
/predict → Predict
/analytics → Analytics
```

### New
```
/ → Landing (public, no app chrome)
/app → Dashboard
/app/listings → Listings
/app/predict → Predict Price
/app/analytics → Analytics
```

### Layout zones
- `/` uses `LandingLayout` — no nav chrome, just the page content
- `/app/*` uses `AppLayout` — sticky top nav + max-width content container

---

## 4. Files to Create / Modify

| File | Action | Description |
|---|---|---|
| `index.html` | Modify | Add Inter font via Google Fonts (Vite root entry) |
| `src/App.jsx` | Modify | Add two layout zones, update all routes to `/app/*` |
| `src/components/Layout.jsx` | Replace | Becomes `AppLayout.jsx` — top nav, no sidebar |
| `src/components/LandingLayout.jsx` | Create | Minimal wrapper for landing page |
| `src/pages/Landing.jsx` | Create | Full landing page (6 sections) |
| `src/pages/Dashboard.jsx` | Modify | Restyle KPI cards and ML banner |
| `src/pages/Analytics.jsx` | Modify | Restyle page header |
| `src/pages/Listings.jsx` | Modify | Restyle page header and buttons |
| `src/pages/Prediction.jsx` | Modify | Restyle page header and buttons |
| `src/components/CarForm.jsx` | Modify | Restyle modal buttons |
| `src/index.css` | Modify | Add Inter, update base card/button utility classes |
| `tailwind.config.js` | Modify | Extend with black/white/gray tokens |

**No backend changes required.**

---

## 5. Landing Page — Section by Section

### 5.1 Navigation Bar
- Sticky, white background, `border-b border-black`
- Left: `AutoScope` wordmark — Inter 700, 20px, black
- Center: pill nav chips — `Market` (→ `/app/analytics`) · `Predict` (→ `/app/predict`) · `Listings` (→ `/app/listings`)
  - Each: `bg-[#efefef] text-black rounded-full px-4 py-2 text-sm font-medium`
  - Hover: `bg-[#e2e2e2]`
- Right: black pill CTA — `Open App →` (→ `/app`)
- Mobile: wordmark + hamburger → full-screen drawer with stacked chips

### 5.2 Hero Section
- White background, `max-w-[1136px] mx-auto`, generous vertical padding
- Overline: `ROMANIAN USED CAR MARKET` — muted gray, 12px, uppercase, tracked
- Headline: `Buy smart.` / `Sell smart.` — Inter 700, 52px, black, line-height 1.23
- Subheadline: Body Gray, 18px, max-width 560px
- Two pill CTAs:
  - `Check a price →` — black pill (primary)
  - `Explore the market` — white pill with black border (secondary)
- Right side: **Live stat card** — white card, whisper shadow, pulls from `GET /api/cars/stats` on mount
  - Shows: total listings, avg price, car brands (total_makes), avg mileage — all from `StatsResponse`

### 5.3 Live Market Snapshot Strip
- Background: `#f9f9f9` (near-white, not chip gray)
- Label: `Live market data` — muted gray, uppercase, 12px
- 4 stat blocks in a row, each: large black number + gray label below
  - Total Listings · Average Price · Car Brands · Average Mileage
- Data pulled from `GET /api/cars/stats` (`total_cars`, `avg_price`, `total_makes`, `avg_mileage`)

### 5.4 How It Works
- White background, 3 columns
- Step number in muted gray (01, 02, 03)
- Step title in Inter 700, 24px
- Step description in body gray, 16px
- Content:
  1. **Browse real listings** — Filter 5,444 real Romanian car listings by make, year, fuel type, price, and more
  2. **Run a price check** — Enter your car's details and get an ML-powered market price estimate in seconds
  3. **Negotiate with confidence** — Know the fair price before you commit to a deal

### 5.5 Trust Signals (Dark Section)
- Black background, white text
- 4 stat blocks in a row:
  - `R² = 0.9343` — 93% of price variance explained by the model
  - `MAE ≈ €1,921` — average prediction accuracy
  - `5,444 listings` — real Romanian market data
  - `32 features` — engineered signals per prediction
- Caption below in muted gray: *"Trained on real autovit.ro listings. Not synthetic data. Not estimated."*

### 5.6 CTA Banner
- White background
- Headline: `Ready to check your car's price?` — 36px bold
- Subheadline in body gray: `It takes less than 30 seconds.`
- Black pill CTA: `Open AutoScope →`

### 5.7 Footer
- Black background, white text, `max-w-[1136px] mx-auto`
- Left: `AutoScope` wordmark + tagline `Buy smart. Sell smart.`
- Right: nav links in muted gray — `Dashboard · Listings · Predict · Analytics`
- Bottom divider, then: `Master VD · 2025 · Data sourced from autovit.ro`

---

## 6. App Layout — Top Navigation

Replaces the current left sidebar entirely.

### Top Nav Bar
- `position: sticky; top: 0; z-index: 50`
- White background, `border-b border-black`
- Height: ~60px
- Left: `AutoScope` wordmark linking to `/`
- Center: 4 pill nav chips — `Dashboard` · `Listings` · `Predict Price` · `Analytics`
  - Inactive: `bg-[#efefef] text-black`
  - Active: `bg-black text-white`
  - All: `rounded-full px-4 py-2 text-sm font-medium`
- Right: reserved (empty for now)

### Content Area
- `max-w-[1136px] mx-auto px-6 py-8`
- Full viewport width minus nav — no sidebar offset

### Page Header Pattern (all 4 pages)
```
<h1> — Inter 700, 32px, black
<p>  — Inter 400, 14px, body gray, mt-1
```

### KPI Cards (Dashboard)
- White background, `rounded-lg shadow-[rgba(0,0,0,0.12)_0px_4px_16px]`
- Top: muted gray uppercase label, 12px
- Middle: Inter 700, 36px, black number
- Bottom: body gray caption, 12px
- **No colored left border**

### Buttons (app-wide)
- Primary: `bg-black text-white rounded-full px-5 py-2 text-sm font-medium`
- Secondary: `bg-white text-black border border-black rounded-full px-5 py-2 text-sm font-medium`
- Destructive: `bg-white text-black border border-black rounded-full ...` with red text only

---

## 7. Tailwind Configuration

Add custom tokens to `tailwind.config.js`:

```js
extend: {
  colors: {
    'as-black': '#000000',
    'as-white': '#ffffff',
    'as-body': '#4b4b4b',
    'as-muted': '#afafaf',
    'as-chip': '#efefef',
    'as-hover': '#e2e2e2',
  },
  boxShadow: {
    'card': 'rgba(0,0,0,0.12) 0px 4px 16px 0px',
    'card-md': 'rgba(0,0,0,0.16) 0px 4px 16px 0px',
  },
  borderRadius: {
    'pill': '999px',
  },
}
```

---

## 8. What Stays Unchanged

- All backend code — zero backend changes
- All API endpoints and data contracts
- All chart logic (Recharts) — charts keep their color palette
- All filter/CRUD logic in Listings.jsx
- All prediction logic in Prediction.jsx (56 equipment checkboxes, etc.)
- All ML inference pipeline
- `api/client.js` — unchanged
- `vite.config.js` — unchanged
- `.env` setup — unchanged

---

## 9. Out of Scope

- Authentication / user accounts
- Saved predictions or favourites
- Mobile app
- PostgreSQL migration
- Docker / deployment
- Illustrations (no time budget — real data stats serve as the warmth)

---

## 10. Success Criteria

- [ ] Landing page at `/` loads and renders all 6 sections with live API data
- [ ] `Open App →` navigates to `/app` (Dashboard)
- [ ] All 4 app pages accessible via top nav pill chips
- [ ] Active nav chip shows black/white inversion correctly
- [ ] No sidebar anywhere in the app
- [ ] No colored borders or blue buttons anywhere in the app chrome
- [ ] `npm run build` passes with zero errors
- [ ] All existing features (CRUD, prediction, charts, filters) still work
