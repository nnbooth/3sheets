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
    if f == "pct1":
        return f"{v:.1f}%"
    if f == "pct0":
        return f"{round(v)}%"
    if f == "money_k":
        return f"${round(v / 1000):,}k" if abs(v) >= 1000 else f"${v}"
    if f == "money0":
        return f"(${-round(v):,})" if v < 0 else f"${round(v):,}"
    if f == "cents_int":
        return f"{round(v)}¢"
    if f == "int":
        return f"{round(v):,}"
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
    below_marks = ch.get("below_marks")
    below = lambda v, i: not plain and ((target is not None and v < target) or (below_marks and marks and v < marks[i]))
    any_below = any(below(v, i) for i, v in enumerate(values))
    height = top + plot_h + (36 if (any_below or marks) else 22 if target is not None else 8)
    mx = max(values + ([target] if target is not None else []) + (marks or [])) * 1.08
    x = lambda v: left + v / mx * (right - left)
    tx = x(target) if target is not None else None
    g = [f'<line x1="{left}" x2="{left}" y1="{top - 3}" y2="{top + plot_h}" stroke="{LINE}" stroke-width="1.5"/>']
    order = sorted(range(len(values)), key=lambda i: -values[i])     # largest first, in every view
    for pos, i in enumerate(order):
        lab, v = labels[i], values[i]
        y = top + pos * row + (row - bh) / 2
        g.append(f'<text x="{left - 8}" y="{y + bh - 3}" text-anchor="end" font-size="11" fill="{MUTED}">{esc(lab)}</text>')
        g.append(f'<rect x="{left}" y="{y}" width="{x(v) - left:.1f}" height="{bh}" rx="2" fill="{SOME if below(v, i) else GOOD}"/>')
        text = fmt_value(v, f)
        lx = x(v) + 5
        if marks:
            mxp = x(marks[i])
            g.append(f'<line x1="{mxp:.1f}" x2="{mxp:.1f}" y1="{y - 3}" y2="{y + bh + 3}" stroke="{INK}" stroke-width="2"/>')
            if x(v) - 1 <= mxp < lx + len(text) * char + 4:    # marker in the way: label goes after it
                lx = mxp + 5
        if tx is not None and lx - 4 < tx < lx + len(text) * char + 4:   # the label would sit on the target line
            lx = tx + 5
        g.append(f'<text x="{lx:.1f}" y="{y + bh - 3}" font-size="10" fill="{INK}">{esc(text)}</text>')
    if target is not None:
        g.append(f'<line x1="{tx:.1f}" x2="{tx:.1f}" y1="{top - 4}" y2="{top + plot_h + 2}" stroke="{INK}" stroke-width="1.2" stroke-dasharray="4 3"/>')
        g.append(f'<text x="{tx:.1f}" y="{top + plot_h + 15}" text-anchor="middle" font-size="10" font-weight="600" fill="{INK}">Target {fmt_value(target, f)}</text>')
    ky = height - 6
    if any_below and not marks:
        g.append(f'<rect x="{left}" y="{ky - 9}" width="10" height="10" rx="2" fill="{SOME}"/><text x="{left + 15}" y="{ky}" font-size="10" fill="{MUTED}">Below target</text>')
    if marks:
        g.append(f'<line x1="{left + 4}" x2="{left + 4}" y1="{ky - 11}" y2="{ky + 1}" stroke="{INK}" stroke-width="2"/><text x="{left + 12}" y="{ky}" font-size="10" fill="{MUTED}">{esc(ch.get("mark_label", ""))}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" '
            f'style="font-family:Inter,Arial,sans-serif" role="img">{"".join(g)}</svg>')


def col_svg(labels, values, status, f, width=700, height=230, target=None):
    """Month-by-month columns (time series). Incomplete or provisional periods are lighter and marked;
    every column carries a small value; quarter labels along the bottom."""
    vals = [v for v in values if v is not None]
    mx = max(vals + ([target] if target is not None else []) + [0]) * 1.12 or 1
    mn = min(vals + [0])
    left, right, top, base = 8, width - 8, 30, height - 36
    span = mx - mn
    y = lambda v: base - (v - mn) / span * (base - top)
    slot = (right - left) / len(values)
    bw = slot * 0.66
    zero = y(0)
    g = [f'<line x1="{left}" x2="{right}" y1="{zero:.1f}" y2="{zero:.1f}" stroke="{LINE}" stroke-width="1.5"/>']
    for i, (lab, v, st) in enumerate(zip(labels, values, status)):
        x0 = left + i * slot + (slot - bw) / 2
        cx = x0 + bw / 2
        if v is not None:
            yy = y(v)
            top_, h_ = min(yy, zero), abs(zero - yy)
            light = st in ("Incomplete", "Provisional")
            extra = f' fill-opacity="0.35" stroke="{GOOD}" stroke-dasharray="3 2"' if light else ""
            g.append(f'<rect x="{x0:.1f}" y="{top_:.1f}" width="{bw:.1f}" height="{h_:.1f}" rx="1.5" fill="{GOOD}"{extra}/>')
            g.append(f'<text transform="translate({cx + 3:.1f},{top_ - 3:.1f}) rotate(-90)" font-size="8" fill="{INK}">{esc(fmt_value(v, f))}</text>')
        if i % 3 == 0 or i == len(labels) - 1:
            g.append(f'<text x="{cx:.1f}" y="{base + 14}" text-anchor="middle" font-size="9" fill="{MUTED}">{esc(lab)}</text>')
        if st == "Incomplete":
            g.append(f'<text x="{cx:.1f}" y="{base + 26}" text-anchor="middle" font-size="8" fill="{BAD}">to date</text>')
    if target is not None:
        ty = y(target)
        g.append(f'<line x1="{left}" x2="{right}" y1="{ty:.1f}" y2="{ty:.1f}" stroke="{INK}" stroke-width="1.2" stroke-dasharray="4 3"/>')
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


def _band(left, right):
    return (f'<div style="width:100%;font-family:Arial,sans-serif;font-size:7.5px;color:#5f6f63;padding:0 12mm;display:flex;justify-content:space-between;gap:8px">'
            f'<span>{left}</span><span>{right}</span></div>')


def pdf_options(business, report_name, filename, retrieved, landscape=False):
    """Every PDF page: header = business and report name; footer = file name, date retrieved, page X of Y."""
    footer = (f'<div style="width:100%;font-family:Arial,sans-serif;font-size:7.5px;color:#5f6f63;padding:0 12mm;display:flex;justify-content:space-between;gap:8px">'
              f'<span>{esc(filename)}</span><span>Data retrieved {esc(retrieved)}</span>'
              f'<span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>')
    return dict(format="A4", landscape=landscape, print_background=True, display_header_footer=True,
                header_template=_band(esc(business), esc(report_name)), footer_template=footer,
                margin={"top": "16mm", "bottom": "16mm", "left": "12mm", "right": "12mm"})


# Excel number formats: ONE per kind, negatives in red brackets
XL_FMT = {"money": '#,##0;[Red](#,##0);"-"', "pct": '0.0%;[Red](0.0%);"-"', "hours": '#,##0.0;[Red](#,##0.0);"-"',
          "int": '#,##0;[Red](#,##0);"-"', "months": '0.0" months";[Red](0.0" months")', "cents": '0"¢";[Red](0"¢")',
          "date": 'd mmm yyyy', "text": '@'}


# ---- print layout: landscape A4, fitted to width. Page breaks are worked out and CHECKED here,
# before the file is saved, so nobody has to fix them at the printer.
PAGE_W_PT = (11.69 - 1.0) * 72          # A4 landscape less 0.5" side margins
PAGE_H_PT = (8.27 - 1.5) * 72           # less 0.75" top and bottom margins (header and footer sit in them)
DEFAULT_ROW_PT = 15.0


def _col_width_pt(ws, c):
    from openpyxl.utils import get_column_letter
    w = ws.column_dimensions[get_column_letter(c)].width or 8.43
    return w * 7 * 0.75 + 4                # Excel width units -> points (approx.)


def xl_scale(ws):
    """Fit-to-width shrink factor for this sheet (1.0 = actual size)."""
    width = sum(_col_width_pt(ws, c) for c in range(1, ws.max_column + 1))
    return min(1.0, PAGE_W_PT / width) if width else 1.0


def row_height(ws, r):
    """Explicit height, or an estimate from wrapped text and font size."""
    import math
    if ws.row_dimensions[r].height:
        return ws.row_dimensions[r].height
    lines, size = 1, 11
    for cell in ws[r]:
        if cell.value is None:
            continue
        if cell.font and cell.font.sz:
            size = max(size, cell.font.sz)
        if cell.alignment and cell.alignment.wrap_text and isinstance(cell.value, str) and not str(cell.value).startswith("="):
            chars = max(1, (ws.column_dimensions[cell.column_letter].width or 8.43) * 1.1)
            lines = max(lines, math.ceil(len(cell.value) / chars))
    return max(DEFAULT_ROW_PT, lines * size * 1.36)


def xl_breaks(ws, block_starts, last_row, header_row=None):
    """Place page breaks only at block boundaries (a block = a statement section, a workings panel,
    a month of a list); split a block only if it is longer than a whole page. Returns the page plan."""
    from openpyxl.worksheet.pagebreak import Break, RowBreak
    ws.row_breaks = RowBreak()
    scale = xl_scale(ws)
    cap = PAGE_H_PT / scale
    rep = row_height(ws, header_row) if header_row else 0
    starts = sorted(set(b for b in block_starts if 1 < b <= last_row))
    pages, top, used = [], 1, 0.0
    block_of = {}
    cur = 1
    for r in range(1, last_row + 1):
        if r in starts:
            cur = r
        block_of[r] = cur
    r = 1
    while r <= last_row:
        h = row_height(ws, r)
        if used + h > cap:
            # break before the start of this row's block, if that keeps the block whole and the page isn't empty
            b = block_of[r]
            brk = b if (b > top and b in starts) else r
            ws.row_breaks.append(Break(id=brk - 1))
            pages.append((top, brk - 1))
            top = brk
            used = rep + sum(row_height(ws, x) for x in range(brk, r))
            if header_row and top <= header_row:
                used -= rep
        used += h
        r += 1
    pages.append((top, last_row))
    return {"scale": scale, "capacity": cap, "pages": pages, "starts": starts, "header": rep}


def xl_review(ws, plan, header_row=None):
    """Check the page plan before saving: every page fits, no block is split unless it is
    longer than a page, and the header row repeats. Returns a one-line summary; raises on a problem."""
    problems = []
    for i, (a, b) in enumerate(plan["pages"], 1):
        h = sum(row_height(ws, r) for r in range(a, b + 1)) + (plan["header"] if (header_row and a > header_row) else 0)
        if h > plan["capacity"] + 0.5:
            problems.append(f"page {i} (rows {a}-{b}) is too tall")
        if i > 1:
            inside = [s for s in plan["starts"] if a < s <= b]
            prev_block = max([s for s in plan["starts"] if s <= a] or [1])
            nxt = min([s for s in plan["starts"] if s > a] or [b + 1])
            block_len = sum(row_height(ws, r) for r in range(prev_block, nxt))
            if a not in plan["starts"] and block_len <= plan["capacity"] and prev_block != 1:
                problems.append(f"page {i} starts part-way through a block (row {a})")
    if header_row and len(plan["pages"]) > 1 and ws.print_title_rows is None:
        problems.append("header row doesn't repeat")
    if problems:
        raise SystemExit(f"Print check FAILED on sheet '{ws.title}': " + "; ".join(problems))
    n = len(plan["pages"])
    return f"{ws.title}: {n} page{'s' if n > 1 else ''}, {round(plan['scale'] * 100)}% scale, no block split"


def xl_print(ws, business, filename, retrieved, landscape=True, header_row=None, gridlines=False):
    """Make a worksheet print like a report. Header: business and sheet name.
    Footer: file name, date retrieved (fixed text) and page X of Y."""
    amp = lambda t: t.replace("&", "&&")          # & starts a code in Excel headers
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.orientation = "landscape" if landscape else "portrait"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_options.horizontalCentered = True
    ws.page_margins.left = ws.page_margins.right = 0.5
    ws.page_margins.top, ws.page_margins.bottom = 0.75, 0.75
    if header_row:
        ws.print_title_rows = f"{header_row}:{header_row}"
    ws.sheet_view.showGridLines = gridlines
    for part, text in [(ws.oddHeader.left, amp(business)), (ws.oddHeader.right, "&A"),
                       (ws.oddFooter.left, amp(filename)), (ws.oddFooter.center, amp(f"Data retrieved {retrieved}")),
                       (ws.oddFooter.right, "Page &P of &N")]:
        part.text = text
        part.size = 8
