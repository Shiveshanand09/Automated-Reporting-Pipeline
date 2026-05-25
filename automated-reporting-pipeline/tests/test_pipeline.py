"""
tests/test_pipeline.py — Unit tests for the reporting pipeline.
Run: pytest tests/ -v
"""

import sqlite3
import sys
from pathlib import Path
import tempfile

import pytest
import pandas as pd

# ── Make project root importable ──────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import _seed_sqlite_if_empty
from reports.weekly_report import generate_weekly_report
from reports.monthly_report import generate_monthly_report
from utils import fmt_currency


# ── Fixtures ──────────────────────────────────────────────────────────────────
@pytest.fixture
def conn():
    """In-memory SQLite connection seeded with sample data."""
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    _seed_sqlite_if_empty(connection)
    yield connection
    connection.close()


@pytest.fixture
def tmp_output(tmp_path):
    out = tmp_path / "output"
    out.mkdir()
    return out


# ── Utility tests ─────────────────────────────────────────────────────────────
class TestFmtCurrency:
    def test_millions(self):
        assert fmt_currency(2_500_000) == "$2.50M"

    def test_thousands(self):
        assert fmt_currency(12_500) == "$12.5K"

    def test_small(self):
        assert fmt_currency(99.5) == "$99.50"


# ── DB seeding tests ──────────────────────────────────────────────────────────
class TestDatabaseSeeding:
    def test_sales_rows_exist(self, conn):
        count = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
        assert count > 0, "Sales table should be seeded"

    def test_tickets_rows_exist(self, conn):
        count = conn.execute("SELECT COUNT(*) FROM support_tickets").fetchone()[0]
        assert count > 0, "Tickets table should be seeded"

    def test_marketing_rows_exist(self, conn):
        count = conn.execute("SELECT COUNT(*) FROM marketing_spend").fetchone()[0]
        assert count > 0, "Marketing table should be seeded"

    def test_sales_revenue_positive(self, conn):
        df = pd.read_sql_query("SELECT MIN(revenue) AS min_rev FROM sales", conn)
        assert df["min_rev"].iloc[0] >= 0


# ── Weekly report tests ───────────────────────────────────────────────────────
class TestWeeklyReport:
    def test_generates_excel(self, conn, tmp_output):
        path = generate_weekly_report(conn, tmp_output)
        assert path.exists(), "Weekly Excel file should be created"
        assert path.suffix == ".xlsx"

    def test_excel_has_expected_sheets(self, conn, tmp_output):
        path = generate_weekly_report(conn, tmp_output)
        xl = pd.ExcelFile(path)
        assert "Summary" in xl.sheet_names
        assert "Sales by Region-Product" in xl.sheet_names

    def test_chart_generated(self, conn, tmp_output):
        generate_weekly_report(conn, tmp_output)
        charts = list(tmp_output.glob("weekly_chart_*.png"))
        assert len(charts) >= 1, "Weekly chart PNG should be generated"


# ── Monthly report tests ──────────────────────────────────────────────────────
class TestMonthlyReport:
    def test_generates_excel(self, conn, tmp_output):
        path = generate_monthly_report(conn, tmp_output)
        assert path.exists(), "Monthly Excel file should be created"
        assert path.suffix == ".xlsx"

    def test_excel_has_kpi_sheet(self, conn, tmp_output):
        path = generate_monthly_report(conn, tmp_output)
        xl = pd.ExcelFile(path)
        assert "KPI Summary" in xl.sheet_names

    def test_chart_generated(self, conn, tmp_output):
        generate_monthly_report(conn, tmp_output)
        charts = list(tmp_output.glob("monthly_chart_*.png"))
        assert len(charts) >= 1, "Monthly chart PNG should be generated"
