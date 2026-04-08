"""
Train XGBoost price predictor from model/data/dataset.csv.
Replicates preprocessing from model/analysis/01-prediction.ipynb.

Usage (from backend/):
    python app/ml/train.py
"""
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder
import xgboost as xgb
import joblib

# ── Paths ──────────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(_HERE, "..", "..", "..", "model", "data", "dataset.csv")
ARTIFACTS_DIR = os.path.join(_HERE, "..", "..", "artifacts")

# ── Feature config (mirrors the notebook) ─────────────────────────────────────
CATEGORICAL_FEATURES = [
    "make", "model", "body_type", "color",
    "fuel_type", "gearbox", "transmission", "pollution_standard",
]
NUMERICAL_FEATURES = ["year", "mileage", "engine_capacity", "engine_power"]
ALL_FEATURES = NUMERICAL_FEATURES + CATEGORICAL_FEATURES
TARGET = "price"

# Best hyperparameters from GridSearchCV in the notebook
XGBOOST_PARAMS = dict(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.1,
    subsample=0.9,
    colsample_bytree=0.8,
    min_child_weight=5,
    random_state=42,
    verbosity=0,
)


def train_and_save():
    data_path = os.path.abspath(DATA_PATH)
    if not os.path.exists(data_path):
        print(f"ERROR: Dataset not found at {data_path}")
        sys.exit(1)

    print(f"Loading dataset from {data_path} ...")
    df = pd.read_csv(data_path, index_col=0)
    print(f"  Loaded {len(df)} rows, {len(df.columns)} columns")

    df = df.dropna(subset=ALL_FEATURES + [TARGET])
    print(f"  After dropping NaN: {len(df)} rows")

    X = df[ALL_FEATURES].copy()
    y = df[TARGET].copy()

    # Encode categorical features exactly as in the notebook
    encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    X[CATEGORICAL_FEATURES] = encoder.fit_transform(X[CATEGORICAL_FEATURES])

    # Stratified train/test split (matching notebook: 80/20 by price bins)
    price_bins = pd.qcut(y, q=10, labels=False, duplicates="drop")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=price_bins
    )
    print(f"  Train: {len(X_train)}  |  Test: {len(X_test)}")

    print("Training XGBoost ...")
    model = xgb.XGBRegressor(**XGBOOST_PARAMS)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))

    print(f"\nModel performance on test set:")
    print(f"  R² Score : {r2:.4f}")
    print(f"  MAE      : €{mae:,.2f}")
    print(f"  RMSE     : €{rmse:,.2f}")

    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    joblib.dump(model, os.path.join(ARTIFACTS_DIR, "model.joblib"))
    joblib.dump(encoder, os.path.join(ARTIFACTS_DIR, "encoder.joblib"))
    joblib.dump(
        {
            "categorical_features": CATEGORICAL_FEATURES,
            "numerical_features": NUMERICAL_FEATURES,
            "all_features": ALL_FEATURES,
            "r2": float(r2),
            "mae": float(mae),
            "rmse": float(rmse),
        },
        os.path.join(ARTIFACTS_DIR, "metadata.joblib"),
    )
    print(f"\nArtifacts saved to: {os.path.abspath(ARTIFACTS_DIR)}")
    return r2, mae, rmse


if __name__ == "__main__":
    train_and_save()
