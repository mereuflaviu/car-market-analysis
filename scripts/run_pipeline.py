"""
CLI entry point for the automated pipeline.

Usage:
    python scripts/run_pipeline.py --mode daily
    python scripts/run_pipeline.py --mode full_sweep
"""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

from app.pipeline.run import run_pipeline


def main():
    parser = argparse.ArgumentParser(description="Run the AutoScope data pipeline")
    parser.add_argument(
        "--mode",
        choices=["daily", "full_sweep"],
        required=True,
        help="daily = new listings only; full_sweep = all pages + stale detection",
    )
    args = parser.parse_args()

    print(f"Starting pipeline (mode={args.mode})...")
    report = run_pipeline(args.mode)
    print(json.dumps(report, indent=2, default=str))

    if report["status"] == "failed":
        sys.exit(1)


if __name__ == "__main__":
    main()
