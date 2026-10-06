#!/usr/bin/env python3
"""
exportkit.py — shared look for every Excel and PDF export, so they print
properly and look the same.

  hbar_svg(chart)          horizontal bar chart as vector SVG (for PDFs):
                           categories down the left, value labels on the
                           bars' ends, the target line ON TOP, and a label
                           that would hit the target line moves past it
  status_box_html(...)     the "how final is this data" panel for page 1
  pdf_footer(...)          footer on every PDF page: page X of Y, status
  xl_print(ws, ...)        Excel print setup: orientation, fit to width,
                           repeated header rows, footer, no gridlines

Palette (muted, and still distinct when printed in black and white):
  sage #5e8b76 on target · sand #c8a77e below target · brick #8f4a3e very
  late / overdue · slate #8e9cab on its way · near-black #2f2f2f targets.
"""

from datetime import date

GOOD, SOME, BAD, OPEN, INK, MUTED, LINE = "#5e8b76", "#c8a77e", "#8f4a3e", "#8e9cab", "#2f2f2f", "#5f6f63", "#dce8dc"
STATUS_COLOUR = {"Locked": "#2f5d4a", "Provisional": "#8a6d3b", "Incomplete": "#8f4a3e", "Future": MUTED}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fmt_value(v, f):
    if f == "pct0":
        return f"{round(v)}%"
    if f == "money_k":
        return f"${round(v / 1000):,}k" if abs(v) >= 1000 else f"${v}"
    if f == "money0":
        return f"${round(v):,}"
    return str(v)


def hbar_svg(ch, width=640):
    """Horizontal bars, sorted as given. Same rules as the website chart."""
    f = ch.get("format", "pct0")
    labels, values = ch["labels"], ch["values"]
    marks, target, plain = ch.get("marks"), ch.get("target"), ch.get("plain")
    char = 6.2
    left = min(230, 12 + max(len(str(l)) for l in labels) * char)
    right = width - 60
    row, bh, top = 24, 14, 8
    plot_h = len(values) * row
    below = lambda v: not plain and target is not None and v < target
    any_below = any(below(v) for v in values)
    height = top + plot_h + (36 if (any_below or marks) else 22 if target is not None else 8)
    mx = max(values + ([target] if target is not None else []) + (marks or [])) * 1.08
    x = lambda v: left + v / mx * (right - left)
    tx = x(target) if target is not None else None
    g = [f'<line x1="{left}" x2="{left}" y1="{top - 3}" y2="{top + plot_h}" stroke="{LINE}" stroke-width="1.5"/>']
    for i, (lab, v) in enumerate(zip(labels, values)):
        y = top + i * row + (row - bh) / 2
        g.append(f'<text x="{left - 8}" y="{y + bh - 3}" text-anchor="end" font-size="11" fill="{MUTED}">{esc(lab)}</text>')
        g.append(f'<rect x="{left}" y="{y}" width="{x(v) - left:.1f}" height="{bh}" rx="2" fill="{SOME if below(v) else GOOD}"/>')
        end = x(v)
        if marks:
            mxp = x(marks[i])
            g.append(f'<line x1="{mxp:.1f}" x2="{mxp:.1f}" y1="{y - 3}" y2="{y + bh + 3}" stroke="{INK}" stroke-width="2"/>')
            end = max(end, mxp)
        text = fmt_value(v, f)
        lx = end + 5
        if tx is not None and lx - 4 < tx < lx + len(text) * char + 4:   # the label would sit on the target line
            lx = tx + 5
        g.append(f'<text x="{lx:.1f}" y="{y + bh - 3}" font-size="10" fill="{INK}">{esc(text)}</text>')
    if target is not None:
        g.append(f'<line x1="{tx:.1f}" x2="{tx:.1f}" y1="{top - 4}" y2="{top + plot_h + 2}" stroke="{INK}" stroke-width="1.2" stroke-dasharray="4 3"/>')
        g.append(f'<text x="{tx:.1f}" y="{top + plot_h + 15}" text-anchor="middle" font-size="10" font-weight="600" fill="{INK}">Target {fmt_value(target, f)}</text>')
    ky = height - 6
    if any_below:
        g.append(f'<rect x="{left}" y="{ky - 9}" width="10" height="10" rx="2" fill="{SOME}"/><text x="{left + 15}" y="{ky}" font-size="10" fill="{MUTED}">Below target</text>')
    if marks:
        g.append(f'<line x1="{left + 4}" x2="{left + 4}" y1="{ky - 11}" y2="{ky + 1}" stroke="{INK}" stroke-width="2"/><text x="{left + 12}" y="{ky}" font-size="10" fill="{MUTED}">{esc(ch.get("mark_label", ""))}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" '
            f'style="font-family:Inter,Arial,sans-serif" role="img">{"".join(g)}</svg>')


def status_box_html(items):
    """items: [(label, status, note)] -> a small 'how final is this data' panel."""
    rows = "".join(f'<tr><td><b>{esc(lab)}</b></td><td><span class="st" style="color:{STATUS_COLOUR.get(st, MUTED)};border-color:{STATUS_COLOUR.get(st, MUTED)}">{esc(st)}</span></td><td>{esc(note)}</td></tr>'
                   for lab, st, note in items)
    return f'<div class="statusbox"><h3>How final is this data?</h3><table>{rows}</table></div>'


STATUS_CSS = """
.statusbox { border: 1px solid #dce8dc; border-radius: 6px; padding: 6px 10px; margin: 8px 0; page-break-inside: avoid; }
.statusbox h3 { margin: 0 0 4px; font-size: 9.5pt; color: #25342a; }
.statusbox table { width: 100%; border-collapse: collapse; } .statusbox td { padding: 2px 6px 2px 0; border: 0; font-size: 8.5pt; vertical-align: top; }
.statusbox td:first-child { white-space: nowrap; width: 1%; } .statusbox td:nth-child(2) { width: 1%; }
.st { display: inline-block; padding: 0 6px; border: 1px solid; border-radius: 999px; font-size: 7.5pt; font-weight: 700; white-space: nowrap; }
"""


def pdf_footer(left_text, status_text):
    """Footer template for Playwright's page.pdf (page numbers filled in by Chrome)."""
    return (f'<div style="width:100%;font-family:Arial,sans-serif;font-size:7.5px;color:#5f6f63;padding:0 12mm;display:flex;justify-content:space-between;gap:8px">'
            f'<span>{esc(left_text)}</span><span>{esc(status_text)}</span>'
            f'<span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>')


def pdf_options(left_text, status_text, landscape=False):
    return dict(format="A4", landscape=landscape, print_background=True, display_header_footer=True,
                header_template="<span></span>", footer_template=pdf_footer(left_text, status_text),
                margin={"top": "12mm", "bottom": "16mm", "left": "12mm", "right": "12mm"})


def xl_print(ws, footer_status, landscape=False, header_row=None, gridlines=False):
    """Make a worksheet print like a report."""
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.orientation = "landscape" if landscape else "portrait"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_options.horizontalCentered = True
    ws.page_margins.left = ws.page_margins.right = 0.5
    ws.page_margins.top, ws.page_margins.bottom = 0.6, 0.7
    if header_row:
        ws.print_title_rows = f"{header_row}:{header_row}"
    ws.sheet_view.showGridLines = gridlines
    ws.oddFooter.left.text = "The 4th Sheet · Sample data"
    ws.oddFooter.left.size = 8
    ws.oddFooter.center.text = footer_status
    ws.oddFooter.center.size = 8
    ws.oddFooter.right.text = "Page &P of &N"
    ws.oddFooter.right.size = 8
    ws.oddHeader.right.text = f"Printed {date.today().strftime('%-d %b %Y')}"
    ws.oddHeader.right.size = 8
