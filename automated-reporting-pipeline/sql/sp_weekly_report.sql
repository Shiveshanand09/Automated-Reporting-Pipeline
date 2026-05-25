-- ============================================================
--  sp_weekly_report.sql
--  Stored procedure: Weekly Sales & Support Summary
--  Compatible with: PostgreSQL 13+
-- ============================================================

-- Drop if exists (idempotent deploy)
DROP PROCEDURE IF EXISTS sp_generate_weekly_report(DATE, DATE);

CREATE OR REPLACE PROCEDURE sp_generate_weekly_report(
    p_week_start DATE,
    p_week_end   DATE
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_total_revenue  NUMERIC(14,2);
    v_total_units    INT;
    v_open_tickets   INT;
    v_resolved_pct   NUMERIC(5,2);
BEGIN

    RAISE NOTICE '====================================================';
    RAISE NOTICE 'Weekly Report  |  % → %', p_week_start, p_week_end;
    RAISE NOTICE '====================================================';

    -- ── 1. Sales summary ──────────────────────────────────────────────────
    SELECT
        COALESCE(SUM(revenue), 0),
        COALESCE(SUM(units_sold), 0)
    INTO v_total_revenue, v_total_units
    FROM sales
    WHERE sale_date BETWEEN p_week_start AND p_week_end;

    RAISE NOTICE '[Sales] Total Revenue : $%', v_total_revenue;
    RAISE NOTICE '[Sales] Units Sold    : %',  v_total_units;

    -- ── 2. Revenue by region ──────────────────────────────────────────────
    RAISE NOTICE '--- Revenue by Region ---';
    FOR r IN
        SELECT region, SUM(revenue) AS rev
        FROM   sales
        WHERE  sale_date BETWEEN p_week_start AND p_week_end
        GROUP  BY region
        ORDER  BY rev DESC
    LOOP
        RAISE NOTICE '  %-10s  $%', r.region, r.rev;
    END LOOP;

    -- ── 3. Top products ───────────────────────────────────────────────────
    RAISE NOTICE '--- Top Products ---';
    FOR r IN
        SELECT product, SUM(revenue) AS rev, SUM(units_sold) AS units
        FROM   sales
        WHERE  sale_date BETWEEN p_week_start AND p_week_end
        GROUP  BY product
        ORDER  BY rev DESC
        LIMIT  5
    LOOP
        RAISE NOTICE '  %-20s  $%  (%  units)', r.product, r.rev, r.units;
    END LOOP;

    -- ── 4. Support tickets ────────────────────────────────────────────────
    SELECT COUNT(*) INTO v_open_tickets
    FROM   support_tickets
    WHERE  created_date BETWEEN p_week_start AND p_week_end
    AND    status = 'open';

    SELECT
        ROUND(
            100.0 * SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(*), 0),
        2)
    INTO v_resolved_pct
    FROM support_tickets
    WHERE created_date BETWEEN p_week_start AND p_week_end;

    RAISE NOTICE '[Support] Open Tickets      : %', v_open_tickets;
    RAISE NOTICE '[Support] Resolution Rate   : %  %%', v_resolved_pct;

    -- ── 5. Write to audit log ─────────────────────────────────────────────
    INSERT INTO report_run_log (report_type, period_start, period_end,
                                 total_revenue, units_sold, ran_at)
    VALUES ('weekly', p_week_start, p_week_end,
             v_total_revenue, v_total_units, NOW())
    ON CONFLICT DO NOTHING;

    RAISE NOTICE '====================================================';
    RAISE NOTICE 'Weekly report procedure completed.';
    RAISE NOTICE '====================================================';

END;
$$;


-- ── Audit log table (run once) ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS report_run_log (
    id            SERIAL PRIMARY KEY,
    report_type   TEXT        NOT NULL,
    period_start  DATE        NOT NULL,
    period_end    DATE        NOT NULL,
    total_revenue NUMERIC(14,2),
    units_sold    INT,
    ran_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (report_type, period_start, period_end)
);


-- ── Example usage ─────────────────────────────────────────────────────────────
-- CALL sp_generate_weekly_report(
--     DATE_TRUNC('week', CURRENT_DATE)::DATE - 7,
--     DATE_TRUNC('week', CURRENT_DATE)::DATE - 1
-- );
