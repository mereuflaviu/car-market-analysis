"""
Force model retraining from current database data.

Usage:
    python scripts/retrain_model.py
    python scripts/retrain_model.py --force
"""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

from app.database import SessionLocal
from app.pipeline.retrain import maybe_retrain


def main():
    parser = argparse.ArgumentParser(description="Retrain the AutoScope ML model")
    parser.add_argument("--force", action="store_true", help="Retrain even if no new data")
    args = parser.parse_args()

    db = SessionLocal()
    print("Checking for retraining...")
    result = maybe_retrain(db, force=args.force)
    db.close()

    print(json.dumps(result, indent=2, default=str))

    if result.get("retrained") and result.get("swapped"):
        print("Model successfully retrained and deployed.")
    elif result.get("retrained") and not result.get("swapped"):
        print("Model retrained but not swapped (current model is better).")
    else:
        print(f"No retraining: {result.get('reason', 'unknown')}")


if __name__ == "__main__":
    main()
