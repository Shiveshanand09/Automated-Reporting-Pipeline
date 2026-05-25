-- ============================================================
--  schema.sql — Database schema for Automated Reporting Pipeline
--  Compatible: PostgreSQL 13+ | SQLite 3 (dev)
-- ============================================================

-- ── Sales ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sales (
    id          SERIAL PRIMARY KEY,
    region      TEXT           NOT NULL,
    product     TEXT           NOT NULL,
    revenue     NUMERIC(12,2)  NOT NULL CHECK (revenue >= 0),
    units_sold  INT            NOT NULL CHECK (units_sold >= 0),
    sale_date   DATE           NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sales_date   ON sales (sale_date);
CREATE INDEX IF NOT EXISTS idx_sales_region ON sales (region);

-- ── Support Tickets ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS support_tickets (
    id             SERIAL PRIMARY KEY,
    category       TEXT NOT NULL,
    status         TEXT NOT NULL CHECK (status IN ('open','resolved','escalated')),
    created_date   DATE NOT NULL,
    resolved_date  DATE
);

CREATE INDEX IF NOT EXISTS idx_tickets_date   ON support_tickets (created_date);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON support_tickets (status);

-- ── Marketing Spend ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS marketing_spend (
    id          SERIAL PRIMARY KEY,
    channel     TEXT           NOT NULL,
    spend       NUMERIC(12,2)  NOT NULL CHECK (spend >= 0),
    impressions INT            NOT NULL CHECK (impressions >= 0),
    clicks      INT            NOT NULL CHECK (clicks >= 0),
    spend_date  DATE           NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_mktg_date    ON marketing_spend (spend_date);
CREATE INDEX IF NOT EXISTS idx_mktg_channel ON marketing_spend (channel);

-- ── Report Run Audit Log ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS report_run_log (
    id            SERIAL PRIMARY KEY,
    report_type   TEXT           NOT NULL,
    period_start  DATE           NOT NULL,
    period_end    DATE           NOT NULL,
    total_revenue NUMERIC(14,2),
    units_sold    INT,
    ran_at        TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    UNIQUE (report_type, period_start, period_end)
);
