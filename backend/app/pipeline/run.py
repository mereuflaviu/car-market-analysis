"""
Pipeline orchestrator. Runs scrape → clean → sync → retrain in sequence.
"""
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Literal

import pandas as pd

from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal
from app.pipeline.scrape import run_scrape
from app.pipeline.clean import clean_raw_data, append_to_cleaned_csv
from app.pipeline.sync_db import sync_listings
from app.pipeline.retrain import maybe_retrain

_SCRAPER_DIR = Path(os.getenv(
    "SCRAPER_DIR",
    str(Path(__file__).resolve().parent.parent.parent.parent / "model" / "extraction"),
))
_CLEANED_CSV = _SCRAPER_DIR.parent / "data" / "cleaned_car_listings_extended.csv"

logger = logging.getLogger("autoscope.pipeline")


def run_pipeline(mode: Literal["daily", "full_sweep"]) -> dict:
    """
    Execute the full pipeline.

    Returns a report dict with results from each step.
    """
    report = {
        "mode": mode,
        "started_at": datetime.utcnow().isoformat(),
        "steps": {},
        "status": "running",
    }

    db = SessionLocal()

    pipeline_run = models.PipelineRun(mode=mode, started_at=datetime.utcnow())
    db.add(pipeline_run)
    db.commit()
    db.refresh(pipeline_run)

    try:
        # Step 1: Scrape
        logger.info("Pipeline [%s] Step 1: Scraping...", mode)
        raw_df, seen_urls = run_scrape(mode)
        report["steps"]["scrape"] = {
            "status": "ok" if raw_df is not None else "no_new_data",
            "new_rows": len(raw_df) if raw_df is not None else 0,
            "seen_urls": len(seen_urls),
        }

        # Step 2: Clean + append to CSV (only when new listings were found)
        if raw_df is not None and not raw_df.empty:
            logger.info("Pipeline [%s] Step 2: Cleaning %d rows...", mode, len(raw_df))
            cleaned_df = clean_raw_data(raw_df)
            append_to_cleaned_csv(cleaned_df, _CLEANED_CSV)
            report["steps"]["clean"] = {"status": "ok", "rows_after": len(cleaned_df)}
        else:
            cleaned_df = None
            report["steps"]["clean"] = {"status": "skipped"}

        # Step 3: Sync to DB
        logger.info("Pipeline [%s] Step 3: Syncing to database...", mode)
        sync_summary = sync_listings(
            cleaned_df if cleaned_df is not None else pd.DataFrame(),
            mode,
            db,
            seen_urls=seen_urls,
        )
        report["steps"]["sync"] = {"status": "ok", **sync_summary}

        # Step 4: Retrain only if new listings were added
        if sync_summary["new"] > 0:
            logger.info("Pipeline [%s] Step 4: Retraining (%d new listings)...", mode, sync_summary["new"])
            retrain_result = maybe_retrain(db)
            report["steps"]["retrain"] = retrain_result
            pipeline_run.retrained = retrain_result.get("swapped", False)
            pipeline_run.new_r2 = retrain_result.get("new_r2")
        else:
            report["steps"]["retrain"] = {"retrained": False, "reason": "no_new_listings"}

        report["status"] = "success"
        pipeline_run.new_listings = sync_summary["new"]

    except Exception as e:
        logger.error("Pipeline [%s] failed: %s", mode, e, exc_info=True)
        report["status"] = "failed"
        report["error"] = str(e)

    finally:
        _finish_run(db, pipeline_run, report)
        db.close()

    report["finished_at"] = datetime.utcnow().isoformat()
    logger.info("Pipeline [%s] finished: %s", mode, report["status"])
    return report


def _finish_run(db: Session, run: models.PipelineRun, report: dict):
    """Update the PipelineRun record with final status."""
    run.finished_at = datetime.utcnow()
    run.status = report["status"]
    run.summary = json.dumps(report, default=str)
    db.commit()
