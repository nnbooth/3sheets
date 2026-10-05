#!/usr/bin/env python3
"""
sample_data.py — the sample data behind every mock-up dashboard and report.

ONE place for the invented "Sample Co" numbers shown on the website:
  - the home-page hero dashboard (small business and not-for-profit views)
  - the live-display screens (warehouse, reception, boardroom)
  - the report previews (sales, purchasing, payroll and overtime)
  - the management-pack template (profit and loss)

Run from the repo root:   python3 tools/sample_data.py
It writes, into sample-data/:
  - one CSV per table (tidy: one row per thing, plain numbers, ISO dates)
  - schema.sql with a CREATE TABLE for each CSV (works in Azure SQL / SQL
    Server and PostgreSQL)
  - it also checks the key figures still appear in the mock-up pages, so the
    pictures and the data don't drift apart. If you change a number here,
    change the mock-up (tools/mockups/*.html or DASH_DATA in script.js) too.

All money is AUD. All data is invented sample data.
"""

import csv
import sys
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "sample-data"
MONTHS_2026 = [date(2026, m, 1) for m in range(1, 13)]

# ---------------------------------------------------------------- the data
# Each entry: table name -> (description, columns, rows)

def weeks(start, n):
    return [start + timedelta(weeks=i) for i in range(n)]

TABLES = {}

def table(name, description, columns, rows):
    TABLES[name] = (description, columns, rows)

# --- Home-page hero dashboard: small business view
table("hero_sb_kpis", "Home hero dashboard, small business view: KPI tiles (as at 30 Sep 2026).",
      ["kpi", "value", "unit", "comparison"],
      [["Cost to win a customer", 184, "AUD", "-20% on last quarter"],
       ["Profit per customer", 1240, "AUD", "+8% on last quarter"],
       ["Cash in 30 days", 42600, "AUD", "after payroll and BAS"]])
table("hero_sb_cost_to_win_monthly", "Home hero dashboard: cost to win a customer by month, against target.",
      ["month", "cost_to_win_aud", "target_aud"],
      [[m.isoformat(), v, 200] for m, v in zip(MONTHS_2026[3:9], [310, 284, 259, 231, 206, 184])])
table("hero_sb_channels", "Home hero dashboard: leads, customers won and cost to win by channel (September). Weighted cost to win = $184.",
      ["channel", "leads", "customers_won", "cost_to_win_aud"],
      [["Referrals", 42, 18, 115], ["Google ads", 61, 14, 225], ["Social", 38, 7, 280]])

# --- Home-page hero dashboard: not-for-profit view
table("hero_nfp_kpis", "Home hero dashboard, not-for-profit view: KPI tiles (as at 30 Sep 2026).",
      ["kpi", "value", "unit", "comparison"],
      [["Cost to raise a dollar", 0.18, "AUD", "-16c since April"],
       ["Cost per program hour", 62, "AUD", "+$4 on last quarter"],
       ["Cash runway", 7.5, "months", "at current spend"]])
table("hero_nfp_cost_to_raise_monthly", "Home hero dashboard: cost to raise a dollar by month, against target.",
      ["month", "cost_to_raise_dollar_aud", "target_aud"],
      [[m.isoformat(), v, 0.20] for m, v in zip(MONTHS_2026[3:9], [0.34, 0.31, 0.27, 0.24, 0.21, 0.18])])
table("hero_nfp_funding_sources", "Home hero dashboard: money raised and cost per dollar by funding source (year to date). Weighted cost per dollar = $0.18.",
      ["funding_source", "raised_aud", "share_pct", "cost_per_dollar_aud"],
      [["Grants", 120000, 59, 0.06], ["Events", 46000, 23, 0.54], ["Donations", 36000, 18, 0.12]])

# --- Live display: warehouse floor (today = 14 Oct 2026)
TODAY = date(2026, 10, 14)
table("display_warehouse_kpis", "Warehouse screen: today's despatch KPIs.",
      ["kpi", "value", "target", "unit"],
      [["Orders picked", 142, 180, "lines"], ["On time, in full", 94, 95, "percent"], ["Late inbound deliveries", 3, 0, "deliveries"]])
table("display_warehouse_picks_by_hour", "Warehouse screen: lines picked per hour today (sums to 142).",
      ["pick_date", "hour_start", "lines_picked"],
      [[TODAY.isoformat(), f"{h:02d}:00", v] for h, v in zip(range(7, 15), [12, 17, 21, 24, 19, 23, 16, 10])])
table("display_warehouse_overdue_deliveries", "Warehouse screen: overdue inbound deliveries.",
      ["supplier", "item", "days_late"],
      [["Supplier A", "Steel coil", 2], ["Supplier B", "Fasteners", 1], ["Supplier C", "Packaging", 1]])

# --- Live display: reception
table("display_reception_kpis", "Reception screen: headline numbers (October 2026).",
      ["kpi", "value", "of_total", "unit", "period"],
      [["Orders shipped", 1248, None, "orders", "month to date"], ["Delivered on time", 96, None, "percent", "last 30 days"],
       ["Team in today", 24, 31, "people", "today"]])
table("display_reception_orders_by_week", "Reception screen: orders shipped by week.",
      ["week_start", "week_label", "orders_shipped"],
      [[w.isoformat(), f"W{i + 1}", v] for i, (w, v) in enumerate(zip(weeks(date(2026, 8, 31), 7), [168, 182, 175, 196, 188, 207, 214]))])
table("display_reception_today", "Reception screen: today's list.",
      ["item", "count"],
      [["Deliveries expected", 6], ["Visitors booked", 4], ["Open jobs on the floor", 37]])

# --- Live display: boardroom management pack (October 2026)
budget = [440, 448, 455, 460, 465, 470, 474, 478, 485, 495, 500, 505]
actual = [438, 452, 470, 478, 476, 488, 492, 494, 502, 530, None, None]
forecast = [None] * 9 + [530, 528, 541]
table("display_boardroom_kpis", "Boardroom screen: management pack KPIs, year to date October 2026.",
      ["kpi", "value", "unit", "comparison"],
      [["Revenue vs budget", 3.2, "percent", "$4.82M actual vs $4.67M budget"],
       ["True gross margin", 31.4, "percent", "-2.1 pts after freight and wastage"],
       ["Customer churn", 4.1, "percent", "+0.6 pts on last quarter"],
       ["Forecast vs budget", 1.8, "percent", "rolling 12 months, driver-based"]])
table("display_boardroom_revenue_monthly", "Boardroom screen: revenue by month, $k. Actual Jan-Oct (sums to 4,820), budget Jan-Dec (Jan-Oct sums to 4,670), forecast Oct-Dec.",
      ["month", "actual_aud_k", "budget_aud_k", "forecast_aud_k"],
      [[m.isoformat(), a, b, f] for m, a, b, f in zip(MONTHS_2026, actual, budget, forecast)])
table("display_boardroom_cost_of_sale", "Boardroom screen: what a sale really costs, as a share of revenue (sums to 100).",
      ["component", "pct_of_revenue"],
      [["Materials", 36.0], ["Labour", 20.6], ["Freight", 6.5], ["Wastage", 3.5], ["Returns", 2.0], ["Left as margin", 31.4]])

# --- Report preview: sales (October 2026)
sales_months = MONTHS_2026[4:10]
table("report_sales_kpis", "Sales report: KPIs for October 2026.",
      ["kpi", "value", "unit", "comparison"],
      [["Revenue", 412300, "AUD", "+6.1% on last month"], ["Orders", 1248, "orders", "+3.4% on last month (1,207)"],
       ["Cancellation rate", 3.8, "percent", "+0.9 pts on last month"], ["Weighted pipeline", 1100000, "AUD", "next 90 days"]])
table("report_sales_revenue_monthly", "Sales report: revenue by month (chart shows $k).",
      ["month", "revenue_aud"],
      [[m.isoformat(), v] for m, v in zip(sales_months, [348000, 362000, 371000, 355000, 388600, 412300])])
table("report_sales_top_customers", "Sales report: top customers, October 2026.",
      ["customer", "revenue_aud", "change_vs_last_year_pct", "cancellation_pct"],
      [["Customer A", 68000, 12, 1.2], ["Customer B", 54000, 4, 2.0], ["Customer C", 41000, -9, 7.5], ["Customer D", 37000, 21, 0.8],
       ["Customer E", 29000, -3, 3.1], ["Customer F", 24000, 7, 1.9], ["Customer G", 19000, -14, 9.2]])
table("report_sales_cancellations_by_reason", "Sales report: cancelled orders by reason (47 of 1,248 = 3.8%).",
      ["reason", "orders_cancelled"],
      [["Late delivery", 19], ["Price", 13], ["Out of stock", 9], ["Changed mind", 6]])

# --- Report preview: purchasing (October 2026)
table("report_purchasing_kpis", "Purchasing report: KPIs for October 2026.",
      ["kpi", "value", "unit", "comparison"],
      [["Spend", 286000, "AUD", "month to date"], ["Delivered on time", 91, "percent", "-3 pts on last month"],
       ["Late purchase orders", 14, "orders", "+5 on last month"], ["Price variance", 4.2, "percent", "paid vs purchase order price"]])
table("report_purchasing_on_time_by_supplier", "Purchasing report: on-time delivery by supplier.",
      ["supplier", "on_time_pct"],
      [[f"Supplier {s}", v] for s, v in zip("ABCDEF", [78, 96, 84, 92, 97, 99])])
table("report_purchasing_late_orders", "Purchasing report: all 14 late purchase orders (the preview shows the worst 7).",
      ["po_number", "supplier", "days_late", "value_aud"],
      [["PO-1042", "Supplier A", 9, 18400], ["PO-1057", "Supplier C", 6, 6100], ["PO-1061", "Supplier A", 4, 11000],
       ["PO-1066", "Supplier D", 3, 2700], ["PO-1070", "Supplier B", 2, 4900], ["PO-1072", "Supplier C", 2, 1800],
       ["PO-1075", "Supplier E", 1, 3300], ["PO-1076", "Supplier B", 1, 2100], ["PO-1078", "Supplier F", 1, 900],
       ["PO-1079", "Supplier A", 1, 5600], ["PO-1081", "Supplier D", 1, 1400], ["PO-1082", "Supplier C", 1, 3000],
       ["PO-1084", "Supplier E", 1, 2200], ["PO-1085", "Supplier A", 1, 4400]])
table("report_purchasing_unit_cost_index", "Purchasing report: unit cost index by month (May = 100).",
      ["month", "freight_index", "steel_index"],
      [[m.isoformat(), f, s] for m, f, s in zip(sales_months, [100, 101, 104, 107, 109, 115], [100, 99, 101, 100, 103, 104])])

# --- Report preview: payroll and overtime (October 2026)
table("report_payroll_kpis", "Payroll and overtime report: KPIs for October 2026.",
      ["kpi", "value", "unit", "comparison"],
      [["Labour cost", 198000, "AUD", "month to date"], ["Overtime hours", 412, "hours", "+18% on last month"],
       ["Overtime share", 9.6, "percent", "of 4,292 hours worked"], ["Labour per job", 143, "AUD", "+$11 on last month (1,383 jobs)"]])
pay_weeks = weeks(date(2026, 9, 7), 6)
table("report_payroll_overtime_by_week", "Payroll and overtime report: overtime hours by week (sums to 412).",
      ["week_start", "week_label", "overtime_hours"],
      [[w.isoformat(), f"W{i + 1}", v] for i, (w, v) in enumerate(zip(pay_weeks, [58, 61, 66, 72, 74, 81]))])
table("report_payroll_by_team", "Payroll and overtime report: overtime, jobs and labour per job by team.",
      ["team", "overtime_hours", "jobs_completed", "labour_per_job_aud"],
      [["Fabrication", 168, 412, 171], ["Assembly", 97, 388, 139], ["Despatch", 74, 520, 96], ["Maintenance", 49, 63, 228], ["Office", 24, None, None]])
table("report_payroll_hours_vs_jobs", "Payroll and overtime report: hours worked vs jobs completed, indexed (W1 = 100).",
      ["week_start", "week_label", "hours_index", "jobs_index"],
      [[w.isoformat(), f"W{i + 1}", h, j] for i, (w, h, j) in enumerate(zip(pay_weeks, [100, 102, 105, 109, 111, 116], [100, 101, 101, 102, 101, 103]))])

# --- Template: management pack, profit and loss (October 2026)
pnl = [["Revenue", 412300, 398000, "Two new customers; volume up 5%"],
       ["Materials", 156700, 151200, "Steel price up 4% from 1 Oct"],
       ["Freight", 28900, 23500, "Fuel levy; three urgent shipments"],
       ["Wastage", 16400, 12000, "Rework on one large job"],
       ["Gross margin", 210300, 211300, "Volume gains eaten by freight and wastage"],
       ["Wages", 98600, 101000, "Overtime down 40 hours"],
       ["Overheads", 61200, 60000, "Annual software renewal"],
       ["Net profit", 50500, 50300, "On budget, but margin needs watching"]]
INCOME = {"Revenue", "Gross margin", "Net profit"}
def variance(line, a, b):  # positive = favourable
    return a - b if line in INCOME else b - a
table("template_pnl", "Management pack template: profit and loss, actual against budget, October 2026. Variance is favourable when positive.",
      ["month", "line", "actual_aud", "budget_aud", "variance_aud", "variance_pct", "what_drove_it"],
      [[date(2026, 10, 1).isoformat(), l, a, b, variance(l, a, b), round(100 * variance(l, a, b) / b, 1), n] for l, a, b, n in pnl])

# ---------------------------------------------------------------- checks

def check_totals():
    """The numbers that are meant to add up, do."""
    t = {k: v[2] for k, v in TABLES.items()}
    assert sum(r[2] for r in t["display_warehouse_picks_by_hour"]) == 142
    assert sum(r[1] for r in t["display_boardroom_revenue_monthly"][:10]) == 4820
    assert sum(r[2] for r in t["display_boardroom_revenue_monthly"][:10]) == 4670
    assert round(sum(r[1] for r in t["display_boardroom_cost_of_sale"]), 1) == 100.0
    assert sum(r[1] for r in t["report_sales_cancellations_by_reason"]) == 47 and round(100 * 47 / 1248, 1) == 3.8
    assert sum(r[2] for r in t["report_payroll_overtime_by_week"]) == 412
    assert sum(r[1] for r in t["report_payroll_by_team"]) == 412
    assert round(198000 / sum(r[2] for r in t["report_payroll_by_team"] if r[2])) == 143
    ch = t["hero_sb_channels"]
    assert round(sum(r[2] * r[3] for r in ch) / sum(r[2] for r in ch)) == 184
    fs = t["hero_nfp_funding_sources"]
    assert round(sum(r[1] * r[3] for r in fs) / sum(r[1] for r in fs), 2) == 0.18
    assert sum(r[2] for r in fs) == 100
    p = {r[1]: r for r in t["template_pnl"]}
    for col in (2, 3):
        assert p["Gross margin"][col] == p["Revenue"][col] - p["Materials"][col] - p["Freight"][col] - p["Wastage"][col]
        assert p["Net profit"][col] == p["Gross margin"][col] - p["Wages"][col] - p["Overheads"][col]

# Key figures that must still appear in each mock-up page
MOCKUP_CHECKS = {
    "tools/mockups/warehouse.html": ["142", "180", "94", "steel coil"],
    "tools/mockups/reception.html": ["1,248", "96", "24", "31"],
    "tools/mockups/boardroom.html": ["+3.2%", "31.4%", "4.1%", "+1.8%"],
    "tools/mockups/report-sales.html": ["$412k", "1,248", "3.8%", "[19, 13, 9, 6]"],
    "tools/mockups/report-purchasing.html": ["$286k", "91%", "+4.2%", "PO-1042"],
    "tools/mockups/report-payroll.html": ["$198k", "412", "9.6%", "$143"],
    "tools/mockups/template-excel.html": ["412,300", "210,300", "50,500"],
    "script.js": ["$184", "$0.18", "'$115'", "'$46k'", "'$0.54'"],
}

def check_mockups():
    missing = []
    for path, needles in MOCKUP_CHECKS.items():
        text = (REPO / path).read_text()
        missing += [f"{path}: {n}" for n in needles if n not in text]
    if missing:
        sys.exit("Mock-ups and sample data disagree:\n  " + "\n  ".join(missing))

# ---------------------------------------------------------------- output

def sql_type(values):
    vals = [v for v in values if v is not None]
    if all(isinstance(v, int) for v in vals):
        return "INT"
    if all(isinstance(v, (int, float)) for v in vals):
        return "DECIMAL(14,2)"
    if all(isinstance(v, str) and len(v) == 10 and v[4] == "-" and v[7] == "-" for v in vals):
        return "DATE"
    return f"VARCHAR({max(20, max(len(str(v)) for v in vals) + 20)})"

def main():
    check_totals()
    check_mockups()
    OUT.mkdir(exist_ok=True)
    schema = ["-- Sample Co tables for The Fourth Sheet mock-ups. Generated by tools/sample_data.py.",
              "-- Works in Azure SQL / SQL Server and PostgreSQL. Load each CSV into the table of the same name.", ""]
    for name, (desc, cols, rows) in TABLES.items():
        with open(OUT / f"{name}.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows([["" if v is None else v for v in r] for r in rows])
        types = [sql_type([r[i] for r in rows]) for i in range(len(cols))]
        schema.append(f"-- {desc}")
        schema.append(f"CREATE TABLE {name} (\n" + ",\n".join(f"    {c} {t}" for c, t in zip(cols, types)) + "\n);\n")
    (OUT / "schema.sql").write_text("\n".join(schema))
    write_readme()
    print(f"Wrote {len(TABLES)} CSVs and schema.sql to {OUT.relative_to(REPO)}/")

GROUPS = [
    ("Home-page hero dashboard (index.html)", "hero_"),
    ("Live-display screens (media/display-*.png)", "display_"),
    ("Report previews (media/report-*.png)", "report_"),
    ("Management-pack template (media/template-excel.png)", "template_"),
]

def write_readme():
    lines = [
        "# Sample data",
        "",
        "The invented \"Sample Co\" numbers behind every mock-up dashboard and report on the website.",
        "**Generated by `tools/sample_data.py`; don't edit these files by hand.** Change the numbers in that script",
        "(and the matching mock-up), then run `python3 tools/sample_data.py`.",
        "",
        "- One CSV per table: a header row, plain numbers (no `$` or commas), ISO dates (`2026-10-01`), empty = no value.",
        "- All money is AUD. Columns ending `_aud_k` are thousands of dollars.",
        "- `schema.sql` has a `CREATE TABLE` for every CSV (Azure SQL / SQL Server and PostgreSQL).",
        "",
        "## Loading into a database",
        "",
        "1. Run `schema.sql` to create the tables.",
        "2. Load each CSV into the table with the same name, for example:",
        "   - **PostgreSQL:** `\\copy report_sales_kpis FROM 'sample-data/report_sales_kpis.csv' CSV HEADER`",
        "   - **Azure SQL / SQL Server:** the Import Flat File wizard (SSMS / Azure Data Studio), or `BULK INSERT ... WITH (FORMAT = 'CSV', FIRSTROW = 2)`",
        "   - **Power BI / Excel:** Get Data > Text/CSV.",
        "",
        "## Tables",
        "",
    ]
    for title, prefix in GROUPS:
        lines.append(f"### {title}")
        lines.append("")
        lines.append("| Table | What it is | Columns |")
        lines.append("| --- | --- | --- |")
        for name, (desc, cols, rows) in TABLES.items():
            if name.startswith(prefix):
                lines.append(f"| `{name}` | {desc} | {', '.join(f'`{c}`' for c in cols)} |")
        lines.append("")
    (OUT / "README.md").write_text("\n".join(lines))

if __name__ == "__main__":
    main()
