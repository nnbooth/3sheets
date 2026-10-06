"""
Run a report for a period, from the data, and build its Excel, PDF and PowerPoint from scratch.

    python3 tools/report.py job-margins --period 2026-06
    python3 tools/report.py board --period 2026-08 --format pdf --out ~/Desktop
    python3 tools/report.py --list                      every report and the periods it can run for
    python3 tools/report.py --all                       everything, for the website (what sample_data.py runs)

Data comes from the CSV folder in OneDrive (or FOURTH_SHEET_DATA); the database will slot in behind the same
interface (fourthsheet/source.py).
"""

import argparse
import sys

from .build import build_all, default_period, load_data, periods_for, run_report, write_files
from .catalogue import REPORTS


def main(argv=None):
    ap = argparse.ArgumentParser(prog="report", description="Build a report from the data, for a period, as Excel, PDF and PowerPoint.")
    ap.add_argument("report", nargs="?", choices=list(REPORTS), help="which report")
    ap.add_argument("--period", help="YYYY-MM (default: the latest month that's over)")
    ap.add_argument("--format", default="xlsx,pdf,pptx", help="any of xlsx,pdf,pptx (default: all three)")
    ap.add_argument("--out", help="folder for the files (default: media/exports/reports/<period>/)")
    ap.add_argument("--list", action="store_true", help="list the reports and their periods")
    ap.add_argument("--all", action="store_true", help="build every report for every period (the website)")
    a = ap.parse_args(argv)
    if a.all:
        build_all(tuple(a.format.split(",")))
        return
    D = load_data()
    if a.list or not a.report:
        for slug in REPORTS:
            ps = periods_for(slug, D)
            print(f"{slug:14} {ps[-1]} to {ps[0]}  (default {default_period(slug, D)})")
        if not a.report:
            return
    period = a.period or default_period(a.report, D)
    r = run_report(a.report, period, D)
    print(f"{r['question']} · {r['business']} · {r['period_label']} ({r['period_status'].lower()})")
    for path, note in write_files(r, a.format.split(","), a.out):
        print(f"  {path}" + (f"  [{note}]" if note else ""))


if __name__ == "__main__":
    main(sys.argv[1:])
