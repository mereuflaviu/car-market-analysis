"""
Database synchronization: upsert new listings, update existing, detect stale/sold.
Keyed on source_url.
"""
import logging
from datetime import datetime, timedelta
from typing import Literal

import pandas as pd
from sqlalchemy.orm import Session

from app import models

logger = logging.getLogger("autoscope.pipeline.sync")

DAYS_MISSING_THRESHOLD = 3
SOLD_EXPIRY_MONTHS = 6


def sync_listings(
    cleaned_df: pd.DataFrame,
    mode: Literal["daily", "full_sweep"],
    db: Session,
    seen_urls: set[str] | None = None,
) -> dict:
    """
    Sync cleaned scraped data into the database.

    Returns summary dict with counts of operations performed.
    """
    summary = {
        "new": 0,
        "updated": 0,
        "price_changed": 0,
        "marked_sold": 0,
        "reactivated": 0,
        "deleted_expired": 0,
    }

    now = datetime.utcnow()

    if "url" not in cleaned_df.columns:
        logger.error("No 'url' column in cleaned data — cannot sync")
        return summary

    scraped_urls = set(cleaned_df["url"].dropna().unique())

    existing_cars = db.query(models.Car).filter(models.Car.source_url.isnot(None)).all()
    existing_by_url = {car.source_url: car for car in existing_cars}
    existing_urls = set(existing_by_url.keys())

    new_urls = scraped_urls - existing_urls
    found_urls = scraped_urls & existing_urls

    # INSERT new listings
    for _, row in cleaned_df[cleaned_df["url"].isin(new_urls)].iterrows():
        car = models.Car(
            make=str(row["make"]),
            model=str(row["model"]),
            year=int(row["year"]),
            body_type=row.get("body_type"),
            mileage=float(row["mileage"]) if pd.notna(row.get("mileage")) else None,
            door_count=int(row["door_count"]) if pd.notna(row.get("door_count")) else None,
            nr_seats=int(row["nr_seats"]) if pd.notna(row.get("nr_seats")) else None,
            color=row.get("color"),
            fuel_type=row.get("fuel_type"),
            engine_capacity=float(row["engine_capacity"]) if pd.notna(row.get("engine_capacity")) else None,
            engine_power=float(row["engine_power"]) if pd.notna(row.get("engine_power")) else None,
            gearbox=row.get("gearbox"),
            transmission=row.get("transmission"),
            pollution_standard=row.get("pollution_standard"),
            price=float(row["price"]),
            source_url=row["url"],
            status="active",
            days_missing=0,
            first_seen=now,
            last_seen=now,
        )
        db.add(car)
        summary["new"] += 1

    # UPDATE existing found listings
    for _, row in cleaned_df[cleaned_df["url"].isin(found_urls)].iterrows():
        car = existing_by_url[row["url"]]
        car.last_seen = now
        car.days_missing = 0

        new_price = float(row["price"])
        if car.price != new_price:
            price_history = models.PriceHistory(
                car_id=car.id,
                old_price=car.price,
                new_price=new_price,
                changed_at=now,
            )
            db.add(price_history)
            car.price = new_price
            summary["price_changed"] += 1

        if car.status == "sold":
            car.status = "active"
            car.sold_at = None
            summary["reactivated"] += 1

        summary["updated"] += 1

    # Stale detection (full sweep only)
    if mode == "full_sweep":
        # seen_urls = every URL the scraper encountered on search result pages (including
        # already-known ones). scraped_urls only has NEW listings, so using it here would
        # incorrectly mark every existing car as missing.
        stale_reference = seen_urls if seen_urls is not None else scraped_urls
        missing_urls = existing_urls - stale_reference
        for url in missing_urls:
            car = existing_by_url[url]
            if car.status == "sold":
                continue
            car.days_missing += 1
            if car.days_missing >= DAYS_MISSING_THRESHOLD:
                car.status = "sold"
                car.sold_at = now
                summary["marked_sold"] += 1

        expiry_date = now - timedelta(days=SOLD_EXPIRY_MONTHS * 30)
        expired = (
            db.query(models.Car)
            .filter(models.Car.status == "sold", models.Car.sold_at < expiry_date)
            .all()
        )
        for car in expired:
            db.delete(car)
            summary["deleted_expired"] += 1

    db.commit()
    logger.info("Sync complete: %s", summary)
    return summary
