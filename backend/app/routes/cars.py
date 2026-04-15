from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from .. import crud, schemas, models
from ..dependencies import get_current_user, get_optional_user
from ..limiter import limiter

router = APIRouter(prefix="/cars", tags=["cars"])


@router.get("/stats", response_model=schemas.StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    return crud.get_car_stats(db)


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
    mine: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_optional_user),
):
    owner_id = current_user.id if (mine and current_user) else None
    items, total = crud.get_cars(
        db, page=page, page_size=page_size,
        make=make, model=model,
        year_min=year_min, year_max=year_max,
        price_min=price_min, price_max=price_max,
        fuel_type=fuel_type, body_type=body_type,
        gearbox=gearbox, transmission=transmission,
        mileage_min=mileage_min, mileage_max=mileage_max,
        power_min=power_min, power_max=power_max,
        owner_id=owner_id,
        sort_by=sort_by, sort_dir=sort_dir or "asc",
    )
    return schemas.CarListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{car_id}", response_model=schemas.CarOut)
def get_car(car_id: int, db: Session = Depends(get_db)):
    car = crud.get_car(db, car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return car


@router.post("", response_model=schemas.CarOut, status_code=201)
@limiter.limit("30/minute")
def create_car(
    request: Request,
    car: schemas.CarCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.create_car(db, car, user_id=current_user.id)


@router.put("/{car_id}", response_model=schemas.CarOut)
@limiter.limit("30/minute")
def update_car(
    request: Request,
    car_id: int,
    car_update: schemas.CarUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    car = crud.get_car(db, car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    if current_user.role != "admin" and car.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own listings")
    updated = crud.update_car(db, car_id, car_update)
    return updated


@router.delete("/{car_id}", status_code=204)
@limiter.limit("30/minute")
def delete_car(
    request: Request,
    car_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    car = crud.get_car(db, car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    if current_user.role != "admin" and car.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own listings")
    crud.delete_car(db, car_id)
