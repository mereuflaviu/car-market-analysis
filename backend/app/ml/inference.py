"""
Lazy-loading inference module.
Compatible with artifacts from train_extended.py (log-price, target encoding, engineered features).
"""
import os
import numpy as np
import joblib
import pandas as pd
from app.ml.encoders import SmoothedTargetEncoder  # noqa: F401 — needed for joblib deserialisation

_HERE = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS_DIR = os.path.join(_HERE, "..", "..", "artifacts")

_model      = None
_ord_enc    = None
_te_enc     = None
_metadata   = None


def _load():
    global _model, _ord_enc, _te_enc, _metadata
    model_path = os.path.join(ARTIFACTS_DIR, "model.joblib")
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model not found at {model_path}. "
            "Run: python backend/app/ml/train_extended.py"
        )
    _model    = joblib.load(model_path)
    _ord_enc  = joblib.load(os.path.join(ARTIFACTS_DIR, "encoder.joblib"))
    _metadata = joblib.load(os.path.join(ARTIFACTS_DIR, "metadata.joblib"))

    te_path = os.path.join(ARTIFACTS_DIR, "te_encoder.joblib")
    _te_enc = joblib.load(te_path) if os.path.exists(te_path) else None


def _ensure_loaded():
    if _model is None:
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
        "n_features":  len(_metadata.get("all_features", [])),
        "features":    _metadata.get("all_features", []),
        "top_features": get_feature_importance(top_n=10),
    }
