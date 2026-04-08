"""
Seed the SQLite database from cleaned_car_listings.csv.

Usage (from backend/):
    python seed.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from app.database import SessionLocal, engine
from app import models

CSV_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "model", "data", "cleaned_car_listings.csv",
)


def seed():
    print("Creating database tables ...")
    models.Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    existing = db.query(models.Car).count()
    if existing > 0:
        print(f"Database already has {existing} cars — skipping seed.")
        db.close()
        return

    csv_path = os.path.abspath(CSV_PATH)
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV not found at {csv_path}")
        sys.exit(1)

    print(f"Loading {csv_path} ...")
    df = pd.read_csv(csv_path)
    print(f"  {len(df)} rows loaded")

    # Replace NaN with None so SQLAlchemy stores NULL
    df = df.where(pd.notna(df), None)

    cars, skipped = [], 0
    for _, row in df.iterrows():
        if not row.get("make") or not row.get("model"):
            skipped += 1
            continue
        if row.get("year") is None or row.get("price") is None:
            skipped += 1
            continue
        try:
            cars.append(
                models.Car(
                    make=str(row["make"]),
                    model=str(row["model"]),
                    year=int(row["year"]),
                    body_type=row.get("body_type"),
                    mileage=float(row["mileage"]) if row.get("mileage") is not None else None,
                    door_count=int(row["door_count"]) if row.get("door_count") is not None else None,
                    nr_seats=int(row["nr_seats"]) if row.get("nr_seats") is not None else None,
                    color=row.get("color"),
                    fuel_type=row.get("fuel_type"),
                    engine_capacity=float(row["engine_capacity"]) if row.get("engine_capacity") is not None else None,
                    engine_power=float(row["engine_power"]) if row.get("engine_power") is not None else None,
                    gearbox=row.get("gearbox"),
                    transmission=row.get("transmission"),
                    pollution_standard=row.get("pollution_standard"),
                    price=float(row["price"]),
                )
            )
        except Exception:
            skipped += 1

    print(f"  Inserting {len(cars)} cars (skipped {skipped}) ...")
    db.bulk_save_objects(cars)
    db.commit()
    db.close()
    print(f"Done! {len(cars)} cars seeded into the database.")


if __name__ == "__main__":
    seed()
