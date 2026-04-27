from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from typing import Optional
from . import models, schemas


# ── CARS ─────────────────────────────────────────────────────────────────────

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
    owner_id: Optional[int] = None,
    sort_by: Optional[str] = None,
    sort_dir: str = "asc",
):
    q = db.query(models.Car).filter(models.Car.status == "active")
    if owner_id is not None:
        q = q.filter(models.Car.user_id == owner_id)
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


def get_car(db: Session, car_id: int):
    return db.query(models.Car).filter(models.Car.id == car_id).first()


def create_car(db: Session, car: schemas.CarCreate, user_id: Optional[int] = None):
    db_car = models.Car(**car.model_dump(), user_id=user_id)
    db.add(db_car)
    db.commit()
    db.refresh(db_car)
    return db_car


def update_car(db: Session, car_id: int, car_update: schemas.CarUpdate):
    db_car = get_car(db, car_id)
    if not db_car:
        return None
    for field, value in car_update.model_dump(exclude_unset=True).items():
        setattr(db_car, field, value)
    db.commit()
    db.refresh(db_car)
    return db_car


def delete_car(db: Session, car_id: int) -> bool:
    db_car = get_car(db, car_id)
    if not db_car:
        return False
    db.delete(db_car)
    db.commit()
    return True


def get_car_stats(db: Session) -> dict:
    active_filter = models.Car.status == "active"
    total = db.query(func.count(models.Car.id)).filter(active_filter).scalar() or 0
    avg_price = db.query(func.avg(models.Car.price)).filter(active_filter).scalar() or 0.0
    min_price = db.query(func.min(models.Car.price)).filter(active_filter).scalar() or 0.0
    max_price = db.query(func.max(models.Car.price)).filter(active_filter).scalar() or 0.0
    avg_mileage = db.query(func.avg(models.Car.mileage)).filter(active_filter).scalar() or 0.0
    total_makes = db.query(func.count(distinct(models.Car.make))).filter(active_filter).scalar() or 0
    return {
        "total_cars": total,
        "avg_price": round(float(avg_price), 2),
        "min_price": round(float(min_price), 2),
        "max_price": round(float(max_price), 2),
        "avg_mileage": round(float(avg_mileage), 2),
        "total_makes": total_makes,
    }


def get_recommendations(
    db: Session,
    make: str,
    model: str,
    year: int,
    mileage: Optional[float] = None,
    predicted_price: Optional[float] = None,
    fuel_type: Optional[str] = None,
    transmission: Optional[str] = None,
    limit: int = 5,
) -> list:
    if predicted_price is not None:
        price_score = func.abs(models.Car.price - predicted_price) / predicted_price
    else:
        price_score = 0

    score_expr = (
        price_score * 10
        + func.abs(models.Car.year - year) * 1.0
        + func.abs(func.coalesce(models.Car.mileage, 0) - (mileage or 0)) / 50000.0
    )

    base = [models.Car.status == "active", models.Car.make == make, models.Car.model == model]
    results: list = []

    def _fill(extra_filters):
        nonlocal results
        needed = limit - len(results)
        if needed <= 0:
            return
        seen = {c.id for c in results}
        excl = [models.Car.id.notin_(seen)] if seen else []
        batch = (
            db.query(models.Car)
            .filter(*base, *excl, *extra_filters)
            .order_by(score_expr.asc())
            .limit(needed)
            .all()
        )
        results += batch

    fuel_f = [models.Car.fuel_type == fuel_type] if fuel_type else []
    trans_f = [models.Car.transmission == transmission] if transmission else []
    yr = models.Car.year

    # Pass 1: exact year + fuel + transmission
    _fill([yr == year, *fuel_f, *trans_f])
    # Pass 2: exact year + fuel
    _fill([yr == year, *fuel_f])
    # Pass 3: exact year, any fuel/transmission
    _fill([yr == year])
    # Pass 4: ±1 year
    _fill([yr >= year - 1, yr <= year + 1])
    # Pass 5: ±2 years
    _fill([yr >= year - 2, yr <= year + 2])
    # Pass 6: ±3 years (last resort, always same make+model)
    _fill([yr >= year - 3, yr <= year + 3])

    return results[:limit]


# ── PREDICTIONS ──────────────────────────────────────────────────────────────

import json as _json

_PRED_FIELDS = {
    "make", "model", "year", "body_type", "mileage",
    "color", "fuel_type", "engine_capacity", "engine_power",
    "gearbox", "transmission", "pollution_standard",
}


def create_prediction_record(db: Session, input_data: dict, predicted_price: float, user_id: Optional[int] = None):
    filtered = {k: v for k, v in input_data.items() if k in _PRED_FIELDS}
    db_pred = models.Prediction(
        **filtered,
        predicted_price=round(predicted_price, 2),
        user_id=user_id,
        payload_json=_json.dumps(input_data),
    )
    db.add(db_pred)
    db.commit()
    db.refresh(db_pred)
    return db_pred


def get_predictions(db: Session, skip: int = 0, limit: int = 50, user_id: Optional[int] = None):
    q = db.query(models.Prediction)
    if user_id is not None:
        q = q.filter(models.Prediction.user_id == user_id)
    return q.order_by(models.Prediction.created_at.desc()).offset(skip).limit(limit).all()


def get_prediction(db: Session, prediction_id: int):
    return db.query(models.Prediction).filter(models.Prediction.id == prediction_id).first()


def delete_prediction(db: Session, prediction_id: int) -> bool:
    db_pred = get_prediction(db, prediction_id)
    if not db_pred:
        return False
    db.delete(db_pred)
    db.commit()
    return True


# ── REFERENCE DATA ────────────────────────────────────────────────────────────

def get_makes(db: Session):
    rows = db.query(distinct(models.Car.make)).filter(models.Car.status == "active").order_by(models.Car.make).all()
    return [r[0] for r in rows if r[0]]


def get_models_for_make(db: Session, make: str):
    rows = (
        db.query(distinct(models.Car.model))
        .filter(models.Car.make == make, models.Car.status == "active")
        .order_by(models.Car.model)
        .all()
    )
    return [r[0] for r in rows if r[0]]


def get_field_options(db: Session) -> dict:
    def vals(col):
        rows = db.query(distinct(col)).filter(models.Car.status == "active").order_by(col).all()
        return sorted([r[0] for r in rows if r[0]])

    return {
        "makes": vals(models.Car.make),
        "fuel_types": vals(models.Car.fuel_type),
        "body_types": vals(models.Car.body_type),
        "gearboxes": vals(models.Car.gearbox),
        "transmissions": vals(models.Car.transmission),
        "pollution_standards": vals(models.Car.pollution_standard),
        "colors": vals(models.Car.color),
    }


def get_model_options(db: Session, make: str, model: str) -> dict:
    """Return only the field values that exist for a specific make+model."""
    base = db.query(models.Car).filter(
        models.Car.make == make,
        models.Car.model == model,
        models.Car.status == "active",
    )

    def vals(col):
        rows = base.with_entities(distinct(col)).order_by(col).all()
        return sorted([r[0] for r in rows if r[0]])

    return {
        "body_types": vals(models.Car.body_type),
        "fuel_types": vals(models.Car.fuel_type),
        "gearboxes": vals(models.Car.gearbox),
        "transmissions": vals(models.Car.transmission),
        "pollution_standards": vals(models.Car.pollution_standard),
        "colors": vals(models.Car.color),
    }


# ── USERS ─────────────────────────────────────────────────────────────────────

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email.lower()).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(db: Session, email: str, password_hash: str, display_name: str,
                phone: Optional[str], role: str) -> models.User:
    user = models.User(
        email=email.lower(),
        password_hash=password_hash,
        display_name=display_name,
        phone=phone,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session, page: int, page_size: int, search: str):
    q = db.query(models.User)
    if search:
        term = f"%{search}%"
        q = q.filter(
            models.User.email.ilike(term) | models.User.display_name.ilike(term)
        )
    total = q.count()
    items = q.order_by(models.User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def update_user_admin(db: Session, user_id: int, role: Optional[str], is_active: Optional[bool]) -> Optional[models.User]:
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    if role is not None:
        user.role = role
    if is_active is not None:
        user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> bool:
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True
