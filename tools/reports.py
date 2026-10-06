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
    last12 = sum(mk[m] for m in MONTHS[-12:]) / sum(nc[m] for m in MONTHS[-12:])
    prev12 = sum(mk[m] for m in MONTHS[:12]) / sum(nc[m] for m in MONTHS[:12])
    s12 = support("Cost to win a customer, last 12 months against the 12 before",
                  "Total marketing ÷ total new customers, for each 12 months", [
                      inp("Marketing, Oct 2025 to Sep 2026", "money", [sum(mk[m] for m in MONTHS[-12:])]),
                      inp("New customers, Oct 2025 to Sep 2026", "int", [sum(nc[m] for m in MONTHS[-12:])]),
                      calc("Cost per customer, last 12 months", "money", "r0/r1"),
                      inp("Marketing, Oct 2024 to Sep 2025", "money", [sum(mk[m] for m in MONTHS[:12])]),
                      inp("New customers, Oct 2024 to Sep 2025", "int", [sum(nc[m] for m in MONTHS[:12])]),
                      calc("Cost per customer, the 12 before", "money", "r3/r4"),
                      calc("Change", "pct", "r2/r5-1")], cols=("12 months",))
    ex = res["trades"]["examples"][1]
    return {
        "slug": "cost-to-win", "audience": "sme", "question": "What does it cost to win a customer?",
        "org": "trades", "business": res["trades"]["model"]["long_name"],
        "intro": "Marketing spend divided by the customers it actually brought in (a customer's first ever job), month by month.",
        "blocks": [{"label": None, "sections": [
            kpis([kpi("September 2026", money(k["xl"]["rows"][2]["values"][0]), f"August {money(k['xl']['rows'][2]['values'][1])}", k),
                  kpi(f"September last year", money(mk[ly] / nc[ly]), f"{nc[ly]} new customers from {money(mk[ly])}", sup[-13]),
                  kpi("Last 12 months", money(last12), f"{FMT['pct'](last12 / prev12 - 1)} on the 12 before ({money(prev12)})", s12)]),
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
            rows_ = [inp("Revenue", "money", [rev[i]]), inp("Direct cost", "money", [cost[i]]), calc("Margin", "money", "r0-r1"),
                     calc("Margin %", "pct", "r2/r0")]
            if prev:
                rows_ += [inp(f"Revenue, {mlabel(MONTHS[i - 12])}", "money", [prev]), calc("Growth on the same month last year", "pct", "r0/r4-1")]
            sups.append(support(f"{line if line != 'All' else 'All lines'}, {mlabel(m)}", "Revenue less direct cost; growth against the same month last year", rows_, cols=(mlabel(m),)))
        views[f"{line}|revenue"] = {"label": "Revenue $", "values": rev, "format": "money0", "supports": sups}
        views[f"{line}|margin_pct"] = {"label": "Margin %", "values": [round(100 * a / b, 1) if b else 0 for a, b in zip(mar, rev)], "format": "pct1", "supports": sups}
        views[f"{line}|margin"] = {"label": "Margin $", "values": mar, "format": "money0", "supports": sups}
        views[f"{line}|growth"] = {"label": "Growth %", "values": [round(100 * (rev[i] / rev[i - 12] - 1), 1) if i >= 12 and rev[i - 12] else None for i in range(len(MONTHS))],
                                   "format": "pct1", "supports": sups}
        for i, m in enumerate(MONTHS):
            data_rows.append([line, mlabel(m), status(m), rev[i], cost[i]])
    return views, data_rows


def line_table(org, lm, lines):
    """Last 12 months against the 12 before, by line."""
    rows = []
    for line in lines + ["All"]:
        ls = lines if line == "All" else [line]
        r12 = sum(r[5] for r in lm if r[0] == org and r[3] in ls and r[1] in MONTHS[-12:])
        p12 = sum(r[5] for r in lm if r[0] == org and r[3] in ls and r[1] in MONTHS[:12])
        m12 = sum(r[7] for r in lm if r[0] == org and r[3] in ls and r[1] in MONTHS[-12:])
        rows.append([line if line != "All" else "Total", r12, p12, "=B{r}/C{r}-1", m12, "=E{r}/B{r}",
                     FMT["pct"](r12 / p12 - 1), FMT["pct"](m12 / r12)])
    return rows


def growing(res, h, lm):
    blocks = []
    for org, lines, noun in (("trades", ["Maintenance contracts", "Installations", "Call-outs and repairs"], "line"),
                             ("services", ["Projects", "Retainers", "Training"], "type of work")):
        views, data_rows = line_views(org, lm, lines)
        tab = line_table(org, lm, lines)
        best = max(tab[:-1], key=lambda r: r[1] / r[2] - 1)
        worst = min(tab[:-1], key=lambda r: r[4] / r[1])
        tot = tab[-1]
        sep, sepl = views["All|revenue"]["values"][-1], views["All|revenue"]["values"][-13]
        k1 = support("Revenue, September against September last year", "September 2026 ÷ September 2025 − 1",
                     [inp("Revenue, Sep 2026", "money", [sep]), inp("Revenue, Sep 2025", "money", [sepl]), calc("Growth", "pct", "r0/r1-1")], cols=("Sep",))
        k2 = support("Revenue, last 12 months against the 12 before", "Oct 2025 to Sep 2026 ÷ Oct 2024 to Sep 2025 − 1",
                     [inp("Last 12 months", "money", [tot[1]]), inp("The 12 before", "money", [tot[2]]), calc("Growth", "pct", "r0/r1-1")], cols=("12 months",))
        k3 = support("Margin, last 12 months", "Revenue less direct cost, over revenue",
                     [inp("Revenue, last 12 months", "money", [tot[1]]), inp("Margin, last 12 months", "money", [tot[4]]), calc("Margin %", "pct", "r1/r0")], cols=("12 months",))
        shows = (f"Revenue grew {FMT['pct'](tot[1] / tot[2] - 1)} on the year before ({money(tot[1])} against {money(tot[2])}). "
                 f"{best[0]} grew fastest ({best[6]}); {worst[0]} has the thinnest margin ({worst[7]}).")
        poss = lambda w: w.lower() + ("'" if w.lower().endswith("s") else "'s")
        action = (f"Put sales effort behind {best[0].lower()}, and before cutting anything, check what's dragging {poss(worst[0])} margin: "
                  "price, the hours it takes, or the materials. Every month is in the downloads.")
        blocks.append({"label": res[org]["model"]["name"], "business": res[org]["model"]["long_name"], "sections": [
            kpis([kpi("September against September last year", FMT["pct"](sep / sepl - 1), f"{money(sep)} against {money(sepl)}", k1),
                  kpi("Last 12 months against the 12 before", FMT["pct"](tot[1] / tot[2] - 1), f"{money(tot[1])} against {money(tot[2])}", k2),
                  kpi("Margin, last 12 months", FMT["pct"](tot[4] / tot[1]), f"{money(tot[4])} after direct costs", k3)]),
            series(f"Revenue, margin and growth by {noun}, by month", MONTHS, views,
                   note="Margin = revenue less direct cost (materials, subcontractors and time at cost for trades; contractors and consultant time for services). Growth compares each month with the same month a year earlier. Tap a month for its workings.",
                   dims={"line": ["All"] + lines, "measure": [("revenue", "Revenue $"), ("margin_pct", "Margin %"), ("margin", "Margin $"), ("growth", "Growth %")]}),
            table(f"By {noun}: last 12 months against the 12 before", ["", "Last 12 months", "The 12 before", "Growth", "Margin $", "Margin %"],
                  [[r_[0], money(r_[1]), money(r_[2]), r_[6], money(r_[4]), r_[7]] for r_ in tab], ["text", "money", "money", "pct", "money", "pct"]),
            text(shows, action)],
            "data": {"head": ["Line", "Month", "Status", "Revenue", "Direct cost", "Margin", "Margin %"],
                     "kinds": ["text", "text", "text", "money", "money", "money", "pct"],
                     "rows": [r_ + ["=D{r}-E{r}", "=IF(D{r}=0,\"\",F{r}/D{r})"] for r_ in data_rows]},
            "table_xl": {"head": ["Line", "Last 12 months", "The 12 before", "Growth", "Margin $", "Margin %"],
                         "kinds": ["text", "money", "money", "pct", "money", "pct"], "rows": [r_[:6] for r_ in tab]}})
    return {"slug": "growth", "audience": "sme", "question": "Which products and services are growing?",
            "org": "trades", "business": "SME sample businesses",
            "intro": "Revenue, margin and growth by product or service line over 24 months, so the decision about what to grow, fix or drop is made on numbers.",
            "blocks": blocks}


def job_margins(res, h, lm):
    f4 = res["trades"]["fourth"]
    ch = f4["chart"]
    ex = res["trades"]["examples"][0]
    lines = ["Maintenance contracts", "Installations", "Call-outs and repairs"]
    views, data_rows = line_views("trades", lm, lines)
    keep = {k: v for k, v in views.items() if k.split("|")[1] in ("margin_pct", "margin")}
    k_ = f4["kpis"][0]["support"]
    return {"slug": "job-margins", "audience": "sme", "question": "Which jobs actually make money?",
            "org": "trades", "business": res["trades"]["model"]["long_name"],
            "intro": "Every job costed: revenue less materials, subcontractors and technician time at $68 an hour. Installation jobs are shown whole, in the month they're invoiced.",
            "blocks": [{"label": None, "sections": [
                kpis([kpi("Gross margin, September", f4["kpis"][0]["value"], f4["kpis"][0]["sub"], k_)]),
                {"type": "bars", "chart": ch},
                text(ex["shows"], ex["action"]),
                series("Margin by type of job, by month", MONTHS, keep,
                       note="Tap a month for its workings.",
                       dims={"line": ["All"] + lines, "measure": [("margin_pct", "Margin %"), ("margin", "Margin $")]})]}],
            "data": {"head": ["Line", "Month", "Status", "Revenue", "Direct cost", "Margin", "Margin %"],
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


def cost_to_raise(res, by_ml):
    vals, sups, by_src = [], [], {"Grants": [], "Donations": [], "Fundraising events": []}
    for m in MONTHS:
        x = nfp_month(by_ml, m)
        cost, raised = x["gw"] + x["dc"] + x["ec"], x["grants"] + x["donations"] + x["events"]
        vals.append(half_up(100 * cost / raised))
        by_src["Grants"].append(half_up(100 * x["gw"] / x["grants"]) if x["grants"] else None)
        by_src["Donations"].append(half_up(100 * x["dc"] / x["donations"]) if x["donations"] else None)
        by_src["Fundraising events"].append(half_up(100 * x["ec"] / x["events"]) if x["events"] else None)
        sups.append(support(f"Cost to raise a dollar, {mlabel(m)}", "Fundraising costs ÷ money raised, in cents", [
            inp("Grant writing and reporting", "money", [x["gw"]]), inp("Donor campaigns", "money", [x["dc"]]), inp("Event costs", "money", [x["ec"]]),
            calc("Fundraising costs", "money", "r0+r1+r2"), inp("Grant income", "money", [x["grants"]]), inp("Donations", "money", [x["donations"]]),
            inp("Fundraising events", "money", [x["events"]]), calc("Money raised", "money", "r4+r5+r6"),
            calc("Cost per dollar raised", "cents", "r3/r7*100")], cols=(mlabel(m),)))
    f4 = res["nfp"]["fourth"]
    ex = res["nfp"]["examples"][0]
    k = f4["kpis"][0]
    tot = lambda ms: (sum(nfp_month(by_ml, m)["gw"] + nfp_month(by_ml, m)["dc"] + nfp_month(by_ml, m)["ec"] for m in ms),
                      sum(nfp_month(by_ml, m)["grants"] + nfp_month(by_ml, m)["donations"] + nfp_month(by_ml, m)["events"] for m in ms))
    c12, r12 = tot(MONTHS[-12:])
    c0, r0 = tot(MONTHS[:12])
    s12 = support("Cost to raise a dollar, last 12 months against the 12 before", "Fundraising costs ÷ money raised, in cents", [
        inp("Fundraising costs, last 12 months", "money", [c12]), inp("Money raised, last 12 months", "money", [r12]),
        calc("Cents per dollar, last 12 months", "cents", "r0/r1*100"), inp("Fundraising costs, the 12 before", "money", [c0]),
        inp("Money raised, the 12 before", "money", [r0]), calc("Cents per dollar, the 12 before", "cents", "r3/r4*100")], cols=("12 months",))
    return {"slug": "cost-to-raise", "audience": "nfp", "question": "What does it cost to raise a dollar?",
            "org": "nfp", "business": res["nfp"]["model"]["long_name"],
            "intro": "What fundraising costs (grant writing, donor campaigns, events) for every dollar it brings in, month by month and by source.",
            "blocks": [{"label": None, "sections": [
                kpis([kpi("September 2026", k["value"], k["sub"], k["support"]),
                      kpi("Last 12 months", f"{half_up(100 * c12 / r12)}¢", f"the 12 before: {half_up(100 * c0 / r0)}¢", s12)]),
                series("Cost to raise a dollar, by month (cents)", MONTHS, {
                    "All|cents": {"label": "All fundraising", "values": vals, "format": "cents_int", "supports": sups},
                    **{f"{s}|cents": {"label": s, "values": v, "format": "cents_int", "supports": sups} for s, v in by_src.items()}},
                    note="September and December include the gala and the Christmas appeal. Tap a month for its workings.",
                    dims={"line": ["All"] + list(by_src), "measure": [("cents", "Cents per $1")]}),
                {"type": "bars", "chart": dict(res["nfp"]["examples"][0]["visual"]["chart"], details=None), "support": ex["support"]},
                text(f"September cost {vals[-1]}¢ to raise each dollar, against {vals[-2]}¢ in August: the gala raised "
                     f"{money(nfp_month(by_ml, '2026-09')['events'])} but cost {money(nfp_month(by_ml, '2026-09')['ec'])}. "
                     f"Over the last 12 months it cost {half_up(100 * c12 / r12)}¢ a dollar, against {half_up(100 * c0 / r0)}¢ the year before.",
                     "Watch the 12-month figure, not single months: events make September and December jump. If the 12-month figure rises two quarters running, "
                     "review the event program first.")]}],
            "data": {"head": ["Month", "Status", "Grant writing", "Donor campaigns", "Event costs", "Grant income", "Donations", "Events", "Cents per $1"],
                     "kinds": ["text", "text", "money", "money", "money", "money", "money", "money", "cents"],
                     "rows": [[mlabel(m), status(m), nfp_month(by_ml, m)["gw"], nfp_month(by_ml, m)["dc"], nfp_month(by_ml, m)["ec"],
                               nfp_month(by_ml, m)["grants"], nfp_month(by_ml, m)["donations"], nfp_month(by_ml, m)["events"],
                               "=SUM(C{r}:E{r})/SUM(F{r}:H{r})*100"] for m in MONTHS]}}


def funding(res, by_ml):
    ex = res["nfp"]["examples"][0]
    views, rows_ = {}, []
    for src, inc, cst in (("Grants", "grants", "gw"), ("Donations", "donations", "dc"), ("Fundraising events", "events", "ec")):
        inc_v = [nfp_month(by_ml, m)[inc] for m in MONTHS]
        cst_v = [nfp_month(by_ml, m)[cst] for m in MONTHS]
        sups = [support(f"{src}, {mlabel(m)}", "Raised, cost of raising it, and what's left", [inp("Raised", "money", [a]), inp("Cost of raising it", "money", [b]),
                calc("Left after fundraising costs", "money", "r0-r1"), calc("Cost per dollar raised", "cents", "r1/r0*100") if a else inp("Cost per dollar raised", "cents", [0])],
                cols=(mlabel(m),)) for m, a, b in zip(MONTHS, inc_v, cst_v)]
        views[f"{src}|raised"] = {"label": "Raised $", "values": inc_v, "format": "money0", "supports": sups}
        views[f"{src}|net"] = {"label": "Left after costs $", "values": [a - b for a, b in zip(inc_v, cst_v)], "format": "money0", "supports": sups}
        rows_ += [[src, mlabel(m), status(m), a, b] for m, a, b in zip(MONTHS, inc_v, cst_v)]
    tab = []
    for src, inc, cst in (("Grants", "grants", "gw"), ("Donations", "donations", "dc"), ("Fundraising events", "events", "ec")):
        a = sum(nfp_month(by_ml, m)[inc] for m in MONTHS[-12:]); b = sum(nfp_month(by_ml, m)[cst] for m in MONTHS[-12:])
        tab.append([src, money(a), money(b), money(a - b), f"{half_up(100 * b / a)}¢"])
    return {"slug": "funding", "audience": "nfp", "question": "Which funding is worth chasing?",
            "org": "nfp", "business": res["nfp"]["model"]["long_name"],
            "intro": "Each source of money compared on what it raises and what it costs to raise, this month and over 24 months.",
            "blocks": [{"label": None, "sections": [
                {"type": "bars", "chart": dict(ex["visual"]["chart"], details=None), "support": ex["support"]},
                text(ex["shows"], ex["action"]),
                table("Last 12 months, by source", ["", "Raised", "Cost of raising it", "Left after costs", "Cost per $1"], tab,
                      ["text", "money", "money", "money", "cents"]),
                series("Raised and left after costs, by source, by month", MONTHS, views,
                       note="Tap a month for its workings.",
                       dims={"line": ["Grants", "Donations", "Fundraising events"], "measure": [("raised", "Raised $"), ("net", "Left after costs $")]})]}],
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
    top = labels[0]
    over = {}
    for code, mo, spend, budget in gsm:
        if mo in MONTHS:
            over.setdefault(code, {})[mo] = spend
    names = {g["code"]: g["program"] for g in res["nfp"]["out"]["grants"]}
    import history
    names.update({g[0]: g[2] for g in history.NFP_PAST_GRANTS})
    progs = sorted(over, key=lambda c: -sum(over[c].values()))
    budgets = {}
    for code, mo, spend, budget in gsm:
        budgets.setdefault(code, {})[mo] = budget
    views = {f"{names[c]}|spend": {"label": "Spend $", "values": [over[c].get(m, 0) for m in MONTHS], "format": "money0",
                                   "supports": [support(f"{names[c]}, {mlabel(m)}", "Grant spending recorded in the month, against the grant's monthly budget",
                                                        [inp("Spent in the month (ledger)", "money", [over[c].get(m, 0)]),
                                                         inp("Monthly budget", "money", [budgets.get(c, {}).get(m, 0)]),
                                                         calc("Over (under) budget", "money", "r0-r1")], cols=(mlabel(m),)) for m in MONTHS]}
             for c in progs}
    shows = (f"{top} is the biggest program: {money(full[top])} in September once its share of untied program costs and administration is added to "
             f"{money(direct[top])} of grant spending. Shared costs add {FMT['pct']((x['untied'] + x['admin']) / tot)} on top of grant spending across all programs.")
    action = "Quote this full cost (not just the grant line) when applying for renewals, and check each funder lets you recover a share of overheads."
    return {"slug": "program-cost", "audience": "nfp", "question": "What does each program really cost?",
            "org": "nfp", "business": res["nfp"]["model"]["long_name"],
            "intro": "Each program's full cost: what its grant pays for, plus its fair share of the costs no single grant covers (untied program costs and administration, shared by grant spending).",
            "blocks": [{"label": None, "sections": [
                {"type": "bars", "chart": chart}, text(shows, action),
                series("Spending on each program, by month", MONTHS, views, note="Grant spending only. Finished grants are included.",
                       dims={"line": [names[c] for c in progs], "measure": [("spend", "Spend $")]})]}],
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
