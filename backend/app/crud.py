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
    sort_by: Optional[str] = None,
    sort_dir: str = "asc",
):
    q = db.query(models.Car)
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

    if sort_by:
        col = getattr(models.Car, sort_by, None)
        if col is not None:
            q = q.order_by(col.desc() if sort_dir == "desc" else col.asc())
    else:
        q = q.order_by(models.Car.id.asc())

    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def get_car(db: Session, car_id: int):
    return db.query(models.Car).filter(models.Car.id == car_id).first()


def create_car(db: Session, car: schemas.CarCreate):
    db_car = models.Car(**car.model_dump())
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
    total = db.query(func.count(models.Car.id)).scalar() or 0
    avg_price = db.query(func.avg(models.Car.price)).scalar() or 0.0
    min_price = db.query(func.min(models.Car.price)).scalar() or 0.0
    max_price = db.query(func.max(models.Car.price)).scalar() or 0.0
    avg_mileage = db.query(func.avg(models.Car.mileage)).scalar() or 0.0
    total_makes = db.query(func.count(distinct(models.Car.make))).scalar() or 0
    return {
        "total_cars": total,
        "avg_price": round(float(avg_price), 2),
        "min_price": round(float(min_price), 2),
        "max_price": round(float(max_price), 2),
        "avg_mileage": round(float(avg_mileage), 2),
        "total_makes": total_makes,
    }


# ── PREDICTIONS ──────────────────────────────────────────────────────────────

_PRED_FIELDS = {
    "make", "model", "year", "body_type", "mileage",
    "color", "fuel_type", "engine_capacity", "engine_power",
    "gearbox", "transmission", "pollution_standard",
}


def create_prediction_record(db: Session, input_data: dict, predicted_price: float):
    filtered = {k: v for k, v in input_data.items() if k in _PRED_FIELDS}
    db_pred = models.Prediction(**filtered, predicted_price=round(predicted_price, 2))
    db.add(db_pred)
    db.commit()
    db.refresh(db_pred)
    return db_pred


def get_predictions(db: Session, skip: int = 0, limit: int = 50):
    return (
        db.query(models.Prediction)
        .order_by(models.Prediction.created_at.desc())
        .offset(skip).limit(limit).all()
    )


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
    rows = db.query(distinct(models.Car.make)).order_by(models.Car.make).all()
    return [r[0] for r in rows if r[0]]


def get_models_for_make(db: Session, make: str):
    rows = (
        db.query(distinct(models.Car.model))
        .filter(models.Car.make == make)
        .order_by(models.Car.model)
        .all()
    )
    return [r[0] for r in rows if r[0]]


def get_field_options(db: Session) -> dict:
    def vals(col):
        rows = db.query(distinct(col)).order_by(col).all()
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
