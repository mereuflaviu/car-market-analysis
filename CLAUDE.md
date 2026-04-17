# AutoScope — Master Context Prompt

## What This Project Is

AutoScope is a full-stack Romanian used-car price intelligence platform built as a Master's academic
project (VD course). It combines a real scraped dataset from autovit.ro with an XGBoost ML model,
a FastAPI REST backend, and a React frontend. The goal: let users input car specs and get an
AI-powered price estimate, browse 5,444 real listings, and see similar cars as recommendations.

The project is currently a working local MVP. The next milestone is production deployment.

---

## Stack

| Layer      | Technology |
|------------|------------|
| ML         | XGBoost (trained via `backend/app/ml/train_extended.py`) |
| Backend    | FastAPI + SQLAlchemy + SQLite (WAL mode) + Pydantic v2 |
| Auth       | JWT in httpOnly cookies, refresh token rotation, bcrypt passwords |
| Frontend   | React 18 + Vite + Tailwind CSS v3 + Recharts |
| Deployment | Docker Compose + nginx (port 80 → /api/ proxy to backend:8001) |

---

## Repository Layout

d:\MASTER\Anul\1\VD\Proiect pred

├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app, startup, inline migrations
│   │   ├── models.py        # SQLAlchemy ORM (Car, User, Prediction)
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── crud.py          # DB queries incl. get_similar_cars()
│   │   ├── database.py      # SQLite engine (WAL, pool)
│   │   ├── dependencies.py  # get_current_user, get_optional_user
│   │   ├── routes/
│   │   │   ├── cars.py      # GET /cars, /cars/similar, /cars/stats, CRUD
│   │   │   ├── predictions.py
│   │   │   ├── analytics.py
│   │   │   ├── makes.py
│   │   │   ├── auth.py
│   │   │   └── admin.py
│   │   └── ml/
│   │       ├── train_extended.py   # XGBoost training script
│   │       └── inference.py        # lazy-load model, predict()
│   ├── artifacts/           # model.joblib, metadata.joblib, encoders
│   ├── seed.py              # seed cars from cleaned CSV
│   └── cars.db              # active SQLite database
├── frontend/
│   └── src/
│       ├── api/client.js    # axios instance + all API methods
│       ├── pages/
│       │   ├── Dashboard.jsx
│       │   ├── Listings.jsx
│       │   ├── Prediction.jsx
│       │   └── Analytics.jsx
│       └── components/
│           ├── CarForm.jsx
│           └── Navbar.jsx
├── model/
│   ├── data/
│   │   ├── raw_scraped_extended.csv
│   │   └── cleaned_car_listings_extended.csv  (75 cols incl. url)
│   └── extraction/
│       └── cleanup_data_extended.ipynb
├── docker-compose.yml
├── docker-compose.prod.yml
├── Dockerfile.backend
└── Dockerfile.frontend



---

## Current State (2026-04-17)

### Database
- **5,445 cars** seeded, all with `source_url` (autovit.ro listing links)
- **2 users** (admin: mereu_flaviu@yahoo.com)
- Active DB: `backend/cars.db`

### ML Model
- Algorithm: XGBoost Regressor
- R² = 0.932 | MAE = €1,986 | RMSE = €3,088
- Features: **88** (16 numerical, 8 categorical, 61 binary equipment flags, 2 target-encoded)
- Training samples: 4,182 | Test samples: 1,046
- Artifacts: `backend/artifacts/model.joblib`, `metadata.joblib`, `encoder.joblib`, `te_encoder.joblib`

### Features Shipped
- JWT auth (httpOnly cookies, refresh rotation, bcrypt)
- Role system: `admin` / `user`
- Car listings: full CRUD, filters (make, model, year, price, mileage, power, fuel, gearbox), sort,
  pagination, "My Listings" toggle, Autovit source link
- Price prediction: 88-feature XGBoost, 57 equipment binary checkboxes, tier badge
- Post-prediction recommendations: `/api/cars/similar` — same make+model primary, same make fallback
- Analytics: 8 charts (price dist, by make, by fuel, by body, year trend, mileage scatter, gearbox
  pie, transmission pie)
- Admin panel: user management (role, active status, delete)
- Model Details + Top Predictive Features cards: **admin-only**
- Docker Compose + nginx for deployment; `docker-compose.prod.yml` hardens JWT, hides port 8001,
  disables OpenAPI docs

### Local Dev Start
```bash
# Backend (from backend/)
uvicorn app.main:app --port 8001 --reload

# Frontend (from frontend/)
npm run dev
Key Design Decisions
SQLite WAL — safe for single-node deployment; no Postgres needed for this scale
Inline migrations — _run_migrations() in main.py adds columns on startup; no Alembic
EQUIPMENT_COLS excluded from seed — url column flows through the cleaned CSV but is excluded from EQUIPMENT_COLS = [c for c in df.columns if c not in BASIC_FEATURES and c != "url"]
Recommendations are pure SQL — no second ML model; get_similar_cars() in crud.py uses a 50%–115% price band with year+price proximity ordering and a same-make fallback if <3 results
VITE_API_URL=/api in Docker (relative path hits nginx proxy); use http://localhost:8001/api for local dev
JWT_SECRET must be set in production — backend raises RuntimeError at startup if unset or using the insecure default
What's Left / Planned Next
Immediate
 Run notebook re-execution to completion (verify 75 columns in cleaned CSV)
 Re-seed DB with full source_url population (python seed.py --force)
 End-to-end test: predict → recommendations → "View on Autovit →" links work
Deployment
 Choose hosting (VPS / Render / Railway)
 Set production env vars: JWT_SECRET, FIRST_ADMIN_EMAIL, CORS_ORIGINS, ENV=production
 Run docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
 Verify nginx serves frontend + proxies /api/ correctly
Potential Improvements (not committed)
Multimodal pricing (LLM + photo analysis) — discussed, not planned
Password reset flow (currently admin resets via Python script)
User profile edit page
Listing detail page (full car view, not just table row)
Equipment filter on Listings page


---

Save this wherever you want — it works as a `CLAUDE.md` at the project root, a Notion doc, 