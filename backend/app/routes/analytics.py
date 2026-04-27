import random
import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Car

router = APIRouter(prefix="/analytics", tags=["analytics"])

_CACHE_1H = "public, max-age=3600"


# ── helpers ───────────────────────────────────────────────────────────────────

def _query_df(db, *cols, col_names):
    rows = db.query(*cols).all()
    return pd.DataFrame([(r[i] for i in range(len(col_names))) for r in rows], columns=col_names)


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.get("/price-distribution")
def price_distribution(response: Response, db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = _CACHE_1H
    """Histogram bins for car prices (20 bins)."""
    prices = [r[0] for r in db.query(Car.price).filter(Car.status == "active").all() if r[0] is not None]
    if not prices:
        return {"data": []}
    arr = np.array(prices)
    counts, edges = np.histogram(arr, bins=20)
    return {
        "data": [
            {
                "range": f"€{int(edges[i]):,}",
                "count": int(counts[i]),
                "price_min": float(edges[i]),
                "price_max": float(edges[i + 1]),
            }
            for i in range(len(counts))
        ]
    }


@router.get("/price-by-make")
def price_by_make(response: Response, db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = _CACHE_1H
    """Average price per brand (top 15 by avg price, min 3 listings)."""
    rows = db.query(Car.make, Car.price).filter(Car.status == "active").all()
    df = pd.DataFrame([(r[0], r[1]) for r in rows], columns=["make", "price"]).dropna()
    agg = (
        df.groupby("make")
        .agg(avg_price=("price", "mean"), count=("price", "count"))
        .reset_index()
    )
    agg = agg[agg["count"] >= 3].sort_values("avg_price", ascending=False).head(15)
    return {
        "data": [
            {"make": r["make"], "avg_price": round(r["avg_price"], 2), "count": int(r["count"])}
            for _, r in agg.iterrows()
        ]
    }


@router.get("/price-by-fuel")
def price_by_fuel(response: Response, db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = _CACHE_1H
    """Average price per fuel type."""
    rows = db.query(Car.fuel_type, Car.price).filter(Car.status == "active").all()
    df = pd.DataFrame([(r[0], r[1]) for r in rows], columns=["fuel_type", "price"]).dropna()
    agg = (
        df.groupby("fuel_type")
        .agg(avg_price=("price", "mean"), count=("price", "count"))
        .reset_index()
        .sort_values("avg_price", ascending=False)
    )
    return {
        "data": [
            {"fuel_type": r["fuel_type"], "avg_price": round(r["avg_price"], 2), "count": int(r["count"])}
            for _, r in agg.iterrows()
        ]
    }


@router.get("/price-by-body-type")
def price_by_body_type(response: Response, db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = _CACHE_1H
    """Average price per body type."""
    rows = db.query(Car.body_type, Car.price).filter(Car.status == "active").all()
    df = pd.DataFrame([(r[0], r[1]) for r in rows], columns=["body_type", "price"]).dropna()
    agg = (
        df.groupby("body_type")
        .agg(avg_price=("price", "mean"), count=("price", "count"))
        .reset_index()
        .sort_values("avg_price", ascending=False)
    )
    return {
        "data": [
            {"body_type": r["body_type"], "avg_price": round(r["avg_price"], 2), "count": int(r["count"])}
            for _, r in agg.iterrows()
        ]
    }


@router.get("/mileage-vs-price")
def mileage_vs_price(response: Response, db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = _CACHE_1H
    """Scatter data: mileage vs price (500 sampled points)."""
    rows = db.query(Car.mileage, Car.price, Car.make, Car.fuel_type).filter(Car.status == "active").all()
    data = [
        {"mileage": r[0], "price": r[1], "make": r[2], "fuel_type": r[3]}
        for r in rows
        if r[0] is not None and r[1] is not None
    ]
    if len(data) > 500:
        random.seed(42)
        data = random.sample(data, 500)
    return {"data": data}


@router.get("/year-vs-price")
def year_vs_price(response: Response, db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = _CACHE_1H
    """Average price by manufacturing year."""
    rows = db.query(Car.year, Car.price).filter(Car.status == "active").all()
    df = pd.DataFrame([(r[0], r[1]) for r in rows], columns=["year", "price"]).dropna()
    agg = (
        df.groupby("year")
        .agg(avg_price=("price", "mean"), count=("price", "count"))
        .reset_index()
        .sort_values("year")
    )
    return {
        "data": [
            {"year": int(r["year"]), "avg_price": round(r["avg_price"], 2), "count": int(r["count"])}
            for _, r in agg.iterrows()
        ]
    }


@router.get("/gearbox-distribution")
def gearbox_distribution(response: Response, db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = _CACHE_1H
    """Count per gearbox type."""
    rows = db.query(Car.gearbox).filter(Car.status == "active").all()
    df = pd.DataFrame([r[0] for r in rows], columns=["gearbox"]).dropna()
    counts = df["gearbox"].value_counts().reset_index()
    counts.columns = ["gearbox", "count"]
    return {
        "data": [{"gearbox": r["gearbox"], "count": int(r["count"])} for _, r in counts.iterrows()]
    }


@router.get("/transmission-distribution")
def transmission_distribution(response: Response, db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = _CACHE_1H
    """Count per transmission type."""
    rows = db.query(Car.transmission).filter(Car.status == "active").all()
    df = pd.DataFrame([r[0] for r in rows], columns=["transmission"]).dropna()
    counts = df["transmission"].value_counts().reset_index()
    counts.columns = ["transmission", "count"]
    return {
        "data": [{"transmission": r["transmission"], "count": int(r["count"])} for _, r in counts.iterrows()]
    }
