"""
Automated Reporting Pipeline
=============================
Generates weekly and monthly reports automatically from SQL data sources.
Eliminates ~40% of manual analyst hours by automating recurring report cycles.

Author: Shivesh Anand
"""

import os
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

from db import get_connection
from reports.weekly_report import generate_weekly_report
from reports.monthly_report import generate_monthly_report
from utils import send_email_report, setup_logging

# ── Logging ──────────────────────────────────────────────────────────────────
setup_logging()
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("reports/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_pipeline(report_type: str = "all", dry_run: bool = False):
    """
    Main pipeline entry point.

    Args:
        report_type: 'weekly', 'monthly', or 'all'
        dry_run:     If True, generate reports but skip email delivery.
    """
    logger.info("=" * 60)
    logger.info("Automated Reporting Pipeline — START")
    logger.info(f"  Report Type : {report_type}")
    logger.info(f"  Dry Run     : {dry_run}")
    logger.info(f"  Timestamp   : {datetime.utcnow().isoformat()}Z")
    logger.info("=" * 60)

    conn = get_connection()

    generated = []

    try:
        if report_type in ("weekly", "all"):
            logger.info("Generating WEEKLY report …")
            path = generate_weekly_report(conn, OUTPUT_DIR)
            generated.append(("Weekly", path))
            logger.info(f"  → Saved: {path}")

        if report_type in ("monthly", "all"):
            logger.info("Generating MONTHLY report …")
            path = generate_monthly_report(conn, OUTPUT_DIR)
            generated.append(("Monthly", path))
            logger.info(f"  → Saved: {path}")

    finally:
        conn.close()

    if not dry_run:
        for label, path in generated:
            send_email_report(label, path)
            logger.info(f"  → Email sent for {label} report")
    else:
        logger.info("Dry-run mode — emails suppressed.")

    logger.info("Pipeline completed successfully.")
    return generated


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated Reporting Pipeline")
    parser.add_argument(
        "--type",
        choices=["weekly", "monthly", "all"],
        default="all",
        help="Which report(s) to generate (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate reports without sending emails",
    )
    args = parser.parse_args()
    run_pipeline(report_type=args.type, dry_run=args.dry_run)
