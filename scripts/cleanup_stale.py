"""
Manually trigger cleanup of listings sold more than 6 months ago.

Usage:
    python scripts/cleanup_stale.py
    python scripts/cleanup_stale.py --dry-run
"""
import argparse
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

from app.database import SessionLocal
from app import models

SOLD_EXPIRY_MONTHS = 6


def main():
    parser = argparse.ArgumentParser(description="Cleanup expired sold listings")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")
    args = parser.parse_args()

    db = SessionLocal()
    expiry_date = datetime.utcnow() - timedelta(days=SOLD_EXPIRY_MONTHS * 30)

    expired = (
        db.query(models.Car)
        .filter(models.Car.status == "sold", models.Car.sold_at < expiry_date)
        .all()
    )

    print(f"Found {len(expired)} listings sold before {expiry_date.date()}")

    if args.dry_run:
        for car in expired[:10]:
            print(f"  Would delete: {car.make} {car.model} {car.year} (sold {car.sold_at.date()})")
        if len(expired) > 10:
            print(f"  ... and {len(expired) - 10} more")
    else:
        for car in expired:
            db.delete(car)
        db.commit()
        print(f"Deleted {len(expired)} expired listings.")

    db.close()


if __name__ == "__main__":
    main()
