#!/usr/bin/env python3
"""
site_check.py — check the whole website in a real browser. Run it after any change, on the Mac or the PC:

    python3 tools/tests/site_check.py          (Windows: py tools\\tests\\site_check.py)

It starts its own local web server, then:
  - every page at desktop, tablet and phone width: no script errors, no sideways scrolling,
    and every local link, image and download resolves;
  - every report page: the Period dropdown changes the report, puts ?period= in the address,
    points the downloads at that period's files (which must exist), deep links work, and the
    "how it's worked out" dialog opens.
Prints PROBLEMS: [] when everything passes (and exits 1 otherwise).
"""

import functools
import http.server
import socket
import sys
import threading
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import winutf8; winutf8.ensure()   # noqa: E402,E702  Windows: run in UTF-8 mode

REPO = Path(__file__).resolve().parents[2]
REPORTS = ["cost-to-win", "job-margins", "growth", "cost-to-raise", "program-cost", "runway", "funding", "board"]


def serve():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Quiet, directory=str(REPO)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{port}/", httpd


def main():
    from playwright.sync_api import sync_playwright
    base, httpd = serve()
    probs, seen = [], {}

    def ok(u):
        if u not in seen:
            try:
                seen[u] = urllib.request.urlopen(urllib.request.Request(u, method="HEAD"), timeout=10).status == 200
            except Exception:
                seen[u] = False
        return seen[u]

    pages = sorted(p.name for p in REPO.glob("*.html"))
    with sync_playwright() as pw:
        try:
            br = pw.chromium.launch(channel="chrome")
        except Exception:
            br = pw.chromium.launch()
        for w in (1280, 768, 375):
            pg = br.new_page(viewport={"width": w, "height": 900})
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.on("console", lambda m: errs.append(m.text) if m.type == "error" and "openstreetmap" not in m.text else None)
            for p in pages:
                errs.clear()
                pg.goto(base + p)
                pg.wait_for_timeout(400)
                if errs:
                    probs.append((w, p, errs[:3]))
                if pg.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1"):
                    probs.append((w, p, "sideways scrolling"))
                if w == 1280:
                    for u in pg.eval_on_selector_all("a[href],img[src],script[src],link[href],video[src],source[src]",
                                                     "els => els.map(e => e.getAttribute('href') || e.getAttribute('src'))"):
                        if not u or u.startswith(("#", "mailto:", "tel:", "http", "data:", "javascript:")):
                            continue
                        full = urljoin(base + p, u.split("#")[0])
                        if urlparse(full).netloc == urlparse(base).netloc and not ok(full):
                            probs.append((p, "broken link", u))
            for s in REPORTS:
                pg.goto(base + f"report-{s}.html")
                pg.wait_for_timeout(400)
                opts = pg.eval_on_selector_all("#report-period option", "o => o.map(x => x.value)")
                if len(opts) < 2:
                    probs.append((w, s, "Period dropdown missing"))
                    continue
                before = pg.inner_text("#report-root")
                other = [o for o in opts if o != pg.eval_on_selector("#report-period", "e => e.value")][-1]
                pg.select_option("#report-period", other)
                pg.wait_for_timeout(600)
                if pg.inner_text("#report-root") == before:
                    probs.append((w, s, "report didn't change with the period"))
                if f"period={other}" not in pg.url:
                    probs.append((w, s, "address doesn't carry the period"))
                for u in pg.eval_on_selector_all("#report-dl a", "a => a.map(x => x.getAttribute('href'))"):
                    if other not in u or not ok(base + u):
                        probs.append((w, s, "download missing", u))
                mid = opts[len(opts) // 2]
                pg.goto(base + f"report-{s}.html?period={mid}")
                pg.wait_for_timeout(600)
                if pg.eval_on_selector("#report-period", "e => e.value") != mid:
                    probs.append((w, s, "?period= link didn't open that period"))
                pg.click("#report-root [data-sup]")
                pg.wait_for_timeout(150)
                if not pg.eval_on_selector("#support-dialog", "d => d.open"):
                    probs.append((w, s, "workings dialog didn't open"))
                pg.keyboard.press("Escape")
        br.close()
    httpd.shutdown()
    print(f"{len(pages)} pages x 3 widths and {len(REPORTS)} reports checked. PROBLEMS: {probs}")
    if probs:
        sys.exit(1)


if __name__ == "__main__":
    main()
