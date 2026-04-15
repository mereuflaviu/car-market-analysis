# AutoScope MVP Deployment Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden AutoScope from a working prototype into a deployable MVP by fixing the most critical production blockers, then layering in product polish.

**Architecture:** FastAPI backend + React/Vite frontend served via nginx reverse proxy in Docker Compose. The frontend calls `/api/...` relative paths (proxied by nginx to the backend container), eliminating CORS friction in production. SQLite with WAL mode is kept for first deploy; a PostgreSQL migration path is documented but deferred.

**Tech Stack:** FastAPI 0.104, SQLAlchemy 2.0, SQLite (WAL), XGBoost 2.0, React 18, Vite, Tailwind CSS v3, nginx (Docker), slowapi, python-jose, passlib+bcrypt

---

## Audit Summary

### Already Product-Ready
- JWT auth in httpOnly cookies with refresh interceptor — correct and secure
- `RequireAuth` / `RequireAdmin` route guards — correctly implemented
- Ownership checks on all CRUD mutations — correct
- ML inference: lazy-loaded, thread-safe, feature-engineered — solid
- Docker multi-stage build + nginx with CSP, gzip, security headers — good baseline
- Health endpoint (`/health`) with DB + ML checks — ready
- Rate limiting via slowapi on mutation endpoints
- Admin panel (ban/promote/delete users) — correct
- SQLite WAL mode + NORMAL synchronous — appropriate for single-node deploy

### Critical Blockers Before Deploy

| # | Issue | Impact |
|---|-------|--------|
| 1 | `VITE_API_URL` baked to `http://localhost:8001/api` at Docker build time | API unreachable in prod because port 8001 is internal only |
| 2 | nginx CSP `connect-src 'self'` + hardcoded full URL = blocked API calls | White screen / all API calls fail |
| 3 | Listings: mileage + power filters are **client-side only** on 20-item page | Users get wrong results when filtering |
| 4 | Prediction.jsx error handler uses `err.response?.data?.detail` but `client.js` already normalizes errors to `err.message` | Error messages never show |
| 5 | `JWT_SECRET` falls back to `"dev-secret-change-in-production"` silently | Insecure in prod if env is misconfigured |
| 6 | Refresh token is **not rotated** on use | Stolen refresh token valid indefinitely |
| 7 | `backend/.env` exists with real secrets but is git-ignored — no example for production operators | Ops confusion, risk of accidental commit |
| 8 | No `VITE_API_URL` set in `frontend/.env.example` | Ops gaps |

### Recommended Polish (after deploy is stable)
- Analytics page: add loading skeletons, empty state, chart tooltips
- Listings: add "my listings" filter tab for logged-in users
- Prediction: fix hard-coded "Training samples: 4,181" (should read from model metadata)
- Dashboard: race condition — all 4 API calls fire in parallel, any single failure kills whole page
- Admin: add listing count per user column
- Improve `SessionLocal` usage consistency in health check

### Future Roadmap
- Alembic for proper schema migrations
- PostgreSQL migration (when user count warrants it)
- Refresh token rotation with a token store
- Background retraining pipeline
- Structured logging / Sentry integration
- E2E tests

---

## File Map

| File | Change |
|------|--------|
| `docker-compose.yml` | Set `VITE_API_URL=/api` (relative, proxied by nginx) |
| `nginx.conf` | Fix CSP `connect-src` to allow `/api/` proxy calls; add `/health` proxy header fix |
| `backend/app/main.py` | Add production hard-fail if `JWT_SECRET` equals the default insecure value |
| `backend/app/routes/auth.py` | Rotate refresh token on `/auth/refresh` |
| `backend/app/routes/cars.py` | Add `mileage_min`, `mileage_max`, `power_min`, `power_max` query params |
| `backend/app/crud.py` | Add mileage + power range filter logic to `get_cars()` |
| `backend/app/schemas.py` | No change needed |
| `frontend/src/pages/Prediction.jsx` | Fix error handler: use `err.message` not `err.response?.data?.detail`; fix hard-coded sample counts |
| `frontend/src/pages/Listings.jsx` | Send mileage/power filter params to API instead of client-side filtering |
| `frontend/.env.example` | Add `VITE_API_URL=` entry with instructions |
| `backend/.env.example` | Verify all required keys documented (already looks good) |

---

## Phase 1 — Deploy-Critical Fixes

### Task 1: Fix VITE_API_URL for Docker (relative API path)

**Problem:** `docker-compose.yml` passes `VITE_API_URL=http://localhost:8001/api` to the frontend build. In the deployed container, `localhost:8001` is only reachable inside the container network — the browser cannot reach it. Nginx already proxies `/api/` → backend, so the frontend should use the relative path `/api`.

**Files:**
- Modify: `docker-compose.yml`
- Modify: `nginx.conf`

- [ ] **Step 1: Update docker-compose.yml to use relative API path**

Open `docker-compose.yml` and change:

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    env_file: backend/.env
    volumes:
      - ./backend/cars.db:/app/cars.db
      - ./backend/artifacts:/app/artifacts
    ports:
      - "8001:8001"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
      args:
        VITE_API_URL: /api
        VITE_API_KEY: ${VITE_API_KEY:-}
    ports:
      - "80:80"
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped
```

Key change: `VITE_API_URL: /api` (was `${VITE_API_URL:-http://localhost:8001/api}`).

- [ ] **Step 2: Fix nginx CSP to allow same-origin API calls**

The CSP `connect-src 'self'` is correct when using relative paths — `'self'` covers same-origin fetch. No CSP change needed. But verify: open `nginx.conf` and confirm the `/api/` proxy block does NOT have a trailing slash mismatch.

Current nginx proxy:
```nginx
location /api/ {
    proxy_pass http://backend:8001/api/;
```

This is correct — `/api/foo` → `http://backend:8001/api/foo`. No change needed.

- [ ] **Step 3: Add `frontend/.env.example`**

Create `frontend/.env.example`:
```
# API base URL — use /api for Docker (nginx proxies it), or http://localhost:8001/api for local dev
VITE_API_URL=
# Optional API key (set if backend is running with ENV=production)
VITE_API_KEY=
```

- [ ] **Step 4: Verify locally that Docker build works**

```bash
docker-compose build --no-cache frontend
docker-compose up -d
curl http://localhost/api/health
```

Expected: `{"status":"ok"}`

- [ ] **Step 5: Verify frontend can reach API through nginx**

Open `http://localhost` in browser → Dashboard should load with data. Open browser DevTools → Network → confirm API calls go to `http://localhost/api/...` not `http://localhost:8001/api/...`.

---

### Task 2: Fix Prediction.jsx error display

**Problem:** `handleSubmit` in `Prediction.jsx` accesses `err.response?.data?.detail` to show errors, but `client.js`'s response interceptor already normalizes all API errors into `new Error(message)` — so the error is on `err.message`. The current code always falls through to the default message.

**Files:**
- Modify: `frontend/src/pages/Prediction.jsx:211`

- [ ] **Step 1: Fix the error handler**

In `frontend/src/pages/Prediction.jsx`, find the catch block in `handleSubmit`:

```js
    } catch (err) {
      setError(err.response?.data?.detail || 'Prediction failed. Is the ML model trained?')
    }
```

Change to:

```js
    } catch (err) {
      setError(err.message || 'Prediction failed. Is the ML model trained?')
    }
```

- [ ] **Step 2: Fix hard-coded model sample counts**

Still in `Prediction.jsx`, find the Model Details card:

```js
                ['Training samples', '4,181'],
                ['Test samples', '1,046'],
```

Change to read from `modelInfo` if available:

```js
                ['Training samples', modelInfo?.train_samples ? modelInfo.train_samples.toLocaleString() : '4,181'],
                ['Test samples', modelInfo?.test_samples ? modelInfo.test_samples.toLocaleString() : '1,046'],
```

- [ ] **Step 3: Update backend to expose train/test sample counts in model-info**

In `backend/app/ml/inference.py`, in `get_model_info()`, add:

```python
    return {
        "status":        "ready",
        "experiment":    _metadata.get("experiment", "unknown"),
        "dataset":       _metadata.get("dataset", "unknown"),
        "log_target":    _metadata.get("log_target", False),
        "r2":            _metadata.get("r2"),
        "mae":           _metadata.get("mae"),
        "rmse":          _metadata.get("rmse"),
        "cv_r2":         _metadata.get("cv_r2"),
        "n_features":    len(_metadata.get("all_features", [])),
        "features":      _metadata.get("all_features", []),
        "top_features":  get_feature_importance(top_n=10),
        "train_samples": _metadata.get("train_samples"),
        "test_samples":  _metadata.get("test_samples"),
    }
```

(These keys will be `None` if the current metadata.joblib doesn't include them — the UI already handles that with the fallback.)

- [ ] **Step 4: Verify**

Start the dev backend and frontend, go to `/app/predict`, submit a prediction with an invalid make (e.g., empty), confirm the error message from the server now renders correctly instead of the default fallback.

```bash
# Backend
cd backend && uvicorn app.main:app --port 8001 --reload

# Frontend (new terminal)
cd frontend && npm run dev
```

Open `http://localhost:5173/app/predict`, attempt to predict without selecting a make → should show the validation error from the server.

---

### Task 3: Add mileage and power range filters to backend

**Problem:** `Listings.jsx` collects `mileage_min`, `mileage_max`, `power_min`, `power_max` from the user but explicitly skips sending them to the backend, instead filtering client-side on the already-paginated 20-row response. This produces incorrect results — a user filtering for "< 50,000 km" only gets rows matching that filter within the current page of 20 results, not across all 5,444 listings.

**Files:**
- Modify: `backend/app/crud.py`
- Modify: `backend/app/routes/cars.py`
- Modify: `frontend/src/pages/Listings.jsx`

- [ ] **Step 1: Add mileage + power filters to `crud.get_cars()`**

In `backend/app/crud.py`, update the `get_cars()` signature and body:

```python
def get_cars(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    make: Optional[str] = None,
    model: Optional[str] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    fuel_type: Optional[str] = None,
    body_type: Optional[str] = None,
    gearbox: Optional[str] = None,
    transmission: Optional[str] = None,
    mileage_min: Optional[float] = None,
    mileage_max: Optional[float] = None,
    power_min: Optional[float] = None,
    power_max: Optional[float] = None,
    sort_by: Optional[str] = None,
    sort_dir: str = "asc",
):
    q = db.query(models.Car)
    if make:
        q = q.filter(models.Car.make == make)
    if model:
        q = q.filter(models.Car.model == model)
    if year_min:
        q = q.filter(models.Car.year >= year_min)
    if year_max:
        q = q.filter(models.Car.year <= year_max)
    if price_min is not None:
        q = q.filter(models.Car.price >= price_min)
    if price_max is not None:
        q = q.filter(models.Car.price <= price_max)
    if fuel_type:
        q = q.filter(models.Car.fuel_type == fuel_type)
    if body_type:
        q = q.filter(models.Car.body_type == body_type)
    if gearbox:
        q = q.filter(models.Car.gearbox == gearbox)
    if transmission:
        q = q.filter(models.Car.transmission == transmission)
    if mileage_min is not None:
        q = q.filter(models.Car.mileage >= mileage_min)
    if mileage_max is not None:
        q = q.filter(models.Car.mileage <= mileage_max)
    if power_min is not None:
        q = q.filter(models.Car.engine_power >= power_min)
    if power_max is not None:
        q = q.filter(models.Car.engine_power <= power_max)

    _SORTABLE = {"price", "year", "mileage", "engine_power", "make"}
    if sort_by and sort_by in _SORTABLE:
        col = getattr(models.Car, sort_by)
        q = q.order_by(col.desc() if sort_dir == "desc" else col.asc())
    else:
        q = q.order_by(models.Car.id.asc())

    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return items, total
```

- [ ] **Step 2: Expose new filters in the cars router**

In `backend/app/routes/cars.py`, update `list_cars()`:

```python
@router.get("", response_model=schemas.CarListResponse)
def list_cars(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    make: Optional[str] = None,
    model: Optional[str] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    fuel_type: Optional[str] = None,
    body_type: Optional[str] = None,
    gearbox: Optional[str] = None,
    transmission: Optional[str] = None,
    mileage_min: Optional[float] = None,
    mileage_max: Optional[float] = None,
    power_min: Optional[float] = None,
    power_max: Optional[float] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = "asc",
    db: Session = Depends(get_db),
):
    items, total = crud.get_cars(
        db, page=page, page_size=page_size,
        make=make, model=model,
        year_min=year_min, year_max=year_max,
        price_min=price_min, price_max=price_max,
        fuel_type=fuel_type, body_type=body_type,
        gearbox=gearbox, transmission=transmission,
        mileage_min=mileage_min, mileage_max=mileage_max,
        power_min=power_min, power_max=power_max,
        sort_by=sort_by, sort_dir=sort_dir or "asc",
    )
    return schemas.CarListResponse(items=items, total=total, page=page, page_size=page_size)
```

- [ ] **Step 3: Fix Listings.jsx to send mileage/power params to the API**

In `frontend/src/pages/Listings.jsx`, find the `fetchCars` function. Remove mileage/power from the `skip` list and remove any client-side filtering:

```js
  const fetchCars = useCallback(
    async (p) => {
      setLoading(true)
      try {
        const params = { page: p, page_size: PAGE_SIZE }
        for (const [k, v] of Object.entries(filters)) {
          if (v === '') continue
          params[k] = v
        }
        const r = await carsApi.list(params)
        setCars(r.data.items)
        setTotal(r.data.total)
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    },
    [filters],
  )
```

Also remove any client-side filtering logic that was applied after fetching (the `const skip = [...]` array and any `.filter()` calls on `r.data.items`).

- [ ] **Step 4: Verify**

```bash
# Backend
cd backend && uvicorn app.main:app --port 8001 --reload

# Test the new params
curl "http://localhost:8001/api/cars?mileage_max=50000&page=1&page_size=5"
```

Expected: Response with `total` reflecting the true count of cars with mileage ≤ 50,000 km (not just 20).

Then in the frontend, open Listings, set a mileage max, and confirm the result count changes correctly.

---

### Task 4: Harden JWT secret validation at startup

**Problem:** If `JWT_SECRET` is not set (empty env var), the fallback is `"dev-secret-change-in-production"` — used silently in production. A startup check should fail fast if ENV=production and JWT_SECRET is the default or empty.

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: Add production secret validation to `validate_config()`**

In `backend/app/main.py`, update the `validate_config` startup handler:

```python
@app.on_event("startup")
def validate_config():
    env = os.getenv("ENV", "development")
    jwt_secret = os.getenv("JWT_SECRET", "")
    insecure_default = "dev-secret-change-in-production"

    if env == "production":
        if not os.getenv("API_KEY"):
            logger.warning("API_KEY not set in production — mutation endpoints unprotected")
        if not jwt_secret or jwt_secret == insecure_default:
            logger.critical(
                "FATAL: JWT_SECRET is not set or is using the insecure default. "
                "Set a strong random JWT_SECRET in your environment before running in production."
            )
            raise RuntimeError("JWT_SECRET must be set in production")

    logger.info("AutoScope API starting — env=%s", env)
```

- [ ] **Step 2: Verify the guard works**

Temporarily set `ENV=production` and leave `JWT_SECRET` unset:

```bash
cd backend
ENV=production JWT_SECRET="" uvicorn app.main:app --port 8001
```

Expected: Server starts then immediately raises `RuntimeError` and exits with a critical log message. Restore `ENV=development` or a proper `JWT_SECRET` to continue dev work.

---

### Task 5: Rotate refresh token on use

**Problem:** `/auth/refresh` issues a new *access* token but does **not** rotate the refresh token. If a refresh token is stolen, it remains valid for the full 7-day lifetime. Rotating it on each use limits the window.

**Files:**
- Modify: `backend/app/routes/auth.py`

- [ ] **Step 1: Rotate refresh token cookie in the `/refresh` endpoint**

The `_set_auth_cookies` helper already issues both tokens. It is already called in `/refresh`. Verify the current implementation:

In `backend/app/routes/auth.py`, the `/refresh` endpoint currently calls `_set_auth_cookies(response, user.id, user.role)` — which issues **both** a new access token and a new refresh token. This is already correct rotation behavior.

Verify by reading the current `refresh` endpoint:

```python
@router.post("/refresh", response_model=schemas.UserOut)
def refresh(
    response: Response,
    refresh_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = decode_token(refresh_token)
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = crud.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or banned")
    _set_auth_cookies(response, user.id, user.role)
    return user
```

`_set_auth_cookies` calls both `create_access_token` and `create_refresh_token` → refresh cookie is overwritten with a new token. Rotation is already in place. No code change needed — this task is a **verification step**.

- [ ] **Step 2: Document the known gap**

Add a code comment above the `/refresh` endpoint:

```python
# NOTE: Refresh token rotation is implemented (new token issued on each use).
# Full revocation (token blacklist) requires a token store (Redis/DB table) and
# is deferred to the post-MVP roadmap. Current rotation limits but doesn't
# eliminate the window for a stolen token.
```

---

### Task 6: Production Docker-compose configuration

**Problem:** The current `docker-compose.yml` exposes port 8001 directly (`"8001:8001"`) — this should be removed in production so only nginx is the public entry point. Also, production needs `ENV=production` and a real `JWT_SECRET` injected at runtime (not from a committed file).

**Files:**
- Modify: `docker-compose.yml`
- Create: `docker-compose.prod.yml`

- [ ] **Step 1: Create a production override file**

Create `docker-compose.prod.yml`:

```yaml
# Production override — use with:
#   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
#
# Required environment variables (set in shell or a .env file that is NOT committed):
#   JWT_SECRET, API_KEY, FIRST_ADMIN_EMAIL, VITE_API_KEY (optional)

services:
  backend:
    ports: []          # Remove direct port exposure — only nginx should be public
    environment:
      - ENV=production
    env_file: backend/.env    # Operator must create this from backend/.env.example

  frontend:
    build:
      args:
        VITE_API_URL: /api    # Relative path — nginx proxies /api/ to backend
        VITE_API_KEY: ${VITE_API_KEY:-}
```

- [ ] **Step 2: Update the base docker-compose.yml VITE_API_URL**

In `docker-compose.yml`, update the frontend build args to use `/api` as the default (safe for both dev and prod Docker):

```yaml
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
      args:
        VITE_API_URL: /api
        VITE_API_KEY: ${VITE_API_KEY:-}
```

- [ ] **Step 3: Test the base compose setup**

```bash
docker-compose down -v
docker-compose up --build -d
curl http://localhost/api/health
curl http://localhost/api/cars?page_size=1
```

Both should return valid JSON responses. Open browser at `http://localhost` and verify the dashboard loads.

---

## Phase 2 — Product Polish

### Task 7: Fix Dashboard parallel API call failure

**Problem:** `Dashboard.jsx` uses `Promise.all([...])` for 4 API calls. If any one fails (e.g., analytics endpoint down), the entire dashboard fails to render. The `modelInfo` call already has `.catch(() => null)` but the others don't.

**Files:**
- Modify: `frontend/src/pages/Dashboard.jsx`

- [ ] **Step 1: Make all dashboard API calls fault-tolerant**

```js
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
```

- [ ] **Step 2: Verify**

Stop the backend, load the dashboard → it should show empty state charts rather than a blank/error page. Restart the backend → charts populate.

---

### Task 8: Add "My Listings" tab to Listings page

**Problem:** Logged-in users cannot easily find their own listings among 5,444. A simple toggle to filter `user_id` would fix this.

**Files:**
- Modify: `backend/app/routes/cars.py`
- Modify: `backend/app/crud.py`
- Modify: `frontend/src/pages/Listings.jsx`

- [ ] **Step 1: Add `mine` filter parameter to backend**

In `backend/app/routes/cars.py`:

```python
@router.get("", response_model=schemas.CarListResponse)
def list_cars(
    ...
    mine: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_optional_user),
):
    owner_id = current_user.id if (mine and current_user) else None
    items, total = crud.get_cars(
        db, ..., owner_id=owner_id, ...
    )
```

Add `get_optional_user` import from `..dependencies`.

In `backend/app/crud.py`, add `owner_id` param:

```python
def get_cars(
    db: Session,
    ...
    owner_id: Optional[int] = None,
    ...
):
    q = db.query(models.Car)
    if owner_id is not None:
        q = q.filter(models.Car.user_id == owner_id)
    ...
```

- [ ] **Step 2: Add "My Listings" toggle in frontend**

In `frontend/src/pages/Listings.jsx`, add a toggle button next to the filter bar:

```jsx
{user && (
  <button
    className={`px-4 py-1.5 rounded-pill text-sm font-medium transition-colors ${
      filters.mine
        ? 'bg-black text-white'
        : 'bg-as-chip text-black hover:bg-as-hover'
    }`}
    onClick={() => {
      setFilters(f => ({ ...f, mine: !f.mine }))
      setPage(1)
    }}
  >
    My Listings
  </button>
)}
```

Add `mine: false` to `EMPTY_FILTERS`.

- [ ] **Step 3: Verify**

Log in, add a listing, then toggle "My Listings" → only your listing appears. Log out → "My Listings" button is hidden.

---

### Task 9: Add loading skeletons to Analytics page

**Problem:** Analytics page shows nothing while 8 API calls load in parallel. This is jarring.

**Files:**
- Modify: `frontend/src/pages/Analytics.jsx`

- [ ] **Step 1: Add a skeleton card component**

At the top of `Analytics.jsx`, add:

```jsx
function ChartSkeleton() {
  return (
    <div className="card animate-pulse">
      <div className="h-4 bg-[#f0f0f0] rounded w-1/3 mb-4" />
      <div className="h-[240px] bg-[#f0f0f0] rounded" />
    </div>
  )
}
```

- [ ] **Step 2: Show skeletons while loading**

Replace the loading conditional with a grid of skeletons matching the real layout:

```jsx
  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-[32px] font-bold text-black leading-tight">Analytics</h1>
          <p className="text-as-body text-sm mt-1">Market intelligence across 5,444 listings</p>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {Array.from({ length: 6 }).map((_, i) => <ChartSkeleton key={i} />)}
        </div>
      </div>
    )
  }
```

- [ ] **Step 3: Verify**

Throttle the network in DevTools (Slow 3G), navigate to `/app/analytics` → skeleton cards appear then resolve to charts.

---

## Phase 3 — Post-Deploy / Scale Direction

### Task 10: Document PostgreSQL migration path

**Objective:** Provide a clear migration guide when SQLite becomes a bottleneck (concurrent writes, multi-instance deployment, managed hosting).

**Files:**
- Create: `docs/plans/postgres-migration.md`

- [ ] **Step 1: Create migration guide**

```markdown
# PostgreSQL Migration Guide

## When to migrate

Migrate from SQLite → PostgreSQL when any of these are true:
- Concurrent write contention (WAL mode helps but doesn't solve multi-writer bottlenecks)
- Deploying to multi-instance / container orchestration (Kubernetes, Railway replicas)
- Needing managed backups, PITR, or replication

## Steps

1. Add psycopg2 dependency: `pip install psycopg2-binary==2.9.9`
2. Change DATABASE_URL env var: `postgresql://user:pass@host:5432/autoscope`
3. Remove `connect_args={"check_same_thread": False}` from `database.py`
4. Remove WAL PRAGMA event listener from `database.py`
5. Add Alembic: `pip install alembic && alembic init alembic`
6. Generate initial migration: `alembic revision --autogenerate -m "initial"`
7. Run migration: `alembic upgrade head`
8. Remove inline migration code from `main.py` (`_run_migrations()`)
9. Update docker-compose.yml to add `postgres` service
10. Export SQLite data: `sqlite3 cars.db .dump > dump.sql` → adapt and import

## Recommended hosting

- **Render**: Managed PostgreSQL, free tier, works with render.yaml deploy
- **Railway**: Automatic PostgreSQL plugin, simple env var injection
- **Fly.io**: Fly Postgres (Patroni), good for low-latency European regions
```

---

## Deploy-Ready Checklist

```
[ ] VITE_API_URL=/api baked into Docker frontend build
[ ] docker-compose.yml no longer exposes port 8001 directly in prod
[ ] JWT_SECRET is a strong random value (not default) in backend/.env
[ ] ENV=production is set in backend/.env on the server
[ ] FIRST_ADMIN_EMAIL is set in backend/.env
[ ] nginx CSP allows connect-src 'self' (correct when using /api relative path)
[ ] Health endpoint responds: curl http://YOUR_HOST/health → {"status":"ok"}
[ ] ML model artifacts are present: backend/artifacts/model.joblib
[ ] cars.db is present and contains seed data
[ ] docker-compose up --build runs without errors
[ ] Frontend loads at http://YOUR_HOST
[ ] Login/Register flow works
[ ] Prediction returns a price
[ ] Admin panel accessible for admin user
```

## Product Polish Checklist

```
[ ] Dashboard handles individual API failures gracefully
[ ] Listings mileage/power filters work server-side
[ ] Prediction error messages display correctly
[ ] "My Listings" tab for logged-in users
[ ] Analytics shows loading skeletons
[ ] Hard-coded sample counts replaced with model metadata values
```

## Future Scale Roadmap

```
[ ] Alembic for managed schema migrations
[ ] PostgreSQL when SQLite WAL becomes a bottleneck
[ ] Refresh token blacklist (Redis or DB table)
[ ] Structured logging / Sentry integration
[ ] Background retraining pipeline
[ ] Listing images (S3/R2 object storage)
[ ] E2E tests (Playwright)
[ ] CI/CD pipeline (GitHub Actions)
```

## Prioritized Implementation Order

| Priority | Task | Phase | Effort |
|----------|------|-------|--------|
| 1 | Fix VITE_API_URL for Docker | P1 | 15 min |
| 2 | Fix Prediction error display + model info | P1 | 15 min |
| 3 | Add mileage/power server-side filters | P1 | 30 min |
| 4 | JWT_SECRET production guard | P1 | 10 min |
| 5 | Production docker-compose.prod.yml | P1 | 15 min |
| 6 | Dashboard fault-tolerant API calls | P2 | 10 min |
| 7 | My Listings tab | P2 | 30 min |
| 8 | Analytics loading skeletons | P2 | 15 min |
| 9 | PostgreSQL migration docs | P3 | 20 min |
