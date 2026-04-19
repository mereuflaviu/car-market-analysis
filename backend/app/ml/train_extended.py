"""
Extended model training on cleaned_car_listings_extended.csv.

Key improvements over the baseline:
  1. Log-price transform  – normalises severely skewed target (skew 2.43 -> 0.15)
  2. Smoothed target encoding for make/model – those two columns alone explain
     30% / 69% of price variance; ordinal integers were throwing that away
  3. Feature engineering – car_age, power_per_liter, brand_tier
  4. Tuned regularisation – colsample/reg_alpha/gamma search

Usage (from project root):
    python backend/app/ml/train_extended.py              # all experiments
    python backend/app/ml/train_extended.py --tune       # + hyperparam search on best
    python backend/app/ml/train_extended.py --experiment full_log --tune
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd
import joblib
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, RandomizedSearchCV, train_test_split
from sklearn.preprocessing import OrdinalEncoder
import sys, os as _os
sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), '..', '..'))
from app.ml.encoders import SmoothedTargetEncoder  # stable import path for joblib

# ── Paths ──────────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(
    _HERE, "..", "..", "..", "model", "data", "cleaned_car_listings_extended.csv"
)
ARTIFACTS_DIR = os.path.join(_HERE, "..", "..", "artifacts")

TARGET = "price"
RANDOM_STATE = 42

# Trim outlier prices before training.
# The top ~3% are rare exotic/luxury cars that skew MAE without representative
# training data. The model is documented as targeting cars in this range.
PRICE_PERCENTILE_LOW  = 0.005  # drop lowest 0.5% (data errors)
PRICE_PERCENTILE_HIGH = 0.985  # drop top 1.5% (keep more luxury cars for learning)

# ── Column definitions ────────────────────────────────────────────────────────
BASE_CAT = [
    "body_type", "color", "fuel_type",
    "gearbox", "transmission", "pollution_standard",
]
# make + model handled via target encoding (not ordinal)
TARGET_ENCODE_COLS = ["make", "model"]

BASE_NUM  = ["year", "mileage", "engine_capacity", "engine_power"]
EXTRA_NUM = [
    "door_count", "nr_seats", "equipment_count",
    "car_age", "log_car_age",
    "power_per_liter",
    "power_over_age",
    "power_auto",
    "equip_per_age",
    "cohort_size",
    "mileage_vs_cohort",
    "mileage_vs_make_model",
    "luxury_power",
    "equipment_value_eur",
    "mileage_per_year",
    "value_density",
]
EXTRA_CAT = ["brand_tier", "power_segment"]
BINARY = ["is_electric", "is_hybrid_plugin", "is_hybrid", "hybrid_plugin_new"]

# ── Brand tiers ───────────────────────────────────────────────────────────────
LUXURY_BRANDS = {
    "Porsche", "BMW", "Mercedes-Benz", "Audi", "Lexus", "Jaguar",
    "Land Rover", "Maserati", "Bentley", "Ferrari", "Lamborghini",
    "Rolls-Royce", "Aston Martin", "McLaren", "Genesis",
}
BUDGET_BRANDS = {
    "Dacia", "Fiat", "Seat", "Chevrolet", "Daewoo", "Lada",
    "Mitsubishi", "Suzuki", "Kia", "Hyundai",
}

# ── Equipment residual value (EUR) ──────────────────────────────────────────
# Used-market residual values, not new-car configurator prices.
# Bundled features are priced as their share of the bundle.
EQUIPMENT_VALUE = {
    # Standard — EUR 0 (expected on any car, no premium)
    "ac": 0, "bluetooth": 0, "cruise_control": 0, "isofix": 0,
    "front_armrest": 0, "usb_port": 0, "upholstery_fabric": 0,
    "climatronic": 0, "climatronic_2zone": 0,

    # Light value
    "follow_me_home": 100, "folding_mirrors": 100,
    "led_lights": 200, "front_park_sensors": 250,
    "rear_park_sensors": 250, "rear_camera": 300,
    "upholstery_leather_mix": 300, "memory_seat": 300,
    "paddle_shifters": 150, "sport_steering_wheel": 150,

    # Bundles (priced as share of bundle)
    "apple_carplay": 200, "android_auto": 200,
    "navigation": 200, "internet": 100,
    "heated_driver_seat": 200, "heated_passenger_seat": 200,
    "electric_driver_seat": 250,
    "keyless_entry": 300, "keyless_go": 300,

    # Mid-premium
    "heated_windshield": 400, "climatronic_3zone": 500,
    "upholstery_alcantara": 500, "sport_suspension": 300,
    "camera_360": 500, "blind_spot": 300,
    "lane_assist": 300, "distance_control": 200,
    "ventilated_front_seats": 400, "ventilated_rear_seats": 200,
    "adaptive_cruise": 500, "predictive_acc": 200,

    # Premium
    "head_up_display": 800, "electric_sunroof": 800,
    "panoramic_roof": 1200, "upholstery_leather": 1200,
    "laser_lights": 1000, "autonomous_driving": 1200,
    "climatronic_4zone": 1800, "air_suspension": 2500,

    # Minor / legacy
    "bi_xenon": 100, "xenon": 100, "dynamic_lights": 100,
    "park_assist": 200, "auto_park": 300,
    "wireless_charging": 200, "manual_sunroof": 400,
    "rear_glass_sunroof": 500,
}

# ── Experiment definitions ────────────────────────────────────────────────────
EXPERIMENTS = {
    # Sanity-check baseline (same as before, just for comparison)
    "baseline": {
        "numerical":   BASE_NUM,
        "categorical": BASE_CAT + ["make", "model"],  # ordinal encoded
        "binary":      [],
        "target_enc":  [],
        "log_target":  False,
        "description": "Original 12 features, ordinal encoding, raw price",
    },
    # Adding engineered features + brand_tier, still raw price
    "engineered": {
        "numerical":   BASE_NUM + EXTRA_NUM,
        "categorical": BASE_CAT + EXTRA_CAT + ["make", "model"],
        "binary":      BINARY,
        "target_enc":  [],
        "log_target":  False,
        "description": "Engineered features (car_age, power_per_liter, brand_tier), raw price",
    },
    # Add smoothed target encoding for make/model
    "target_enc": {
        "numerical":   BASE_NUM + EXTRA_NUM,
        "categorical": BASE_CAT + EXTRA_CAT,
        "binary":      BINARY,
        "target_enc":  TARGET_ENCODE_COLS,
        "log_target":  False,
        "description": "Engineered + smoothed target encoding for make/model, raw price",
    },
    # Full: target encoding + log price
    "full_log": {
        "numerical":   BASE_NUM + EXTRA_NUM,
        "categorical": BASE_CAT + EXTRA_CAT,
        "binary":      BINARY,
        "target_enc":  TARGET_ENCODE_COLS,
        "log_target":  True,
        "description": "Engineered + target encoding + log(price) transform",
    },
    # THE KEY EXPERIMENT: cohort (make+model+year) target encoding
    # Cohort explains 94.9% of price variance vs model-alone 68.7%
    # Cohort mean has 0.9744 correlation vs model mean's 0.7631
    "cohort_enc": {
        "numerical":   BASE_NUM + EXTRA_NUM,
        "categorical": BASE_CAT + EXTRA_CAT,
        "binary":      BINARY,
        "target_enc":  TARGET_ENCODE_COLS + ["cohort"],   # make, model, AND cohort
        "log_target":  False,
        "description": "Cohort (make+model+year) smoothed target encoding — biggest unlock",
    },
    # Cohort + log price
    "cohort_log": {
        "numerical":   BASE_NUM + EXTRA_NUM,
        "categorical": BASE_CAT + EXTRA_CAT,
        "binary":      BINARY,
        "target_enc":  TARGET_ENCODE_COLS + ["cohort"],
        "log_target":  True,
        "description": "Cohort target encoding + log(price)",
    },
}

DEFAULT_ORDER = ["target_enc"]

# ── Fixed hyperparams (from previous tuning) ─────────────────────────────────
FIXED_PARAMS = dict(
    n_estimators=500,
    max_depth=4,
    learning_rate=0.1,
    subsample=0.9,
    colsample_bytree=0.7,
    min_child_weight=5,
    reg_alpha=0.3,
    reg_lambda=3.0,
    gamma=0.2,
    random_state=RANDOM_STATE,
    verbosity=0,
    n_jobs=1,
)

PARAM_DISTRIBUTIONS = {
    "n_estimators":     [300, 400, 500, 600, 800],
    "max_depth":        [3, 4, 5, 6],
    "learning_rate":    [0.03, 0.05, 0.08, 0.1],
    "subsample":        [0.7, 0.8, 0.9, 1.0],
    "colsample_bytree": [0.5, 0.6, 0.7, 0.8],
    "min_child_weight": [3, 5, 7, 10],
    "reg_alpha":        [0.0, 0.1, 0.3, 0.5, 1.0],
    "reg_lambda":       [1.0, 2.0, 3.0, 5.0],
    "gamma":            [0.0, 0.1, 0.2, 0.3],
}


# ── Feature engineering ───────────────────────────────────────────────────────

def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # ── Age ──────────────────────────────────────────────────────────────────
    df["car_age"]      = 2026 - df["year"]
    df["log_car_age"]  = np.log1p(df["car_age"])   # logarithmic depreciation curve

    # ── Engine / performance ──────────────────────────────────────────────────
    df["power_per_liter"] = df["engine_power"] / (df["engine_capacity"] / 1000).clip(lower=0.1)

    # power relative to age — a 300HP car loses value fast; captures newness × performance
    df["power_over_age"] = df["engine_power"] / (df["car_age"] + 1)

    # automatic gearbox × engine power — premium for powerful automatics
    is_auto = (df["gearbox"] == "Automata").astype(float)
    df["power_auto"] = df["engine_power"] * is_auto

    # ── Equipment relative to age ─────────────────────────────────────────────
    # A well-equipped new car vs a well-equipped old car are different propositions
    df["equip_per_age"] = df["equipment_count"] / (df["car_age"] + 1)

    # ── Fuel type flags (electric/hybrid price dynamics are totally different) ─
    fuel_lower = df["fuel_type"].str.lower()
    df["is_electric"]      = fuel_lower.str.contains("electric", na=False).astype(int)
    df["is_hybrid_plugin"] = fuel_lower.str.contains("plug", na=False).astype(int)
    df["is_hybrid"]        = (
        fuel_lower.str.contains("hibrid", na=False) &
        ~fuel_lower.str.contains("plug", na=False)
    ).astype(int)

    # ── Brand tier ────────────────────────────────────────────────────────────
    df["brand_tier"] = df["make"].apply(
        lambda x: "luxury" if x in LUXURY_BRANDS
        else "budget" if x in BUDGET_BRANDS
        else "mainstream"
    )

    # ── Cohort statistics (make + model + year) — NO target leakage ─────────
    # These are computed from mileage/count, NOT from price, so they're safe.
    df["cohort"] = df["make"] + "|" + df["model"] + "|" + df["year"].astype(str)

    # How many listings of this exact make+model+year?  → rarity/liquidity signal
    df["cohort_size"] = df.groupby("cohort")["cohort"].transform("count")

    # Is this car over/under-mileaged vs its peers? → condition signal
    cohort_mean_mileage = df.groupby("cohort")["mileage"].transform("mean")
    cohort_std_mileage  = df.groupby("cohort")["mileage"].transform("std").fillna(1)
    df["mileage_vs_cohort"] = (df["mileage"] - cohort_mean_mileage) / cohort_std_mileage.clip(lower=1)

    # Same for make+model only (denser, more stable)
    make_model_mean_mileage = df.groupby(["make", "model"])["mileage"].transform("mean")
    df["mileage_vs_make_model"] = df["mileage"] - make_model_mean_mileage

    # ── Interaction features ──────────────────────────────────────────────────
    # Hybrid/electric premium is stronger for newer cars
    df["hybrid_plugin_new"] = df["is_hybrid_plugin"] * (2026 - df["year"]).clip(upper=5).apply(lambda x: 1 if x <= 3 else 0)

    # High-power + luxury brand → strong premium signal
    df["luxury_power"] = (df["brand_tier"] == "luxury").astype(float) * df["engine_power"]

    # ── Equipment value (EUR) — replaces 57 sparse binary flags ──────────
    equip_cols_in_df = [c for c in EQUIPMENT_VALUE if c in df.columns]
    df["equipment_value_eur"] = sum(
        df[col].fillna(0) * EQUIPMENT_VALUE[col] for col in equip_cols_in_df
    )

    # ── Power segment — separates 190HP from 374HP within same model ─────
    df["power_segment"] = pd.cut(
        df["engine_power"],
        bins=[0, 120, 180, 250, 350, 9999],
        labels=["economy", "mid", "strong", "performance", "super"],
    ).astype(str)

    # ── Mileage per year — is this car high/low mileage for its age? ─────
    df["mileage_per_year"] = df["mileage"] / (df["car_age"] + 1)

    # ── Value density — option value relative to car age ─────────────────
    df["value_density"] = df["equipment_value_eur"] / (df["car_age"] + 1)

    return df


# ── Smoothed target encoding ───────────────────────────────────────────────────

# ── Data preparation ──────────────────────────────────────────────────────────

def load_and_engineer(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    print(f"  Loaded {len(df)} rows x {len(df.columns)} columns")
    df = add_engineered_features(df)

    before = len(df)
    q_low  = df[TARGET].quantile(PRICE_PERCENTILE_LOW)
    q_high = df[TARGET].quantile(PRICE_PERCENTILE_HIGH)
    df = df[(df[TARGET] >= q_low) & (df[TARGET] <= q_high)].reset_index(drop=True)
    print(f"  Price filter [{q_low:.0f} – {q_high:.0f} EUR]: kept {len(df)} / {before} rows "
          f"(dropped {before - len(df)} outliers)")
    return df


def prepare_features(df: pd.DataFrame, exp: dict) -> tuple:
    num_cols = [c for c in exp["numerical"]  if c in df.columns]
    cat_cols = [c for c in exp["categorical"] if c in df.columns]
    bin_cols = [c for c in exp["binary"]      if c in df.columns]
    tenc_cols = [c for c in exp["target_enc"] if c in df.columns]

    all_input_cols = num_cols + cat_cols + bin_cols + tenc_cols
    missing = set(exp["numerical"] + exp["categorical"] + exp["binary"] + exp["target_enc"]) - set(df.columns)
    if missing:
        print(f"  WARNING – skipping missing columns: {sorted(missing)}")

    sub = df[all_input_cols + [TARGET]].dropna(subset=all_input_cols + [TARGET])
    print(f"  Features: {len(all_input_cols)} "
          f"({len(num_cols)} num, {len(cat_cols)} cat, {len(bin_cols)} binary, {len(tenc_cols)} target-enc)")
    print(f"  Rows after dropna: {len(sub)}")
    return sub[all_input_cols].copy(), sub[TARGET].copy(), num_cols, cat_cols, bin_cols, tenc_cols


def encode_features(
    X_train: pd.DataFrame, y_train: pd.Series,
    X_test:  pd.DataFrame,
    cat_cols: list, tenc_cols: list,
) -> tuple[pd.DataFrame, pd.DataFrame, OrdinalEncoder, SmoothedTargetEncoder | None]:

    ord_enc = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    if cat_cols:
        ord_enc.fit(X_train[cat_cols])
        X_train = X_train.copy()
        X_test  = X_test.copy()
        X_train[cat_cols] = ord_enc.transform(X_train[cat_cols])
        X_test[cat_cols]  = ord_enc.transform(X_test[cat_cols])

    te_enc = None
    if tenc_cols:
        # Cohort (make+model+year) is very sparse → higher smoothing to avoid overfit
        # Make/model are denser → lower smoothing is fine
        smoothing_per_col = {col: (20.0 if col == "cohort" else 10.0) for col in tenc_cols}
        te_enc = SmoothedTargetEncoder(smoothing=10.0, smoothing_per_col=smoothing_per_col)
        X_train = te_enc.fit_transform(X_train, y_train, tenc_cols)
        X_test  = te_enc.transform(X_test, tenc_cols)

    # Coerce all to float
    for col in X_train.columns:
        X_train[col] = pd.to_numeric(X_train[col], errors="coerce").fillna(0)
        X_test[col]  = pd.to_numeric(X_test[col],  errors="coerce").fillna(0)

    return X_train, X_test, ord_enc, te_enc


# ── Evaluation ────────────────────────────────────────────────────────────────

def evaluate(model, X_test, y_test, log_target: bool) -> dict:
    raw_pred = model.predict(X_test)
    if log_target:
        y_pred  = np.exp(raw_pred)
        y_true  = np.exp(y_test) if hasattr(y_test, "values") else np.exp(np.array(y_test))
    else:
        y_pred = raw_pred
        y_true = np.array(y_test)

    r2   = float(r2_score(y_true, y_pred))
    mae  = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    return {"r2": r2, "mae": mae, "rmse": rmse}


def cv_r2(model_params: dict, X_enc: pd.DataFrame, y: pd.Series, n_splits: int = 5) -> float:
    """K-fold CV R² on the encoded (and possibly log-transformed) target."""
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
    params = {k: v for k, v in model_params.items() if k != "n_jobs"}
    model  = xgb.XGBRegressor(**params, n_jobs=1)
    scores = cross_val_r2(model, X_enc, y, kf)
    return float(np.mean(scores))


def cross_val_r2(model, X, y, cv) -> list:
    """Manual CV to avoid joblib issues on Windows."""
    scores = []
    X_arr = np.array(X)
    y_arr = np.array(y)
    for train_idx, test_idx in cv.split(X_arr, y_arr):
        m = xgb.XGBRegressor(**{k: v for k, v in model.get_params().items()})
        m.fit(X_arr[train_idx], y_arr[train_idx])
        pred = m.predict(X_arr[test_idx])
        scores.append(r2_score(y_arr[test_idx], pred))
    return scores


def feature_importance_table(model, feature_names: list, top_n: int = 20) -> pd.DataFrame:
    imp = model.feature_importances_
    df  = pd.DataFrame({"feature": feature_names, "importance": imp})
    return df.sort_values("importance", ascending=False).head(top_n).reset_index(drop=True)


def tune_hyperparams(X_enc: pd.DataFrame, y: pd.Series, n_iter: int = 40) -> dict:
    print(f"  Hyperparameter search: {n_iter} iterations, 5-fold CV ...")
    kf     = KFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    base   = xgb.XGBRegressor(random_state=RANDOM_STATE, verbosity=0, n_jobs=1)
    search = RandomizedSearchCV(
        base, PARAM_DISTRIBUTIONS, n_iter=n_iter,
        cv=kf, scoring="r2", random_state=RANDOM_STATE, n_jobs=1, verbose=0,
    )
    search.fit(X_enc, y)
    print(f"  Best CV R²: {search.best_score_:.4f}")
    print(f"  Best params: {search.best_params_}")
    return search.best_params_


# ── Main experiment runner ────────────────────────────────────────────────────

def run_experiment(name: str, df: pd.DataFrame, do_tune: bool = False, n_iter: int = 40) -> dict:
    exp = EXPERIMENTS[name]
    print(f"\n{'='*62}")
    print(f"EXPERIMENT: {name.upper()}")
    print(f"  {exp['description']}")
    print(f"{'='*62}")

    X, y, num_cols, cat_cols, bin_cols, tenc_cols = prepare_features(df, exp)
    max_equip_val = float(df["equipment_value_eur"].max()) if "equipment_value_eur" in df.columns else 15000.0
    log_target = exp["log_target"]
    y_model = np.log(y) if log_target else y

    # Stratified split by price bins
    price_bins = pd.qcut(y, q=10, labels=False, duplicates="drop")
    X_tr, X_te, ym_tr, ym_te, y_tr, _ = train_test_split(
        X, y_model, y, test_size=0.2, random_state=RANDOM_STATE, stratify=price_bins
    )
    print(f"  Train: {len(X_tr)}  |  Test: {len(X_te)}"
          + ("  |  target: log(price)" if log_target else "  |  target: price"))

    X_tr_enc, X_te_enc, ord_enc, te_enc = encode_features(
        X_tr, y_tr, X_te, cat_cols, tenc_cols
    )

    all_cols = list(X_tr_enc.columns)

    # Hyperparameter selection
    if do_tune:
        best_params = tune_hyperparams(X_tr_enc, ym_tr, n_iter=n_iter)
        model_params = {**FIXED_PARAMS, **best_params}
    else:
        model_params = FIXED_PARAMS.copy()

    print("  Training XGBoost ...")
    model = xgb.XGBRegressor(**model_params)
    model.fit(X_tr_enc, ym_tr)

    metrics = evaluate(model, X_te_enc, ym_te, log_target)
    print(f"\n  Test-set results:")
    print(f"    R2   : {metrics['r2']:.4f}")
    print(f"    MAE  : EUR {metrics['mae']:,.0f}")
    print(f"    RMSE : EUR {metrics['rmse']:,.0f}")

    # CV on training data (in model-space, i.e. log if applicable)
    print("  Running 5-fold CV ...")
    kf = KFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    cv_scores = cross_val_r2(model, X_tr_enc, ym_tr, kf)
    cv_mean = float(np.mean(cv_scores))
    cv_std  = float(np.std(cv_scores))
    print(f"    CV R2: {cv_mean:.4f} +/- {cv_std:.4f}")

    fi = feature_importance_table(model, all_cols)
    print(f"\n  Top 15 features:")
    for _, row in fi.head(15).iterrows():
        bar = "#" * int(row["importance"] * 200)
        print(f"    {row['feature']:35s} {row['importance']:.4f}  {bar}")

    # Save cohort statistics for inference (mileage lookup tables — no target leakage)
    cohort_stats = None
    if "cohort" in df.columns:
        cohort_stats = {
            "cohort_mean_mileage":      df.groupby("cohort")["mileage"].mean().to_dict(),
            "cohort_std_mileage":       df.groupby("cohort")["mileage"].std().fillna(1).to_dict(),
            "cohort_size":              df.groupby("cohort")["cohort"].count().to_dict(),
            "make_model_mean_mileage":  df.groupby(["make","model"])["mileage"].mean().to_dict(),
            "global_mean_mileage":      float(df["mileage"].mean()),
        }

    return {
        "experiment":    name,
        "model":         model,
        "ord_encoder":   ord_enc,
        "te_encoder":    te_enc,
        "log_target":    log_target,
        "model_params":  model_params,
        "metrics":       {**metrics, "cv_r2": cv_mean, "cv_std": cv_std},
        "feature_names": all_cols,
        "numerical_features":   num_cols,
        "categorical_features": cat_cols,
        "binary_features":      bin_cols,
        "target_enc_features":  tenc_cols,
        "feature_importance":   fi,
        "cohort_stats":         cohort_stats,
        "max_equipment_value_eur": max_equip_val,
    }


# ── Artifact persistence ──────────────────────────────────────────────────────

def save_artifacts(result: dict, suffix: str = ""):
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    tag = f"_{suffix}" if suffix else ""

    joblib.dump(result["model"],          os.path.join(ARTIFACTS_DIR, f"model{tag}.joblib"))
    joblib.dump(result["ord_encoder"],    os.path.join(ARTIFACTS_DIR, f"encoder{tag}.joblib"))
    joblib.dump(result["te_encoder"],     os.path.join(ARTIFACTS_DIR, f"te_encoder{tag}.joblib"))
    if result.get("cohort_stats") is not None:
        joblib.dump(result["cohort_stats"], os.path.join(ARTIFACTS_DIR, f"cohort_stats{tag}.joblib"))

    fi_dict = result["feature_importance"].set_index("feature")["importance"].to_dict()
    joblib.dump({
        "experiment":           result["experiment"],
        "numerical_features":   result["numerical_features"],
        "categorical_features": result["categorical_features"],
        "binary_features":      result["binary_features"],
        "target_enc_features":  result["target_enc_features"],
        "all_features":         result["feature_names"],
        "log_target":           result["log_target"],
        "model_params":         result["model_params"],
        "r2":    result["metrics"]["r2"],
        "mae":   result["metrics"]["mae"],
        "rmse":  result["metrics"]["rmse"],
        "cv_r2": result["metrics"]["cv_r2"],
        "cv_std": result["metrics"]["cv_std"],
        "max_equipment_value_eur": result.get("max_equipment_value_eur", 15000.0),
        "feature_importance": fi_dict,
        "dataset": "cleaned_car_listings_extended.csv",
    }, os.path.join(ARTIFACTS_DIR, f"metadata{tag}.joblib"))

    print(f"\n  Saved: model{tag}.joblib, encoder{tag}.joblib, te_encoder{tag}.joblib, metadata{tag}.joblib")


def compare(results: list[dict]):
    print(f"\n{'='*70}")
    print("COMPARISON SUMMARY")
    print(f"{'='*70}")
    print(f"{'Experiment':24s}  {'R2':>7s}  {'CV R2':>7s}  {'MAE':>9s}  {'RMSE':>9s}  {'log':>4s}")
    print("-" * 70)
    # Pick by lowest MAE (better for absolute price predictions)
    best = min(results, key=lambda r: r["metrics"]["mae"])
    for r in results:
        marker = " << BEST" if r == best else ""
        m = r["metrics"]
        print(
            f"{r['experiment']:24s}  {m['r2']:7.4f}  {m['cv_r2']:7.4f}"
            f"  EUR{m['mae']:>7,.0f}  EUR{m['rmse']:>7,.0f}"
            f"  {'Y' if r['log_target'] else 'N'}{marker}"
        )
    return best


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", choices=list(EXPERIMENTS) + ["all"], default="all")
    parser.add_argument("--tune", action="store_true")
    parser.add_argument("--n-iter", type=int, default=50)
    parser.add_argument("--save-all", action="store_true")
    args = parser.parse_args()

    data_path = os.path.abspath(DATA_PATH)
    if not os.path.exists(data_path):
        print(f"ERROR: dataset not found at {data_path}")
        sys.exit(1)

    print(f"Loading data: {data_path}")
    df = load_and_engineer(data_path)

    to_run = DEFAULT_ORDER if args.experiment == "all" else [args.experiment]

    results = []
    for name in to_run:
        do_tune = args.tune and (args.experiment != "all" or name == to_run[-1])
        r = run_experiment(name, df, do_tune=do_tune, n_iter=args.n_iter)
        results.append(r)
        if args.save_all:
            save_artifacts(r, suffix=name)

    best = compare(results) if len(results) > 1 else results[0]
    print(f"\nSaving '{best['experiment']}' as active model ...")
    save_artifacts(best)

    print("\nDone. Restart backend to use new artifacts.")


if __name__ == "__main__":
    main()
