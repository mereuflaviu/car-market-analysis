import os
import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

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
