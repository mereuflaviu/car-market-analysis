import os
from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError
from typing import Optional

from ..database import get_db
from .. import schemas, crud
from ..jwt_utils import create_access_token, create_refresh_token, decode_token
from ..dependencies import get_current_user

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
_IS_PROD = os.getenv("ENV", "development") == "production"
_FIRST_ADMIN = os.getenv("FIRST_ADMIN_EMAIL", "").strip().lower()

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookies(response: Response, user_id: int, role: str) -> None:
    kwargs = {"httponly": True, "samesite": "strict", "secure": _IS_PROD}
    response.set_cookie(
        "access_token", create_access_token(user_id, role),
        max_age=15 * 60, path="/", **kwargs,
    )
    response.set_cookie(
        "refresh_token", create_refresh_token(user_id),
        max_age=7 * 24 * 3600, path="/api/auth/refresh", **kwargs,
    )


@router.post("/register", response_model=schemas.UserOut, status_code=201)
def register(payload: schemas.RegisterIn, response: Response, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, payload.email):
        raise HTTPException(status_code=409, detail="Email already registered")
    role = "admin" if (_FIRST_ADMIN and payload.email.lower() == _FIRST_ADMIN) else "user"
    user = crud.create_user(
        db,
        email=payload.email,
        password_hash=_pwd.hash(payload.password),
        display_name=payload.display_name,
        phone=payload.phone,
        role=role,
    )
    _set_auth_cookies(response, user.id, user.role)
    return user


@router.post("/login", response_model=schemas.UserOut)
def login(payload: schemas.LoginIn, response: Response, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, payload.email)
    if not user or not _pwd.verify(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is banned")
    _set_auth_cookies(response, user.id, user.role)
    return user


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/api/auth/refresh")
    return {"message": "Logged out"}


@router.get("/me", response_model=schemas.UserOut)
def me(user=Depends(get_current_user)):
    return user


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
