"""
Pipeline wrapper around the existing AutovitExtendedScraper.
Provides two modes: daily (new-only) and full_sweep (all pages).
"""
import logging
import os
import sys
from pathlib import Path
from typing import Literal

import pandas as pd

_EXTRACTION_DIR = Path(os.getenv(
    "SCRAPER_DIR",
    str(Path(__file__).resolve().parent.parent.parent.parent / "model" / "extraction"),
))

logger = logging.getLogger("autoscope.pipeline.scrape")


def run_scrape(mode: Literal["daily", "full_sweep"]) -> tuple[pd.DataFrame | None, set[str]]:
    """
    Run the scraper and return (new_listings_df, seen_urls).

    new_listings_df: only listings not previously in the raw CSV (None if scrape failed)
    seen_urls: every URL encountered on search result pages — used for stale detection

    daily:      scrape forward until no new listings found (~5-15 min)
    full_sweep: scrape all pages to get complete listing set (~30-60 min)
    """
    # Lazy import — keeps the scraper out of the module-level import chain so the
    # backend can start even before /model is mounted or scraper deps are available.
    if str(_EXTRACTION_DIR) not in sys.path:
        sys.path.insert(0, str(_EXTRACTION_DIR))
    try:
        from scraper_extended import AutovitExtendedScraper  # noqa: E402
    except ImportError as e:
        logger.error("Cannot import scraper from %s: %s", _EXTRACTION_DIR, e)
        return None, set()

    try:
        if mode == "daily":
            scraper = AutovitExtendedScraper(max_listings=10000, delay=0.8)
        else:
            scraper = AutovitExtendedScraper(max_listings=20000, delay=0.8)

        initial_count = len(scraper.data)

        if mode == "daily":
            scraper.scrape(start_page=1, max_consecutive_empty=3)
        else:
            scraper.scrape(start_page=1, max_consecutive_empty=10)

        seen_urls = scraper.seen_urls
        new_rows = scraper.data[initial_count:]

        if not new_rows:
            logger.info("Scrape complete: 0 new rows, %d URLs seen (mode=%s)", len(seen_urls), mode)
            return None, seen_urls

        df = pd.DataFrame(new_rows)
        logger.info("Scrape complete: %d new rows, %d URLs seen (mode=%s)", len(df), len(seen_urls), mode)
        return df, seen_urls

    except Exception as e:
        logger.error("Scraping failed: %s", e, exc_info=True)
        return None, set()
