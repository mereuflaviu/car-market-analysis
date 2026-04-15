from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from .. import schemas, crud, models
from ..dependencies import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=schemas.AdminUserListResponse)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query("", max_length=100),
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    items, total = crud.list_users(db, page=page, page_size=page_size, search=search)
    return schemas.AdminUserListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/users/{user_id}", response_model=schemas.UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/users/{user_id}", response_model=schemas.UserOut)
def update_user(
    user_id: int,
    payload: schemas.AdminUserUpdate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(require_admin),
):
    if user_id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot modify your own account via admin panel")
    if payload.role is not None and payload.role not in ("user", "admin"):
        raise HTTPException(status_code=422, detail="Role must be 'user' or 'admin'")
    user = crud.update_user_admin(db, user_id, role=payload.role, is_active=payload.is_active)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(require_admin),
):
    if user_id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    if not crud.delete_user(db, user_id):
        raise HTTPException(status_code=404, detail="User not found")
