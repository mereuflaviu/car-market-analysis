# AutoScope — Romanian Used-Car Price Intelligence

> Full-stack platform for browsing, listing, and AI-pricing Romanian second-hand cars — with an automated live data pipeline powered by XGBoost ML and secured with JWT authentication.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![XGBoost](https://img.shields.io/badge/XGBoost-R²%200.931-orange)
![SQLite](https://img.shields.io/badge/SQLite-WAL-003B57?logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

---

## Overview

AutoScope is a full-stack marketplace and analytics platform for the Romanian used-car market. It combines **real listing data** scraped from autovit.ro (~30,000+ cars), **interactive market analytics**, and an **AI price prediction engine** trained with XGBoost (R² = 0.931, MAE ≈ €1,986).

A fully automated pipeline keeps the dataset and model up to date — scraping new listings daily, detecting sold cars, and retraining the model when significant new data arrives.

---

## Features

| Area | What it does |
|------|-------------|
| **Landing page** | Public hero + feature overview, no login required |
| **Auth** | Register / Login / Logout with JWT in httpOnly cookies, 15-min access token + 7-day refresh |
| **Dashboard** | KPI cards (total listings, avg price, avg mileage, brands) + price distribution + gearbox split |
| **Listings** | Full CRUD with 12+ server-side filters (make, model, year, price, mileage, power, fuel, body, gearbox), "My Listings" toggle, cascading make→model select, pagination |
| **Price Prediction** | 88-feature XGBoost, 57 equipment checkboxes, tier badge (Basic/Standard/Premium/Ultra), price-range bar with ±MAE confidence interval, model metrics, feature importance, prediction history |
| **Recommendations** | Post-prediction similar car suggestions ranked by price proximity + year + mileage |
| **Analytics** | 8 Recharts charts: price by make/fuel/body-type, year vs price, mileage scatter, gearbox + transmission |
| **Admin → Users** | Paginated user table, promote/demote roles, ban/unban, delete |
| **Admin → Pipeline** | Trigger scrape runs, force model retrain, view run history and live metrics |
| **REST API** | 30+ endpoints, documented at `/docs` (dev only) |

---

## Automated Data Pipeline

The pipeline runs automatically every day at **03:00 Bucharest time** via APScheduler embedded in the FastAPI process. Every 3rd day it runs a full sweep instead of a daily scrape. Both can also be triggered manually from the **Admin → Pipeline** page.

```
daily scrape  (~5–15 min)
  └── scrape new listings from autovit.ro (stops after 3 empty pages)
  └── clean raw data (hard quality rules)
  └── append cleaned rows to cleaned_car_listings_extended.csv
  └── sync new listings into DB
  └── retrain XGBoost if new data was added

full sweep  (~2–4 hrs, every 3 days)
  └── same as daily, but also:
  └── scan all pages (stops after 10 consecutive empty pages)
  └── track which existing URLs were seen (seen_urls)
  └── listings not seen → days_missing++
  └── mark as sold after 3 missed sweeps (hidden from listings page)
  └── reactivate if a sold listing reappears on autovit
  └── permanently delete after 6 months sold
```

Car lifecycle: `active` → `sold` (after 3 missed full sweeps) → deleted (6 months after sold date)

---

## Quick Start

### Docker (recommended)

```bash
docker compose up --build
```

App at **http://localhost** — backend health at **http://localhost/health**

After code changes:
```bash
docker compose build --no-cache && docker compose up
```

### Local Dev

```bash
# Backend
cd backend
cp .env.example .env          # fill in JWT_SECRET, FIRST_ADMIN_EMAIL
pip install -r requirements.txt
python app/ml/train_extended.py   # train XGBoost (~1 min)
python seed.py                    # load listings into SQLite
uvicorn app.main:app --reload --port 8001

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Frontend: **http://localhost:5173** — API docs: **http://localhost:8001/docs**

---

## Environment Variables (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `ENV` | yes | `development` or `production` |
| `JWT_SECRET` | yes | Strong random string — `python -c "import secrets; print(secrets.token_hex(32))"` |
| `FIRST_ADMIN_EMAIL` | yes | First user to register with this email becomes admin |
| `DB_PATH` | no | SQLite file path (default: `cars.db` in working dir) |
| `SCRAPER_DIR` | no | Path to scraper module — set to `/model/extraction` in Docker |
| `PIPELINE_FULL_SWEEP_DAYS` | no | Full sweep every N days (default: `3`) |
| `DISABLE_SCHEDULER` | no | Set `1` to skip auto-scheduling |
| `API_KEY` | prod | Mutation guard header |
| `CORS_ORIGINS` | prod | Comma-separated allowed origins |

> **Production**: `ENV=production` enforces `JWT_SECRET` at startup, hides API docs, enforces API key on mutations.

---

## ML Model

| Metric | Value |
|---|---|
| Algorithm | XGBoost Regressor |
| R² (test) | **0.931** |
| MAE | **≈ €1,986** |
| RMSE | ≈ €3,088 |
| Features | **88** (16 numerical, 8 categorical, 61 equipment flags, 2 target-encoded) |
| Training data | `model/data/cleaned_car_listings_extended.csv` — grows with each pipeline run |

### Feature Engineering highlights

| Feature | Description |
|---|---|
| `car_age` / `log_car_age` | Age from current year, linear + log |
| `power_per_liter` | Engine power ÷ displacement |
| `power_over_age` | Power ÷ (age + 1) — freshness × performance |
| `equip_per_age` | Equipment count ÷ (age + 1) |
| `brand_tier` | luxury / mainstream / budget classification |
| `cohort` | make\|model\|year smoothed target encoding |
| `equipment_count` | Sum of 61 binary equipment flags |

Retraining: triggered automatically after new listings sync. New model only replaces current if R² doesn't drop more than 0.01 or MAE stays within 5%.

---

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, startup, inline migrations, APScheduler
│   │   ├── models.py            # ORM: Car, User, Prediction, PriceHistory, PipelineRun
│   │   ├── schemas.py           # Pydantic v2 schemas
│   │   ├── crud.py              # DB queries
│   │   ├── dependencies.py      # get_current_user, require_admin
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── cars.py
│   │   │   ├── predictions.py
│   │   │   ├── analytics.py
│   │   │   ├── makes.py
│   │   │   └── admin.py         # user management + pipeline endpoints
│   │   ├── ml/
│   │   │   ├── train_extended.py  # XGBoost training (88 features)
│   │   │   └── inference.py       # lazy-load model + predict()
│   │   └── pipeline/
│   │       ├── run.py           # orchestrator: scrape → clean → sync → retrain
│   │       ├── scrape.py        # AutovitExtendedScraper wrapper (lazy import)
│   │       ├── clean.py         # hard data-quality rules + append_to_cleaned_csv
│   │       ├── sync_db.py       # upsert engine keyed on source_url + stale detection
│   │       └── retrain.py       # conditional retraining with metric comparison
│   ├── artifacts/               # model.joblib, metadata.joblib, encoders (git-ignored)
│   ├── seed.py                  # CSV → SQLite loader
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/client.js        # Axios + 401 refresh interceptor + all API methods
│       ├── context/AuthContext.jsx
│       ├── components/
│       │   ├── AppLayout.jsx    # sticky nav with admin sub-nav
│       │   └── RequireAuth.jsx  # route guards
│       └── pages/
│           ├── Dashboard.jsx
│           ├── Listings.jsx
│           ├── Prediction.jsx
│           ├── Analytics.jsx
│           ├── AdminUsers.jsx
│           └── AdminPipeline.jsx  # pipeline control + history
├── model/
│   ├── data/
│   │   ├── raw_scraped_extended.csv
│   │   └── cleaned_car_listings_extended.csv
│   └── extraction/
│       ├── scraper_extended.py    # autovit.ro scraper (seen_urls tracking for stale detection)
│       └── cleanup_data_extended.ipynb
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── nginx.conf
```

---

## REST API

| Group | Endpoints |
|---|---|
| Auth | `POST /api/auth/register` `/login` `/logout` `/refresh` · `GET /api/auth/me` |
| Cars | `GET POST /api/cars` · `GET PUT DELETE /api/cars/{id}` · `GET /api/cars/stats` `/cars/recommendations` |
| Predictions | `POST /api/predictions/predict` · `GET /api/predictions/history` · `GET DELETE /api/predictions/{id}` · `GET /api/predictions/model-info` |
| Analytics | `/price-distribution` `/price-by-make` `/price-by-fuel` `/price-by-body-type` `/mileage-vs-price` `/year-vs-price` `/gearbox-distribution` `/transmission-distribution` |
| Reference | `GET /api/makes` `/api/makes/options` `/api/makes/{make}/models` |
| Admin Users | `GET /api/admin/users` · `GET PATCH DELETE /api/admin/users/{id}` |
| Admin Pipeline | `POST /api/admin/pipeline/run` · `GET /api/admin/pipeline/status` `/history` · `POST /api/admin/pipeline/retrain` |
| Health | `GET /health` |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Backend crashes on startup with `SyntaxError` or `ImportError` | Rebuild with `docker compose build --no-cache` |
| UI shows old version after code changes | `docker compose build --no-cache && docker compose up` |
| `ModuleNotFoundError: No module named 'app'` | Run `uvicorn` from inside `backend/` |
| Dropdowns empty in Predict / Listings | Backend not running or `VITE_API_URL` mismatch |
| Model shows "not trained" | Run `python app/ml/train_extended.py` inside `backend/` |
| Pipeline retrain fails with `KeyError: equipment_count` | Ensure `SCRAPER_DIR` env var points to `/model/extraction` and the CSV is mounted |
| `RuntimeError: JWT_SECRET must be set` | Set a real `JWT_SECRET` in `backend/.env` when using `ENV=production` |

---

## License

Academic project — Master's programme, VD course.
