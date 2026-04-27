"""
Conditional model retraining.
Only retrains if new data exists since the last training run.
Compares metrics before swapping artifacts.
"""
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

import joblib
from sqlalchemy.orm import Session

from app import models

logger = logging.getLogger("autoscope.pipeline.retrain")

_HERE = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS_DIR = os.path.join(_HERE, "..", "..", "artifacts")
SOLD_EXPIRY_MONTHS = 6

# Cleaned CSV has all features (equipment flags + equipment_count).
# DB only stores basic car fields — not sufficient for training.
_SCRAPER_DIR = Path(os.getenv(
    "SCRAPER_DIR",
    str(Path(__file__).resolve().parent.parent.parent.parent / "model" / "extraction"),
))
_CLEANED_CSV = _SCRAPER_DIR.parent / "data" / "cleaned_car_listings_extended.csv"


def _get_db_count(db: Session) -> int:
    """Count cars eligible for training: active + sold within 6 months."""
    expiry = datetime.utcnow() - timedelta(days=SOLD_EXPIRY_MONTHS * 30)
    return (
        db.query(models.Car)
        .filter(
            (models.Car.status == "active") |
            ((models.Car.status == "sold") & (models.Car.sold_at > expiry))
        )
        .count()
    )


def _get_last_training_count() -> int | None:
    """Read the training sample count stored in the last metadata artifact."""
    meta_path = os.path.join(ARTIFACTS_DIR, "metadata.joblib")
    if not os.path.exists(meta_path):
        return None
    meta = joblib.load(meta_path)
    return meta.get("training_dataset_size")


def maybe_retrain(db: Session, force: bool = False) -> dict:
    """
    Retrain the model if new data is available.

    Uses the cleaned CSV as training data (it has all features including equipment flags).
    The DB count is used only to decide whether retraining is needed.

    Returns a report dict describing what happened.
    """
    import sys
    sys.path.insert(0, os.path.join(_HERE, "..", ".."))
    from app.ml.train_extended import load_and_engineer, run_experiment, save_artifacts

    if not _CLEANED_CSV.exists():
        return {"retrained": False, "reason": "cleaned_csv_not_found", "path": str(_CLEANED_CSV)}

    current_count = _get_db_count(db)
    if current_count == 0:
        return {"retrained": False, "reason": "no_training_data"}

    last_count = _get_last_training_count()
    if not force and last_count is not None and current_count <= last_count:
        return {"retrained": False, "reason": "no_new_data", "dataset_size": current_count}

    logger.info("Retraining model: %d DB rows (previous: %s), CSV: %s", current_count, last_count, _CLEANED_CSV)

    old_metrics = {"r2": 0, "mae": float("inf")}
    meta_path = os.path.join(ARTIFACTS_DIR, "metadata.joblib")
    if os.path.exists(meta_path):
        old_meta = joblib.load(meta_path)
        old_metrics = {"r2": old_meta.get("r2", 0), "mae": old_meta.get("mae", float("inf"))}

    engineered_df = load_and_engineer(str(_CLEANED_CSV))
    result = run_experiment("target_enc", engineered_df, do_tune=False)
    new_metrics = result["metrics"]

    # Swap if new model is not significantly worse (allow 0.01 R² drop if MAE improved)
    r2_ok = new_metrics["r2"] >= old_metrics["r2"] - 0.01
    mae_ok = new_metrics["mae"] <= old_metrics["mae"] * 1.05
    should_swap = r2_ok or mae_ok

    if should_swap:
        result["metrics"]["training_dataset_size"] = current_count
        save_artifacts(result)
        from app.ml import inference
        inference._model = None  # force lazy reload on next predict
        logger.info(
            "Model swapped: R²=%.4f→%.4f, MAE=%.0f→%.0f",
            old_metrics["r2"], new_metrics["r2"],
            old_metrics["mae"], new_metrics["mae"],
        )
    else:
        logger.info(
            "New model not better, keeping current. R²=%.4f vs %.4f",
            new_metrics["r2"], old_metrics["r2"],
        )

    return {
        "retrained": True,
        "swapped": should_swap,
        "dataset_size": current_count,
        "old_r2": old_metrics["r2"],
        "new_r2": new_metrics["r2"],
        "old_mae": old_metrics["mae"],
        "new_mae": new_metrics["mae"],
    }
