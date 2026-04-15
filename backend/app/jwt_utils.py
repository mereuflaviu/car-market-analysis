import os
from datetime import datetime, timedelta
from jose import JWTError, jwt

_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
_ALGORITHM = "HS256"
_ACCESS_MINUTES = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES", "15"))
_REFRESH_DAYS = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))


def create_access_token(user_id: int, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=_ACCESS_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "role": role, "exp": expire},
        _SECRET, algorithm=_ALGORITHM,
    )


def create_refresh_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(days=_REFRESH_DAYS)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire},
        _SECRET, algorithm=_ALGORITHM,
    )


def decode_token(token: str) -> dict:
    """Raises jose.JWTError on invalid/expired token."""
    return jwt.decode(token, _SECRET, algorithms=[_ALGORITHM])
