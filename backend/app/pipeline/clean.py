"""
Data cleaning for scraped autovit.ro listings.
Extracted from model/extraction/cleanup_data_extended.ipynb.

Hard data-quality rules only — no statistical trimming (that lives in retrain.py).
"""
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger("autoscope.pipeline.clean")

BASIC_FEATURES = [
    "make", "model", "year", "body_type", "mileage", "door_count", "nr_seats",
    "color", "fuel_type", "engine_capacity", "engine_power",
    "gearbox", "transmission", "pollution_standard", "price",
]

CATEGORICAL_COLS = [
    "make", "model", "body_type", "color", "fuel_type",
    "gearbox", "transmission", "pollution_standard",
]

NUMERICAL_STRING_COLS = ["mileage", "engine_capacity", "engine_power", "price"]
NUMERICAL_INT_COLS = ["year", "door_count", "nr_seats"]


def clean_raw_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply hard data-quality rules to raw scraped data.

    Returns a cleaned DataFrame suitable for DB insertion.
    Drops rows that are broken/unusable; does NOT do percentile outlier removal.
    """
    df = df.copy()

    # 1. Drop rows missing required basic features
    df = df.dropna(subset=["make", "model", "year", "price"])

    # 2. Clean categorical columns — normalize whitespace
    for col in CATEGORICAL_COLS:
        if col in df.columns:
            df[col] = df[col].astype(str).apply(lambda s: " ".join(s.split()))
            df[col] = df[col].replace("nan", None).replace("None", None)

    # 3. Parse numerical strings (remove units: km, cm3, CP)
    if "mileage" in df.columns and df["mileage"].dtype == object:
        df["mileage"] = df["mileage"].astype(str).str.replace("km", "", regex=False)
    if "engine_capacity" in df.columns and df["engine_capacity"].dtype == object:
        df["engine_capacity"] = df["engine_capacity"].astype(str).str.replace("cm3", "", regex=False)
    if "engine_power" in df.columns and df["engine_power"].dtype == object:
        df["engine_power"] = df["engine_power"].astype(str).str.replace("CP", "", regex=False)
    if "price" in df.columns and df["price"].dtype == object:
        df["price"] = df["price"].astype(str).str.replace(",", ".", regex=False)

    # Remove spaces and convert to numeric
    for col in NUMERICAL_STRING_COLS + NUMERICAL_INT_COLS:
        if col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].str.replace(" ", "", regex=False)
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 4. Hard outlier rules
    df = df[df["price"] >= 500]
    df = df[df["price"].notna()]

    if "mileage" in df.columns:
        df = df[(df["mileage"].isna()) | ((df["mileage"] >= 0) & (df["mileage"] <= 1_000_000))]

    # 5. Fill equipment columns with 0 (binary flags)
    equipment_cols = [
        c for c in df.columns
        if c not in BASIC_FEATURES and c != "url"
        and c not in ("equipment_count", "is_well_equipped", "equipment_tier")
    ]
    for col in equipment_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # 6. Add equipment_count
    premium_signal_cols = [c for c in equipment_cols if c != "upholstery_fabric"]
    df["equipment_count"] = df[premium_signal_cols].sum(axis=1)

    # 7. Drop duplicates by URL
    if "url" in df.columns:
        df = df.drop_duplicates(subset=["url"], keep="last")

    return df.reset_index(drop=True)


def append_to_cleaned_csv(df: pd.DataFrame, csv_path: Path) -> None:
    """Append cleaned new listings to the master cleaned CSV."""
    if df.empty:
        return
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not csv_path.exists() or csv_path.stat().st_size == 0
    df.to_csv(csv_path, mode="a", header=write_header, index=False, encoding="utf-8")
    logger.info("Appended %d rows to %s", len(df), csv_path)
