# CarMarket — Used Car Price Analysis & Prediction Platform

> Full-stack web platform for analysing the Romanian second-hand car market and predicting vehicle prices with machine learning.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![XGBoost](https://img.shields.io/badge/XGBoost-R²%200.9343-orange)
![SQLite](https://img.shields.io/badge/SQLite-cars.db-003B57?logo=sqlite&logoColor=white)

---

## Overview

CarMarket scrapes, cleans, and analyses **5,444 real car listings** from autovit.ro, then serves them through a REST API consumed by a React SPA. The centrepiece is an XGBoost regression model that predicts market price from 32 features — including engineered signals like power-per-litre, brand tier, and smoothed target encoding for make/model — achieving **R² = 0.9343** and **MAE ≈ €1,921**.

---

## Features

- **Dashboard** — KPI cards + interactive charts (price distribution, gearbox split)
- **Listings** — full CRUD table with 10+ filters, cascading make → model select, pagination
- **Price Prediction** — 56 individual equipment checkboxes, live tier badge, price-range visualisation
- **Analytics** — 7 Recharts charts covering price by make/fuel/body, mileage vs price scatter, depreciation trend
- **REST API** — 19 endpoints, auto-documented at `/docs`

---

## Quick Start

```bash
# 1 — Backend
cd backend
pip install -r requirements.txt
python app/ml/train_extended.py   # trains XGBoost, saves artifacts (~1 min)
python seed.py                    # loads 5,444 listings into SQLite
uvicorn app.main:app --reload --port 8001

# 2 — Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — API docs at **http://localhost:8001/docs**.

> Re-seed from scratch: `python seed.py --force`

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

### Feature Engineering

Beyond the raw inputs the model uses several derived signals:

| Feature | Description |
|---------|-------------|
| `car_age` / `log_car_age` | Age from current year, linear + log |
| `power_per_liter` | Engine power ÷ displacement (sportiness proxy) |
| `power_over_age` | Power ÷ (age + 1) — performance × newness |
| `power_auto` | Power × automatic gearbox indicator |
| `equip_per_age` | Equipment count ÷ (age + 1) |
| `brand_tier` | luxury / mainstream / budget |
| `mileage_vs_cohort` | Z-score vs same make+model+year |
| `make` / `model` | Smoothed target encoding (SmoothedTargetEncoder) |
| `equipment_count` | Count of 56 optional extras |

### Training

```bash
cd backend
python app/ml/train_extended.py           # default experiment (target_enc)
python app/ml/train_extended.py --tune    # + RandomizedSearchCV (slower)
```

Artifacts are saved to `backend/artifacts/`: `model.joblib`, `encoder.joblib`, `te_encoder.joblib`, `metadata.joblib`.

---

## REST API

| Group | Endpoints |
|-------|-----------|
| Cars CRUD | `GET/POST /api/cars`, `GET/PUT/DELETE /api/cars/{id}`, `GET /api/cars/stats` |
| Predictions | `POST /api/predictions/predict`, `GET /api/predictions/history`, `GET/DELETE /api/predictions/{id}` |
| Reference | `GET /api/makes`, `GET /api/makes/options`, `GET /api/makes/{make}/models` |
| Analytics | `price-distribution`, `price-by-make`, `price-by-fuel`, `price-by-body-type`, `mileage-vs-price`, `year-vs-price` |

### Example — predict price

```bash
curl -X POST http://localhost:8001/api/predictions/predict \
  -H "Content-Type: application/json" \
  -d '{
    "make": "BMW", "model": "Seria 5", "year": 2019,
    "body_type": "Sedan", "mileage": 85000, "color": "Negru",
    "fuel_type": "Diesel", "engine_capacity": 1995, "engine_power": 190,
    "gearbox": "Automata", "transmission": "4x4 (automat)",
    "pollution_standard": "Euro 6", "equipment_count": 12
  }'
```

---

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, router registration
│   │   ├── database.py          # SQLAlchemy + SQLite
│   │   ├── models.py            # ORM: Car, Prediction
│   │   ├── schemas.py           # Pydantic v2 schemas
│   │   ├── crud.py              # DB helpers
│   │   ├── routes/              # cars · predictions · analytics · makes
│   │   └── ml/
│   │       ├── encoders.py      # SmoothedTargetEncoder (stable import path)
│   │       ├── train_extended.py# Full training pipeline (6 experiments)
│   │       └── inference.py     # Lazy-load, feature engineering, predict
│   ├── artifacts/               # Saved model files (git-ignored)
│   ├── seed.py                  # CSV → SQLite loader (--force to re-seed)
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── api/client.js        # Axios wrappers
│       ├── components/
│       │   ├── Layout.jsx       # Sidebar nav
│       │   └── CarForm.jsx      # Add / Edit modal
│       └── pages/
│           ├── Dashboard.jsx
│           ├── Listings.jsx     # Filters, CRUD, pagination
│           ├── Prediction.jsx   # 56-checkbox equipment, price range bar
│           └── Analytics.jsx    # 7 interactive charts
│
└── model/
    ├── data/
    │   ├── cleaned_car_listings_extended.csv  # 5,444 cleaned rows
    │   └── raw_scraped_extended.csv           # 11,000 raw rows
    └── extraction/
        ├── scraper_extended.py                # autovit.ro → Next.js JSON scraper
        └── cleanup_data_extended.ipynb        # cleaning + feature engineering
```

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React 18, Vite, Tailwind CSS, Recharts, React Router v6, Axios |
| Backend | FastAPI, Uvicorn, SQLAlchemy, Pydantic v2 |
| Database | SQLite |
| ML | XGBoost, scikit-learn, pandas, numpy, joblib |
| Scraping | requests, BeautifulSoup4, Next.js `__NEXT_DATA__` extraction |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: No module named 'app'` | Run `uvicorn` from inside `backend/` |
| Port 8001 in use | Add `--port 8080`, update `frontend/src/api/client.js` |
| Dropdowns empty in Predict form | Backend not running or port mismatch |
| Model shows "not trained" | Run `python app/ml/train_extended.py` inside `backend/` |
| Database empty | Run `python seed.py` (or `--force` to replace existing data) |
| Windows `n_jobs` multiprocessing error | Already set to `n_jobs=1` everywhere |

---

## License

