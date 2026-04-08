"""
Lazy-loading inference module.
Loads artifacts from backend/artifacts/ on first call to predict().
"""
import os
import joblib
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS_DIR = os.path.join(_HERE, "..", "..", "artifacts")

_model = None
_encoder = None
_metadata = None


def _load():
    global _model, _encoder, _metadata
    model_path = os.path.join(ARTIFACTS_DIR, "model.joblib")
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model not found at {model_path}. "
            "Run: cd backend && python app/ml/train.py"
        )
    _model = joblib.load(model_path)
    _encoder = joblib.load(os.path.join(ARTIFACTS_DIR, "encoder.joblib"))
    _metadata = joblib.load(os.path.join(ARTIFACTS_DIR, "metadata.joblib"))


def is_ready() -> bool:
    return os.path.exists(os.path.join(ARTIFACTS_DIR, "model.joblib"))


def predict(input_data: dict) -> dict:
    if _model is None:
        _load()

    cat_feats = _metadata["categorical_features"]
    all_feats = _metadata["all_features"]

    X = pd.DataFrame([input_data])[all_feats]
    X[cat_feats] = _encoder.transform(X[cat_feats])

    raw = float(_model.predict(X)[0])
    return {
        "predicted_price": max(0.0, round(raw, 2)),
        "r2": _metadata.get("r2"),
        "mae": _metadata.get("mae"),
    }


def get_model_info() -> dict:
    if not is_ready():
        return {"status": "not_trained"}
    if _metadata is None:
        _load()
    return {
        "status": "ready",
        "r2": _metadata.get("r2"),
        "mae": _metadata.get("mae"),
        "rmse": _metadata.get("rmse"),
        "features": _metadata.get("all_features", []),
    }
