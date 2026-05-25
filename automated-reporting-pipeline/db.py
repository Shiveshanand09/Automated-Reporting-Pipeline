"""
db.py — Database connection factory
Supports PostgreSQL (prod) and SQLite (local dev / CI).
"""

import os
import logging
import sqlite3

logger = logging.getLogger(__name__)

DB_TYPE = os.getenv("DB_TYPE", "sqlite")          # 'postgres' | 'sqlite'
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "reporting_db")
DB_USER = os.getenv("DB_USER", "analyst")
DB_PASS = os.getenv("DB_PASSWORD", "")
SQLITE_PATH = os.getenv("SQLITE_PATH", "reporting_dev.db")


def get_connection():
    """
    Return a DB-API 2.0 connection.
    Uses psycopg2 for Postgres in production; sqlite3 for local dev.
    """
    if DB_TYPE == "postgres":
        try:
            import psycopg2  # type: ignore
            conn = psycopg2.connect(
                host=DB_HOST,
                port=int(DB_PORT),
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
            )
            logger.info(f"Connected to PostgreSQL: {DB_HOST}/{DB_NAME}")
            return conn
        except ImportError:
            raise RuntimeError(
                "psycopg2 is not installed. Run: pip install psycopg2-binary"
            )
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        logger.info(f"Connected to SQLite: {SQLITE_PATH}")
        _seed_sqlite_if_empty(conn)
        return conn


def _seed_sqlite_if_empty(conn: sqlite3.Connection):
    """Seed the SQLite dev DB with sample data if tables are missing."""
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS sales (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            region      TEXT    NOT NULL,
            product     TEXT    NOT NULL,
            revenue     REAL    NOT NULL,
            units_sold  INTEGER NOT NULL,
            sale_date   TEXT    NOT NULL   -- ISO-8601 YYYY-MM-DD
        );

        CREATE TABLE IF NOT EXISTS support_tickets (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            category        TEXT NOT NULL,
            status          TEXT NOT NULL,   -- open | resolved | escalated
            created_date    TEXT NOT NULL,
            resolved_date   TEXT
        );

        CREATE TABLE IF NOT EXISTS marketing_spend (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            channel     TEXT  NOT NULL,
            spend       REAL  NOT NULL,
            impressions INTEGER NOT NULL,
            clicks      INTEGER NOT NULL,
            spend_date  TEXT  NOT NULL
        );
    """)

    # Only seed if empty
    row_count = cur.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    if row_count == 0:
        import random, datetime
        random.seed(42)
        regions   = ["North", "South", "East", "West", "APAC"]
        products  = ["Pro Plan", "Starter Plan", "Enterprise", "Add-on"]
        channels  = ["Search", "Social", "Email", "Display", "Referral"]
        categories = ["Billing", "Technical", "Feature Request", "Account"]
        statuses  = ["resolved", "resolved", "resolved", "open", "escalated"]

        today = datetime.date.today()

        sales_rows = []
        for i in range(180):
            d = today - datetime.timedelta(days=i)
            for _ in range(random.randint(2, 6)):
                sales_rows.append((
                    random.choice(regions),
                    random.choice(products),
                    round(random.uniform(200, 8000), 2),
                    random.randint(1, 50),
                    d.isoformat(),
                ))
        cur.executemany(
            "INSERT INTO sales (region, product, revenue, units_sold, sale_date) VALUES (?,?,?,?,?)",
            sales_rows,
        )

        ticket_rows = []
        for i in range(180):
            d = today - datetime.timedelta(days=i)
            for _ in range(random.randint(1, 4)):
                st = random.choice(statuses)
                resolved = (
                    (d + datetime.timedelta(days=random.randint(1, 5))).isoformat()
                    if st == "resolved" else None
                )
                ticket_rows.append((random.choice(categories), st, d.isoformat(), resolved))
        cur.executemany(
            "INSERT INTO support_tickets (category, status, created_date, resolved_date) VALUES (?,?,?,?)",
            ticket_rows,
        )

        mktg_rows = []
        for i in range(180):
            d = today - datetime.timedelta(days=i)
            for ch in channels:
                mktg_rows.append((
                    ch,
                    round(random.uniform(100, 3000), 2),
                    random.randint(5000, 200000),
                    random.randint(50, 5000),
                    d.isoformat(),
                ))
        cur.executemany(
            "INSERT INTO marketing_spend (channel, spend, impressions, clicks, spend_date) VALUES (?,?,?,?,?)",
            mktg_rows,
        )

        conn.commit()
        logger.info("SQLite dev DB seeded with 180 days of sample data.")
