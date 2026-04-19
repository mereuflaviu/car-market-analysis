"""
Lazy-loading inference module.
Compatible with artifacts from train_extended.py (log-price, target encoding, engineered features).
"""
import os
import threading
import logging
import numpy as np
import joblib
import pandas as pd
from app.ml.encoders import SmoothedTargetEncoder  # noqa: F401 — needed for joblib deserialisation
from app.ml.train_extended import EQUIPMENT_VALUE

logger = logging.getLogger("autoscope.inference")

_HERE = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS_DIR = os.path.join(_HERE, "..", "..", "artifacts")

_model        = None
_ord_enc      = None
_te_enc       = None
_metadata     = None
_cohort_stats = None
_lock         = threading.Lock()


def _load():
    global _model, _ord_enc, _te_enc, _metadata, _cohort_stats
    model_path = os.path.join(ARTIFACTS_DIR, "model.joblib")
    if not os.path.exists(model_path):
        raise FileNotFoundError("ML model artifacts not found. Train the model first.")
    logger.info("Loading ML model artifacts from %s", ARTIFACTS_DIR)
    _model    = joblib.load(model_path)
    _ord_enc  = joblib.load(os.path.join(ARTIFACTS_DIR, "encoder.joblib"))
    _metadata = joblib.load(os.path.join(ARTIFACTS_DIR, "metadata.joblib"))

    te_path = os.path.join(ARTIFACTS_DIR, "te_encoder.joblib")
    _te_enc = joblib.load(te_path) if os.path.exists(te_path) else None
    logger.info("ML model loaded (R²=%.4f)", _metadata.get("r2", 0))

    global _cohort_stats
    cs_path = os.path.join(ARTIFACTS_DIR, "cohort_stats.joblib")
    _cohort_stats = joblib.load(cs_path) if os.path.exists(cs_path) else None
    if _cohort_stats:
        logger.info("Cohort stats loaded (%d cohorts)", len(_cohort_stats.get("cohort_size", {})))


def _ensure_loaded():
    if _model is None:
        with _lock:
            if _model is None:  # double-checked locking
                _load()


def is_ready() -> bool:
    return os.path.exists(os.path.join(ARTIFACTS_DIR, "model.joblib"))


_LUXURY_BRANDS = {
    "Porsche", "BMW", "Mercedes-Benz", "Audi", "Lexus", "Jaguar",
    "Land Rover", "Maserati", "Bentley", "Ferrari", "Lamborghini",
    "Rolls-Royce", "Aston Martin", "McLaren", "Genesis",
}
_BUDGET_BRANDS = {
    "Dacia", "Fiat", "Seat", "Chevrolet", "Daewoo", "Lada",
    "Mitsubishi", "Suzuki", "Kia", "Hyundai",
}


def _add_engineered(row: dict) -> dict:
    """Derive all engineered features from raw inputs."""
    make  = row.get("make", "")
    year  = int(row.get("year") or 2010)
    ep    = float(row.get("engine_power", 0) or 0)
    ec    = float(row.get("engine_capacity", 1000) or 1000)
    eq    = float(row.get("equipment_count", 0) or 0)
    gearbox = row.get("gearbox", "")

    car_age = 2026 - year
    row["car_age"]      = car_age
    row["log_car_age"]  = float(np.log1p(car_age))
    row["power_per_liter"] = ep / max(ec / 1000, 0.1)
    row["power_over_age"]  = ep / (car_age + 1)
    row["power_auto"]      = ep * (1.0 if gearbox == "Automata" else 0.0)
    row["equip_per_age"]   = eq / (car_age + 1)

    fuel = str(row.get("fuel_type", "")).lower()
    row["is_electric"]      = int("electric" in fuel)
    row["is_hybrid_plugin"] = int("plug" in fuel)
    row["is_hybrid"]        = int("hibrid" in fuel and "plug" not in fuel)

    row["brand_tier"] = (
        "luxury"     if make in _LUXURY_BRANDS
        else "budget" if make in _BUDGET_BRANDS
        else "mainstream"
    )

    # Cohort key — will be target-encoded from training map
    model = row.get("model", "unknown")
    row["cohort"] = f"{make}|{model}|{year}"

    # ── Equipment value (EUR) ────────────────────────────────────────────
    equip_total = sum(
        EQUIPMENT_VALUE.get(k, 0)
        for k, v in row.items()
        if k in EQUIPMENT_VALUE and v in (1, True, "1", "true", "True")
    )
    # Cap at training max to prevent extrapolation
    max_equip_val = _metadata.get("max_equipment_value_eur", 15000) if _metadata else 15000
    row["equipment_value_eur"] = min(equip_total, max_equip_val)

    # ── Power segment ────────────────────────────────────────────────────
    if ep <= 120:
        row["power_segment"] = "economy"
    elif ep <= 180:
        row["power_segment"] = "mid"
    elif ep <= 250:
        row["power_segment"] = "strong"
    elif ep <= 350:
        row["power_segment"] = "performance"
    else:
        row["power_segment"] = "super"

    # ── Mileage per year ─────────────────────────────────────────────────
    mileage = float(row.get("mileage", 0) or 0)
    row["mileage_per_year"] = mileage / (car_age + 1)

    # ── Value density ────────────────────────────────────────────────────
    row["value_density"] = row["equipment_value_eur"] / (car_age + 1)

    # ── Cohort statistics (from training data, no leakage) ───────────────
    cohort_key = row["cohort"]
    make_model_key = (make, model) if isinstance(make, str) else (str(make), str(model))

    if _cohort_stats:
        row["cohort_size"] = _cohort_stats["cohort_size"].get(cohort_key, 1)

        cohort_mean_m = _cohort_stats["cohort_mean_mileage"].get(cohort_key)
        cohort_std_m = _cohort_stats["cohort_std_mileage"].get(cohort_key, 1)
        if cohort_mean_m is not None:
            row["mileage_vs_cohort"] = (mileage - cohort_mean_m) / max(cohort_std_m, 1)
        else:
            row["mileage_vs_cohort"] = 0.0

        mm_mean = _cohort_stats["make_model_mean_mileage"].get(make_model_key)
        if mm_mean is not None:
            row["mileage_vs_make_model"] = mileage - mm_mean
        else:
            row["mileage_vs_make_model"] = 0.0
    else:
        row["cohort_size"] = 1
        row["mileage_vs_cohort"] = 0.0
        row["mileage_vs_make_model"] = 0.0

    return row


def predict(input_data: dict) -> dict:
    _ensure_loaded()

    row = dict(input_data)
    row = _add_engineered(row)

    all_feats  = _metadata["all_features"]
    cat_feats  = _metadata["categorical_features"]
    bin_feats  = _metadata.get("binary_features", [])
    num_feats  = _metadata["numerical_features"]
    tenc_feats = _metadata.get("target_enc_features", [])
    log_target = _metadata.get("log_target", False)

    # Build feature row — missing equipment flags default to 0
    feat_row = {}
    for col in all_feats:
        val = row.get(col)
        if val is not None:
            feat_row[col] = val
        elif col in bin_feats:
            feat_row[col] = 0
        else:
            feat_row[col] = None

    X = pd.DataFrame([feat_row])[all_feats]

    # Ordinal encode categoricals
    if cat_feats:
        X[cat_feats] = _ord_enc.transform(X[cat_feats])

    # Smoothed target encode make/model
    if tenc_feats and _te_enc is not None:
        X = _te_enc.transform(X, tenc_feats)

    # Numeric coercion
    for col in num_feats + bin_feats:
        if col in X.columns:
            X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0)

    raw = float(_model.predict(X)[0])
    predicted = float(np.exp(raw)) if log_target else raw
    predicted = max(0.0, round(predicted, 2))

    return {
        "predicted_price": predicted,
        "r2":        _metadata.get("r2"),
        "mae":       _metadata.get("mae"),
        "rmse":      _metadata.get("rmse"),
        "cv_r2":     _metadata.get("cv_r2"),
        "experiment": _metadata.get("experiment", "unknown"),
    }


def predict_batch(cars: list[dict]) -> list[dict]:
    """Run inference on multiple cars and return deal scores.

    Each car dict must have: make, model, year, and ideally mileage,
    engine_power, engine_capacity, fuel_type, gearbox, transmission,
    body_type, pollution_standard, color.  equipment_count defaults to 0.

    Returns a list of {car_id, predicted_price, deal_pct, deal_label}.
    """
    _ensure_loaded()
    log_target = _metadata.get("log_target", False)
    all_feats  = _metadata["all_features"]
    cat_feats  = _metadata["categorical_features"]
    bin_feats  = _metadata.get("binary_features", [])
    num_feats  = _metadata["numerical_features"]
    tenc_feats = _metadata.get("target_enc_features", [])

    rows = []
    car_ids = []
    actual_prices = []
    for car in cars:
        row = dict(car)
        row.setdefault("equipment_count", 0)
        row = _add_engineered(row)
        rows.append(row)
        car_ids.append(car["id"])
        actual_prices.append(float(car["price"]))

    # Build DataFrame for all cars at once
    feat_rows = []
    for row in rows:
        feat_row = {}
        for col in all_feats:
            val = row.get(col)
            if val is not None:
                feat_row[col] = val
            elif col in bin_feats:
                feat_row[col] = 0
            else:
                feat_row[col] = None
        feat_rows.append(feat_row)

    X = pd.DataFrame(feat_rows)[all_feats]

    if cat_feats:
        X[cat_feats] = _ord_enc.transform(X[cat_feats])
    if tenc_feats and _te_enc is not None:
        X = _te_enc.transform(X, tenc_feats)
    for col in num_feats + bin_feats:
        if col in X.columns:
            X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0)

    raw_preds = _model.predict(X)

    results = []
    for i, raw in enumerate(raw_preds):
        predicted = float(np.exp(raw)) if log_target else float(raw)
        predicted = max(0.0, round(predicted, 2))
        actual = actual_prices[i]

        if predicted > 0:
            deal_pct = round((actual - predicted) / predicted * 100, 1)
        else:
            deal_pct = 0.0

        if deal_pct <= -15:
            deal_label = "Great Deal"
        elif deal_pct <= -5:
            deal_label = "Good Deal"
        elif deal_pct <= 5:
            deal_label = "Fair Price"
        elif deal_pct <= 15:
            deal_label = "Above Market"
        else:
            deal_label = "Overpriced"

        results.append({
            "car_id": car_ids[i],
            "predicted_price": predicted,
            "deal_pct": deal_pct,
            "deal_label": deal_label,
        })

    return results


def get_feature_importance(top_n: int = 15) -> list[dict]:
    _ensure_loaded()
    fi = _metadata.get("feature_importance", {})
    if not fi:
        return []
    sorted_fi = sorted(fi.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [{"feature": k, "importance": round(v, 6)} for k, v in sorted_fi]


def get_model_info() -> dict:
    if not is_ready():
        return {"status": "not_trained"}
    _ensure_loaded()
    return {
        "status":      "ready",
        "experiment":  _metadata.get("experiment", "unknown"),
        "dataset":     _metadata.get("dataset", "unknown"),
        "log_target":  _metadata.get("log_target", False),
        "r2":          _metadata.get("r2"),
        "mae":         _metadata.get("mae"),
        "rmse":        _metadata.get("rmse"),
        "cv_r2":       _metadata.get("cv_r2"),
        "n_features":    len(_metadata.get("all_features", [])),
        "features":      _metadata.get("all_features", []),
        "top_features":  get_feature_importance(top_n=10),
        "train_samples": _metadata.get("train_samples"),
        "test_samples":  _metadata.get("test_samples"),
    }
