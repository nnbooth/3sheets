#!/usr/bin/env python3
"""Create reporting views for the legal finance transaction model.

Quick summary:
- This script creates/refreshes PostgreSQL reporting views.
- It reads existing tables in the legal schema.
- It does not generate new transactional rows.

Targets PostgreSQL database portfolio_data.
"""

import os
from pathlib import Path

import psycopg

SCRIPT_DIR = Path(__file__).resolve().parent
LEGAL_DIR = SCRIPT_DIR.parent
PGHOST = os.getenv("PGHOST", "127.0.0.1")
PGPORT = int(os.getenv("PGPORT", "5432"))
PGDATABASE = os.getenv("PGDATABASE", "portfolio_data")
PGUSER = os.getenv("PGUSER", os.getenv("USER", "postgres"))
PGPASSWORD = os.getenv("PGPASSWORD", "")
PGSCHEMA = os.getenv("PGSCHEMA", "legal")

VIEW_SQL = [
    """
    DROP VIEW IF EXISTS vw_matter_financials;
    CREATE VIEW vw_matter_financials AS
    SELECT
        fm.matter_id,
        dm.matter_reference,
        dm.matter_name,
        dm.client_id,
        dc.client_name,
        dc.client_segment,
        fm.practice_area_id,
        pa.practice_area_name,
        fm.fee_earner_id,
        fe.name AS fee_earner_name,
        fe.role AS fee_earner_role,
        fm.referral_source_id,
        rs.source_name AS referral_source_name,
        fm.open_date,
        fm.close_date,
        d_open.year AS open_year,
        d_open.month AS open_month,
        d_open.quarter AS open_quarter,
        d_open.financial_year AS open_financial_year,
        d_close.year AS close_year,
        d_close.month AS close_month,
        d_close.quarter AS close_quarter,
        d_close.financial_year AS close_financial_year,
        fm.status,
        fm.fee_type,
        fm.estimated_claim_value,
        fm.settlement_value,
        fm.legal_fees_billed,
        fm.disbursements_paid,
        fm.amount_collected,
        fm.write_off_amount,
        CASE WHEN fm.legal_fees_billed > 0 THEN fm.amount_collected / fm.legal_fees_billed END AS realization_rate,
        CASE WHEN fm.legal_fees_billed > 0 THEN fm.write_off_amount / fm.legal_fees_billed END AS write_off_rate,
        CASE WHEN fm.estimated_claim_value > 0 THEN fm.settlement_value / fm.estimated_claim_value END AS settlement_to_estimate_ratio,
        CASE WHEN fm.open_date IS NOT NULL AND fm.close_date IS NOT NULL THEN (fm.close_date::date - fm.open_date::date) END AS matter_age_days,
        CASE WHEN fm.status = 'Open' THEN 1 ELSE 0 END AS is_open,
        CASE WHEN fm.status = 'Settled' THEN 1 ELSE 0 END AS is_settled,
        CASE WHEN fm.status LIKE 'Trial%' THEN 1 ELSE 0 END AS is_trial,
        CASE WHEN fm.fee_type = 'No Win No Fee' THEN 1 ELSE 0 END AS is_nwnf
    FROM fact_matter fm
    LEFT JOIN dim_matter dm ON fm.matter_id = dm.matter_id
    LEFT JOIN dim_client dc ON dm.client_id = dc.client_id
    LEFT JOIN dim_practice_area pa ON fm.practice_area_id = pa.practice_area_id
    LEFT JOIN dim_fee_earner fe ON fm.fee_earner_id = fe.fee_earner_id
    LEFT JOIN dim_referral_source rs ON fm.referral_source_id = rs.referral_source_id
    LEFT JOIN dim_date d_open ON fm.open_date = d_open.date
    LEFT JOIN dim_date d_close ON fm.close_date = d_close.date;
    """,
    """
    DROP VIEW IF EXISTS vw_work_performed;
    CREATE VIEW vw_work_performed AS
    SELECT
        wp.timecard_id,
        wp.matter_id,
        dm.matter_reference,
        dm.matter_name,
        dm.client_id,
        dc.client_name,
        dc.client_segment,
        wp.work_date,
        wp.ledger_date,
        wp.ledger_date AS period_date,
        d.year,
        d.month,
        d.month_name,
        d.quarter,
        d.financial_year,
        to_char(make_date(d.year::int, d.month::int, 1), 'YYYY-MM-DD') AS year_month,
        wp.fee_earner_id,
        fe.name AS fee_earner_name,
        fe.role AS fee_earner_role,
        fe.hourly_rate,
        dm.practice_area_id,
        dm.practice_area_name,
        dm.referral_source_id,
        rs.source_name AS referral_source_name,
        wp.hours_worked,
        wp.work_value_generated,
        wp.narrative
    FROM fact_work_performed wp
    LEFT JOIN dim_matter dm ON wp.matter_id = dm.matter_id
    LEFT JOIN dim_client dc ON dm.client_id = dc.client_id
    LEFT JOIN dim_fee_earner fe ON wp.fee_earner_id = fe.fee_earner_id
    LEFT JOIN dim_practice_area pa ON dm.practice_area_id = pa.practice_area_id
    LEFT JOIN dim_referral_source rs ON dm.referral_source_id = rs.referral_source_id
    LEFT JOIN dim_date d ON wp.work_date = d.date;
    """,
    """
    DROP VIEW IF EXISTS vw_billing_line_items;
    CREATE VIEW vw_billing_line_items AS
    SELECT
        b.billing_id,
        b.timecard_id,
        b.matter_id,
        dm.matter_reference,
        dm.matter_name,
        dm.client_id,
        dc.client_name,
        dc.client_segment,
        b.billing_date,
        b.ledger_date,
        b.ledger_date AS period_date,
        d.year,
        d.month,
        d.month_name,
        d.quarter,
        d.financial_year,
        to_char(make_date(d.year::int, d.month::int, 1), 'YYYY-MM-DD') AS year_month,
        b.fee_earner_id,
        fe.name AS fee_earner_name,
        fe.role AS fee_earner_role,
        fe.hourly_rate,
        dm.practice_area_id,
        dm.practice_area_name,
        dm.referral_source_id,
        rs.source_name AS referral_source_name,
        wp.work_date,
        wp.narrative AS work_narrative,
        b.billed_hours,
        b.billed_rate,
        b.billed_amount,
        b.writeoff_amount,
        b.billing_status,
        b.billing_narrative,
        CASE WHEN b.billing_status = 'Written Off' THEN 1 ELSE 0 END AS is_writeoff
    FROM fact_billing b
    LEFT JOIN fact_work_performed wp ON b.timecard_id = wp.timecard_id
    LEFT JOIN dim_matter dm ON b.matter_id = dm.matter_id
    LEFT JOIN dim_client dc ON dm.client_id = dc.client_id
    LEFT JOIN dim_fee_earner fe ON b.fee_earner_id = fe.fee_earner_id
    LEFT JOIN dim_practice_area pa ON dm.practice_area_id = pa.practice_area_id
    LEFT JOIN dim_referral_source rs ON dm.referral_source_id = rs.referral_source_id
    LEFT JOIN dim_date d ON b.ledger_date = d.date;
    """,
    """
    DROP VIEW IF EXISTS vw_wip_ledger_transactions;
    CREATE VIEW vw_wip_ledger_transactions AS
    SELECT
        wp.timecard_id,
        NULL AS billing_id,
        wp.matter_id,
        wp.matter_reference,
        wp.matter_name,
        wp.client_id,
        wp.client_name,
        wp.client_segment,
        wp.practice_area_id,
        wp.practice_area_name,
        wp.fee_earner_id,
        wp.fee_earner_name,
        wp.fee_earner_role,
        wp.work_date AS transaction_date,
        wp.ledger_date,
        'Work' AS transaction_type,
        wp.hours_worked,
        wp.work_value_generated AS work_value,
        0.0 AS billed_amount,
        0.0 AS writeoff_amount,
        wp.work_value_generated AS signed_wip_delta,
        wp.narrative AS narrative
    FROM vw_work_performed wp
    UNION ALL
    SELECT
        bl.timecard_id,
        bl.billing_id,
        bl.matter_id,
        bl.matter_reference,
        bl.matter_name,
        bl.client_id,
        bl.client_name,
        bl.client_segment,
        bl.practice_area_id,
        bl.practice_area_name,
        bl.fee_earner_id,
        bl.fee_earner_name,
        bl.fee_earner_role,
        bl.billing_date AS transaction_date,
        bl.ledger_date,
        CASE WHEN bl.is_writeoff = 1 THEN 'Writeoff' ELSE 'Billing' END AS transaction_type,
        -bl.billed_hours AS hours_worked,
        0.0 AS work_value,
        bl.billed_amount AS billed_amount,
        bl.writeoff_amount AS writeoff_amount,
        -(bl.billed_amount + bl.writeoff_amount) AS signed_wip_delta,
        bl.billing_narrative AS narrative
    FROM vw_billing_line_items bl;
    """,
    """
    DROP VIEW IF EXISTS vw_matter_wip_balance_daily;
    CREATE VIEW vw_matter_wip_balance_daily AS
    WITH daily AS (
        SELECT
            matter_id,
            matter_reference,
            matter_name,
            client_id,
            client_name,
            client_segment,
            practice_area_id,
            practice_area_name,
            fee_earner_id,
            fee_earner_name,
            fee_earner_role,
            ledger_date,
            SUM(signed_wip_delta) AS daily_delta,
            SUM(CASE WHEN transaction_type = 'Work' THEN work_value ELSE 0 END) AS daily_work_value,
            SUM(CASE WHEN transaction_type = 'Billing' THEN billed_amount ELSE 0 END) AS daily_billed_amount,
            SUM(CASE WHEN transaction_type = 'Writeoff' THEN writeoff_amount ELSE 0 END) AS daily_writeoff_amount
        FROM vw_wip_ledger_transactions
        GROUP BY
            matter_id,
            matter_reference,
            matter_name,
            client_id,
            client_name,
            client_segment,
            practice_area_id,
            practice_area_name,
            fee_earner_id,
            fee_earner_name,
            fee_earner_role,
            ledger_date
    )
    SELECT
        daily.*,
        cal.year,
        cal.month,
        cal.month_name,
        cal.quarter,
        cal.financial_year,
        SUM(daily_delta) OVER (
            PARTITION BY matter_id
            ORDER BY ledger_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS wip_balance,
        SUM(daily_work_value) OVER (
            PARTITION BY matter_id
            ORDER BY ledger_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_work_value,
        SUM(daily_billed_amount) OVER (
            PARTITION BY matter_id
            ORDER BY ledger_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_billed_amount,
        SUM(daily_writeoff_amount) OVER (
            PARTITION BY matter_id
            ORDER BY ledger_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_writeoff_amount
    FROM daily
    LEFT JOIN dim_date cal ON daily.ledger_date = cal.date;
    """,
    """
    DROP VIEW IF EXISTS vw_matter_recoverability;
    CREATE VIEW vw_matter_recoverability AS
    WITH work_totals AS (
        SELECT
            matter_id,
            matter_reference,
            matter_name,
            client_id,
            client_name,
            client_segment,
            practice_area_id,
            practice_area_name,
            fee_earner_id,
            fee_earner_name,
            fee_earner_role,
            COUNT(*) AS timecards_worked,
            MIN(work_date) AS first_work_date,
            MAX(work_date) AS last_work_date,
            SUM(hours_worked) AS total_work_hours,
            SUM(work_value_generated) AS total_work_value
        FROM vw_work_performed
        GROUP BY
            matter_id,
            matter_reference,
            matter_name,
            client_id,
            client_name,
            client_segment,
            practice_area_id,
            practice_area_name,
            fee_earner_id,
            fee_earner_name,
            fee_earner_role
    ),
    bill_totals AS (
        SELECT
            matter_id,
            SUM(billed_hours) AS total_billed_hours,
            SUM(billed_amount) AS total_billed_amount,
            SUM(writeoff_amount) AS total_writeoff_amount,
            SUM(CASE WHEN is_writeoff = 1 THEN 1 ELSE 0 END) AS written_off_timecards,
            SUM(CASE WHEN is_writeoff = 0 THEN 1 ELSE 0 END) AS billed_timecards
        FROM vw_billing_line_items
        GROUP BY matter_id
    ),
    latest_balance AS (
        SELECT *
        FROM (
            SELECT
                matter_id,
                matter_reference,
                matter_name,
                client_id,
                client_name,
                client_segment,
                practice_area_id,
                practice_area_name,
                fee_earner_id,
                fee_earner_name,
                fee_earner_role,
                ledger_date,
                wip_balance,
                ROW_NUMBER() OVER (PARTITION BY matter_id ORDER BY ledger_date DESC) AS rn
            FROM vw_matter_wip_balance_daily
        )
        WHERE rn = 1
    )
    SELECT
        work_totals.*,
        COALESCE(bill_totals.total_billed_hours, 0) AS total_billed_hours,
        COALESCE(bill_totals.total_billed_amount, 0) AS total_billed_amount,
        COALESCE(bill_totals.total_writeoff_amount, 0) AS total_writeoff_amount,
        COALESCE(bill_totals.written_off_timecards, 0) AS written_off_timecards,
        COALESCE(bill_totals.billed_timecards, 0) AS billed_timecards,
        COALESCE(latest_balance.wip_balance, 0) AS latest_wip_balance,
        CASE WHEN work_totals.total_work_value > 0 THEN COALESCE(bill_totals.total_billed_amount, 0) / work_totals.total_work_value END AS billed_value_recoverability,
        CASE WHEN work_totals.total_work_hours > 0 THEN COALESCE(bill_totals.total_billed_hours, 0) / work_totals.total_work_hours END AS billed_hour_recoverability,
        CASE WHEN work_totals.total_work_value > 0 THEN COALESCE(bill_totals.total_writeoff_amount, 0) / work_totals.total_work_value END AS writeoff_rate
    FROM work_totals
    LEFT JOIN bill_totals ON work_totals.matter_id = bill_totals.matter_id
    LEFT JOIN latest_balance ON work_totals.matter_id = latest_balance.matter_id;
    """,
    """
    DROP VIEW IF EXISTS vw_practice_area_health;
    CREATE VIEW vw_practice_area_health AS
    SELECT
        practice_area_id,
        practice_area_name,
        fee_type,
        COUNT(*) AS matter_count,
        SUM(legal_fees_billed) AS total_billed_fees,
        SUM(amount_collected) AS total_collected_fees,
        SUM(settlement_value) AS total_settlement_value,
        AVG(realization_rate) AS avg_realization_rate,
        AVG(settlement_to_estimate_ratio) AS avg_settlement_to_estimate_ratio,
        SUM(write_off_amount) AS total_write_off_amount
    FROM vw_matter_financials
    GROUP BY practice_area_id, practice_area_name, fee_type;
    """,
    """
    DROP VIEW IF EXISTS vw_referral_quality;
    CREATE VIEW vw_referral_quality AS
    SELECT
        referral_source_id,
        referral_source_name,
        practice_area_id,
        practice_area_name,
        fee_type,
        COUNT(*) AS matter_count,
        SUM(settlement_value) AS total_settlement_value,
        AVG(settlement_value) AS avg_settlement_value,
        AVG(estimated_claim_value) AS avg_estimated_claim_value,
        SUM(legal_fees_billed) AS total_billed_fees,
        SUM(amount_collected) AS total_collected_fees,
        AVG(realization_rate) AS avg_realization_rate,
        SUM(write_off_amount) AS total_write_off_amount
    FROM vw_matter_financials
    GROUP BY referral_source_id, referral_source_name, practice_area_id, practice_area_name, fee_type;
    """,
    """
    DROP VIEW IF EXISTS vw_fee_earner_performance;
    CREATE VIEW vw_fee_earner_performance AS
    WITH billing_by_earner AS (
        SELECT
            fee_earner_id,
            SUM(billed_amount) AS total_billed_revenue,
            SUM(writeoff_amount) AS total_writeoff_amount,
            SUM(CASE WHEN is_writeoff = 1 THEN 1 ELSE 0 END) AS written_off_timecards
        FROM vw_billing_line_items
        GROUP BY fee_earner_id
    )
    SELECT
        wp.fee_earner_id,
        wp.fee_earner_name,
        wp.fee_earner_role,
        wp.practice_area_id,
        wp.practice_area_name,
        COUNT(*) AS timecards_worked,
        COUNT(DISTINCT wp.matter_id) AS matters_worked,
        SUM(wp.hours_worked) AS total_work_hours,
        SUM(wp.work_value_generated) AS total_work_value,
        COALESCE(MAX(be.total_billed_revenue), 0) AS total_billed_revenue,
        COALESCE(MAX(be.total_writeoff_amount), 0) AS total_writeoff_amount,
        COALESCE(MAX(be.written_off_timecards), 0) AS written_off_timecards,
        CASE WHEN SUM(wp.work_value_generated) > 0 THEN COALESCE(MAX(be.total_billed_revenue), 0) / SUM(wp.work_value_generated) END AS value_recoverability,
        CASE WHEN SUM(wp.hours_worked) > 0 THEN COALESCE(MAX(be.total_billed_revenue), 0) / SUM(wp.hours_worked) END AS revenue_per_work_hour
    FROM vw_work_performed wp
    LEFT JOIN billing_by_earner be ON wp.fee_earner_id = be.fee_earner_id
    GROUP BY
        wp.fee_earner_id,
        wp.fee_earner_name,
        wp.fee_earner_role,
        wp.practice_area_id,
        wp.practice_area_name;
    """,
    """
    DROP VIEW IF EXISTS vw_fee_earner_budget_monthly;
    CREATE VIEW vw_fee_earner_budget_monthly AS
    WITH work_monthly AS (
        SELECT
            fee_earner_id,
            year,
            month,
            financial_year,
            SUM(hours_worked) AS actual_hours
        FROM vw_work_performed
        GROUP BY fee_earner_id, year, month, financial_year
    ),
    billing_monthly AS (
        SELECT
            fee_earner_id,
            year,
            month,
            financial_year,
            SUM(billed_amount) AS actual_billed_revenue,
            SUM(writeoff_amount) AS actual_writeoff_amount
        FROM vw_billing_line_items
        GROUP BY fee_earner_id, year, month, financial_year
    )
    SELECT
        b.budget_id,
        b.fee_earner_id,
        fe.name AS fee_earner_name,
        fe.role AS fee_earner_role,
        b.practice_area_id,
        pa.practice_area_name,
        to_char(make_date(b.year::int, b.month::int, 1), 'YYYY-MM-DD') AS period_date,
        b.year,
        b.month,
        b.month_name,
        b.financial_year,
        b.workdays_in_month,
        b.budget_hours,
        b.budget_revenue,
        COALESCE(w.actual_hours, 0) AS actual_hours,
        COALESCE(bl.actual_billed_revenue, 0) AS actual_billed_revenue,
        COALESCE(bl.actual_writeoff_amount, 0) AS actual_writeoff_amount,
        CASE WHEN b.budget_hours > 0 THEN COALESCE(w.actual_hours, 0) / b.budget_hours END AS hours_to_budget_ratio,
        CASE WHEN b.budget_revenue > 0 THEN COALESCE(bl.actual_billed_revenue, 0) / b.budget_revenue END AS revenue_to_budget_ratio,
        COALESCE(w.actual_hours, 0) - b.budget_hours AS hours_variance_vs_budget,
        COALESCE(bl.actual_billed_revenue, 0) - b.budget_revenue AS revenue_variance_vs_budget
    FROM fact_fee_earner_budget_monthly b
    LEFT JOIN dim_fee_earner fe ON b.fee_earner_id = fe.fee_earner_id
    LEFT JOIN dim_practice_area pa ON b.practice_area_id = pa.practice_area_id
    LEFT JOIN work_monthly w
      ON b.fee_earner_id = w.fee_earner_id
     AND b.year = w.year
     AND b.month = w.month
     AND b.financial_year = w.financial_year
    LEFT JOIN billing_monthly bl
      ON b.fee_earner_id = bl.fee_earner_id
     AND b.year = bl.year
     AND b.month = bl.month
     AND b.financial_year = bl.financial_year;
    """,
    """
    DROP VIEW IF EXISTS vw_matter_wip_balance_month_end;
    CREATE VIEW vw_matter_wip_balance_month_end AS
    WITH month_ends AS (
        SELECT
            year,
            month,
            month_name,
            quarter,
            financial_year,
            MAX(date) AS period_date
        FROM dim_date
        GROUP BY year, month, month_name, quarter, financial_year
    ),
    matters AS (
        SELECT DISTINCT
            matter_id,
            matter_reference,
            matter_name,
            client_id,
            client_name,
            client_segment,
            practice_area_id,
            practice_area_name,
            fee_earner_id,
            fee_earner_name,
            fee_earner_role
        FROM vw_matter_wip_balance_daily
    ),
    scaffold AS (
        SELECT
            m.matter_id,
            m.matter_reference,
            m.matter_name,
            m.client_id,
            m.client_name,
            m.client_segment,
            m.practice_area_id,
            m.practice_area_name,
            m.fee_earner_id,
            m.fee_earner_name,
            m.fee_earner_role,
            me.year,
            me.month,
            me.month_name,
            me.quarter,
            me.financial_year,
            me.period_date
        FROM matters m
        CROSS JOIN month_ends me
    ),
    ranked AS (
        SELECT
            scaffold.*,
            daily.ledger_date AS balance_date,
            daily.daily_delta,
            daily.daily_work_value,
            daily.daily_billed_amount,
            daily.daily_writeoff_amount,
            daily.wip_balance,
            daily.cumulative_work_value,
            daily.cumulative_billed_amount,
            daily.cumulative_writeoff_amount,
            ROW_NUMBER() OVER (
                PARTITION BY scaffold.matter_id, scaffold.year, scaffold.month
                ORDER BY daily.ledger_date DESC
            ) AS rn
        FROM scaffold
        LEFT JOIN vw_matter_wip_balance_daily daily
            ON daily.matter_id = scaffold.matter_id
           AND daily.ledger_date <= scaffold.period_date
    )
    SELECT
        matter_id,
        matter_reference,
        matter_name,
        client_id,
        client_name,
        client_segment,
        practice_area_id,
        practice_area_name,
        fee_earner_id,
        fee_earner_name,
        fee_earner_role,
        year,
        month,
        month_name,
        quarter,
        financial_year,
        period_date,
        balance_date,
        COALESCE(daily_delta, 0) AS daily_delta,
        COALESCE(daily_work_value, 0) AS daily_work_value,
        COALESCE(daily_billed_amount, 0) AS daily_billed_amount,
        COALESCE(daily_writeoff_amount, 0) AS daily_writeoff_amount,
        COALESCE(wip_balance, 0) AS wip_balance,
        COALESCE(cumulative_work_value, 0) AS cumulative_work_value,
        COALESCE(cumulative_billed_amount, 0) AS cumulative_billed_amount,
        COALESCE(cumulative_writeoff_amount, 0) AS cumulative_writeoff_amount
    FROM ranked
    WHERE rn = 1;
    """,
    """
    DROP VIEW IF EXISTS vw_wip_total_gl_period_end;
    CREATE VIEW vw_wip_total_gl_period_end AS
    WITH daily_totals AS (
        SELECT
            ledger_date,
            SUM(signed_wip_delta) AS daily_wip_delta
        FROM vw_wip_ledger_transactions
        GROUP BY ledger_date
    ),
    running_total AS (
        SELECT
            ledger_date,
            SUM(daily_wip_delta) OVER (
                ORDER BY ledger_date
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) AS total_wip_balance
        FROM daily_totals
    ),
    month_ends AS (
        SELECT
            year,
            month,
            month_name,
            quarter,
            financial_year,
            MAX(date) AS period_date
        FROM dim_date
        GROUP BY year, month, month_name, quarter, financial_year
    ),
    ranked AS (
        SELECT
            me.year,
            me.month,
            me.month_name,
            me.quarter,
            me.financial_year,
            me.period_date,
            rt.ledger_date AS balance_date,
            rt.total_wip_balance,
            ROW_NUMBER() OVER (
                PARTITION BY me.year, me.month
                ORDER BY rt.ledger_date DESC
            ) AS rn
        FROM month_ends me
        LEFT JOIN running_total rt
            ON rt.ledger_date <= me.period_date
    )
    SELECT
        year,
        month,
        month_name,
        quarter,
        financial_year,
        period_date,
        balance_date,
        COALESCE(total_wip_balance, 0) AS total_wip_balance
    FROM ranked
    WHERE rn = 1;
    """,
    """
    DROP VIEW IF EXISTS vw_fee_earner_department_performance;
    CREATE VIEW vw_fee_earner_department_performance AS
    WITH monthly AS (
        SELECT
            fee_earner_id,
            fee_earner_name,
            fee_earner_role,
            practice_area_id,
            practice_area_name,
            year_month,
            year,
            month,
            financial_year,
            COUNT(*) AS timecards_worked,
            COUNT(DISTINCT matter_id) AS matters_worked,
            SUM(hours_worked) AS hours_worked,
            SUM(work_value_generated) AS work_value
        FROM vw_work_performed
        GROUP BY
            fee_earner_id,
            fee_earner_name,
            fee_earner_role,
            practice_area_id,
            practice_area_name,
            year_month,
            year,
            month,
            financial_year
    ),
    billed_monthly AS (
        SELECT
            fee_earner_id,
            year_month,
            SUM(billed_amount) AS billed_revenue
        FROM vw_billing_line_items
        GROUP BY fee_earner_id, year_month
    )
    SELECT
        monthly.*,
        COALESCE(billed_monthly.billed_revenue, 0) AS billed_revenue,
        CASE WHEN monthly.work_value > 0 THEN COALESCE(billed_monthly.billed_revenue, 0) / monthly.work_value END AS value_recoverability,
        COUNT(*) OVER (PARTITION BY monthly.practice_area_id, monthly.year_month) AS fee_earners_in_department_month,
        RANK() OVER (
            PARTITION BY monthly.practice_area_id, monthly.year_month
            ORDER BY monthly.hours_worked DESC, COALESCE(billed_monthly.billed_revenue, 0) DESC
        ) AS rank_in_department_by_hours,
        SUM(monthly.hours_worked) OVER (PARTITION BY monthly.fee_earner_id, monthly.year) AS ytd_hours_worked,
        SUM(COALESCE(billed_monthly.billed_revenue, 0)) OVER (PARTITION BY monthly.fee_earner_id, monthly.year) AS ytd_billed_revenue
    FROM monthly
    LEFT JOIN billed_monthly
      ON monthly.fee_earner_id = billed_monthly.fee_earner_id
     AND monthly.year_month = billed_monthly.year_month;
    """,
    """
    DROP VIEW IF EXISTS vw_yesterday_activity;
    CREATE VIEW vw_yesterday_activity AS
    WITH latest_activity AS (
        SELECT MAX(activity_date) AS activity_date
        FROM (
            SELECT work_date AS activity_date FROM vw_work_performed
            UNION ALL
            SELECT ledger_date AS activity_date FROM vw_billing_line_items
        )
    ),
    work_daily AS (
        SELECT
            work_date AS activity_date,
            COUNT(*) AS timecards_worked,
            COUNT(DISTINCT matter_id) AS matters_worked,
            SUM(hours_worked) AS hours_worked,
            SUM(work_value_generated) AS work_value
        FROM vw_work_performed
        GROUP BY work_date
    ),
    billing_daily AS (
        SELECT
            ledger_date AS activity_date,
            SUM(billed_amount) AS billed_revenue,
            SUM(writeoff_amount) AS writeoff_amount,
            SUM(CASE WHEN is_writeoff = 1 THEN 1 ELSE 0 END) AS written_off_timecards
        FROM vw_billing_line_items
        GROUP BY ledger_date
    )
    SELECT
        latest_activity.activity_date,
        d.year,
        d.month,
        d.month_name,
        d.quarter,
        d.financial_year,
        COALESCE(work_daily.timecards_worked, 0) AS timecards_worked,
        COALESCE(work_daily.matters_worked, 0) AS matters_worked,
        COALESCE(work_daily.hours_worked, 0) AS hours_worked,
        COALESCE(work_daily.work_value, 0) AS work_value,
        COALESCE(billing_daily.billed_revenue, 0) AS billed_revenue,
        COALESCE(billing_daily.writeoff_amount, 0) AS writeoff_amount,
        COALESCE(billing_daily.written_off_timecards, 0) AS written_off_timecards
    FROM latest_activity
    LEFT JOIN dim_date d ON latest_activity.activity_date = d.date
    LEFT JOIN work_daily ON latest_activity.activity_date = work_daily.activity_date
    LEFT JOIN billing_daily ON latest_activity.activity_date = billing_daily.activity_date;
    """,
]


def main() -> None:
    with psycopg.connect(
        host=PGHOST,
        port=PGPORT,
        dbname=PGDATABASE,
        user=PGUSER,
        password=PGPASSWORD,
        autocommit=True,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {PGSCHEMA}")
            cur.execute(f"SET search_path TO {PGSCHEMA}, public")

            pending = list(VIEW_SQL)
            max_passes = 4
            for _ in range(max_passes):
                next_pending = []
                progressed = 0
                for statement in pending:
                    try:
                        ddl = statement.replace(
                            ";\n    CREATE VIEW",
                            " CASCADE;\n    CREATE VIEW",
                        )
                        cur.execute(ddl)
                        progressed += 1
                    except psycopg.Error:
                        next_pending.append(statement)
                if not next_pending:
                    break
                if progressed == 0:
                    raise RuntimeError("Unable to resolve view dependencies in build_legal_models.py")
                pending = next_pending

            print(f"Created business models in {PGDATABASE}.{PGSCHEMA}")
            for view_name in [
                "vw_matter_financials",
                "vw_work_performed",
                "vw_billing_line_items",
                "vw_wip_ledger_transactions",
                "vw_matter_wip_balance_daily",
                "vw_matter_wip_balance_month_end",
                "vw_wip_total_gl_period_end",
                "vw_matter_recoverability",
                "vw_practice_area_health",
                "vw_referral_quality",
                "vw_fee_earner_performance",
                "vw_fee_earner_budget_monthly",
                "vw_fee_earner_department_performance",
                "vw_yesterday_activity",
            ]:
                cur.execute(f"SELECT COUNT(*) FROM {view_name}")
                print(f"  {view_name}: {cur.fetchone()[0]} rows")

            print("\nSample KPI checks:")
            print(cur.execute("SELECT ROUND(AVG(realization_rate), 3) FROM vw_matter_financials").fetchone()[0])
            print(cur.execute("SELECT ROUND(AVG(billed_value_recoverability), 3) FROM vw_matter_recoverability").fetchone()[0])
            print(cur.execute("SELECT practice_area_name, hours_worked FROM vw_fee_earner_department_performance ORDER BY hours_worked DESC LIMIT 5").fetchall())
            print(cur.execute("SELECT activity_date, timecards_worked, hours_worked FROM vw_yesterday_activity").fetchall())



if __name__ == "__main__":
    main()
