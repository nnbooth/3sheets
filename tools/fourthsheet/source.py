"""
source.py — where a report's data comes from.

Every report reads its data through a Source, never from the model that invented it. Today that's the CSV
folder in OneDrive (Data/); later it's the cloud database. Both give back the same tables, so the reports
don't change when the database arrives:

    src = CsvSource()                 # Data/ in OneDrive, or FOURTH_SHEET_DATA
    src.table("trades", "fact_job_month")   -> list of dicts, numbers as numbers

A database source only has to implement table(org, name) with the same column names (schema.sql).
"""

import csv
import os
from functools import lru_cache
from pathlib import Path

ORG_FOLDERS = {"trades": "SME trades", "services": "SME services", "nfp": "Not-for-profit"}
COMMON = ("dim_date", "dim_org", "target", "simulation_parameter")


def data_root():
    if os.getenv("FOURTH_SHEET_DATA"):
        return Path(os.getenv("FOURTH_SHEET_DATA")).expanduser()
    for base in (os.getenv("OneDriveConsumer"), os.getenv("OneDrive"),
                 Path.home() / "Library/CloudStorage/OneDrive-Personal", Path.home() / "OneDrive"):
        if base and (Path(base) / "Projects/The 4th Sheet/Data").exists():
            return Path(base) / "Projects/The 4th Sheet/Data"
    raise SystemExit("Can't find the data folder (OneDrive 'Projects/The 4th Sheet/Data'). Set FOURTH_SHEET_DATA to it.")


def _num(v):
    if v == "":
        return None
    try:
        f = float(v)
    except ValueError:
        return v
    return int(f) if f.is_integer() and "." not in v else f


class CsvSource:
    """Reads the tables from the CSV folder (one folder per organisation, plus Common)."""

    def __init__(self, root=None):
        self.root = Path(root) if root else data_root()
        self.name = f"CSV files in {self.root}"

    @lru_cache(maxsize=None)
    def _read(self, path):
        with open(path, newline="", encoding="utf-8") as f:
            return [{k: (v if k in ("month_key", "job_id", "engagement_id", "grant_id", "date_key_text") else _num(v)) for k, v in r.items()}
                    for r in csv.DictReader(f)]

    def table(self, org, name):
        p = (self.root / "Common" / f"{name}.csv") if name in COMMON else (self.root / "Month-end dashboard" / ORG_FOLDERS[org] / f"{name}.csv")
        if not p.exists():
            raise SystemExit(f"Missing data: {p}")
        rows = self._read(str(p))
        if name in COMMON and org:
            rows = [r for r in rows if r.get("org_id") in (org, None)] if rows and "org_id" in rows[0] else rows
        return rows


class OrgData:
    """One organisation's data, shaped for reporting: monthly P&L from the ledger, lines, jobs, drivers."""

    def __init__(self, src, org):
        self.src, self.org = src, org
        acc = {a["account_id"]: a for a in src.table(org, "dim_account")}
        self.accounts = acc
        pnl = {}
        for g in src.table(org, "fact_gl_daily"):
            a = acc[g["account_id"]]
            if a["statement"] != "P&L":
                continue
            mo = str(g["date_key"])[:4] + "-" + str(g["date_key"])[4:6]
            d = pnl.setdefault(mo, {})
            d[a["line"]] = d.get(a["line"], 0) + g["amount"]
        self.pnl_lines = pnl              # {month: {ledger line: amount}} (income +, costs −)
        self.sections = {a["line"]: a["section"] for a in acc.values() if a["statement"] == "P&L"}
        self.months = sorted(pnl)
        self.lines = src.table(org, "fact_line_month")
        self.drivers = {}
        for d in src.table(org, "driver_month"):
            self.drivers.setdefault(d["driver"], {})[d["month_key"]] = d["value"]
        self.rates = {r["rate"]: r["value"] for r in src.table(org, "cost_rate")}
        self.targets = {t["target"]: t["value"] for t in src.table(org, "target")}
        self.about = next(o for o in src.table(None, "dim_org") if o["org_id"] == org)

    def line(self, mo, name):
        return self.pnl_lines.get(mo, {}).get(name, 0)

    def section(self, mo, section):
        return sum(v for k, v in self.pnl_lines.get(mo, {}).items() if self.sections.get(k) == section)

    def by_line(self, mo):
        return self.pnl_lines.get(mo, {})

    def line_month(self, mo, line=None):
        rows = [r for r in self.lines if r["month_key"] == mo and (line is None or r["line"] == line)]
        return {k: sum(r[k] or 0 for r in rows) for k in ("revenue", "direct_cost", "gross_margin")}


def load(src=None):
    src = src or CsvSource()
    return src, {o: OrgData(src, o) for o in ORG_FOLDERS}
