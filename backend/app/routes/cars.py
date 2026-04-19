from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import re
import urllib.request
import asyncio
import logging

from ..database import get_db
from .. import crud, schemas, models
from ..dependencies import get_current_user, get_optional_user
from ..limiter import limiter
from ..ml import inference

logger = logging.getLogger("autoscope")

router = APIRouter(prefix="/cars", tags=["cars"])

# Simple in-memory cache: car_id → image_url (or None if unavailable)
_og_image_cache: dict[int, str | None] = {}

def _fetch_og_image(url: str) -> str | None:
    """Fetch the og:image URL from a listing page. Runs in a thread pool."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "ro-RO,ro;q=0.9,en;q=0.8",
            },
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            html = resp.read(64 * 1024).decode("utf-8", errors="ignore")
        match = re.search(
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](https?://[^"\']+)["\']',
            html,
            re.IGNORECASE,
        ) or re.search(
            r'<meta[^>]+content=["\'](https?://[^"\']+)["\'][^>]+property=["\']og:image["\']',
            html,
            re.IGNORECASE,
        )
        if match:
            return match.group(1)
    except Exception as exc:
        logger.debug("og:image fetch failed for %s: %s", url, exc)
    return None


@router.get("/stats", response_model=schemas.StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    return crud.get_car_stats(db)


@router.post("/deal-scores")
def deal_scores(
    car_ids: List[int],
    db: Session = Depends(get_db),
):
    """Batch-predict fair prices for given car IDs and return deal scores."""
    if not car_ids or len(car_ids) > 100:
        raise HTTPException(status_code=400, detail="Provide 1-100 car IDs")

    cars = db.query(models.Car).filter(models.Car.id.in_(car_ids)).all()
    if not cars:
        return {"scores": []}

    car_dicts = []
    for car in cars:
        car_dicts.append({
            "id": car.id,
            "make": car.make,
            "model": car.model,
            "year": car.year,
            "body_type": car.body_type,
            "mileage": car.mileage,
            "color": car.color,
            "fuel_type": car.fuel_type,
            "engine_capacity": car.engine_capacity,
            "engine_power": car.engine_power,
            "gearbox": car.gearbox,
            "transmission": car.transmission,
            "pollution_standard": car.pollution_standard,
            "price": car.price,
            "equipment_count": 0,
        })

    try:
        scores = inference.predict_batch(car_dicts)
        return {"scores": scores}
    except Exception as exc:
        logger.error("Deal score batch failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not compute deal scores")


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


@router.get("/{car_id}/og-image")
async def get_og_image(car_id: int, db: Session = Depends(get_db)):
    """Return a redirect to the listing's og:image (the car's actual photo)."""
    if car_id in _og_image_cache:
        image_url = _og_image_cache[car_id]
        if not image_url:
            raise HTTPException(status_code=404, detail="Preview not available")
        return RedirectResponse(url=image_url, status_code=302)

    car = db.query(models.Car).filter(models.Car.id == car_id).first()
    if not car or not car.source_url:
        _og_image_cache[car_id] = None
        raise HTTPException(status_code=404, detail="No source URL")

    image_url = await asyncio.to_thread(_fetch_og_image, car.source_url)
    _og_image_cache[car_id] = image_url

    if not image_url:
        raise HTTPException(status_code=404, detail="Preview not available")
    return RedirectResponse(url=image_url, status_code=302)


@router.get("/recommendations", response_model=List[schemas.CarOut])
def get_recommendations(
    make: str = Query(..., min_length=1),
    model: str = Query(..., min_length=1),
    year: int = Query(..., ge=1950, le=2030),
    mileage: float = Query(0.0, ge=0),
    predicted_price: float = Query(None, ge=0),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    return crud.get_recommendations(db, make=make, model=model, year=year, mileage=mileage, predicted_price=predicted_price, limit=limit)


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
