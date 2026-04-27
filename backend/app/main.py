import os
import logging
import traceback
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
)
logger = logging.getLogger("autoscope")

_IS_PROD = os.getenv("ENV", "development") == "production"
_INSECURE_JWT_DEFAULT = "dev-secret-change-in-production"

from .database import engine, SessionLocal
from . import models
from .limiter import limiter
from .routes import cars, predictions, analytics, makes, auth, admin

models.Base.metadata.create_all(bind=engine)

# ── Schema migrations for existing DBs (add new nullable columns if missing) ──
def _run_migrations():
    with engine.connect() as conn:
        car_cols = [r[1] for r in conn.execute(text("PRAGMA table_info(cars)")).fetchall()]
        if "user_id" not in car_cols:
            conn.execute(text("ALTER TABLE cars ADD COLUMN user_id INTEGER REFERENCES users(id)"))
            logger.info("Migration: added cars.user_id")

        pred_cols = [r[1] for r in conn.execute(text("PRAGMA table_info(predictions)")).fetchall()]
        if "user_id" not in pred_cols:
            conn.execute(text("ALTER TABLE predictions ADD COLUMN user_id INTEGER REFERENCES users(id)"))
            logger.info("Migration: added predictions.user_id")

        if "source_url" not in car_cols:
            conn.execute(text("ALTER TABLE cars ADD COLUMN source_url TEXT"))
            logger.info("Migration: added cars.source_url")

        if "status" not in car_cols:
            conn.execute(text("ALTER TABLE cars ADD COLUMN status TEXT NOT NULL DEFAULT 'active'"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cars_status ON cars(status)"))
            logger.info("Migration: added cars.status")

        if "days_missing" not in car_cols:
            conn.execute(text("ALTER TABLE cars ADD COLUMN days_missing INTEGER NOT NULL DEFAULT 0"))
            logger.info("Migration: added cars.days_missing")

        if "first_seen" not in car_cols:
            conn.execute(text("ALTER TABLE cars ADD COLUMN first_seen TIMESTAMP"))
            conn.execute(text("UPDATE cars SET first_seen = created_at WHERE first_seen IS NULL"))
            logger.info("Migration: added cars.first_seen")

        if "last_seen" not in car_cols:
            conn.execute(text("ALTER TABLE cars ADD COLUMN last_seen TIMESTAMP"))
            conn.execute(text("UPDATE cars SET last_seen = updated_at WHERE last_seen IS NULL"))
            logger.info("Migration: added cars.last_seen")

        if "sold_at" not in car_cols:
            conn.execute(text("ALTER TABLE cars ADD COLUMN sold_at TIMESTAMP"))
            logger.info("Migration: added cars.sold_at")

        conn.commit()

_run_migrations()

_raw_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://localhost:4173",
)
CORS_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

_MAX_BODY = 1 * 1024 * 1024


class LimitBodySizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > _MAX_BODY:
            return JSONResponse(status_code=413, content={"detail": "Request body too large."})
        return await call_next(request)


app = FastAPI(
    title="AutoScope API",
    version="1.0.0",
    docs_url=None if _IS_PROD else "/docs",
    redoc_url=None if _IS_PROD else "/redoc",
    openapi_url=None if _IS_PROD else "/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(LimitBodySizeMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,          # required for cookies
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(cars.router, prefix="/api")
app.include_router(predictions.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(makes.router, prefix="/api")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on %s %s: %s\n%s",
                 request.method, request.url.path, exc, traceback.format_exc())
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


_scheduler = BackgroundScheduler(timezone="Europe/Bucharest")
_full_sweep_interval = int(os.getenv("PIPELINE_FULL_SWEEP_DAYS", "3"))


def _run_daily():
    """Scheduled daily pipeline: scrape new listings, sync DB, retrain if new data."""
    # Every Nth day run a full sweep instead of daily
    today = datetime.now().timetuple().tm_yday  # day-of-year 1..365
    mode = "full_sweep" if today % _full_sweep_interval == 0 else "daily"
    logger.info("Scheduled pipeline starting (mode=%s)", mode)
    try:
        from .pipeline.run import run_pipeline
        report = run_pipeline(mode)
        logger.info("Scheduled pipeline finished: status=%s new=%s retrained=%s",
                    report["status"],
                    report.get("steps", {}).get("sync", {}).get("new", "?"),
                    report.get("steps", {}).get("retrain", {}).get("retrained", False))
    except Exception as exc:
        logger.error("Scheduled pipeline crashed: %s", exc, exc_info=True)


@app.on_event("startup")
def validate_config():
    if _IS_PROD:
        if not os.getenv("API_KEY"):
            logger.warning("API_KEY not set in production — mutation endpoints unprotected")
        jwt_secret = os.getenv("JWT_SECRET", "")
        if not jwt_secret or jwt_secret == _INSECURE_JWT_DEFAULT:
            logger.critical(
                "FATAL: JWT_SECRET is not set or uses the insecure default. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
            raise RuntimeError("JWT_SECRET must be set to a strong random value in production")
    logger.info("AutoScope API starting — env=%s", "production" if _IS_PROD else "development")


@app.on_event("startup")
def start_scheduler():
    if os.getenv("DISABLE_SCHEDULER", "").lower() in ("1", "true", "yes"):
        logger.info("Pipeline scheduler disabled via DISABLE_SCHEDULER env var")
        return
    _scheduler.add_job(
        _run_daily,
        CronTrigger(hour=3, minute=0, timezone="Europe/Bucharest"),
        id="pipeline_daily",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(
        "Pipeline scheduler started — daily at 03:00 Bucharest, "
        "full sweep every %d days", _full_sweep_interval
    )


@app.on_event("shutdown")
def stop_scheduler():
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Pipeline scheduler stopped")


@app.get("/")
def root():
    return {"message": "AutoScope API", "version": "1.0.0"}


@app.get("/health")
def health():
    issues = []
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("Health check — DB unreachable: %s", exc)
        issues.append("database_unreachable")
    from .ml import inference
    if not inference.is_ready():
        issues.append("model_not_trained")
    if issues:
        return JSONResponse(status_code=503, content={"status": "degraded", "issues": issues})
    return {"status": "ok"}
