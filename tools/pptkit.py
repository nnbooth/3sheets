#!/usr/bin/env python3
"""
pptkit.py — PowerPoint versions of every PDF export, with one shared look.

16:9 slides; header = business and title; footer = file name, date retrieved, slide X of Y.
Charts are native PowerPoint charts (editable): horizontal bars for categories (green on target,
grey below), area charts for months (strong line, light fill). Tables split across slides.
Negative numbers are always red, in brackets.
"""

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

GREEN, GREY, INK, MUTED, BRAND, NEG, LINE = "0E9F6E", "A7B0B8", "25342A", "5F6F63", "2F7A5D", "B42318", "DCE8DC"
FMT = {"money0": '$#,##0;[Red]($#,##0);"-"', "pct1": '0.0"%";[Red](0.0"%")', "cents_int": '0"¢";[Red](0"¢")', "int": '#,##0;[Red](#,##0)'}
W, H = Inches(13.333), Inches(7.5)
ROWS_PER_SLIDE = 14
FONT = "Roboto"         # like the site and the business cards (exportkit.XL_FONT for Excel)


def rgb(h):
    return RGBColor.from_string(h)


def is_neg(t):
    t = str(t).strip()
    return (t.startswith("(") or t.startswith("-")) and any(c.isdigit() for c in t)


class Deck:
    def __init__(self, business, title, filename, retrieved):
        self.p = Presentation()
        self.p.slide_width, self.p.slide_height = W, H
        self.business, self.title, self.filename, self.retrieved = business, title, filename, retrieved
        self.blank = self.p.slide_layouts[6]

    # ---------------------------------------------------------------- basics
    def text(self, slide, x, y, w, h, txt, size=12, bold=False, colour=INK, align=None):
        tb = slide.shapes.add_textbox(x, y, w, h)
        tf = tb.text_frame
        tf.word_wrap = True
        for k, line in enumerate(str(txt).split("\n")):
            para = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
            run = para.add_run()
            run.text = line
            run.font.size, run.font.bold, run.font.name = Pt(size), bold, FONT
            run.font.color.rgb = rgb(NEG if is_neg(line) and size >= 18 else colour)
            if align:
                para.alignment = align
        return tb

    def slide(self, heading, sub=None):
        s = self.p.slides.add_slide(self.blank)
        bar = s.shapes.add_shape(1, 0, 0, W, Inches(0.08))
        bar.fill.solid(); bar.fill.fore_color.rgb = rgb(BRAND); bar.line.fill.background()
        self.text(s, Inches(0.5), Inches(0.18), Inches(8), Inches(0.3), f"{self.business} · {self.title}", 10, colour=MUTED)
        self.text(s, Inches(0.5), Inches(0.45), Inches(12.3), Inches(0.6), heading, 24, bold=True)
        if sub:
            self.text(s, Inches(0.5), Inches(1.05), Inches(12.3), Inches(0.5), sub, 12, colour=MUTED)
        return s

    def footers(self):
        n = len(self.p.slides)
        for i, s in enumerate(self.p.slides, 1):
            y = H - Inches(0.4)
            self.text(s, Inches(0.5), y, Inches(4), Inches(0.3), self.filename, 9, colour=MUTED)
            self.text(s, Inches(4.7), y, Inches(4), Inches(0.3), f"Data retrieved {self.retrieved} · Sample data", 9, colour=MUTED, align=PP_ALIGN.CENTER)
            self.text(s, Inches(9.3), y, Inches(3.5), Inches(0.3), f"Slide {i} of {n}", 9, colour=MUTED, align=PP_ALIGN.RIGHT)

    def save(self, path):
        self.footers()
        self.fonts()
        self.p.save(str(path))

    def fonts(self):
        """Roboto everywhere: every run of text, every table cell and every chart (titles, axes, labels, legends)."""
        def runs(tf):
            for para in tf.paragraphs:
                para.font.name = FONT
                for r in para.runs:
                    r.font.name = FONT
        for slide in self.p.slides:
            for sh in slide.shapes:
                if sh.has_text_frame:
                    runs(sh.text_frame)
                if getattr(sh, "has_table", False) and sh.has_table:
                    for row in sh.table.rows:
                        for cell in row.cells:
                            runs(cell.text_frame)
                if getattr(sh, "has_chart", False) and sh.has_chart:
                    sh.chart.font.name = FONT

    # ---------------------------------------------------------------- slides
    def title_slide(self, intro, status_lines):
        s = self.p.slides.add_slide(self.blank)
        box = s.shapes.add_shape(1, Inches(0.5), Inches(0.6), Inches(0.7), Inches(0.7))
        box.fill.solid(); box.fill.fore_color.rgb = rgb(BRAND); box.line.fill.background()
        box.text_frame.text = "4th"
        r_ = box.text_frame.paragraphs[0].runs[0]; r_.font.size = Pt(16); r_.font.bold = True; r_.font.color.rgb = rgb("FFFFFF")
        self.text(s, Inches(1.35), Inches(0.72), Inches(6), Inches(0.5), "The Fourth Sheet", 18, bold=True)
        self.text(s, Inches(0.5), Inches(1.7), Inches(12), Inches(0.4), "SAMPLE DATA · invented figures for demonstration", 11, bold=True, colour="8A7A52")
        self.text(s, Inches(0.5), Inches(2.2), Inches(12.3), Inches(1.2), self.title, 34, bold=True)
        self.text(s, Inches(0.5), Inches(3.45), Inches(12.3), Inches(0.5), self.business, 16, colour=MUTED)
        self.text(s, Inches(0.5), Inches(4.05), Inches(12.3), Inches(1.2), intro, 14)
        self.text(s, Inches(0.5), Inches(5.4), Inches(12.3), Inches(1.2), "How final is this data?\n" + "\n".join(status_lines), 11, colour=MUTED)

    def kpi_slide(self, heading, items, sub=None):
        s = self.slide(heading, sub)
        n = max(1, len(items))
        w = (W - Inches(1.0) - Inches(0.3) * (n - 1)) / n
        for i, (label, value, note) in enumerate(items):
            x = Inches(0.5) + i * (w + Inches(0.3))
            card = s.shapes.add_shape(1, x, Inches(1.8), w, Inches(2.2))
            card.fill.solid(); card.fill.fore_color.rgb = rgb("F7FAF7"); card.line.color.rgb = rgb(LINE)
            self.text(s, x + Inches(0.2), Inches(1.95), w - Inches(0.4), Inches(0.5), label, 12, colour=MUTED)
            t = self.text(s, x + Inches(0.2), Inches(2.45), w - Inches(0.4), Inches(0.8), value, 30, bold=True, colour=BRAND)
            if is_neg(value):
                t.text_frame.paragraphs[0].runs[0].font.color.rgb = rgb(NEG)
            self.text(s, x + Inches(0.2), Inches(3.3), w - Inches(0.4), Inches(0.6), note, 11, colour=MUTED)
        return s

    def bar_slide(self, heading, labels, values, fmt="pct1", target=None, below=None, sub=None, order_by=None):
        s = self.slide(heading, sub)
        by = order_by or values
        order = sorted(range(len(values)), key=lambda i: by[i])          # PowerPoint draws bars bottom-up: largest ends on top
        cd = CategoryChartData()
        cd.categories = [labels[i] for i in order]
        cd.add_series("Value", [values[i] for i in order], number_format=FMT.get(fmt, "General"))
        top = Inches(1.6 if sub else 1.3)
        gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.5), top, Inches(12.3), H - top - Inches(0.7), cd)
        ch = gf.chart
        ch.has_legend = False
        ch.value_axis.visible = False
        ch.value_axis.has_major_gridlines = False
        ch.category_axis.tick_labels.font.size = Pt(12)
        ch.category_axis.format.line.fill.background()
        plot = ch.plots[0]
        plot.gap_width = 60
        plot.has_data_labels = True
        dl = plot.data_labels
        dl.number_format, dl.number_format_is_linked = FMT.get(fmt, "General"), False
        dl.position = XL_LABEL_POSITION.OUTSIDE_END
        dl.font.size = Pt(11)
        ser = plot.series[0]
        for k, i in enumerate(order):
            pt = ser.points[k]
            pt.format.fill.solid()
            pt.format.fill.fore_color.rgb = rgb(GREY if (below and below[i]) else GREEN)
        if target is not None:
            self.text(s, Inches(0.5), H - Inches(0.75), Inches(12), Inches(0.3),
                      f"Target {target}  ·  grey = below target", 10, colour=MUTED)
        return s

    def area_slide(self, heading, labels, values, fmt="money0", sub=None):
        s = self.slide(heading, sub)
        pts = [(l, v) for l, v in zip(labels, values) if v is not None]
        cd = CategoryChartData()
        cd.categories = [l for l, _ in pts]
        cd.add_series("Value", [v for _, v in pts], number_format=FMT.get(fmt, "General"))
        top = Inches(1.6 if sub else 1.3)
        gf = s.shapes.add_chart(XL_CHART_TYPE.AREA, Inches(0.5), top, Inches(12.3), H - top - Inches(0.7), cd)
        ch = gf.chart
        ch.has_legend = False
        va = ch.value_axis
        va.has_major_gridlines = True
        va.major_gridlines.format.line.color.rgb = rgb("E6EAE7")
        va.tick_labels.number_format, va.tick_labels.number_format_is_linked = FMT.get(fmt, "General"), False
        va.tick_labels.font.size = Pt(10)
        va.format.line.fill.background()
        ch.category_axis.tick_labels.font.size = Pt(10)
        ser = ch.plots[0].series[0]
        ser.format.fill.solid()
        ser.format.fill.fore_color.rgb = rgb(GREEN)
        # light fill (75% transparent) with a strong line, like the website
        sf = ser.format.fill._xPr.find(qn("a:solidFill"))
        clr = sf.find(qn("a:srgbClr"))
        alpha = clr.makeelement(qn("a:alpha"), {"val": "25000"})
        clr.append(alpha)
        ser.format.line.color.rgb = rgb(GREEN)
        ser.format.line.width = Pt(2.5)
        return s

    def table_slides(self, heading, head, rows, sub=None, money_cols=None):
        for start in range(0, max(1, len(rows)), ROWS_PER_SLIDE):
            chunk = rows[start:start + ROWS_PER_SLIDE]
            more = f" ({start // ROWS_PER_SLIDE + 1} of {-(-len(rows) // ROWS_PER_SLIDE)})" if len(rows) > ROWS_PER_SLIDE else ""
            s = self.slide(heading + more, sub)
            top = Inches(1.6 if sub else 1.3)
            shape = s.shapes.add_table(len(chunk) + 1, len(head), Inches(0.5), top, Inches(12.3), Inches(0.36) * (len(chunk) + 1))
            t = shape.table
            for c, h_ in enumerate(head):
                cell = t.cell(0, c)
                cell.text = str(h_)
                cell.fill.solid(); cell.fill.fore_color.rgb = rgb(BRAND)
                para = cell.text_frame.paragraphs[0]
                if para.runs:                                          # a blank header cell has no text to style
                    para.runs[0].font.size, para.runs[0].font.bold = Pt(11), True
                    para.runs[0].font.color.rgb = rgb("FFFFFF")
                if c:
                    para.alignment = PP_ALIGN.RIGHT
            for r, row_ in enumerate(chunk, 1):
                row_ = (list(row_) + [""] * len(head))[:len(head)]       # every row exactly as wide as the table
                for c, val in enumerate(row_):
                    cell = t.cell(r, c)
                    cell.text = "" if val is None else str(val)
                    cell.fill.solid(); cell.fill.fore_color.rgb = rgb("FFFFFF" if r % 2 else "F7FAF7")
                    para = cell.text_frame.paragraphs[0]
                    if para.runs:
                        para.runs[0].font.size = Pt(10.5)
                        para.runs[0].font.color.rgb = rgb(NEG if is_neg(val) else INK)
                        if str(row_[0]).startswith("Total") or str(row_[0]) in ("Net profit after tax", "Surplus for the month", "Net assets", "Cash at end of month"):
                            para.runs[0].font.bold = True
                    if c:
                        para.alignment = PP_ALIGN.RIGHT

    def text_slide(self, heading, blocks, sub=None):
        """blocks: [(title, text)] side by side (up to 2) or stacked."""
        s = self.slide(heading, sub)
        n = len(blocks)
        w = (W - Inches(1.0) - Inches(0.3) * (n - 1)) / n
        for i, (t, body) in enumerate(blocks):
            x = Inches(0.5) + i * (w + Inches(0.3))
            card = s.shapes.add_shape(1, x, Inches(1.7), w, Inches(4.8))
            card.fill.solid(); card.fill.fore_color.rgb = rgb("EEF5F0" if i else "FFFFFF"); card.line.color.rgb = rgb(LINE)
            self.text(s, x + Inches(0.25), Inches(1.85), w - Inches(0.5), Inches(0.4), t.upper(), 11, bold=True, colour=MUTED)
            self.text(s, x + Inches(0.25), Inches(2.3), w - Inches(0.5), Inches(4.1), body, 16)
        return s

    def image_slide(self, heading, png, sub=None):
        s = self.slide(heading, sub)
        top = Inches(1.6 if sub else 1.3)
        s.shapes.add_picture(str(png), Inches(0.5), top, height=H - top - Inches(0.7))
        return s
