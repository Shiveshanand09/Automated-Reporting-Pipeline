-- ============================================================
--  sp_monthly_report.sql
--  Stored procedure: Monthly Executive Summary
--  Compatible with: PostgreSQL 13+
-- ============================================================

DROP PROCEDURE IF EXISTS sp_generate_monthly_report(INT, INT);

CREATE OR REPLACE PROCEDURE sp_generate_monthly_report(
    p_year  INT,
    p_month INT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_month_start    DATE := MAKE_DATE(p_year, p_month, 1);
    v_month_end      DATE := (MAKE_DATE(p_year, p_month, 1) + INTERVAL '1 month - 1 day')::DATE;
    v_total_revenue  NUMERIC(14,2);
    v_prev_revenue   NUMERIC(14,2);
    v_mom_pct        NUMERIC(6,2);
    v_total_spend    NUMERIC(14,2);
    v_roas           NUMERIC(8,4);
BEGIN

    RAISE NOTICE '====================================================';
    RAISE NOTICE 'Monthly Executive Report  |  %-%', p_year, LPAD(p_month::TEXT, 2, '0');
    RAISE NOTICE 'Period: % → %', v_month_start, v_month_end;
    RAISE NOTICE '====================================================';

    -- ── 1. Revenue ────────────────────────────────────────────────────────
    SELECT COALESCE(SUM(revenue), 0)
    INTO   v_total_revenue
    FROM   sales
    WHERE  sale_date BETWEEN v_month_start AND v_month_end;

    -- Previous month
    SELECT COALESCE(SUM(revenue), 0)
    INTO   v_prev_revenue
    FROM   sales
    WHERE  sale_date BETWEEN (v_month_start - INTERVAL '1 month')::DATE
                         AND (v_month_end   - INTERVAL '1 month')::DATE;

    v_mom_pct := CASE
        WHEN v_prev_revenue = 0 THEN NULL
        ELSE ROUND(100.0 * (v_total_revenue - v_prev_revenue) / v_prev_revenue, 2)
    END;

    RAISE NOTICE '[Revenue] This Month : $%',   v_total_revenue;
    RAISE NOTICE '[Revenue] Last Month : $%',   v_prev_revenue;
    RAISE NOTICE '[Revenue] MoM Change : % %%', COALESCE(v_mom_pct::TEXT, 'N/A');

    -- ── 2. Top regions ────────────────────────────────────────────────────
    RAISE NOTICE '--- Top Regions ---';
    FOR r IN
        SELECT region, SUM(revenue) AS rev,
               ROUND(100.0 * SUM(revenue) / NULLIF(v_total_revenue,0), 1) AS pct
        FROM   sales
        WHERE  sale_date BETWEEN v_month_start AND v_month_end
        GROUP  BY region
        ORDER  BY rev DESC
        LIMIT  5
    LOOP
        RAISE NOTICE '  %-10s  $%  (% %%)', r.region, r.rev, r.pct;
    END LOOP;

    -- ── 3. Marketing & ROAS ───────────────────────────────────────────────
    SELECT COALESCE(SUM(spend), 0)
    INTO   v_total_spend
    FROM   marketing_spend
    WHERE  spend_date BETWEEN v_month_start AND v_month_end;

    v_roas := CASE
        WHEN v_total_spend = 0 THEN NULL
        ELSE ROUND(v_total_revenue / v_total_spend, 4)
    END;

    RAISE NOTICE '[Marketing] Total Spend : $%',  v_total_spend;
    RAISE NOTICE '[Marketing] ROAS        : %x', COALESCE(v_roas::TEXT, 'N/A');

    -- ── 4. Channel performance ────────────────────────────────────────────
    RAISE NOTICE '--- Channel Performance ---';
    FOR r IN
        SELECT channel,
               SUM(spend)       AS spend,
               SUM(clicks)      AS clicks,
               SUM(impressions) AS impressions,
               ROUND(100.0 * SUM(clicks) / NULLIF(SUM(impressions),0), 2) AS ctr
        FROM   marketing_spend
        WHERE  spend_date BETWEEN v_month_start AND v_month_end
        GROUP  BY channel
        ORDER  BY spend DESC
    LOOP
        RAISE NOTICE '  %-10s  spend=$%  CTR=% %%', r.channel, r.spend, r.ctr;
    END LOOP;

    -- ── 5. Support health ─────────────────────────────────────────────────
    FOR r IN
        SELECT status, COUNT(*) AS cnt
        FROM   support_tickets
        WHERE  created_date BETWEEN v_month_start AND v_month_end
        GROUP  BY status
    LOOP
        RAISE NOTICE '[Support] %-12s : %', r.status, r.cnt;
    END LOOP;

    -- ── 6. Audit log ──────────────────────────────────────────────────────
    INSERT INTO report_run_log (report_type, period_start, period_end,
                                 total_revenue, ran_at)
    VALUES ('monthly', v_month_start, v_month_end, v_total_revenue, NOW())
    ON CONFLICT DO NOTHING;

    RAISE NOTICE '====================================================';
    RAISE NOTICE 'Monthly report procedure completed.';
    RAISE NOTICE '====================================================';

END;
$$;


-- ── Example usage ─────────────────────────────────────────────────────────────
-- CALL sp_generate_monthly_report(
--     EXTRACT(YEAR  FROM CURRENT_DATE - INTERVAL '1 month')::INT,
--     EXTRACT(MONTH FROM CURRENT_DATE - INTERVAL '1 month')::INT
-- );
