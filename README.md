# AutoScope — Romanian Used Car Marketplace & Price Prediction

> Full-stack web platform for browsing, listing, and pricing Romanian second-hand cars — powered by XGBoost ML and secured with JWT authentication.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![XGBoost](https://img.shields.io/badge/XGBoost-R²%200.9343-orange)
![SQLite](https://img.shields.io/badge/SQLite-WAL-003B57?logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

---

## Overview

AutoScope is a full-stack marketplace and analytics platform for the Romanian used-car market. It combines **real listing data** (5,444 cars scraped from autovit.ro), **interactive market analytics**, and an **AI price prediction engine** trained with XGBoost (R² = 0.9343, MAE ≈ €1,921).

Users can browse listings, add their own cars for sale, get an instant price estimate for any vehicle, and explore market trends across 8 interactive charts. Admins can manage users, ban accounts, and moderate the platform.

---

## Features

| Area | What it does |
|------|-------------|
| **Landing page** | Public hero + feature overview, no login required |
| **Auth** | Register / Login / Logout with JWT in httpOnly cookies, 15-min access token + 7-day refresh |
| **Dashboard** | KPI cards (total listings, avg price, avg mileage, brands) + price distribution + gearbox split |
| **Listings** | Full CRUD with 12+ server-side filters (make, model, year, price, mileage, power, fuel, body, gearbox), "My Listings" toggle, cascading make→model select, pagination |
| **Price Prediction** | 56 equipment checkboxes, tier badge (Basic/Standard/Premium/Ultra), price-range bar with ±MAE confidence interval, model metrics, feature importance, prediction history |
| **Analytics** | 8 Recharts charts: price by make/fuel/body-type, year vs price, mileage vs price scatter, gearbox + transmission distribution |
| **Admin panel** | Paginated user table, promote/demote, ban/unban, delete users |
| **REST API** | 25+ endpoints, documented at `/docs` (dev only) |

---

## Quick Start (Local Dev)

```bash
# 1 — Backend
cd backend
cp .env.example .env          # fill in JWT_SECRET, FIRST_ADMIN_EMAIL
pip install -r requirements.txt
python app/ml/train_extended.py   # trains XGBoost (~1 min), saves to artifacts/
python seed.py                    # loads 5,444 listings into SQLite
uvicorn app.main:app --reload --port 8001

# 2 — Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — API docs at **http://localhost:8001/docs**

> Re-seed from scratch: `python seed.py --force`

---

## Docker

```bash
# Local Docker (all services, port 80)
docker-compose up --build -d
# → App at http://localhost   API health at http://localhost/health

# Production Docker (closes backend port, enforces ENV=production)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

The backend is never exposed publicly in production — only nginx (port 80) is the entry point. nginx proxies `/api/` to the backend container internally.

---

## Environment Variables

### Backend (`backend/.env`)

Copy from `backend/.env.example`:

| Variable | Required | Description |
|----------|----------|-------------|
| `ENV` | yes | `development` or `production` |
| `JWT_SECRET` | yes | Strong random string — generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `JWT_ACCESS_EXPIRE_MINUTES` | no | Default: 15 |
| `JWT_REFRESH_EXPIRE_DAYS` | no | Default: 7 |
| `FIRST_ADMIN_EMAIL` | yes | First user to register with this email becomes admin |
| `API_KEY` | prod only | Mutation guard — generate same way as JWT_SECRET |
| `CORS_ORIGINS` | prod only | Comma-separated allowed origins, e.g. `https://yourdomain.com` |

> **Production**: `ENV=production` enforces `JWT_SECRET` validation at startup (app refuses to start with a weak/default secret), hides API docs, and enforces the API key on mutation endpoints.

### Frontend (`frontend/.env`)

Only needed for local dev without Docker:

```
VITE_API_URL=http://localhost:8001/api
```

In Docker, `VITE_API_URL` is baked in as `/api` at build time — nginx proxies it.

---

## Auth Flow

- Credentials → httpOnly cookies (`access_token` + `refresh_token`)  
- `samesite=strict`, `secure=true` in production (HTTPS required)
- 401 → automatic silent refresh, one retry, then redirect to `/login`
- Roles: `guest` (unauthenticated) / `user` / `admin`
- Admin bootstrap: set `FIRST_ADMIN_EMAIL` in `.env` — the first registration with that email gets the admin role automatically

---

## ML Model

| Metric | Value |
|--------|-------|
| Algorithm | XGBoost Regressor |
| R² (test) | **0.9343** |
| MAE | **€1,921** |
| RMSE | €3,034 |
| CV R² (5-fold) | 0.931 |
| Training samples | 4,181 |
| Test samples | 1,046 |
| Features | 32 |
| Dataset | 5,444 Romanian listings |

### Feature Engineering

| Feature | Description |
|---------|-------------|
| `car_age` / `log_car_age` | Age from 2026, linear + log transform |
| `power_per_liter` | Engine power ÷ displacement |
| `power_over_age` | Power ÷ (age + 1) — performance × freshness |
| `power_auto` | Power × automatic gearbox flag |
| `equip_per_age` | Equipment count ÷ (age + 1) |
| `brand_tier` | luxury / mainstream / budget classification |
| `cohort` | make\|model\|year — smoothed target encoding |
| `equipment_count` | Count of 56 optional extras |

### Training

```bash
cd backend
python app/ml/train_extended.py           # default experiment
python app/ml/train_extended.py --tune    # + RandomizedSearchCV (slower)
```

Artifacts saved to `backend/artifacts/`: `model.joblib`, `encoder.joblib`, `te_encoder.joblib`, `metadata.joblib` (all git-ignored).

---

## REST API

| Group | Endpoints |
|-------|-----------|
| Auth | `POST /api/auth/register`, `/login`, `/logout`, `/refresh` · `GET /api/auth/me` |
| Cars | `GET/POST /api/cars` · `GET/PUT/DELETE /api/cars/{id}` · `GET /api/cars/stats` |
| Predictions | `POST /api/predictions/predict` · `GET /api/predictions/history` · `GET/DELETE /api/predictions/{id}` · `GET /api/predictions/model-info` |
| Analytics | `/price-distribution` `/price-by-make` `/price-by-fuel` `/price-by-body-type` `/mileage-vs-price` `/year-vs-price` `/gearbox-distribution` `/transmission-distribution` |
| Reference | `GET /api/makes` · `/api/makes/options` · `/api/makes/{make}/models` |
| Admin | `GET /api/admin/users` · `GET/PATCH/DELETE /api/admin/users/{id}` |
| Health | `GET /health` |

### Example — predict price

```bash
curl -X POST http://localhost:8001/api/predictions/predict \
  -H "Content-Type: application/json" \
  --cookie "access_token=<your_token>" \
  -d '{
    "make": "BMW", "model": "Seria 5", "year": 2019,
    "body_type": "Sedan", "mileage": 85000, "color": "Negru",
    "fuel_type": "Diesel", "engine_capacity": 1995, "engine_power": 190,
    "gearbox": "Automata", "transmission": "4x4 (automat)",
    "pollution_standard": "Euro 6", "equipment_count": 12
  }'
```

> Prediction endpoint requires authentication (JWT cookie).

---

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, middleware, router registration
│   │   ├── database.py          # SQLAlchemy + SQLite (WAL mode)
│   │   ├── models.py            # ORM: User, Car, Prediction
│   │   ├── schemas.py           # Pydantic v2 schemas
│   │   ├── crud.py              # DB helpers (all queries here)
│   │   ├── dependencies.py      # get_current_user, get_optional_user, require_admin
│   │   ├── jwt_utils.py         # Token creation + decoding
│   │   ├── limiter.py           # slowapi rate limiter instance
│   │   └── routes/
│   │       ├── auth.py          # register, login, logout, me, refresh
│   │       ├── admin.py         # user management (admin only)
│   │       ├── cars.py          # car CRUD with ownership checks
│   │       ├── predictions.py   # predict + history
│   │       ├── analytics.py     # 8 analytics endpoints
│   │       └── makes.py         # reference data (makes, models, options)
│   ├── ml/
│   │   ├── encoders.py          # SmoothedTargetEncoder
│   │   ├── train_extended.py    # full training pipeline (6 experiments)
│   │   └── inference.py         # lazy-load, feature engineering, predict
│   ├── artifacts/               # model files (git-ignored)
│   ├── seed.py                  # CSV → SQLite loader
│   ├── .env.example             # env template
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── api/client.js        # Axios instance + interceptors (401 refresh)
│       ├── context/
│       │   └── AuthContext.jsx  # global auth state + useAuth hook
│       ├── components/
│       │   ├── AppLayout.jsx    # sticky nav (guest/user/admin states)
│       │   ├── LandingLayout.jsx
│       │   ├── RequireAuth.jsx  # route guards (RequireAuth, RequireAdmin, RedirectIfAuth)
│       │   ├── ErrorBoundary.jsx
│       │   └── CarForm.jsx      # add/edit listing modal
│       └── pages/
│           ├── Landing.jsx      # public hero page
│           ├── Login.jsx
│           ├── Register.jsx
│           ├── Dashboard.jsx    # KPIs + charts
│           ├── Listings.jsx     # filters, CRUD, My Listings, pagination
│           ├── Prediction.jsx   # 56 equipment checkboxes, price range, history
│           ├── Analytics.jsx    # 8 interactive charts
│           ├── AdminUsers.jsx   # user management table
│           └── NotFound.jsx
│
├── model/
│   ├── data/
│   │   ├── cleaned_car_listings_extended.csv   # 5,444 cleaned rows
│   │   └── raw_scraped_extended.csv            # ~11,000 raw rows
│   └── extraction/
│       ├── scraper_extended.py                 # autovit.ro scraper
│       └── cleanup_data_extended.ipynb         # cleaning notebook
│
├── Dockerfile.backend
├── Dockerfile.frontend
├── docker-compose.yml           # local Docker dev
├── docker-compose.prod.yml      # production overrides
├── nginx.conf                   # reverse proxy + CSP + gzip
└── .gitignore
```

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React 18, Vite, Tailwind CSS v3, Recharts, React Router v6, Axios |
| Backend | FastAPI 0.104, Uvicorn, SQLAlchemy 2.0, Pydantic v2 |
| Auth | python-jose (JWT), passlib + bcrypt, httpOnly cookies |
| Database | SQLite with WAL mode |
| ML | XGBoost 2.0, scikit-learn, pandas, numpy, joblib |
| Rate limiting | slowapi |
| Deployment | Docker Compose, nginx (reverse proxy) |
| Data collection | requests, BeautifulSoup4, Next.js `__NEXT_DATA__` extraction |

---

## Deployment

AutoScope is Docker-ready. For a production deploy on any VPS or cloud host:

1. Clone the repo and `cd` into it
2. Create `backend/.env` from `backend/.env.example` with real secrets
3. Run `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d`
4. Point a domain at port 80 and add HTTPS (Cloudflare or Let's Encrypt)
5. Update `CORS_ORIGINS` in `backend/.env` to match your domain

> SQLite is suitable for single-server deployments. For multi-instance or high-write workloads, migrate to PostgreSQL by swapping `DATABASE_URL` and removing the WAL PRAGMA setup.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: No module named 'app'` | Run `uvicorn` from inside `backend/` |
| Port 8001 in use | Change `--port`, set `VITE_API_URL=http://localhost:<port>/api` in `frontend/.env` |
| Dropdowns empty in Predict / Listings | Backend not running or port mismatch |
| Model shows "not trained" | Run `python app/ml/train_extended.py` inside `backend/` |
| Database empty | Run `python seed.py` (or `--force` to replace) |
| App starts but prediction returns 503 | Artifacts missing — retrain the model |
| `RuntimeError: JWT_SECRET must be set` | You're running with `ENV=production` but no `JWT_SECRET` in `.env` |
| Login works locally but not in Docker | Check `CORS_ORIGINS` includes your frontend origin |
| Windows `n_jobs` multiprocessing error | Already set to `n_jobs=1` in training script |

---

## License

