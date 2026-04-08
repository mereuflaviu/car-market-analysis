from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from .. import crud, schemas

router = APIRouter(prefix="/cars", tags=["cars"])


@router.get("/stats", response_model=schemas.StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    """Aggregate statistics for the entire dataset."""
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
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = "asc",
    db: Session = Depends(get_db),
):
    """Paginated, filtered car listings."""
    items, total = crud.get_cars(
        db,
        page=page, page_size=page_size,
        make=make, model=model,
        year_min=year_min, year_max=year_max,
        price_min=price_min, price_max=price_max,
        fuel_type=fuel_type, body_type=body_type,
        gearbox=gearbox, transmission=transmission,
        sort_by=sort_by, sort_dir=sort_dir or "asc",
    )
    return schemas.CarListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{car_id}", response_model=schemas.CarOut)
def get_car(car_id: int, db: Session = Depends(get_db)):
    """Get a single car by ID."""
    car = crud.get_car(db, car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return car


@router.post("", response_model=schemas.CarOut, status_code=201)
def create_car(car: schemas.CarCreate, db: Session = Depends(get_db)):
    """Create a new car listing."""
    return crud.create_car(db, car)


@router.put("/{car_id}", response_model=schemas.CarOut)
def update_car(car_id: int, car_update: schemas.CarUpdate, db: Session = Depends(get_db)):
    """Update an existing car listing."""
    car = crud.update_car(db, car_id, car_update)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return car


@router.delete("/{car_id}", status_code=204)
def delete_car(car_id: int, db: Session = Depends(get_db)):
    """Delete a car listing."""
    if not crud.delete_car(db, car_id):
        raise HTTPException(status_code=404, detail="Car not found")
