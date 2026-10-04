#!/usr/bin/env python3
"""
render_mockups.py: turn the HTML dashboard mock-ups in tools/mockups/ into
the PNG images used on the website (media/display-*.png and media/report-*.png, 1600x900).

The data in them is invented ("Sample Co") and labelled illustrative.
Edit a .html file, then run from the repo root:   python3 tools/render_mockups.py
(Needs Playwright: pip install playwright; uses your installed Google Chrome.)
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "tools" / "mockups"
OUT = REPO / "media"
NAMES = {
    "warehouse": "display-warehouse.png", "reception": "display-reception.png", "boardroom": "display-boardroom.png",
    "report-sales": "report-sales.png", "report-purchasing": "report-purchasing.png", "report-payroll": "report-payroll.png",
}

with sync_playwright() as p:
    try:
        browser = p.chromium.launch(channel="chrome")
    except Exception:
        browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1600, "height": 900})
    for name, out in NAMES.items():
        page.goto((SRC / f"{name}.html").as_uri())
        page.screenshot(path=str(OUT / out))
        print("wrote", (OUT / out).relative_to(REPO))
    browser.close()
