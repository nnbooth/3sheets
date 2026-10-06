#!/usr/bin/env python3
"""
reports.py — one report for each question on the SME and not-for-profit pages.

Each report is built from the same data as everything else (the locked
August/September model, 24 months of history, October to date) and carries:
  - sections: headline numbers, bar charts (categories), column charts (months),
    tables, and "what it shows / what you'd do about it"
  - workings behind every number (inputs + calculation), as on the home dashboard
  - data status for every month (Locked / Provisional / Incomplete)

Built by tools/build_reports.py into report-*.html pages, data/reports-data.js,
and an Excel + PDF per report.
"""

from datetime import date

import data_status as ds
import financial_model as fm
from financial_model import FMT, calc, half_up, inp, money, support

MONTHS = None    # set in build(): Oct 2024 to Sep 2026 (24 locked or provisional months)
FYTD = ["2026-07", "2026-08", "2026-09"]      # financial year to date (FY2027: July to September 2026)
PFYTD = ["2025-07", "2025-08", "2025-09"]     # the same period last financial year
FYTD_L, PFYTD_L = "Year to date (Jul to Sep 2026)", "same period last year (Jul to Sep 2025)"


def mlabel(mo):
    return date.fromisoformat(mo + "-01").strftime("%b %y")


def status(mo):
    return ds.month_status(mo)[0]


def series(title, months, views, note=None, dims=None):
    """A month-by-month column chart. views: {view id: {label, values, format, supports?}}."""
    return {"type": "series", "title": title, "labels": [mlabel(m) for m in months], "months": months,
            "status": [status(m) for m in months], "views": views, "dims": dims, "note": note}


def kpis(items):
    return {"type": "kpis", "items": items}


def kpi(label, value, sub, sp, cls=""):
    return {"label": label, "value": value, "sub": sub, "cls": cls, "support": sp}


def text(shows, action):
    return {"type": "text", "shows": shows, "action": action}


def table(title, head, rows, kinds, note=None):
    return {"type": "table", "title": title, "head": head, "rows": rows, "kinds": kinds, "note": note}


def growth(cur, prev):
    return None if not prev else (cur - prev) / prev


# ---------------------------------------------------------------- page filters
# A block can carry one filter (e.g. line, source, program). Every section either ignores it, or is a
# "vary" section with a version for each filter value, so the whole page follows the filter.

def filt(label, options):
    """options: [(value, label)]; the first is the default."""
    return {"label": label, "options": options}


def vary(by):
    return {"type": "vary", "by": by}


def line_kpis(org, lm, line, lines):
    """September margin and growth for one line (or all lines), with workings."""
    ls = lines if line == "All" else [line]
    def tot(mo, k):
        return sum(r[k] for r in lm if r[0] == org and r[3] in ls and r[1] == mo)
    sep, aug, ly = "2026-09", "2026-08", "2025-09"
    sp_m = support(f"{'All lines' if line == 'All' else line}: gross margin, September and August", "Revenue less direct cost, over revenue. Before overheads.", [
        inp("Revenue", "money", [tot(sep, 5), tot(aug, 5)]), inp("Direct cost", "money", [tot(sep, 6), tot(aug, 6)]),
        calc("Gross margin", "money", "r0-r1"), calc("Gross margin %", "pct", "r2/r0")])
    r12 = sum(r[5] for r in lm if r[0] == org and r[3] in ls and r[1] in FYTD)
    p12 = sum(r[5] for r in lm if r[0] == org and r[3] in ls and r[1] in PFYTD)
    m12 = sum(r[7] for r in lm if r[0] == org and r[3] in ls and r[1] in FYTD)
    sp_y = support(f"{'All lines' if line == 'All' else line}: September against September last year", "September 2026 ÷ September 2025 − 1 (year on year)",
                   [inp("Revenue, Sep 2026", "money", [tot(sep, 5)]), inp("Revenue, Sep 2025", "money", [tot(ly, 5)]), calc("Growth", "pct", "r0/r1-1")], cols=("Sep",))
    sp_12 = support(f"{'All lines' if line == 'All' else line}: year to date against the same period last year", "July to September 2026 ÷ July to September 2025 − 1 (financial year to date)",
                    [inp("Revenue, year to date (Jul to Sep 2026)", "money", [r12]), inp("Revenue, same period last year", "money", [p12]), calc("Growth", "pct", "r0/r1-1"),
                     inp("Gross margin, year to date", "money", [m12]), calc("Gross margin %, year to date", "pct", "r3/r0")], cols=("Year to date",))
    return {"sep": tot(sep, 5), "sep_cost": tot(sep, 6), "aug": tot(aug, 5), "ly": tot(ly, 5), "sep_m": sp_m["xl"]["rows"][3]["values"][0], "aug_m": sp_m["xl"]["rows"][3]["values"][1],
            "r12": r12, "p12": p12, "m12": m12, "sp_m": sp_m, "sp_y": sp_y, "sp_12": sp_12}


def job_support(j, rate):
    return support(j["description"], "Gross profit ÷ revenue for this job", [
        inp("Revenue", "money", [j["revenue"]]), inp("Materials", "money", [-j["materials"]]), inp("Subcontractors", "money", [-j["subcontractors"]]),
        inp("Technician hours", "hours", [j["hours"]]), inp("Technician cost rate ($/hour, wages and all on-costs)", "money", [rate]),
        calc("Technician time", "money", "-r3*r4"), calc("Job gross margin", "money", "r0+r1+r2+r5"), calc("Job gross margin %", "pct", "r6/r0")], cols=("This job",))


ONCOSTS = "Wages always include all on-costs: super, payroll tax, workers' compensation insurance and leave."
DEF = {
    "trades": ("Gross margin is not profit. Job gross margin = revenue less materials, subcontractors and technician time charged to the job at "
               "$68 an hour (wages and all on-costs). Not included: technician time not charged to any job (travel, training, waiting), and overheads "
               "(office wages, marketing, vehicles, rent, insurance, IT, depreciation, interest). Profit is what's left after those. " + ONCOSTS),
    "services": ("Gross margin is not profit. Gross margin = revenue less contractors and consultant time charged to the work at $60 an hour "
                 "(wages and all on-costs). Not included: consultant time not charged to clients, and overheads (management and admin wages, "
                 "marketing, rent, IT, insurance, travel, depreciation, interest). Profit is what's left after those. " + ONCOSTS),
}


def definition(org):
    return {"type": "definition", "title": "Gross margin, not profit", "text": DEF[org], "link": "numbers-explained.html#gross-margin"}


def bridge(res, org):
    """From September's gross margin on the work to profit before tax, tied to the locked P&L."""
    r = res[org]["out"]["r"]["2026-09"]
    wages, charged = (r["techw"], r["allocated"]) if org == "trades" else (r["sal"], r["allocated"])
    gm_work = r["jobs_gp"] if org == "trades" else r["contribution"]
    who = "Technician" if org == "trades" else "Consultant"
    work = "jobs" if org == "trades" else "client work"
    sp = support("From gross margin to profit, September 2026", "Gross margin on the work − time not charged − overheads = profit before tax", [
        inp(f"Gross margin on {work}", "money", [gm_work]), inp(f"{who} wages and on-costs", "money", [wages]),
        inp(f"{who} time charged to {work} (at cost)", "money", [charged]), calc(f"{who} time not charged to {work}", "money", "r1-r2"),
        calc("Gross profit (the P&L)", "money", "r0-r3"), inp("Overheads (operating expenses, depreciation, interest)", "money", [r["gp"] - r["pbt"]]),
        calc("Profit before tax (the P&L)", "money", "r4-r5"), inp("Revenue", "money", [r["revenue"]]),
        calc(f"Gross margin on {work}, %", "pct", "r0/r7"), calc("Profit before tax, % of revenue", "pct", "r6/r7"),
        calc(f"Gross margin {work} need just to cover overheads and time not charged", "pct", "(r3+r5)/r7")],
        "Ties to the September P&L (locked). " + ONCOSTS, cols=("Sep 2026",))
    x = sp["xl"]["rows"]
    if round(x[4]["values"][0]) != r["gp"] or round(x[6]["values"][0]) != r["pbt"]:
        raise SystemExit(f"bridge for {org} doesn't tie to the P&L")
    v = lambda i: x[i]["values"][0]
    line = (f"September's {work} made {money(v(0))} gross margin ({FMT['pct'](v(8))}). {who} time not charged to {work} took {money(v(3))} and overheads "
            f"{money(v(5))}, leaving {money(v(6))} profit before tax ({FMT['pct'](v(9))} of revenue). To cover overheads, {work} {'need' if work == 'jobs' else 'needs'} a "
            f"{FMT['pct'](v(10))} gross margin on average.")
    return {"type": "insight", "title": "From gross margin to profit", "text": line, "support": sp}


def break_even(res, org):
    """The gross margin the work needs just to cover overheads and time not charged (September, from the P&L)."""
    r = res[org]["out"]["r"]["2026-09"]
    wages = r["techw"] if org == "trades" else r["sal"]
    return ((wages - r["allocated"]) + (r["gp"] - r["pbt"])) / r["revenue"]


def margin_action(name, gm, be, noun="work"):
    """Plain and short: the gross margin, against what overheads need. No instructions; the owner knows why."""
    if gm < 0:
        return f"{name}: {FMT['pct'](gm)} gross margin. Losing money before overheads."
    if gm < be:
        return f"{name}: {FMT['pct'](gm)} gross margin, below the {FMT['pct'](be)} needed to cover overheads."
    return f"{name}: {FMT['pct'](gm)} gross margin, {round(100 * (gm - be), 1):.1f} points clear of the {FMT['pct'](be)} overheads need."


def margin_chart(title, subtitle, labels, rev, gp, target, details):
    """Bars with a margin % / gross profit $ toggle; $ view marks each item's target profit."""
    pct_ = [round(100 * g / r, 1) for g, r in zip(gp, rev)]
    return {"title": title, "subtitle": subtitle, "labels": labels, "values": pct_, "target": float(target), "format": "pct1", "details": details,
            "views": [{"id": "pct", "label": "Gross margin %", "values": pct_, "format": "pct1", "target": float(target)},
                      {"id": "dollars", "label": "Gross margin $", "values": gp, "format": "money0",
                       "marks": [half_up(r * target / 100) for r in rev], "mark_label": f"Target gross margin ({target:.1f}% of revenue)", "below_marks": True}]}


# ======================================================================= SME

def cost_to_win(res, h):
    T = fm.TRADES
    mk, nc = {}, {}
    for org, mo, drv, val, _ in h["drivers"]:
        if org == "trades" and mo in MONTHS:
            if drv == "Marketing spend":
                mk[mo] = val
            if drv.startswith("New customers"):
                nc[mo] = val
    for mo in fm.PERIODS:
        mk[mo], nc[mo] = T["opex"]["Marketing"][mo], T["new_customers"][mo]
    cost = [mk[m] / nc[m] for m in MONTHS]
    sup = [support(f"Cost to win a customer, {mlabel(m)}", "Marketing spend ÷ new customers",
                   [inp("Marketing spend", "money", [mk[m]]), inp("New customers (first job ever)", "int", [nc[m]]),
                    calc("Cost per new customer", "money", "r0/r1")], cols=(mlabel(m),)) for m in MONTHS]
    k = res["trades"]["fourth"]["kpis"][1]["support"]
    ly = MONTHS[-13]
    last12 = sum(mk[m] for m in FYTD) / sum(nc[m] for m in FYTD)
    prev12 = sum(mk[m] for m in PFYTD) / sum(nc[m] for m in PFYTD)
    s12 = support("Cost to win a customer, year to date against the same period last year",
                  "Total marketing ÷ total new customers, for each period", [
                      inp("Marketing, Jul to Sep 2026", "money", [sum(mk[m] for m in FYTD)]),
                      inp("New customers, Jul to Sep 2026", "int", [sum(nc[m] for m in FYTD)]),
                      calc("Cost per customer, year to date", "money", "r0/r1"),
                      inp("Marketing, Jul to Sep 2025", "money", [sum(mk[m] for m in PFYTD)]),
                      inp("New customers, Jul to Sep 2025", "int", [sum(nc[m] for m in PFYTD)]),
                      calc("Cost per customer, same period last year", "money", "r3/r4"),
                      calc("Change", "pct", "r2/r5-1")], cols=("Year to date",))
    ex = res["trades"]["examples"][1]
    return {
        "slug": "cost-to-win", "audience": "sme", "question": "What does it cost to win a customer?",
        "org": "trades", "business": res["trades"]["model"]["long_name"],
        "intro": "Marketing spend divided by the customers it actually brought in (a customer's first ever job), month by month.",
        "blocks": [{"label": None, "sections": [
            kpis([kpi("September 2026", money(k["xl"]["rows"][2]["values"][0]), f"August {money(k['xl']['rows'][2]['values'][1])}", k),
                  kpi(f"September last year", money(mk[ly] / nc[ly]), f"{nc[ly]} new customers from {money(mk[ly])}", sup[-13]),
                  kpi("Year to date (Jul to Sep)", money(last12), f"{FMT['pct'](last12 / prev12 - 1)} on the same period last year ({money(prev12)})", s12)]),
            series("Cost to win a customer, by month", MONTHS, {
                "All|cost": {"label": "$ per new customer", "values": [half_up(c) for c in cost], "format": "money0", "supports": sup},
                "All|customers": {"label": "New customers", "values": [nc[m] for m in MONTHS], "format": "int", "supports": sup},
                "All|marketing": {"label": "Marketing $", "values": [mk[m] for m in MONTHS], "format": "money0", "supports": sup}},
                note="Customers are counted in the month of their first job. Tap a month for its workings.",
                dims={"line": ["All"], "measure": [("cost", "$ per new customer"), ("customers", "New customers"), ("marketing", "Marketing $")]}),
            text(ex["shows"], ex["action"])]}],
        "data": {"head": ["Month", "Status", "Marketing spend", "New customers", "Cost per new customer"],
                 "kinds": ["text", "text", "money", "int", "money"],
                 "rows": [[mlabel(m), status(m), mk[m], nc[m], "=C{r}/D{r}"] for m in MONTHS]},
    }


def line_views(org, lm, lines):
    """Revenue, margin and growth by line, month by month, with workings for every point."""
    get = {(r[1], r[3]): r for r in lm if r[0] == org}
    views, data_rows = {}, []
    for line in ["All"] + lines:
        rev, mar, cost = [], [], []
        for m in MONTHS:
            rows = [get[(m, l)] for l in (lines if line == "All" else [line])]
            rev.append(sum(r[5] for r in rows)); cost.append(sum(r[6] for r in rows)); mar.append(sum(r[7] for r in rows))
        sups = []
        for i, m in enumerate(MONTHS):
            prev = rev[i - 12] if i >= 12 else None
            rows_ = [inp("Revenue", "money", [rev[i]]), inp("Direct cost", "money", [cost[i]]), calc("Gross margin", "money", "r0-r1"),
                     calc("Gross margin %", "pct", "r2/r0")]
            if prev:
                rows_ += [inp(f"Revenue, {mlabel(MONTHS[i - 12])}", "money", [prev]), calc("Growth on the same month last year", "pct", "r0/r4-1")]
            sups.append(support(f"{line if line != 'All' else 'All lines'}, {mlabel(m)}", "Revenue less direct cost; growth against the same month last year", rows_, cols=(mlabel(m),)))
        views[f"{line}|revenue"] = {"label": "Revenue $", "values": rev, "format": "money0", "supports": sups}
        views[f"{line}|margin_pct"] = {"label": "Gross margin %", "values": [round(100 * a / b, 1) if b else 0 for a, b in zip(mar, rev)], "format": "pct1", "supports": sups}
        views[f"{line}|margin"] = {"label": "Gross margin $", "values": mar, "format": "money0", "supports": sups}
        views[f"{line}|growth"] = {"label": "Growth vs same month last year", "values": [round(100 * (rev[i] / rev[i - 12] - 1), 1) if i >= 12 and rev[i - 12] else None for i in range(len(MONTHS))],
                                   "format": "pct1", "supports": sups}
        for i, m in enumerate(MONTHS):
            data_rows.append([line, mlabel(m), status(m), rev[i], cost[i]])
    return views, data_rows


def line_table(org, lm, lines):
    """Year to date against the same period last year, by line."""
    rows = []
    for line in lines + ["All"]:
        ls = lines if line == "All" else [line]
        r12 = sum(r[5] for r in lm if r[0] == org and r[3] in ls and r[1] in FYTD)
        p12 = sum(r[5] for r in lm if r[0] == org and r[3] in ls and r[1] in PFYTD)
        m12 = sum(r[7] for r in lm if r[0] == org and r[3] in ls and r[1] in FYTD)
        rows.append([line if line != "All" else "Total", r12, p12, "=B{r}/C{r}-1", m12, "=E{r}/B{r}",
                     FMT["pct"](r12 / p12 - 1), FMT["pct"](m12 / r12)])
    return rows


def growing(res, h, lm):
    blocks = []
    for org, lines, noun in (("trades", ["Maintenance contracts", "Installations", "Call-outs and repairs"], "line"),
                             ("services", ["Projects", "Retainers", "Training"], "type of work")):
        views, data_rows = line_views(org, lm, lines)
        tab = line_table(org, lm, lines)
        tot = tab[-1]
        kp, tx = {}, {}
        for line in ["All"] + lines:
            k = line_kpis(org, lm, line, lines)
            kp[line] = kpis([kpi("September against September last year", FMT["pct"](k["sep"] / k["ly"] - 1), f"{money(k['sep'])} against {money(k['ly'])}", k["sp_y"]),
                             kpi("Year to date against the same period last year", FMT["pct"](k["r12"] / k["p12"] - 1), f"{money(k['r12'])} against {money(k['p12'])}", k["sp_12"]),
                             kpi("Gross margin, year to date", FMT["pct"](k["m12"] / k["r12"]), f"{money(k['m12'])} before overheads", k["sp_12"])])
            if line == "All":
                best = max(tab[:-1], key=lambda r_: r_[1] / r_[2] - 1)
                worst = min(tab[:-1], key=lambda r_: r_[4] / r_[1])
                poss = lambda w: w.lower() + ("'" if w.lower().endswith("s") else "'s")
                be = break_even(res, org)
                rich = max(tab[:-1], key=lambda r_: r_[4] / r_[1])
                tx[line] = text(f"Revenue is {FMT['pct'](tot[1] / tot[2] - 1)} up on the same period last year, year to date ({money(tot[1])} against {money(tot[2])}). "
                                f"{rich[0]} {'make' if rich[0].endswith('s') else 'makes'} the highest gross margin ({rich[7]}); {worst[0]} the lowest ({worst[7]}). The business needs "
                                f"{FMT['pct'](be)} gross margin just to cover overheads.",
                                f"{rich[0]}: {rich[7]} gross margin, the most profitable work you do."
                                + (f"{worst[0]}: {worst[7]} gross margin, below the {FMT['pct'](be)} needed to cover overheads."
                                   if worst[4] / worst[1] < be else
                                   f"{worst[0]}: {worst[7]} gross margin, the thinnest, still above the {FMT['pct'](be)} overheads need."))
            else:
                g, mg, tg, tm = k["r12"] / k["p12"] - 1, k["m12"] / k["r12"], tot[1] / tot[2] - 1, tot[4] / tot[1]
                tx[line] = text(f"{line} brought in {money(k['r12'])} this financial year to date, {FMT['pct'](g)} on the same period last year "
                                f"({'faster' if g > tg else 'slower'} than the business as a whole, {FMT['pct'](tg)}), at a {FMT['pct'](mg)} gross margin "
                                f"({'above' if mg > tm else 'below'} the {FMT['pct'](tm)} overall).",
                                margin_action(line, mg, break_even(res, org), noun))
        blocks.append({"label": res[org]["model"]["name"], "business": res[org]["model"]["long_name"],
                       "filter": filt(noun.capitalize(), [("All", "All")] + [(l, l) for l in lines]), "sections": [
            definition(org), vary(kp),
            series(f"Revenue, gross margin and growth by {noun}, by month", MONTHS, views,
                   note="Gross margin = revenue less direct cost (materials, subcontractors and time at cost for trades; contractors and consultant time for services), before overheads. Growth is year on year: each month against the same month a year earlier. Tap a month for its workings.",
                   dims={"line": ["All"] + lines, "measure": [("revenue", "Revenue $"), ("margin_pct", "Gross margin %"), ("margin", "Gross margin $"), ("growth", "Growth vs same month last year")]}),
            dict(table(f"By {noun}: financial year to date (Jul to Sep) against the same period last year", ["", "Year to date", "Same period last year", "Growth", "Gross margin $", "Gross margin %"],
                       [[r_[0], money(r_[1]), money(r_[2]), r_[6], money(r_[4]), r_[7]] for r_ in tab], ["text", "money", "money", "pct", "money", "pct"]), highlight_filter=True),
            bridge(res, org), vary(tx)],
            "data": {"head": ["Line", "Month", "Status", "Revenue", "Direct cost", "Gross margin", "Gross margin %"],
                     "kinds": ["text", "text", "text", "money", "money", "money", "pct"],
                     "rows": [r_ + ["=D{r}-E{r}", "=IF(D{r}=0,\"\",F{r}/D{r})"] for r_ in data_rows]},
            "table_xl": {"head": ["Line", "Year to date", "Same period last year", "Growth", "Gross margin $", "Gross margin %"],
                         "kinds": ["text", "money", "money", "pct", "money", "pct"], "rows": [r_[:6] for r_ in tab]}})
    return {"slug": "growth", "audience": "sme", "question": "Which products and services are growing?",
            "org": "trades", "business": "SME sample businesses",
            "intro": "Revenue, gross margin and growth (year on year) by product or service line over 24 months. Pick a line and every number, chart and note follows it.",
            "blocks": blocks}


def job_margins(res, h, lm):
    T = fm.TRADES
    f4 = res["trades"]["fourth"]
    lines = ["Maintenance contracts", "Installations", "Call-outs and repairs"]
    views, data_rows = line_views("trades", lm, lines)
    keep = {k: v for k, v in views.items() if k.split("|")[1] in ("margin_pct", "margin")}
    sepj = [j for j in res["trades"]["out"]["jobs"] if j["month"] == "2026-09"]
    rate, tgt = T["tech_cost_rate"], T["target_margin"]
    by = {"kpis": {}, "bars": {}, "text": {}}
    for line in ["All"] + lines:
        k = line_kpis("trades", lm, line, lines)
        nm = "All jobs" if line == "All" else line
        by["kpis"][line] = kpis([kpi(f"Job gross margin, September · {nm}", FMT["pct"](k["sep_m"]), f"August {FMT['pct'](k['aug_m'])}", k["sp_m"])])
    # All: one bar per type of job
    tk = {l: line_kpis("trades", lm, l, lines) for l in lines}
    det = [support(f"{l}, September", "Revenue less direct cost (materials, subcontractors, technician time at cost)", [
        inp("Revenue", "money", [tk[l]["sep"]]), inp("Direct cost", "money", [tk[l]["sep_cost"]]),
        calc("Gross margin", "money", "r0-r1"), calc("Gross margin %", "pct", "r2/r0")], cols=("Sep 2026",)) for l in lines]
    gp_all = [d["xl"]["rows"][2]["values"][0] for d in det]
    by["bars"]["All"] = {"type": "bars", "chart": margin_chart("Job gross margin by type of job, September 2026", f"Revenue less materials, subcontractors and technician time at ${rate}/hour.",
                                                              lines, [tk[l]["sep"] for l in lines], gp_all, tgt, det)}
    worst = min(lines, key=lambda l: tk[l]["sep_m"])
    be = break_even(res, "trades")
    best = max(lines, key=lambda l: tk[l]["sep_m"])
    by["text"]["All"] = text("In September " + ", ".join(f"{l.lower()} made a {FMT['pct'](tk[l]['sep_m'])} job gross margin" for l in lines)
                             + f" (technician time at ${rate} an hour, wages and all on-costs). Jobs need {FMT['pct'](be)} just to cover overheads.",
                             f"{best}: {FMT['pct'](tk[best]['sep_m'])} gross margin, the most profitable work you do."
                             + (f"{worst}: {FMT['pct'](tk[worst]['sep_m'])} gross margin, below the {FMT['pct'](be)} needed to cover overheads."
                                if tk[worst]["sep_m"] < be else f"Every type of job clears it; {worst.lower()} only just."))
    # Installations: each job
    by["bars"]["Installations"] = {"type": "bars", "chart": f4["chart"]}
    ex = res["trades"]["examples"][0]
    inst = [j for j in sepj if j["type"] == "Installation"]
    neg = [j for j in inst if j["gross_profit"] < 0]
    under = [j for j in inst if 0 <= j["gross_profit"] / j["revenue"] < be]
    top = max(inst, key=lambda j: j["gross_profit"] / j["revenue"])
    by["text"]["Installations"] = text(ex["shows"] + f" Jobs need {FMT['pct'](be)} gross margin just to cover overheads.",
        (f"{len(neg)} installation(s) lost money before overheads. " if neg else "")
        + (f"Below the {FMT['pct'](be)} overheads need: " + ", ".join(f"{j['description']} ({FMT['pct'](j['gross_profit'] / j['revenue'])})" for j in under) + ". " if under else "")
        + f"Most profitable: {top['description']} ({FMT['pct'](top['gross_profit'] / top['revenue'])}).")
    # Maintenance contracts: each contract
    mc = sorted([j for j in sepj if j["type"] == "Maintenance contract"], key=lambda j: -j["gross_profit"] / j["revenue"])
    by["bars"]["Maintenance contracts"] = {"type": "bars", "chart": margin_chart(
        "Job gross margin on each maintenance contract, September 2026", f"The month's fee less materials and technician time at ${rate}/hour.",
        [j["description"] for j in mc], [j["revenue"] for j in mc], [j["gross_profit"] for j in mc], tgt, [job_support(j, rate) for j in mc])}
    lo = mc[-1]
    by["text"]["Maintenance contracts"] = text(
        f"All {len(mc)} contracts made more than the {tgt:.1f}% job gross margin target. The thinnest was {lo['description']} at "
        f"{FMT['pct'](lo['gross_profit'] / lo['revenue'])} job gross margin: {FMT['hours'](lo['hours'])} of technician time on a {money(lo['revenue'])} monthly fee."
        if all(j["gross_profit"] / j["revenue"] >= tgt / 100 for j in mc) else
        f"{sum(j['gross_profit'] / j['revenue'] < tgt / 100 for j in mc)} of {len(mc)} contracts made less than the {tgt:.1f}% job gross margin target; the thinnest was {lo['description']}.",
        margin_action(f"The {lo['description']} contract", lo["gross_profit"] / lo["revenue"], be, "work")
        + " Maintenance contracts overall: " + FMT["pct"](sum(j["gross_profit"] for j in mc) / sum(j["revenue"] for j in mc))
        + " gross margin, the most profitable work you do.")
    # Call-outs: grouped by length
    co = [j for j in sepj if j["type"] == "Call-out"]
    hrs_ = sorted({j["hours"] for j in co})
    grp = {h_: [j for j in co if j["hours"] == h_] for h_ in hrs_}
    labs = [f"{h_:g}-hour call-outs ({len(grp[h_])})" for h_ in hrs_]
    rev_ = [sum(j["revenue"] for j in grp[h_]) for h_ in hrs_]
    gp_ = [sum(j["gross_profit"] for j in grp[h_]) for h_ in hrs_]
    det = [support(lab, "Call-outs of this length in September, added together", [
        inp("Call-outs", "int", [len(grp[h_])]), inp("Revenue", "money", [r_]), inp("Materials", "money", [-sum(j["materials"] for j in grp[h_])]),
        inp("Technician time at cost", "money", [-sum(j["labour_cost"] for j in grp[h_])]), calc("Job gross margin", "money", "r1+r2+r3"),
        calc("Job gross margin %", "pct", "r4/r1")], cols=("Sep 2026",)) for lab, h_, r_ in zip(labs, hrs_, rev_)]
    by["bars"]["Call-outs and repairs"] = {"type": "bars", "chart": margin_chart(
        "Job gross margin on call-outs by length, September 2026", f"Charged at ${T['callout_rate']}/hour plus materials at cost × {T['materials_markup']}; technician time at ${rate}/hour.",
        labs, rev_, gp_, tgt, det)}
    mg = [g / r for g, r in zip(gp_, rev_)]
    by["text"]["Call-outs and repairs"] = text(
        f"{len(co)} call-outs in September made a {FMT['pct'](sum(gp_) / sum(rev_))} job gross margin between them. Gross margins run from {FMT['pct'](min(mg))} to {FMT['pct'](max(mg))} "
        "by length: the hourly rate covers technician time comfortably, so the gross margin mostly moves with how much material goes on the van.",
        margin_action("Call-outs", sum(gp_) / sum(rev_), be, "work"))
    return {"slug": "job-margins", "audience": "sme", "question": "Which jobs actually make money?",
            "org": "trades", "business": res["trades"]["model"]["long_name"],
            "intro": f"Every job's gross margin: revenue less materials, subcontractors and technician time at ${rate} an hour (fully loaded: wages and all on-costs). Before overheads, so this is not profit. Pick a type of job and every number, chart and note on the page follows it.",
            "blocks": [{"label": None, "filter": filt("Type of job", [("All", "All jobs")] + [(l, l) for l in lines]), "sections": [
                definition("trades"), vary(by["kpis"]), vary(by["bars"]), bridge(res, "trades"), vary(by["text"]),
                series("Job gross margin by month", MONTHS, keep, note="Tap a month for its workings.",
                       dims={"line": ["All"] + lines, "measure": [("margin_pct", "Gross margin %"), ("margin", "Gross margin $")]})]}],
            "data": {"head": ["Line", "Month", "Status", "Revenue", "Direct cost", "Gross margin", "Gross margin %"],
                     "kinds": ["text", "text", "text", "money", "money", "money", "pct"],
                     "rows": [r_ + ["=D{r}-E{r}", "=IF(D{r}=0,\"\",F{r}/D{r})"] for r_ in data_rows]}}


# ======================================================================= NFP

def nfp_month(by_ml, mo):
    g = by_ml.get(mo, {})
    grants = sum(v for k, v in g.items() if k.endswith(" grant"))
    return {"grants": grants, "donations": g.get("Donations", 0), "events": g.get("Fundraising events", 0),
            "fees": g.get("Program fees", 0), "gw": -g.get("Grant writing and reporting", 0), "dc": -g.get("Donor campaigns", 0),
            "ec": -g.get("Event costs", 0), "untied": -(g.get("Program delivery wages (untied)", 0) + g.get("Program costs (untied)", 0)),
            "admin": -(g.get("Administration wages", 0) + g.get("Occupancy", 0) + g.get("Other administration", 0)), "g": g}


SOURCES = [("Grants", "grants", "gw", "grant writing and reporting"), ("Donations", "donations", "dc", "donor campaigns"),
           ("Fundraising events", "events", "ec", "event costs")]


def src_totals(by_ml, months, inc_keys, cost_keys):
    m = [nfp_month(by_ml, x) for x in months]
    return sum(sum(x[k] for k in inc_keys) for x in m), sum(sum(x[k] for k in cost_keys) for x in m)


def cost_to_raise(res, by_ml):
    groups = {"All": (["grants", "donations", "events"], ["gw", "dc", "ec"])} | {s_[0]: ([s_[1]], [s_[2]]) for s_ in SOURCES}
    views, sups, kp, tx = {}, {}, {}, {}
    for name, (ik, ck) in groups.items():
        vals, sp_ = [], []
        for m in MONTHS:
            x = nfp_month(by_ml, m)
            raised, cost = sum(x[k] for k in ik), sum(x[k] for k in ck)
            vals.append(half_up(100 * cost / raised) if raised else None)
            sp_.append(support(f"Cost to raise a dollar, {'all fundraising' if name == 'All' else name.lower()}, {mlabel(m)}", "Fundraising cost ÷ money raised, in cents",
                               [inp("Cost of raising it", "money", [cost]), inp("Money raised", "money", [raised]),
                                calc("Cents per dollar raised", "cents", "r0/r1*100") if raised else inp("Cents per dollar raised", "cents", [0])], cols=(mlabel(m),)))
        views[f"{name}|cents"] = {"label": "Cents per $1", "values": vals, "format": "cents_int", "supports": sp_}
        r_s, c_s = src_totals(by_ml, ["2026-09"], ik, ck)
        r_a, c_a = src_totals(by_ml, ["2026-08"], ik, ck)
        r12, c12 = src_totals(by_ml, FYTD, ik, ck)
        r0, c0 = src_totals(by_ml, PFYTD, ik, ck)
        lab = "all fundraising" if name == "All" else name.lower()
        k1 = support(f"Cost to raise a dollar, {lab}, September and August", "Cost of raising it ÷ money raised, in cents",
                     [inp("Cost of raising it", "money", [c_s, c_a]), inp("Money raised", "money", [r_s, r_a]),
                      calc("Cents per dollar", "cents", "r0/r1*100") if r_s and r_a else
                      inp("Cents per dollar (nothing raised in one of the months)", "cents", [half_up(100 * c_s / r_s) if r_s else 0, half_up(100 * c_a / r_a) if r_a else 0])])
        k2 = support(f"Cost to raise a dollar, {lab}, year to date against the same period last year", "Cost ÷ money raised, in cents",
                     [inp("Cost, year to date", "money", [c12]), inp("Raised, year to date", "money", [r12]), calc("Cents, year to date", "cents", "r0/r1*100"),
                      inp("Cost, same period last year", "money", [c0]), inp("Raised, same period last year", "money", [r0]), calc("Cents, same period last year", "cents", "r3/r4*100")], cols=("Year to date",))
        sep_c = f"{half_up(100 * c_s / r_s)}¢" if r_s else "–"
        aug_c = f"{half_up(100 * c_a / r_a)}¢" if r_a else "none raised"
        kp[name] = kpis([kpi(f"September · {'all fundraising' if name == 'All' else name}", sep_c, f"August {aug_c}", k1),
                         kpi("Year to date (Jul to Sep)", f"{half_up(100 * c12 / r12)}¢", f"same period last year: {half_up(100 * c0 / r0)}¢", k2)])
        if name == "All":
            tx[name] = text(f"September cost {sep_c} to raise each dollar, against {aug_c} in August: the gala raised "
                            f"{money(nfp_month(by_ml, '2026-09')['events'])} but cost {money(nfp_month(by_ml, '2026-09')['ec'])}. "
                            f"This financial year to date it has cost {half_up(100 * c12 / r12)}¢ a dollar, against {half_up(100 * c0 / r0)}¢ in the same period last year.",
                            "Watch the year-to-date figure, not single months: events make September and December jump. Pick a source above to see which one moves it.")
        else:
            cost_name = next(s_[3] for s_ in SOURCES if s_[0] == name)
            tx[name] = text(f"{name} cost {half_up(100 * c12 / r12)}¢ to raise each dollar this financial year to date ({money(c12)} of {cost_name} for {money(r12)}), "
                            f"against {half_up(100 * c0 / r0)}¢ in the same period last year.",
                            {"Grants": "The cheapest money to raise: protect the time that goes into applications and acquittals.",
                             "Donations": "Steady and cheap: keep the June and December appeals, and ask regular donors to give monthly.",
                             "Fundraising events": "The dearest money to raise: keep events for what else they bring (new donors, profile), and count those too."}[name])
    ex = res["nfp"]["examples"][0]
    return {"slug": "cost-to-raise", "audience": "nfp", "question": "What does it cost to raise a dollar?",
            "org": "nfp", "business": res["nfp"]["model"]["long_name"],
            "intro": "What fundraising costs (grant writing, donor campaigns, events) for every dollar it brings in. Pick a source and every number, chart and note follows it.",
            "blocks": [{"label": None, "filter": filt("Source", [("All", "All fundraising")] + [(s_[0], s_[0]) for s_ in SOURCES]), "sections": [
                vary(kp),
                series("Cost to raise a dollar, by month (cents)", MONTHS, views,
                       note="September and December include the gala and the Christmas appeal. Tap a month for its workings.",
                       dims={"line": ["All"] + [s_[0] for s_ in SOURCES], "measure": [("cents", "Cents per $1")]}),
                {"type": "bars", "chart": dict(ex["visual"]["chart"], details=None), "support": ex["support"], "highlight_filter": True},
                vary(tx)]}],
            "data": {"head": ["Month", "Status", "Grant writing", "Donor campaigns", "Event costs", "Grant income", "Donations", "Events", "Cents per $1"],
                     "kinds": ["text", "text", "money", "money", "money", "money", "money", "money", "cents"],
                     "rows": [[mlabel(m), status(m), nfp_month(by_ml, m)["gw"], nfp_month(by_ml, m)["dc"], nfp_month(by_ml, m)["ec"],
                               nfp_month(by_ml, m)["grants"], nfp_month(by_ml, m)["donations"], nfp_month(by_ml, m)["events"],
                               "=SUM(C{r}:E{r})/SUM(F{r}:H{r})*100"] for m in MONTHS]}}


def funding(res, by_ml):
    ex = res["nfp"]["examples"][0]
    views, rows_, tx = {}, [], {}
    groups = {"All": (["grants", "donations", "events"], ["gw", "dc", "ec"])} | {s_[0]: ([s_[1]], [s_[2]]) for s_ in SOURCES}
    for name, (ik, ck) in groups.items():
        inc_v = [sum(nfp_month(by_ml, m)[k] for k in ik) for m in MONTHS]
        cst_v = [sum(nfp_month(by_ml, m)[k] for k in ck) for m in MONTHS]
        sups = [support(f"{'All sources' if name == 'All' else name}, {mlabel(m)}", "Raised, cost of raising it, and what's left", [inp("Raised", "money", [a]), inp("Cost of raising it", "money", [b]),
                calc("Left after fundraising costs", "money", "r0-r1")], cols=(mlabel(m),)) for m, a, b in zip(MONTHS, inc_v, cst_v)]
        views[f"{name}|raised"] = {"label": "Raised $", "values": inc_v, "format": "money0", "supports": sups}
        views[f"{name}|net"] = {"label": "Left after costs $", "values": [a - b for a, b in zip(inc_v, cst_v)], "format": "money0", "supports": sups}
        if name != "All":
            rows_ += [[name, mlabel(m), status(m), a, b] for m, a, b in zip(MONTHS, inc_v, cst_v)]
        r12, c12 = sum(inc_v[-12:]), sum(cst_v[-12:])
        share = r12 / sum(sum(nfp_month(by_ml, m)[k] for k in ("grants", "donations", "events")) for m in FYTD)
        tx[name] = text(ex["shows"], ex["action"]) if name == "All" else text(
            f"{name}: {money(r12)} raised this financial year to date ({FMT['pct'](share)} of everything raised), {money(c12)} to raise it, "
            f"so {money(r12 - c12)} left for programs: {half_up(100 * c12 / r12)}¢ per dollar.",
            {"Grants": "Most of the money, cheapest to raise: the first place for extra effort, starting with grants that renew.",
             "Donations": "Cheap and flexible (untied): the money that builds reserves, so grow regular giving.",
             "Fundraising events": "Dearest per dollar: run fewer, better events, and measure the new donors each one brings."}[name])
    tab = []
    for name, inc, cst, _ in SOURCES:
        a = sum(nfp_month(by_ml, m)[inc] for m in FYTD); b = sum(nfp_month(by_ml, m)[cst] for m in FYTD)
        tab.append([name, money(a), money(b), money(a - b), f"{half_up(100 * b / a)}¢"])
    return {"slug": "funding", "audience": "nfp", "question": "Which funding is worth chasing?",
            "org": "nfp", "business": res["nfp"]["model"]["long_name"],
            "intro": "Each source of money compared on what it raises and what it costs to raise. Pick a source and every chart, table row and note follows it.",
            "blocks": [{"label": None, "filter": filt("Source", [("All", "All sources")] + [(s_[0], s_[0]) for s_ in SOURCES]), "sections": [
                {"type": "bars", "chart": dict(ex["visual"]["chart"], details=None), "support": ex["support"], "highlight_filter": True},
                vary(tx),
                dict(table("Financial year to date (Jul to Sep 2026), by source", ["", "Raised", "Cost of raising it", "Left after costs", "Cost per $1"], tab,
                           ["text", "money", "money", "money", "cents"]), highlight_filter=True),
                series("Raised and left after costs, by month", MONTHS, views, note="Tap a month for its workings.",
                       dims={"line": ["All"] + [s_[0] for s_ in SOURCES], "measure": [("raised", "Raised $"), ("net", "Left after costs $")]})]}],
            "data": {"head": ["Source", "Month", "Status", "Raised", "Cost of raising it", "Left after costs", "Cents per $1"],
                     "kinds": ["text", "text", "text", "money", "money", "money", "cents"],
                     "rows": [r_ + ["=D{r}-E{r}", "=IF(D{r}=0,\"\",E{r}/D{r}*100)"] for r_ in rows_]}}


def program_cost(res, by_ml, gsm):
    """Full cost of each program in September: its grant spending, plus a share of untied program costs and administration."""
    G = sorted(res["nfp"]["out"]["grants"], key=lambda g: -g["spent_sep"])
    x = nfp_month(by_ml, "2026-09")
    direct = {g["program"]: g["spent_sep"] for g in G}
    tot = sum(direct.values())
    sups, full = [], {}
    for g in G:
        sp = support(f"{g['program']}: full cost, September", "Grant spending + its share of untied program costs and administration (shared by grant spending)", [
            inp("Grant spending on the program", "money", [direct[g["program"]]]), inp("All grant-funded program spending", "money", [tot]),
            calc("Share of program spending", "pct", "r0/r1"), inp("Untied program costs (all programs)", "money", [x["untied"]]),
            calc("Share of untied program costs", "money", "r2*r3"), inp("Administration (all)", "money", [x["admin"]]),
            calc("Share of administration", "money", "r2*r5"), calc("Full cost of the program", "money", "r0+r4+r6")], cols=("Sep 2026",))
        sups.append(sp)
        full[g["program"]] = sp["xl"]["rows"][-1]["values"][0]
    labels = [g["program"] for g in G]
    chart = {"title": "Full cost of each program, September 2026", "labels": labels, "values": [half_up(full[l]) for l in labels],
             "format": "money0", "plain": True, "details": sups,
             "views": [{"id": "dollars", "label": "$", "values": [half_up(full[l]) for l in labels], "format": "money0"},
                       {"id": "pct", "label": "% of total", "values": [round(100 * full[l] / sum(full.values()), 1) for l in labels], "format": "pct1"}]}
    spend, budgets = {}, {}
    for code, mo, sp_, bud in gsm:
        if mo in MONTHS:
            spend.setdefault(code, {})[mo] = sp_
            budgets.setdefault(code, {})[mo] = bud
    code_of = {g["program"]: g["code"] for g in G}
    views, tx = {}, {}
    def view(name, codes):
        vals = [sum(spend.get(c, {}).get(m, 0) for c in codes) for m in MONTHS]
        buds = [sum(budgets.get(c, {}).get(m, 0) for c in codes) for m in MONTHS]
        return {"label": "Spend $", "values": vals, "format": "money0",
                "supports": [support(f"{name}, {mlabel(m)}", "Grant spending recorded in the month, against the monthly budget",
                                     [inp("Spent in the month (ledger)", "money", [v]), inp("Monthly budget", "money", [bd]), calc("Over (under) budget", "money", "r0-r1")],
                                     cols=(mlabel(m),)) for m, v, bd in zip(MONTHS, vals, buds)]}
    views["All|spend"] = view("All programs", list(spend))
    top = labels[0]
    tx["All"] = text(f"{top} is the biggest program: {money(full[top])} in September once its share of untied program costs and administration is added to "
                     f"{money(direct[top])} of grant spending. Shared costs add {FMT['pct']((x['untied'] + x['admin']) / tot)} on top of grant spending across all programs.",
                     "Quote the full cost (not just the grant line) when applying for renewals, and check each funder lets you recover a share of overheads. Pick a program above to see it on its own.")
    for g in G:
        l = g["program"]
        views[f"{l}|spend"] = view(l, [g["code"]])
        shared = full[l] - direct[l]
        tx[l] = text(f"{l} cost {money(full[l])} in full in September: {money(direct[l])} paid by the {g['funder']} grant, and {money(shared)} of shared costs "
                     f"no grant covers. It has spent {FMT['pct'](g['spent_to_date'] / g['budget_to_date'])} of its budget to date, with {money(g['unspent'])} "
                     f"left and {g['months_left']} months to go.",
                     f"When this grant is renewed, ask for the full {money(full[l])} a month (or as much of the {money(shared)} shared cost as the funder allows), "
                     "not just the program spending.")
    return {"slug": "program-cost", "audience": "nfp", "question": "What does each program really cost?",
            "org": "nfp", "business": res["nfp"]["model"]["long_name"],
            "intro": "Each program's full cost: what its grant pays for, plus its fair share of the costs no single grant covers (untied program costs and administration, shared by grant spending). Pick a program and every chart and note follows it.",
            "blocks": [{"label": None, "filter": filt("Program", [("All", "All programs")] + [(l, l) for l in labels]), "sections": [
                {"type": "bars", "chart": chart, "highlight_filter": True}, vary(tx),
                series("Grant spending, by month", MONTHS, views, note="Grant spending only (the program's direct cost). All programs includes grants that have finished. Tap a month for its workings.",
                       dims={"line": ["All"] + labels, "measure": [("spend", "Spend $")]})]}],
            "data": {"head": ["Program", "Grant spending, Sep", "Share", "Untied costs share", "Administration share", "Full cost"],
                     "kinds": ["text", "money", "pct", "money", "money", "money"],
                     "inputs": [("tot", "All grant-funded program spending, September", tot, "money"),
                                ("untied", "Untied program costs, September (all programs)", x["untied"], "money"),
                                ("admin", "Administration, September (all)", x["admin"], "money")],
                     "rows": [[l, direct[l], "=B{r}/{tot}", "=C{r}*{untied}", "=C{r}*{admin}", "=B{r}+D{r}+E{r}"] for l in labels]}}


def runway(res, bal):
    ex = res["nfp"]["examples"][2]
    f4 = res["nfp"]["fourth"]
    days_ = [r for r in bal if r[1] == "nfp"]
    days_.sort()
    lab = [date(r[0] // 10000, r[0] // 100 % 100, r[0] % 100) for r in days_]
    opening = res["nfp"]["out"]["bs"]["2026-07"]["cash"]
    stat = [ds.day_status(d) for d in lab]
    return {"slug": "runway", "audience": "nfp", "question": "How many months of runway do we have?",
            "org": "nfp", "business": res["nfp"]["model"]["long_name"],
            "intro": "How long the organisation could keep going on its own money: cash at bank, less unspent grant money (which belongs to the funders' programs), divided by a month's spending.",
            "blocks": [{"label": None, "sections": [
                kpis([kpi(i["label"], i["value"], i.get("sub", ""), ex["support"]) for i in ex["visual"]["kpis"]]
                     + [kpi("Runway in August", FMT["months"](f4["kpis"][1]["support"]["xl"]["rows"][-1]["values"][1]), "at August's rate of spending", f4["kpis"][1]["support"])]),
                text(ex["shows"], ex["action"]),
                {"type": "series", "title": "Cash at bank, every day (1 Aug to 6 Oct)", "labels": [d.strftime("%-d %b") for d in lab],
                 "months": [d.isoformat() for d in lab], "status": stat,
                 "views": {"All|cash": {"label": "Cash at bank $", "values": [r[2] for r in days_], "format": "money0",
                                        "supports": [support(f"Cash at bank, {d.strftime('%-d %b %Y')}", "Yesterday's closing cash + the day's money in less money out",
                                                             [inp("Cash at bank, end of the day before", "money", [prev]), inp("Net money in (out) on the day", "money", [cur - prev]),
                                                              calc("Cash at bank, end of the day", "money", "r0+r1")], cols=(d.strftime("%-d %b"),))
                                                     for d, prev, cur in zip(lab, [opening] + [r[2] for r in days_[:-1]], [r[2] for r in days_])]}},
                 "dims": {"line": ["All"], "measure": [("cash", "Cash at bank $")]},
                 "note": "Cash at bank includes unspent grant money. Today (6 Oct) is incomplete; 1-5 October is provisional."}]}],
            "data": {"head": ["Date", "Status", "Cash at bank"], "kinds": ["text", "text", "money"],
                     "rows": [[d.isoformat(), s_, r[2]] for d, s_, r in zip(lab, stat, days_)]}}


def board(res, by_ml):
    n = res["nfp"]
    r = n["out"]["r"]
    f4 = n["fourth"]
    jul = nfp_month(by_ml, "2026-07")
    def ie(mo):
        if mo == "2026-07":
            g = jul["g"]
            inc = sum(v for v in g.values() if v > 0)
            exp = -sum(v for v in g.values() if v < 0)
            return inc, exp
        return r[mo]["income"], r[mo]["expenses"]
    rows, ytd_i, ytd_e = [], 0, 0
    for mo in ["2026-07", "2026-08", "2026-09"]:
        i_, e_ = ie(mo)
        ytd_i += i_; ytd_e += e_
    sp = support("Year to date (July to September 2026)", "Income less expenses, financial year to date", [
        inp("Income, July", "money", [ie("2026-07")[0]]), inp("Income, August", "money", [ie("2026-08")[0]]), inp("Income, September", "money", [ie("2026-09")[0]]),
        calc("Income, year to date", "money", "r0+r1+r2"), inp("Expenses, July", "money", [ie("2026-07")[1]]), inp("Expenses, August", "money", [ie("2026-08")[1]]),
        inp("Expenses, September", "money", [ie("2026-09")[1]]), calc("Expenses, year to date", "money", "r4+r5+r6"), calc("Surplus, year to date", "money", "r3-r7")],
        "July is provisional history; August and September are locked.", cols=("FY2027 to date",))
    surplus_ytd = sp["xl"]["rows"][-1]["values"][0]
    ex = n["examples"]
    grants = [[g["program"], money(g["spent_to_date"]), money(g["budget_to_date"]), FMT["pct"](g["spent_to_date"] / g["budget_to_date"]),
               money(g["unspent"]), str(g["months_left"])] for g in sorted(n["out"]["grants"], key=lambda g: g["months_left"])]
    notes = [ex[2]["shows"], ex[1]["shows"], ex[0]["shows"]]
    return {"slug": "board", "audience": "nfp", "question": "What does the board need to see?",
            "org": "nfp", "business": n["model"]["long_name"],
            "intro": "A one-page board summary for September 2026: the result, the money, the risks, and the decisions to make. The full statements are in the downloads.",
            "blocks": [{"label": None, "sections": [
                kpis([kpi("Surplus, September", money(r["2026-09"]["surplus"]), f"August {money(r['2026-08']['surplus'])}",
                          support("Surplus, September and August", "Income less expenses", [inp("Income", "money", [r["2026-09"]["income"], r["2026-08"]["income"]]),
                                  inp("Expenses", "money", [r["2026-09"]["expenses"], r["2026-08"]["expenses"]]), calc("Surplus", "money", "r0-r1")])),
                      kpi("Surplus (deficit), year to date", money(surplus_ytd), "July to September", sp),
                      kpi(f4["kpis"][1]["label"], f4["kpis"][1]["value"], f4["kpis"][1]["sub"], f4["kpis"][1]["support"]),
                      kpi(f4["kpis"][0]["label"], f4["kpis"][0]["value"], f4["kpis"][0]["sub"], f4["kpis"][0]["support"])]),
                {"type": "list", "title": "What the board should note", "items": notes},
                table("Grants", ["Program", "Spent to date", "Budget to date", "Against budget", "Still to spend", "Months left"], grants,
                      ["text", "money", "money", "pct", "money", "int"]),
                {"type": "list", "title": "Decisions to make", "items": [ex[2]["action"], ex[1]["action"], ex[0]["action"]]}]}],
            "data": {"head": ["Program", "Spent to date", "Budget to date", "Against budget", "Still to spend", "Months left"],
                     "kinds": ["text", "money", "money", "pct", "money", "int"],
                     "rows": [[g["program"], g["spent_to_date"], g["budget_to_date"], "=B{r}/C{r}", g["unspent"], g["months_left"]]
                              for g in sorted(n["out"]["grants"], key=lambda g: g["months_left"])]}}


def build(res, h, lm, by_ml, gsm, bal):
    global MONTHS
    import history
    MONTHS = history.HIST + ["2026-08", "2026-09"]
    return [cost_to_win(res, h), job_margins(res, h, lm), growing(res, h, lm),
            cost_to_raise(res, by_ml), program_cost(res, by_ml, gsm), runway(res, bal), funding(res, by_ml), board(res, by_ml)]
