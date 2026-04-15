import os
import hmac
from typing import Optional

from fastapi import Security, HTTPException, status, Cookie, Depends
from fastapi.security import APIKeyHeader
from jose import JWTError
from sqlalchemy.orm import Session

from .database import get_db
from .jwt_utils import decode_token
from . import models

# ── Legacy API key (kept for backwards compat during transition) ──────────────
_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(key: str = Security(_API_KEY_HEADER)) -> None:
    if os.getenv("ENV", "development") != "production":
        return
    expected = os.getenv("API_KEY", "")
    if not expected:
        raise HTTPException(status_code=500, detail="API_KEY is not configured on the server.")
    if not hmac.compare_digest(key or "", expected):
        raise HTTPException(status_code=403, detail="Invalid or missing API key.")


# ── JWT cookie auth ───────────────────────────────────────────────────────────

def get_current_user(
    access_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> models.User:
    """Read access_token cookie → return User or raise 401."""
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_token(access_token)
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is banned")
    return user


def get_optional_user(
    access_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> Optional[models.User]:
    """Like get_current_user but returns None instead of raising 401."""
    if not access_token:
        return None
    try:
        payload = decode_token(access_token)
        user_id = int(payload["sub"])
        user = db.query(models.User).filter(models.User.id == user_id).first()
        return user if (user and user.is_active) else None
    except Exception:
        return None


def require_admin(user: models.User = Depends(get_current_user)) -> models.User:
    """Require role == 'admin', else 403."""
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user
