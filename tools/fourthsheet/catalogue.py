"""
catalogue.py — the eight reports, each worked out from the data for any reporting period.

    report = REPORTS["job-margins"](data, period)

Nothing here is typed in: every number comes from the data source (source.py) for the period asked for,
and every sentence is written from those numbers. Each report carries:
  - sections: headline numbers, bar charts (categories), area charts (months), tables, notes
  - workings behind every number (inputs + calculation; the Excel version turns them into formulas)
  - the data status of every month (Locked / Provisional / Incomplete)
"""

from datetime import date

import data_status as ds
import exportkit as ek
from financial_model import FMT, calc, half_up, inp, money, support

from .period import add_months, mdate, mlabel

pct = FMT["pct"]
TRADE_LINES = ["Maintenance contracts", "Installations", "Call-outs and repairs"]
SERVICE_LINES = ["Projects", "Retainers", "Training"]


# ------------------------------------------------------------------ section helpers

def kpis(items):
    return {"type": "kpis", "items": items}


def kpi(label, value, sub, sp, cls="", tone=""):
    """tone: 'good' / 'warn' / 'bad' when the value is judged against a target (colour by meaning, not sign)."""
    return {"label": label, "value": value, "sub": sub, "cls": cls, "support": sp, "tone": tone}


def text(shows, action):
    return {"type": "text", "shows": shows, "action": action}


def table(title, head, rows, kinds, note=None):
    return {"type": "table", "title": title, "head": head, "rows": rows, "kinds": kinds, "note": note}


def filt(label, options):
    return {"label": label, "options": options}


def vary(by):
    return {"type": "vary", "by": by}


def series(P, title, views, note=None, dims=None):
    return {"type": "series", "title": title, "labels": [mlabel(m) for m in P.window], "months": P.window,
            "status": [P.status_of(m) for m in P.window], "views": views, "dims": dims, "note": note}


def cents(cost, raised):
    return f"{half_up(100 * cost / raised)}¢" if raised else "–"


def ratio(a, b):
    return a / b if b else None


def growth_text(a, b):
    return pct(a / b - 1) if b else "–"


# ------------------------------------------------------------------ shared data shapes

def jobs(src):
    dim = {j["job_id"]: j for j in src.table("trades", "dim_job")}
    return [dict(month=r["month_key"], id=r["job_id"], type=dim[r["job_id"]]["job_type"], description=dim[r["job_id"]]["description"],
                 revenue=r["revenue"], labour_revenue=r["labour_revenue"], materials_revenue=r["materials_revenue"],
                 materials=r["materials"], subcontractors=r["subcontractors"], hours=r["tech_hours"],
                 labour_cost=r["labour_cost"], gross_profit=r["gross_profit"]) for r in src.table("trades", "fact_job_month")]


def engagements(src):
    dim = {e["engagement_id"]: e for e in src.table("services", "dim_engagement")}
    return [dict(month=r["month_key"], id=r["engagement_id"], type=dim[r["engagement_id"]]["engagement_type"],
                 description=dim[r["engagement_id"]]["description"], revenue=r["revenue"], hours=r["hours"], contractors=r["contractors"],
                 time_cost=r["consultant_time_cost"], contribution=r["contribution"]) for r in src.table("services", "fact_engagement_month")]


def lines_by_month(D, org, lines):
    out = {}
    for r in D[org].lines:
        out[(r["month_key"], r["line"])] = r
    return out


ONCOSTS = "Wages always include all on-costs: super, payroll tax, workers' compensation insurance and leave."


def definition(D, org):
    rate = D[org].rates["Technician cost rate" if org == "trades" else "Consultant cost rate"]
    txt = {"trades": ("Gross margin is not profit. Job gross margin = revenue less materials, subcontractors and technician time charged to the job at "
                      f"${rate} an hour (wages and all on-costs). Not included: technician time not charged to any job (travel, training, waiting), and overheads "
                      "(office wages, marketing, vehicles, rent, insurance, IT, depreciation, interest). Profit is what's left after those. " + ONCOSTS),
           "services": ("Gross margin is not profit. Gross margin = revenue less contractors and consultant time charged to the work at "
                        f"${rate} an hour (wages and all on-costs). Not included: consultant time not charged to clients, and overheads (management and admin wages, "
                        "marketing, rent, IT, insurance, travel, depreciation, interest). Profit is what's left after those. " + ONCOSTS)}[org]
    return {"type": "definition", "title": "Gross margin, not profit", "text": txt, "link": "numbers-explained.html#gross-margin"}


def pnl(D, org, mo):
    """The month's P&L from the ledger: revenue, gross profit, overheads, profit before tax, and the work's own gross margin."""
    o = D[org]
    revenue = o.section(mo, "Revenue")
    gp = revenue + o.section(mo, "Cost of sales")
    pbt = gp + sum(v for k, v in o.by_line(mo).items() if o.sections.get(k) == "Operating expenses" and not k.startswith("Income tax"))
    if org == "trades":
        wages = -o.line(mo, "Technician wages (incl. on-costs)")
        js = [j for j in D["_jobs"] if j["month"] == mo]
        charged, gm_work = sum(j["labour_cost"] for j in js), sum(j["gross_profit"] for j in js)
    else:
        wages = -o.line(mo, "Consultant salaries (incl. on-costs)")
        es = [e for e in D["_engagements"] if e["month"] == mo]
        charged, gm_work = sum(e["time_cost"] for e in es), sum(e["contribution"] for e in es)
    if gm_work - (wages - charged) != gp:
        raise SystemExit(f"{org} {mo}: the work's gross margin ({gm_work}) less time not charged ({wages - charged}) doesn't tie to the ledger's gross profit ({gp})")
    return dict(revenue=revenue, gp=gp, pbt=pbt, wages=wages, charged=charged, gm_work=gm_work, overheads=gp - pbt)


def bridge(D, P, org):
    """From the month's gross margin on the work to profit before tax, tied to the P&L (the latest complete month)."""
    mo = P.full
    r = pnl(D, org, mo)
    who = "Technician" if org == "trades" else "Consultant"
    work = "jobs" if org == "trades" else "client work"
    lab = mdate(mo).strftime("%B %Y")
    sp = support(f"From gross margin to profit, {lab}", "Gross margin on the work − time not charged − overheads = profit before tax", [
        inp(f"Gross margin on {work}", "money", [r["gm_work"]]), inp(f"{who} wages and on-costs", "money", [r["wages"]]),
        inp(f"{who} time charged to {work} (at cost)", "money", [r["charged"]]), calc(f"{who} time not charged to {work}", "money", "r1-r2"),
        calc("Gross profit (the P&L)", "money", "r0-r3"), inp("Overheads (operating expenses, depreciation, interest)", "money", [r["overheads"]]),
        calc("Profit before tax (the P&L)", "money", "r4-r5"), inp("Revenue", "money", [r["revenue"]]),
        calc(f"Gross margin on {work}, %", "pct", "r0/r7"), calc("Profit before tax, % of revenue", "pct", "r6/r7"),
        calc(f"Gross margin {work} need just to cover overheads and time not charged", "pct", "(r3+r5)/r7")],
        f"Ties to the {lab} P&L ({P.status_of(mo).lower()}). " + ONCOSTS + (f" {P.month} is still in progress, so this uses {P.full_month}." if P.incomplete else ""),
        cols=(mdate(mo).strftime("%b %Y"),))
    x = sp["xl"]["rows"]
    if round(x[4]["values"][0]) != r["gp"] or round(x[6]["values"][0]) != r["pbt"]:
        raise SystemExit(f"bridge for {org} {mo} doesn't tie to the P&L")
    v = lambda i: x[i]["values"][0]
    pre = (f"{P.month} is still in progress and wages are paid fortnightly, so a part month can't be bridged: this is {P.full_month}, the latest closed month. "
           if P.incomplete else "")
    line = (pre + f"{P.full_month}'s {work} made {money(v(0))} gross margin ({pct(v(8))}). {who} time not charged to {work} took {money(v(3))} and overheads "
            f"{money(v(5))}, leaving {money(v(6))} profit before tax ({pct(v(9))} of revenue). To cover overheads, {work} {'need' if work == 'jobs' else 'needs'} a "
            f"{pct(v(10))} gross margin on average.")
    title = "From gross margin to profit" + (f" · latest closed month: {P.full_month}" if P.incomplete else "")
    return {"type": "insight", "title": title, "text": line, "support": sp, "period": lab}


def break_even(D, P, org):
    r = pnl(D, org, P.full)
    return ((r["wages"] - r["charged"]) + r["overheads"]) / r["revenue"]


def quant_flag(name, gm, rev, target, be, when):
    """A flag, not an instruction: the gross margin against the target, and what the gap is worth in dollars.
    target and be are fractions; rev is the revenue the margin was earned on; when e.g. 'in September'."""
    if rev <= 0:
        return f"{name}: no revenue {when}."
    if gm < 0:
        return f"{name}: {pct(gm)} gross margin, {money(-gm * rev)} lost before overheads on {money(rev)} of revenue {when}."
    if gm < target:
        tail = f" It's below the {pct(be)} needed to cover overheads, too." if gm < be else ""
        return (f"{name}: {pct(gm)} gross margin, {100 * (target - gm):.1f} points under the {100 * target:.1f}% target: "
                f"about {money((target - gm) * rev)} on {money(rev)} of revenue {when}.{tail}")
    return f"{name}: {pct(gm)} gross margin, {100 * (gm - target):.1f} points over the {100 * target:.1f}% target ({money((gm - target) * rev)} ahead on {money(rev)} {when})."


def margin_action(name, gm, be):
    if gm < 0:
        return f"{name}: {pct(gm)} gross margin. Losing money before overheads."
    if gm < be:
        return f"{name}: {pct(gm)} gross margin, below the {pct(be)} needed to cover overheads."
    return f"{name}: {pct(gm)} gross margin, {round(100 * (gm - be), 1):.1f} points clear of the {pct(be)} overheads need."


def margin_chart(title, subtitle, labels, rev, gp, target, details, be=None):
    """Bars with a gross margin % / $ toggle; the $ view marks each item's target gross margin. be (a fraction) adds the
    break-even line (the gross margin that just covers overheads and time not charged) beside the target."""
    pct_ = [round(100 * g / r, 1) if r else 0 for g, r in zip(gp, rev)]
    bev = round(100 * be, 1) if be is not None else None
    if bev is not None:
        subtitle = (subtitle + f" Target {float(target):.1f}% is what to price for; break-even {bev:.1f}% only covers overheads and time not charged.").strip()
    return {"title": title, "subtitle": subtitle, "labels": labels, "values": pct_, "target": float(target), "breakeven": bev, "format": "pct1", "details": details,
            "views": [{"id": "pct", "label": "Gross margin %", "values": pct_, "format": "pct1", "target": float(target), "breakeven": bev},
                      {"id": "dollars", "label": "Gross margin $", "values": gp, "format": "money0",
                       "marks": [half_up(r * target / 100) for r in rev], "mark_label": f"Target gross margin ({target:.1f}% of revenue)", "below_marks": True}]}


def job_support(j, rate):
    return support(j["description"], "Job gross margin ÷ revenue for this job (before overheads)", [
        inp("Revenue", "money", [j["revenue"]]), inp("Materials", "money", [-j["materials"]]), inp("Subcontractors", "money", [-j["subcontractors"]]),
        inp("Technician hours", "hours", [j["hours"]]), inp("Technician cost rate ($/hour, wages and all on-costs)", "money", [rate]),
        calc("Technician time", "money", "-r3*r4"), calc("Job gross margin", "money", "r0+r1+r2+r5"), calc("Job gross margin %", "pct", "r6/r0")], cols=("This job",))


def report(slug, audience, question, org, D, P, intro, blocks, data=None, answer=None):
    """answer: the question answered in one sentence (the report's card on the SME / not-for-profit page)."""
    return {"slug": slug, "answer": answer, "audience": audience, "question": question, "org": org,
            "business": D[org].about["legal_name"] if org in D else "SME sample businesses",
            "intro": intro, "blocks": blocks, "data": data, "period": P.mo, "period_label": P.label, "period_short": P.short,
            "period_status": P.status, "status_months": P.status_months, "part_note": P.part_note}


# ======================================================================= SME

def cost_to_win(D, P):
    o = D["trades"]
    mk = {m: -o.line(m, "Marketing") for m in o.months}
    nc = o.drivers["New customers (first job ever)"]
    W = P.window

    def sp_month(m):
        return support(f"Cost to win a customer, {mlabel(m)}", "Marketing spend ÷ new customers",
                       [inp("Marketing spend (ledger)", "money", [mk[m]]), inp("New customers (first job ever)", "int", [nc[m]]),
                        calc("Cost per new customer", "money", "r0/r1")], cols=(mlabel(m),))
    sup = [sp_month(m) for m in W]
    k = support(f"Cost to win a customer, {P.month} and {P.prev_month}", "Marketing spend ÷ new customers", [
        inp("Marketing spend (ledger)", "money", [mk[P.mo], mk[P.prev]]), inp("New customers (first job ever)", "int", [nc[P.mo], nc[P.prev]]),
        calc("Cost per new customer", "money", "r0/r1")], P.part_note or None, cols=(mlabel(P.mo), mlabel(P.prev)))
    ytd_m, ytd_c = sum(mk[m] for m in P.fytd), sum(nc[m] for m in P.fytd)
    items = [kpi(P.label, money(mk[P.mo] / nc[P.mo]), f"{P.prev_month} {money(mk[P.prev] / nc[P.prev])}", k)]
    if P.ly_ok:
        items.append(kpi(f"{P.month} last year", money(mk[P.ly] / nc[P.ly]), f"{nc[P.ly]} new customers from {money(mk[P.ly])}", sp_month(P.ly)))
    if P.pfytd_ok:
        pm, pc = sum(mk[m] for m in P.pfytd), sum(nc[m] for m in P.pfytd)
        s12 = support("Cost to win a customer, year to date against the same period last year", "Total marketing ÷ total new customers, for each period", [
            inp(f"Marketing, {P.fytd_l}", "money", [ytd_m]), inp(f"New customers, {P.fytd_l}", "int", [ytd_c]), calc("Cost per customer, year to date", "money", "r0/r1"),
            inp(f"Marketing, {P.pfytd_l}", "money", [pm]), inp(f"New customers, {P.pfytd_l}", "int", [pc]),
            calc("Cost per customer, same period last year", "money", "r3/r4"), calc("Change", "pct", "r2/r5-1")], P.part_note or None, cols=("Year to date",))
        items.append(kpi(P.ytd_name, money(ytd_m / ytd_c), f"{pct((ytd_m / ytd_c) / (pm / pc) - 1)} on the same period last year ({money(pm / pc)})", s12))
    else:
        s12 = support(f"Cost to win a customer, {P.fy} to date", "Total marketing ÷ total new customers", [
            inp(f"Marketing, {P.fytd_l}", "money", [ytd_m]), inp(f"New customers, {P.fytd_l}", "int", [ytd_c]), calc("Cost per customer, year to date", "money", "r0/r1")],
            "The same period last year is " + P.no_ly[0].lower() + P.no_ly[1:], cols=("Year to date",))
        items.append(kpi(P.ytd_name, money(ytd_m / ytd_c), "same period last year: not in the data", s12))
    cpc, cpp = mk[P.mo] / nc[P.mo], mk[P.prev] / nc[P.prev]
    shows = (f"{nc[P.mo]} new customers came from {money(mk[P.mo])} of marketing in {P.when}, against {nc[P.prev]} from {money(mk[P.prev])} in {P.prev_month}: "
             f"{money(cpc)} each, {'down' if cpc < cpp else 'up'} from {money(cpp)}." + (f" {P.part_note}" if P.incomplete else ""))
    action = ("A lower cost per customer with steady spend usually means the marketing mix is working. Recording where each new customer came from shows the cost per channel."
              if cpc <= cpp else "Worth knowing which channels brought this month's customers in: recording the source of each new customer shows the cost per channel.")
    answer = f"{money(cpc)} per new customer in {P.when}: {nc[P.mo]} new customers from {money(mk[P.mo])} of marketing."
    r = report("cost-to-win", "sme", "What does it cost to win a customer?", "trades", D, P,
                  "Marketing spend divided by the customers it actually brought in (a customer's first ever job), month by month.",
                  [{"label": None, "sections": [
                      kpis(items),
                      series(P, "Cost to win a customer, by month", {
                          "All|cost": {"label": "$ per new customer", "values": [half_up(mk[m] / nc[m]) for m in W], "format": "money0", "supports": sup},
                          "All|customers": {"label": "New customers", "values": [nc[m] for m in W], "format": "int", "supports": sup},
                          "All|marketing": {"label": "Marketing $", "values": [mk[m] for m in W], "format": "money0", "supports": sup}},
                          note="Customers are counted in the month of their first job. Tap a month for its workings.",
                          dims={"line": ["All"], "measure": [("cost", "$ per new customer"), ("customers", "New customers"), ("marketing", "Marketing $")]}),
                      text(shows, action)]}],
                  {"head": ["Month", "Status", "Marketing spend", "New customers", "Cost per new customer"],
                   "kinds": ["text", "text", "money", "int", "money"],
                   "rows": [[mlabel(m), P.status_of(m), mk[m], nc[m], "=C{r}/D{r}"] for m in W]}, answer)
    later = [m for m in o.months if m > max(nc)]
    if later:      # the month in progress has no count yet
        r["periods_note"] = f"No {mdate(later[0]).strftime('%B')} yet: new customers are counted at month end."
    return r


def line_kpis(D, P, org, line, lines):
    ls = lines if line == "All" else [line]
    o = D[org]
    tot = lambda mo, k: sum(o.line_month(mo, l)[k] for l in ls)
    nm = "All lines" if line == "All" else line
    sp_m = support(f"{nm}: gross margin, {P.month} and {P.prev_month}", "Revenue less direct cost, over revenue. Before overheads.", [
        inp("Revenue", "money", [tot(P.mo, "revenue"), tot(P.prev, "revenue")]), inp("Direct cost", "money", [tot(P.mo, "direct_cost"), tot(P.prev, "direct_cost")]),
        calc("Gross margin", "money", "r0-r1"), calc("Gross margin %", "pct", "r2/r0")], P.part_note or None, cols=(mlabel(P.mo), mlabel(P.prev)))
    r12 = sum(tot(m, "revenue") for m in P.fytd)
    m12 = sum(tot(m, "gross_margin") for m in P.fytd)
    p12 = sum(tot(m, "revenue") for m in P.pfytd) if P.pfytd_ok else None
    sp_y = (support(f"{nm}: {P.month} against {P.month} last year", f"{P.label} ÷ {mdate(P.ly).strftime('%B %Y')} − 1 (year on year)",
                    [inp(f"Revenue, {P.short}", "money", [tot(P.mo, "revenue")]), inp(f"Revenue, {mdate(P.ly).strftime('%b %Y')}", "money", [tot(P.ly, "revenue")]),
                     calc("Growth", "pct", "r0/r1-1")], P.part_note or None, cols=(mdate(P.mo).strftime("%b"),)) if P.ly_ok else None)
    rows = [inp(f"Revenue, year to date ({P.fytd_l})", "money", [r12])]
    if p12:
        rows += [inp(f"Revenue, same period last year ({P.pfytd_l})", "money", [p12]), calc("Growth", "pct", "r0/r1-1"),
                 inp("Gross margin, year to date", "money", [m12]), calc("Gross margin %, year to date", "pct", "r3/r0")]
    else:
        rows += [inp("Gross margin, year to date", "money", [m12]), calc("Gross margin %, year to date", "pct", "r1/r0")]
    sp_12 = support(f"{nm}: year to date" + (" against the same period last year" if p12 else ""),
                    f"{P.fytd_l} ÷ {P.pfytd_l} − 1 (financial year to date)" if p12 else "Financial year to date. " + P.no_ly, rows,
                    P.part_note or None, cols=("Year to date",))
    xm = sp_m["xl"]["rows"][3]["values"]
    return {"cur": tot(P.mo, "revenue"), "cur_cost": tot(P.mo, "direct_cost"), "prev": tot(P.prev, "revenue"),
            "ly": tot(P.ly, "revenue") if P.ly_ok else None, "cur_m": xm[0], "prev_m": xm[1],
            "r12": r12, "p12": p12, "m12": m12, "sp_m": sp_m, "sp_y": sp_y, "sp_12": sp_12}


def line_views(D, P, org, lines):
    o = D[org]
    W = P.window
    views, data_rows = {}, []
    for line in ["All"] + lines:
        ls = lines if line == "All" else [line]
        rev = [sum(o.line_month(m, l)["revenue"] for l in ls) for m in W]
        cost = [sum(o.line_month(m, l)["direct_cost"] for l in ls) for m in W]
        mar = [a - b for a, b in zip(rev, cost)]
        ly = {m: sum(o.line_month(add_months(m, -12), l)["revenue"] for l in ls) if add_months(m, -12) in o.months else None for m in W}
        sups = []
        for i, m in enumerate(W):
            rows_ = [inp("Revenue", "money", [rev[i]]), inp("Direct cost", "money", [cost[i]]), calc("Gross margin", "money", "r0-r1")]
            rows_ += [calc("Gross margin %", "pct", "r2/r0")]
            if ly[m]:
                rows_ += [inp(f"Revenue, {mlabel(add_months(m, -12))}", "money", [ly[m]]), calc("Growth on the same month last year", "pct", "r0/r4-1")]
            sups.append(support(f"{'All lines' if line == 'All' else line}, {mlabel(m)}", "Revenue less direct cost; growth against the same month last year", rows_, cols=(mlabel(m),)))
        views[f"{line}|revenue"] = {"label": "Revenue $", "values": rev, "format": "money0", "supports": sups}
        views[f"{line}|margin_pct"] = {"label": "Gross margin %", "values": [round(100 * a / b, 1) if b else 0 for a, b in zip(mar, rev)], "format": "pct1", "supports": sups}
        views[f"{line}|margin"] = {"label": "Gross margin $", "values": mar, "format": "money0", "supports": sups}
        views[f"{line}|growth"] = {"label": "Growth vs same month last year", "values": [round(100 * (rev[i] / ly[m] - 1), 1) if ly[m] else None for i, m in enumerate(W)],
                                   "format": "pct1", "supports": sups}
        for i, m in enumerate(W):
            data_rows.append([line, mlabel(m), P.status_of(m), rev[i], cost[i]])
    return views, data_rows


def line_table(D, P, org, lines):
    o = D[org]
    rows = []
    for line in lines + ["All"]:
        ls = lines if line == "All" else [line]
        r12 = sum(o.line_month(m, l)["revenue"] for m in P.fytd for l in ls)
        m12 = sum(o.line_month(m, l)["gross_margin"] for m in P.fytd for l in ls)
        p12 = sum(o.line_month(m, l)["revenue"] for m in P.pfytd for l in ls) if P.pfytd_ok else None
        rows.append([line if line != "All" else "Total", r12, p12, '=IF(C{r}=0,"",B{r}/C{r}-1)', m12, '=IF(B{r}=0,"",E{r}/B{r})',
                     growth_text(r12, p12), pct(m12 / r12) if r12 else "–"])
    return rows


def growing(D, P):
    blocks = []
    for org, lines, noun in (("trades", TRADE_LINES, "line"), ("services", SERVICE_LINES, "type of work")):
        views, data_rows = line_views(D, P, org, lines)
        tab = line_table(D, P, org, lines)
        tot = tab[-1]
        be = break_even(D, P, org)
        T = D[org].targets["Installation job margin" if org == "trades" else "Engagement margin"]
        kp, tx = {}, {}
        for line in ["All"] + lines:
            k = line_kpis(D, P, org, line, lines)
            items = []
            if k["sp_y"]:
                items.append(kpi(f"{P.when} against {P.month} last year", growth_text(k["cur"], k["ly"]), f"{money(k['cur'])} against {money(k['ly'])}", k["sp_y"]))
            items.append(kpi("Year to date against the same period last year" if k["p12"] else P.ytd_name,
                             growth_text(k["r12"], k["p12"]) if k["p12"] else money(k["r12"]),
                             f"{money(k['r12'])} against {money(k['p12'])}" if k["p12"] else "same period last year: not in the data", k["sp_12"]))
            items.append(kpi("Gross margin, year to date", pct(k["m12"] / k["r12"]) if k["r12"] else "–", f"{money(k['m12'])} before overheads", k["sp_12"]))
            kp[line] = kpis(items)
            if line == "All":
                rich = max(tab[:-1], key=lambda r_: r_[4] / r_[1] if r_[1] else -9)
                worst = min(tab[:-1], key=lambda r_: r_[4] / r_[1] if r_[1] else 9)
                g_part = (f"Revenue is {tot[6]} {'up' if tot[1] >= tot[2] else 'down'} on the same period last year, year to date ({money(tot[1])} against {money(tot[2])}). "
                          if tot[2] else f"Revenue is {money(tot[1])} this financial year to date ({P.fytd_l}). ")
                tx[line] = text(g_part + f"{rich[0]} {'make' if rich[0].endswith('s') else 'makes'} the highest gross margin ({rich[7]}); {worst[0]} the lowest ({worst[7]}). "
                                f"The business needs {pct(be)} gross margin just to cover overheads.",
                                quant_flag(worst[0], worst[4] / worst[1], worst[1], T, be, "this financial year to date") + " "
                                + quant_flag(rich[0], rich[4] / rich[1], rich[1], T, be, "this financial year to date"))
            else:
                mg, tm = k["m12"] / k["r12"], tot[4] / tot[1]
                if k["p12"]:
                    g, tg = k["r12"] / k["p12"] - 1, tot[1] / tot[2] - 1
                    gpart = f", {pct(g)} on the same period last year ({'faster' if g > tg else 'slower'} than the business as a whole, {pct(tg)})"
                else:
                    gpart = ""
                tx[line] = text(f"{line} brought in {money(k['r12'])} this financial year to date{gpart}, at a {pct(mg)} gross margin "
                                f"({'above' if mg > tm else 'below'} the {pct(tm)} overall).", quant_flag(line, mg, k["r12"], T, be, "this financial year to date"))
        blocks.append({"label": D[org].about["toggle_name"].split(" · ")[-1].capitalize() if org != "nfp" else "Not-for-profit",
                       "business": D[org].about["legal_name"],
                       "filter": filt(noun.capitalize(), [("All", "All")] + [(l, l) for l in lines]), "sections": [
            definition(D, org), vary(kp),
            series(P, f"Revenue, gross margin and growth by {noun}, by month", views,
                   note="Growth is year on year: each month against the same month a year earlier. Tap a month for its workings.",
                   dims={"line": ["All"] + lines, "measure": [("revenue", "Revenue $"), ("margin_pct", "Gross margin %"), ("margin", "Gross margin $"), ("growth", "Growth vs same month last year")]}),
            dict(table(f"By {noun}: financial year to date ({P.fytd_l}) against the same period last year", ["", "Year to date", "Same period last year", "Growth", "Gross margin $", "Gross margin %"],
                       [[r_[0], money(r_[1]), money(r_[2]) if r_[2] else "–", r_[6], money(r_[4]), r_[7]] for r_ in tab], ["text", "money", "money", "pct", "money", "pct"],
                       note=None if P.pfytd_ok else "Same period last year: " + P.no_ly), highlight_filter=True),
            bridge(D, P, org), vary(tx)],
            "data": {"head": ["Line", "Month", "Status", "Revenue", "Direct cost", "Gross margin", "Gross margin %"],
                     "kinds": ["text", "text", "text", "money", "money", "money", "pct"],
                     "rows": [r_ + ["=D{r}-E{r}", "=IF(D{r}=0,\"\",F{r}/D{r})"] for r_ in data_rows]},
            "table_xl": {"head": ["Line", "Year to date", "Same period last year", "Growth", "Gross margin $", "Gross margin %"],
                         "kinds": ["text", "money", "money", "pct", "money", "pct"], "rows": [r_[:6] for r_ in tab]}})
    blocks[0]["label"], blocks[1]["label"] = "Trades", "Services"
    def yoy(org, lines):
        t = line_table(D, P, org, lines)[-1]
        g = t[1] / t[2] - 1
        return f"{'up' if g >= 0 else 'down'} {abs(g) * 100:.1f}%"
    answer = (f"Year to date, trades revenue is {yoy('trades', TRADE_LINES)} and services {yoy('services', SERVICE_LINES)} on the same period last year."
              if P.pfytd_ok else f"Revenue by line, month by month, with growth on the same month last year.")
    r = report("growth", "sme", "Which products and services are growing?", "trades", D, P,
               "Revenue, gross margin and growth (year on year) by product or service line over 24 months. Pick a line and every number, chart and note follows it.", blocks, answer=answer)
    r["business"] = "SME sample businesses"
    return r


def job_margins(D, P):
    o = D["trades"]
    rate, tgt = o.rates["Technician cost rate"], 100 * o.targets["Installation job margin"]
    views, data_rows = line_views(D, P, "trades", TRADE_LINES)
    keep = {k: v for k, v in views.items() if k.split("|")[1] in ("margin_pct", "margin")}
    pj = [j for j in D["_jobs"] if j["month"] == P.mo]
    be = break_even(D, P, "trades")
    by = {"kpis": {}, "bars": {}, "text": {}}
    tk = {l: line_kpis(D, P, "trades", l, TRADE_LINES) for l in ["All"] + TRADE_LINES}
    bridge_sp = bridge(D, P, "trades")["support"]
    T = tgt / 100
    tn = lambda m: ek.tone(m, "higher", T, T - be)          # good at target, amber between break-even and target, red below break-even
    for line in ["All"] + TRADE_LINES:
        k = tk[line]
        nm = "All jobs" if line == "All" else line
        by["kpis"][line] = kpis([kpi(f"Job gross margin, {P.when} · {nm}", pct(k["cur_m"]), f"target {tgt:.1f}%", k["sp_m"], tone=tn(k["cur_m"])),
                                 kpi(f"Job gross margin, {P.prev_month} · {nm}", pct(k["prev_m"]), f"target {tgt:.1f}%", k["sp_m"], tone=tn(k["prev_m"])),
                                 kpi("Gross margin jobs need to break even", pct(be), f"covers overheads and time not charged ({P.full_month})", bridge_sp)])
    det = [support(f"{l}, {P.when}", "Revenue less direct cost (materials, subcontractors, technician time at cost)", [
        inp("Revenue", "money", [tk[l]["cur"]]), inp("Direct cost", "money", [tk[l]["cur_cost"]]),
        calc("Gross margin", "money", "r0-r1"), calc("Gross margin %", "pct", "r2/r0")], cols=(P.short,)) for l in TRADE_LINES]
    by["bars"]["All"] = {"type": "bars", "chart": margin_chart(f"Job gross margin by type of job, {P.label}", f"Revenue less materials, subcontractors and technician time at ${rate}/hour.",
                                                              TRADE_LINES, [tk[l]["cur"] for l in TRADE_LINES], [d["xl"]["rows"][2]["values"][0] for d in det], tgt, det, be)}
    worst = min(TRADE_LINES, key=lambda l: tk[l]["cur_m"])
    best = max(TRADE_LINES, key=lambda l: tk[l]["cur_m"])
    by["text"]["All"] = text(f"In {P.when} " + ", ".join(f"{l.lower()} made a {pct(tk[l]['cur_m'])} job gross margin" for l in TRADE_LINES)
                             + f" (technician time at ${rate} an hour, wages and all on-costs). Jobs need {pct(be)} just to cover overheads.",
                             quant_flag(worst, tk[worst]["cur_m"], tk[worst]["cur"], T, be, f"in {P.when}") + " "
                             + quant_flag(best, tk[best]["cur_m"], tk[best]["cur"], T, be, f"in {P.when}"))
    # Installations: each job invoiced in the period
    inst = sorted([j for j in pj if j["type"] == "Installation"], key=lambda j: -j["gross_profit"] / j["revenue"])
    if inst:
        by["bars"]["Installations"] = {"type": "bars", "chart": margin_chart(
            f"Job gross margin on each installation invoiced in {P.label}",
            f"Whole job, recognised when invoiced: revenue less materials, subcontractors and technician time at ${rate}/hour. One target for every job for now.",
            [j["description"] for j in inst], [j["revenue"] for j in inst], [j["gross_profit"] for j in inst], tgt, [job_support(j, rate) for j in inst], be)}
        below = [j for j in inst if j["gross_profit"] / j["revenue"] < tgt / 100]
        w = inst[-1]
        neg = [j for j in inst if j["gross_profit"] < 0]
        under = [j for j in inst if 0 <= j["gross_profit"] / j["revenue"] < be]
        top = inst[0]
        gapj = max(below, key=lambda j: T * j["revenue"] - j["gross_profit"]) if below else None
        by["text"]["Installations"] = text(
            f"{len(below)} of the {len(inst)} installation jobs invoiced in {P.when} made less than the {tgt:.1f}% job gross margin target. "
            f"The {w['description']} made a {pct(w['gross_profit'] / w['revenue'])} job gross margin: {FMT['hours'](w['hours'])} of technician time "
            f"({money(w['labour_cost'])}) and {money(w['subcontractors'])} of subcontractors on a {money(w['revenue'])} job. Jobs need {pct(be)} gross margin just to cover overheads.",
            (f"{len(below)} installation{'s' if len(below) != 1 else ''} under the {tgt:.1f}% target, worth about "
             f"{money(sum(T * j['revenue'] - j['gross_profit'] for j in below))} between them on {money(sum(j['revenue'] for j in below))} of revenue. "
             if below else f"Every installation cleared the {tgt:.1f}% target. ")
            + (f"{len(neg)} lost money before overheads. " if neg else "")
            + (quant_flag(f"The biggest gap, {gapj['description']}", gapj["gross_profit"] / gapj["revenue"], gapj["revenue"], T, be, f"in {P.when}") if below else
               f"Most profitable: {top['description']} ({pct(top['gross_profit'] / top['revenue'])})."))
    # Maintenance contracts: each contract
    mc = sorted([j for j in pj if j["type"] == "Maintenance contract"], key=lambda j: -j["gross_profit"] / j["revenue"])
    if mc:
        by["bars"]["Maintenance contracts"] = {"type": "bars", "chart": margin_chart(
            f"Job gross margin on each maintenance contract, {P.label}", f"The month's fee less materials and technician time at ${rate}/hour.",
            [j["description"] for j in mc], [j["revenue"] for j in mc], [j["gross_profit"] for j in mc], tgt, [job_support(j, rate) for j in mc], be)}
        lo = mc[-1]
        n_under = sum(j["gross_profit"] / j["revenue"] < tgt / 100 for j in mc)
        by["text"]["Maintenance contracts"] = text(
            (f"All {len(mc)} contracts made more than the {tgt:.1f}% job gross margin target. The thinnest was {lo['description']} at "
             f"{pct(lo['gross_profit'] / lo['revenue'])} job gross margin: {FMT['hours'](lo['hours'])} of technician time on a {money(lo['revenue'])} monthly fee.")
            if not n_under else
            f"{n_under} of {len(mc)} contracts made less than the {tgt:.1f}% job gross margin target; the thinnest was {lo['description']} at {pct(lo['gross_profit'] / lo['revenue'])}.",
            quant_flag(f"The thinnest, {lo['description']}", lo["gross_profit"] / lo["revenue"], lo["revenue"], T, be, f"in {P.when}") + " "
            + quant_flag("All maintenance contracts", sum(j["gross_profit"] for j in mc) / sum(j["revenue"] for j in mc), sum(j["revenue"] for j in mc), T, be, f"in {P.when}"))
    # Call-outs: grouped by length
    co = [j for j in pj if j["type"] == "Call-out"]
    if co:
        hrs_ = sorted({j["hours"] for j in co})
        grp = {h_: [j for j in co if j["hours"] == h_] for h_ in hrs_}
        labs = [f"{h_:g}-hour call-outs ({len(grp[h_])})" for h_ in hrs_]
        rev_ = [sum(j["revenue"] for j in grp[h_]) for h_ in hrs_]
        gp_ = [sum(j["gross_profit"] for j in grp[h_]) for h_ in hrs_]
        crate, mk = o.rates["Call-out charge rate"], o.rates["Materials mark-up on call-outs"]
        det = [support(lab, f"Call-outs of this length in {P.when}, added together", [
            inp("Call-outs", "int", [len(grp[h_])]),
            inp(f"Technician time charged (${crate}/hour)", "money", [sum(j["labour_revenue"] for j in grp[h_])]),
            inp(f"Materials charged (cost × {mk})", "money", [sum(j["materials_revenue"] for j in grp[h_])]),
            calc("Revenue", "money", "r1+r2"), inp("Materials at cost", "money", [-sum(j["materials"] for j in grp[h_])]),
            inp("Technician time at cost", "money", [-sum(j["labour_cost"] for j in grp[h_])]), calc("Job gross margin", "money", "r3+r4+r5"),
            calc("Job gross margin %", "pct", "r6/r3")], cols=(P.short,)) for lab, h_, r_ in zip(labs, hrs_, rev_)]
        lab_rev, mat_rev, mat_cost = (sum(j[k] for j in co) for k in ("labour_revenue", "materials_revenue", "materials"))
        rev_split = support(f"Call-out revenue, {P.when}", f"Technician time charged at ${crate}/hour + materials charged at cost × {mk}", [
            inp(f"Technician time charged (${crate}/hour)", "money", [lab_rev]), inp("Materials at cost", "money", [mat_cost]),
            inp("Mark-up on materials", "pct", [mk - 1]), calc(f"Materials charged (cost × {mk})", "money", "r1*(1+r2)"),
            inp("Materials charged (as invoiced, rounded per call-out)", "money", [mat_rev]), calc("Call-out revenue", "money", "r0+r4"),
            calc("Technician time, % of call-out revenue", "pct", "r0/r5")], cols=(P.short,))
        by["kpis"]["Call-outs and repairs"]["items"] += [
            kpi(f"Technician time charged, {P.when}", money(lab_rev), f"{pct(lab_rev / (lab_rev + mat_rev))} of call-out revenue", rev_split),
            kpi(f"Materials charged, {P.when}", money(mat_rev), f"{money(mat_cost)} at cost, plus {round(100 * (mk - 1))}%", rev_split)]
        by["bars"]["Call-outs and repairs"] = {"type": "bars", "chart": margin_chart(
            f"Job gross margin on call-outs by length, {P.label}",
            f"Charged at ${o.rates['Call-out charge rate']}/hour plus materials at cost × {o.rates['Materials mark-up on call-outs']}; technician time at ${rate}/hour.",
            labs, rev_, gp_, tgt, det, be)}
        mg = [g / r for g, r in zip(gp_, rev_)]
        by["text"]["Call-outs and repairs"] = text(
            f"{len(co)} call-outs in {P.when} billed {money(lab_rev)} of technician time and {money(mat_rev)} of materials ({money(mat_cost)} at cost plus {round(100 * (mk - 1))}%), "
            f"and made a {pct(sum(gp_) / sum(rev_))} job gross margin between them. Gross margins run from {pct(min(mg))} to {pct(max(mg))} "
            "by length: the hourly rate covers technician time comfortably, so the gross margin mostly moves with how much material goes on the van.",
            quant_flag("All call-outs", sum(gp_) / sum(rev_), sum(rev_), T, be, f"in {P.when}"))
    answer = (f"Jobs made a {pct(tk['All']['cur_m'])} gross margin in {P.when}: {best.lower()} the most ({pct(tk[best]['cur_m'])}), "
              f"{worst.lower()} the least ({pct(tk[worst]['cur_m'])}).")
    return report("job-margins", "sme", "Which jobs actually make money?", "trades", D, P,
                  f"Every job's gross margin: revenue less materials, subcontractors and technician time at ${rate} an hour (fully loaded: wages and all on-costs). Pick a type of job and every number, chart and note on the page follows it.",
                  [{"label": None, "filter": filt("Type of job", [("All", "All jobs")] + [(l, l) for l in TRADE_LINES]), "sections": [
                      definition(D, "trades"), vary(by["kpis"]), vary(by["bars"]), bridge(D, P, "trades"), vary(by["text"]),
                      series(P, "Job gross margin by month", keep, note="Tap a month for its workings.",
                             dims={"line": ["All"] + TRADE_LINES, "measure": [("margin_pct", "Gross margin %"), ("margin", "Gross margin $")]})]}],
                  {"head": ["Line", "Month", "Status", "Revenue", "Direct cost", "Gross margin", "Gross margin %"],
                   "kinds": ["text", "text", "text", "money", "money", "money", "pct"],
                   "rows": [r_ + ["=D{r}-E{r}", "=IF(D{r}=0,\"\",F{r}/D{r})"] for r_ in data_rows]}, answer)


# ======================================================================= NFP

SOURCES = [("Grants", "grants", "gw", "grant writing and reporting", "Grant writing and reporting"),
           ("Donations", "donations", "dc", "donor campaigns", "Donor campaigns"),
           ("Fundraising events", "events", "ec", "event costs", "Event costs")]


def nfp_month(D, mo):
    g = D["nfp"].by_line(mo)
    return {"grants": sum(v for k, v in g.items() if k.endswith(" grant")), "donations": g.get("Donations", 0), "events": g.get("Fundraising events", 0),
            "fees": g.get("Program fees", 0), "gw": -g.get("Grant writing and reporting", 0), "dc": -g.get("Donor campaigns", 0),
            "ec": -g.get("Event costs", 0), "untied": -(g.get("Program delivery wages (untied)", 0) + g.get("Program costs (untied)", 0)),
            "admin": -(g.get("Administration wages", 0) + g.get("Occupancy", 0) + g.get("Other administration", 0)),
            "income": sum(v for k, v in g.items() if D["nfp"].sections.get(k) == "Income"),
            "expenses": -sum(v for k, v in g.items() if D["nfp"].sections.get(k) != "Income"),
            "depreciation": -g.get("Depreciation", 0), "g": g}


def src_totals(D, months, inc_keys, cost_keys):
    m = [nfp_month(D, x) for x in months]
    return sum(sum(x[k] for k in inc_keys) for x in m), sum(sum(x[k] for k in cost_keys) for x in m)


GROUPS = {"All": (["grants", "donations", "events"], ["gw", "dc", "ec"])} | {s_[0]: ([s_[1]], [s_[2]]) for s_ in SOURCES}


def by_source_chart(D, P):
    """Cost to raise a dollar by source, for the period (a source that raised nothing is left out and said so)."""
    x = nfp_month(D, P.mo)
    have = [s_ for s_ in SOURCES if x[s_[1]]]
    rows = []
    for name, inc, cst, _, cost_line in have:
        rows += [inp(f"{name}: cost ({cost_line.lower()})", "money", [x[cst]]), inp(f"{name}: raised", "money", [x[inc]])]
    rows += [calc(f"{s_[0]}: cost per dollar raised", "cents", f"r{2 * i}/r{2 * i + 1}*100") for i, s_ in enumerate(have)]
    missing = [s_[0] for s_ in SOURCES if s_ not in have]
    sp = support(f"Cost to raise a dollar, by source, {P.label}", "Fundraising cost ÷ money raised, for each source, in cents", rows,
                 (f"Nothing raised from {', '.join(m.lower() for m in missing)} in {P.when}. " if missing else "") + (P.part_note or "") or None, cols=(P.short,))
    c = [sp["xl"]["rows"][2 * len(have) + i]["values"][0] for i in range(len(have))]
    chart = {"title": f"Cost to raise a dollar, by source, {P.label} (cents)", "labels": [s_[0] for s_ in have],
             "values": [half_up(v) for v in c], "format": "cents_int", "plain": True}
    return chart, sp, dict(zip([s_[0] for s_ in have], c)), x


def cost_to_raise(D, P):
    W = P.window
    views, kp, tx = {}, {}, {}
    x = nfp_month(D, P.mo)
    for name, (ik, ck) in GROUPS.items():
        vals, sp_ = [], []
        lab = "all fundraising" if name == "All" else name.lower()
        for m in W:
            raised, cost = src_totals(D, [m], ik, ck)
            vals.append(half_up(100 * cost / raised) if raised else None)
            sp_.append(support(f"Cost to raise a dollar, {lab}, {mlabel(m)}", "Fundraising cost ÷ money raised, in cents",
                               [inp("Cost of raising it", "money", [cost]), inp("Money raised", "money", [raised])]
                               + ([calc("Cents per dollar raised", "cents", "r0/r1*100")] if raised else []),
                               None if raised else "Nothing raised this month.", cols=(mlabel(m),)))
        views[f"{name}|cents"] = {"label": "Cents per $1", "values": vals, "format": "cents_int", "supports": sp_}
        r_s, c_s = src_totals(D, [P.mo], ik, ck)
        r_a, c_a = src_totals(D, [P.prev], ik, ck)
        r12, c12 = src_totals(D, P.fytd, ik, ck)
        both = bool(r_s and r_a)
        k1 = support(f"Cost to raise a dollar, {lab}, {P.month} and {P.prev_month}", "Cost of raising it ÷ money raised, in cents",
                     [inp("Cost of raising it", "money", [c_s, c_a]), inp("Money raised", "money", [r_s, r_a])]
                     + ([calc("Cents per dollar", "cents", "r0/r1*100")] if both else []),
                     None if both else "Nothing raised in one of the months, so there's no cost per dollar for it.", cols=(mlabel(P.mo), mlabel(P.prev)))
        items = [kpi(f"{P.when} · {'all fundraising' if name == 'All' else name}", cents(c_s, r_s), f"{P.prev_month} {cents(c_a, r_a) if r_a else 'none raised'}", k1)]
        if P.pfytd_ok:
            r0, c0 = src_totals(D, P.pfytd, ik, ck)
            k2 = support(f"Cost to raise a dollar, {lab}, year to date against the same period last year", "Cost ÷ money raised, in cents",
                         [inp("Cost, year to date", "money", [c12]), inp("Raised, year to date", "money", [r12]), calc("Cents, year to date", "cents", "r0/r1*100"),
                          inp("Cost, same period last year", "money", [c0]), inp("Raised, same period last year", "money", [r0])]
                         + ([calc("Cents, same period last year", "cents", "r3/r4*100")] if r0 else []), cols=("Year to date",))
            items.append(kpi(P.ytd_name, cents(c12, r12), f"same period last year: {cents(c0, r0)}", k2))
        else:
            r0 = c0 = None
            k2 = support(f"Cost to raise a dollar, {lab}, year to date", "Cost ÷ money raised, in cents",
                         [inp("Cost, year to date", "money", [c12]), inp("Raised, year to date", "money", [r12])]
                         + ([calc("Cents, year to date", "cents", "r0/r1*100")] if r12 else []), "Same period last year: " + P.no_ly, cols=("Year to date",))
            items.append(kpi(P.ytd_name, cents(c12, r12), "same period last year: not in the data", k2))
        kp[name] = kpis(items)
        ytd_part = (f"This financial year to date it has cost {cents(c12, r12)} a dollar" + (f", against {cents(c0, r0)} in the same period last year." if r0 else "."))
        if name == "All":
            ev = f" Fundraising events raised {money(x['events'])} and cost {money(x['ec'])}." if x["events"] else ""
            tx[name] = text(f"{P.when} cost {cents(c_s, r_s)} to raise each dollar, against {cents(c_a, r_a)} in {P.prev_month}.{ev} {ytd_part}"
                            + (f" {P.part_note}" if P.incomplete else ""),
                            "The year-to-date figure is steadier than single months: events make some months jump. Pick a source above to see which one moves it.")
        else:
            cost_name = next(s_[3] for s_ in SOURCES if s_[0] == name)
            tx[name] = text(f"{name} cost {cents(c12, r12)} to raise each dollar this financial year to date ({money(c12)} of {cost_name} for {money(r12)})"
                            + (f", against {cents(c0, r0)} in the same period last year." if r0 else "."),
                            {"Grants": "Usually the cheapest money to raise, as long as the time that goes into applications and acquittals is protected.",
                             "Donations": "Steady and cheap, and untied: the money that builds reserves.",
                             "Fundraising events": "Usually the dearest money to raise: events are worth counting for what else they bring too (new donors, profile)."}[name])
    chart, sp, _, _ = by_source_chart(D, P)
    r_all, c_all = src_totals(D, [P.mo], *GROUPS["All"])
    ry, cy = src_totals(D, P.fytd, *GROUPS["All"])
    answer = f"Each dollar raised cost {cents(c_all, r_all)} in {P.when}, and {cents(cy, ry)} a dollar this financial year to date."
    return report("cost-to-raise", "nfp", "What does it cost to raise a dollar?", "nfp", D, P,
                  "What fundraising costs (grant writing, donor campaigns, events) for every dollar it brings in. Pick a source and every number, chart and note follows it.",
                  [{"label": None, "filter": filt("Source", [("All", "All fundraising")] + [(s_[0], s_[0]) for s_ in SOURCES]), "sections": [
                      vary(kp),
                      series(P, "Cost to raise a dollar, by month (cents)", views,
                             note="Months with an event (the gala, the Christmas appeal) jump. A gap means nothing was raised that month. Tap a month for its workings.",
                             dims={"line": ["All"] + [s_[0] for s_ in SOURCES], "measure": [("cents", "Cents per $1")]}),
                      {"type": "bars", "chart": chart, "support": sp, "highlight_filter": True},
                      vary(tx)]}],
                  {"head": ["Month", "Status", "Grant writing", "Donor campaigns", "Event costs", "Grant income", "Donations", "Events", "Cents per $1"],
                   "kinds": ["text", "text", "money", "money", "money", "money", "money", "money", "cents"],
                   "rows": [[mlabel(m), P.status_of(m), nfp_month(D, m)["gw"], nfp_month(D, m)["dc"], nfp_month(D, m)["ec"],
                             nfp_month(D, m)["grants"], nfp_month(D, m)["donations"], nfp_month(D, m)["events"],
                             "=IF(SUM(F{r}:H{r})=0,\"\",SUM(C{r}:E{r})/SUM(F{r}:H{r})*100)"] for m in W]}, answer)


def funding(D, P):
    W = P.window
    views, rows_, tx = {}, [], {}
    chart, sp, cpd, x = by_source_chart(D, P)
    for name, (ik, ck) in GROUPS.items():
        inc_v = [src_totals(D, [m], ik, ck)[0] for m in W]
        cst_v = [src_totals(D, [m], ik, ck)[1] for m in W]
        sups = [support(f"{'All sources' if name == 'All' else name}, {mlabel(m)}", "Raised, cost of raising it, and what's left", [inp("Raised", "money", [a]), inp("Cost of raising it", "money", [b]),
                calc("Left after fundraising costs", "money", "r0-r1")], cols=(mlabel(m),)) for m, a, b in zip(W, inc_v, cst_v)]
        views[f"{name}|raised"] = {"label": "Raised $", "values": inc_v, "format": "money0", "supports": sups}
        views[f"{name}|net"] = {"label": "Left after costs $", "values": [a - b for a, b in zip(inc_v, cst_v)], "format": "money0", "supports": sups}
        if name != "All":
            rows_ += [[name, mlabel(m), P.status_of(m), a, b] for m, a, b in zip(W, inc_v, cst_v)]
        r12, c12 = src_totals(D, P.fytd, ik, ck)
        all12 = src_totals(D, P.fytd, *GROUPS["All"])[0]
        if name == "All":
            cheap = min(cpd, key=cpd.get)
            dear = max(cpd, key=cpd.get)
            tx[name] = text(", ".join(f"{k.lower() if i else k} {half_up(v)}¢" for i, (k, v) in enumerate(cpd.items())).replace(", f", " and f", 1)
                            .join(["In " + P.when + " it cost: ", " to raise each dollar."]) + (f" {P.part_note}" if P.incomplete else ""),
                            f"Cheapest to raise in {P.when}: {cheap.lower()} ({half_up(cpd[cheap])}¢ a dollar). Dearest: {dear.lower()} ({half_up(cpd[dear])}¢). "
                            "Events are worth counting for what else they bring too (new donors, profile).")
        else:
            tx[name] = text(
                f"{name}: {money(r12)} raised this financial year to date ({pct(r12 / all12) if all12 else '–'} of everything raised), {money(c12)} to raise it, "
                f"so {money(r12 - c12)} left for programs: {cents(c12, r12)} per dollar.",
                {"Grants": "Most of the money, and usually the cheapest to raise, starting with grants that renew.",
                 "Donations": "Cheap and flexible (untied): the money that builds reserves.",
                 "Fundraising events": "The dearest per dollar: worth measuring the new donors each event brings in too."}[name])
    tab, raised_rows = [], []
    for name, inc, cst, _, _ in SOURCES:
        a, b = src_totals(D, P.fytd, [inc], [cst])
        tab.append([name, money(a), money(b), money(a - b), cents(b, a)])
        raised_rows.append(inp(f"{name}, raised", "money", [a]))
    cheap, dear = min(cpd, key=cpd.get), max(cpd, key=cpd.get)
    sp_ytd = support(f"Raised, financial year to date ({P.fytd_l})", "Grants + donations + fundraising events",
                     raised_rows + [calc("Raised, year to date", "money", "+".join(f"r{i}" for i in range(len(raised_rows))))], cols=("Year to date",))
    head = kpis([kpi(f"Cheapest to raise: {cheap}", f"{half_up(cpd[cheap])}¢", f"per $1 raised in {P.when}", sp),
                 kpi(f"Dearest to raise: {dear}", f"{half_up(cpd[dear])}¢", f"per $1 raised in {P.when}", sp),
                 kpi("Raised, year to date", money(sp_ytd["xl"]["rows"][-1]["values"][0]), P.fytd_l, sp_ytd)])
    answer = f"{cheap} cost {half_up(cpd[cheap])}¢ to raise each dollar in {P.when}; {dear.lower()} {half_up(cpd[dear])}¢."
    return report("funding", "nfp", "Which funding is worth chasing?", "nfp", D, P,
                  "Each source of money compared on what it raises and what it costs to raise. Pick a source and every chart, table row and note follows it.",
                  [{"label": None, "filter": filt("Source", [("All", "All sources")] + [(s_[0], s_[0]) for s_ in SOURCES]), "sections": [
                      head,
                      {"type": "bars", "chart": chart, "support": sp, "highlight_filter": True},
                      vary(tx),
                      dict(table(f"Financial year to date ({P.fytd_l}), by source", ["", "Raised", "Cost of raising it", "Left after costs", "Cost per $1"], tab,
                                 ["text", "money", "money", "money", "cents"]), highlight_filter=True),
                      series(P, "Raised and left after costs, by month", views, note="Tap a month for its workings.",
                             dims={"line": ["All"] + [s_[0] for s_ in SOURCES], "measure": [("raised", "Raised $"), ("net", "Left after costs $")]})]}],
                  {"head": ["Source", "Month", "Status", "Raised", "Cost of raising it", "Left after costs", "Cents per $1"],
                   "kinds": ["text", "text", "text", "money", "money", "money", "cents"],
                   "rows": [r_ + ["=D{r}-E{r}", "=IF(D{r}=0,\"\",E{r}/D{r}*100)"] for r_ in rows_]}, answer)


def grant_positions(D, P):
    """Each grant at the end of the period: spent and budget to date, received, still to spend, months left."""
    src = D["_src"]
    spend = src.table("nfp", "fact_grant_spend_month")
    inst = src.table("nfp", "fact_grant_instalment")
    first = min(r["month_key"] for r in spend)
    end_key = int(P.end_date().strftime("%Y%m%d"))
    out = []
    for g in src.table("nfp", "dim_grant"):
        s_, e_ = g["start_date"][:7], g["end_date"][:7]
        rows = [r for r in spend if r["grant_id"] == g["grant_id"]]
        if not rows or s_ > P.mo:
            continue
        per_month = rows[0]["budget"]
        before = 0
        while add_months(s_, before) < first:
            before += 1
        upto = [r for r in rows if r["month_key"] <= P.mo]
        spent = per_month * before + sum(r["spend"] for r in upto)
        budget = per_month * before + sum(r["budget"] for r in upto)
        left = 0
        while add_months(P.mo, left + 1) <= e_:
            left += 1
        out.append(dict(code=g["grant_id"], program=g["program"], funder=g["funder"], total=g["grant_total"], start=g["start_date"], end=g["end_date"],
                        active=s_ <= P.mo <= e_, spent_now=next((r["spend"] for r in rows if r["month_key"] == P.mo), 0),
                        spent_to_date=spent, budget_to_date=budget, assumed_before=per_month * before, months_before=before,
                        received=sum(i["amount"] for i in inst if i["grant_id"] == g["grant_id"] and i["date_key"] <= end_key),
                        unspent=g["grant_total"] - spent, months_left=left,
                        monthly=[(r["month_key"], r["spend"], r["budget"]) for r in upto]))
    return out


def program_cost(D, P):
    G = sorted([g for g in grant_positions(D, P) if g["active"] and g["spent_now"]], key=lambda g: -g["spent_now"])
    x = nfp_month(D, P.mo)
    tot = sum(g["spent_now"] for g in G)
    sups, full = [], {}
    for g in G:
        sp = support(f"{g['program']}: full cost, {P.when}", "Grant spending + its share of untied program costs and administration (shared by grant spending)", [
            inp("Grant spending on the program", "money", [g["spent_now"]]), inp("All grant-funded program spending", "money", [tot]),
            calc("Share of program spending", "pct", "r0/r1"), inp("Untied program costs (all programs)", "money", [x["untied"]]),
            calc("Share of untied program costs", "money", "r2*r3"), inp("Administration (all)", "money", [x["admin"]]),
            calc("Share of administration", "money", "r2*r5"), calc("Full cost of the program", "money", "r0+r4+r6")], P.part_note or None, cols=(P.short,))
        sups.append(sp)
        full[g["program"]] = sp["xl"]["rows"][-1]["values"][0]
    labels = [g["program"] for g in G]
    chart = {"title": f"Full cost of each program, {P.label}", "labels": labels, "values": [half_up(full[l]) for l in labels],
             "format": "money0", "plain": True, "details": sups,
             "views": [{"id": "dollars", "label": "$", "values": [half_up(full[l]) for l in labels], "format": "money0"},
                       {"id": "pct", "label": "% of total", "values": [round(100 * full[l] / sum(full.values()), 1) for l in labels], "format": "pct1"}]}
    spend = {}
    for r in D["_src"].table("nfp", "fact_grant_spend_month"):
        spend.setdefault(r["grant_id"], {})[r["month_key"]] = (r["spend"], r["budget"])
    W = P.window
    def view(name, codes):
        vals = [sum(spend.get(c, {}).get(m, (0, 0))[0] for c in codes) for m in W]
        buds = [sum(spend.get(c, {}).get(m, (0, 0))[1] for c in codes) for m in W]
        return {"label": "Spend $", "values": vals, "format": "money0",
                "supports": [support(f"{name}, {mlabel(m)}", "Grant spending recorded in the month, against the monthly budget",
                                     [inp("Spent in the month (ledger)", "money", [v]), inp("Monthly budget", "money", [bd]), calc("Over (under) budget", "money", "r0-r1")],
                                     cols=(mlabel(m),)) for m, v, bd in zip(W, vals, buds)]}
    views = {"All|spend": view("All programs", list(spend))}
    tx = {}
    top = labels[0]
    tx["All"] = text(f"{top} is the biggest program: {money(full[top])} in {P.when} once its share of untied program costs and administration is added to "
                     f"{money(G[0]['spent_now'])} of grant spending. Shared costs add {pct((x['untied'] + x['admin']) / tot)} on top of grant spending across all programs.",
                     "The full cost (not just the grant line) is the number for renewal applications, where the funder lets you recover a share of overheads. Pick a program above to see it on its own.")
    for g in G:
        l = g["program"]
        views[f"{l}|spend"] = view(l, [g["code"]])
        shared = full[l] - g["spent_now"]
        assumed = f" (spending before {mdate(D['_grant_first']).strftime('%B %Y')} taken at budget)" if g["months_before"] else ""
        tx[l] = text(f"{l} cost {money(full[l])} in full in {P.when}: {money(g['spent_now'])} paid by the {g['funder']} grant, and {money(shared)} of shared costs "
                     f"no grant covers. It has spent {pct(g['spent_to_date'] / g['budget_to_date'])} of its budget to date{assumed}, with {money(g['unspent'])} "
                     f"left and {g['months_left']} months to go.",
                     f"The full cost is {money(full[l])} a month; {money(shared)} of it is shared cost the grant doesn't pay for. Worth asking for as much of it as the funder allows at renewal.")
    answer = (f"{top} costs {money(full[top])} in full in {P.when}: {money(full[top] - G[0]['spent_now'])} more than its grant spending, "
              "once its share of shared costs is added.")
    return report("program-cost", "nfp", "What does each program really cost?", "nfp", D, P,
                  "Each program's full cost: what its grant pays for, plus its fair share of the costs no single grant covers (untied program costs and administration, shared by grant spending). Pick a program and every chart and note follows it.",
                  [{"label": None, "filter": filt("Program", [("All", "All programs")] + [(l, l) for l in labels]), "sections": [
                      {"type": "bars", "chart": chart, "highlight_filter": True}, vary(tx),
                      series(P, "Grant spending, by month", views, note="Grant spending only (the program's direct cost). All programs includes grants that have finished. Tap a month for its workings.",
                             dims={"line": ["All"] + labels, "measure": [("spend", "Spend $")]})]}],
                  {"head": ["Program", f"Grant spending, {P.short}", "Share", "Untied costs share", "Administration share", "Full cost"],
                   "kinds": ["text", "money", "pct", "money", "money", "money"],
                   "inputs": [("tot", f"All grant-funded program spending, {P.label}", tot, "money"),
                              ("untied", f"Untied program costs, {P.label} (all programs)", x["untied"], "money"),
                              ("admin", f"Administration, {P.label} (all)", x["admin"], "money")],
                   "rows": [[g["program"], g["spent_now"], "=B{r}/{tot}", "=C{r}*{untied}", "=C{r}*{admin}", "=B{r}+D{r}+E{r}"] for g in G]}, answer)


# ------------------------------------------------------------------ cash (needs the balance sheet: from the opening balance on)

def cash_at(D, mo, P=None):
    """Cash at bank and unspent grant money at the end of a month (or today, for the month in progress)."""
    src = D["_src"]
    ob = {r["line"]: r["amount"] for r in src.table("nfp", "opening_balance")}
    ob_mo = src.table("nfp", "opening_balance")[0]["as_at"][:7]
    if mo == ob_mo:
        return ob["Cash at bank"], ob["Grants received in advance (unspent)"]
    end = min(ds.month_end(mo), ds.AS_AT.date())
    bal = [r for r in src.table("nfp", "fact_balance_daily") if r["date_key"] <= int(end.strftime("%Y%m%d"))]
    from .period import Period
    Q = Period(mo, D["nfp"].months)
    adv = sum(max(0, g["received"] - g["spent_to_date"]) for g in grant_positions(D, Q) if g["code"] in D["_current_grants"])
    return bal[-1]["cash_at_bank"], adv


def cash_months(D):
    """Months the cash reports can run for: the opening balance month onwards."""
    ob_mo = D["_src"].table("nfp", "opening_balance")[0]["as_at"][:7]
    return [m for m in D["nfp"].months if m > ob_mo]


def runway_numbers(D, P, mo):
    cash, adv = cash_at(D, mo)
    rate_mo = P.prev if (mo == P.mo and P.incomplete) else mo
    x = nfp_month(D, rate_mo)
    return cash, adv, x["expenses"] - x["depreciation"], rate_mo


def runway_support(D, P, mo):
    cash, adv, spend, rate_mo = runway_numbers(D, P, mo)
    lab = mdate(mo).strftime("%B %Y")
    return support(f"Unrestricted cash runway, {lab}", "(Cash at bank − unspent grant money) ÷ a month's cash spending", [
        inp("Cash at bank", "money", [cash]), inp("Less unspent grant money (belongs to funders' programs)", "money", [-adv]),
        calc("Unrestricted cash", "money", "r0+r1"), inp(f"Cash spending in {mdate(rate_mo).strftime('%B')} (expenses less depreciation)", "money", [spend]),
        calc("Runway", "months", "r2/r3")],
        (f"{P.month} is still in progress, so the rate of spending is {P.prev_month}'s. " if rate_mo != mo else "")
        + f"Reserves target: {FMT['months'](D['_targets']['Reserves (unrestricted cash runway)'])}.", cols=(mdate(mo).strftime("%b %Y"),))


def runway(D, P):
    tgt = D["_targets"]["Reserves (unrestricted cash runway)"]
    s_now, s_prev = runway_support(D, P, P.mo), runway_support(D, P, P.prev)
    v = lambda s, i: s["xl"]["rows"][i]["values"][0]
    run, unres, spend = v(s_now, 4), v(s_now, 2), v(s_now, 3)
    sp3 = support(f"Reserves: how far from {FMT['months'](tgt)}?", "Target months × monthly cash spending − unrestricted cash", [
        inp("Unrestricted cash", "money", [unres]), inp("A month's cash spending", "money", [spend]),
        calc("Runway", "months", "r0/r1"), inp("Reserves target", "months", [float(tgt)]),
        calc("Cash needed for the target", "money", "r3*r1"), calc("Gap to the target", "money", "r4-r0")], cols=(P.short,))
    gap = sp3["xl"]["rows"][5]["values"][0]
    src = D["_src"]
    ob_mo = src.table("nfp", "opening_balance")[0]["as_at"][:7]
    days_ = sorted([r for r in src.table("nfp", "fact_balance_daily") if r["date_key"] <= int(P.end_date().strftime("%Y%m%d"))], key=lambda r: r["date_key"])
    lab = [date(r["date_key"] // 10000, r["date_key"] // 100 % 100, r["date_key"] % 100) for r in days_]
    opening = {r["line"]: r["amount"] for r in src.table("nfp", "opening_balance")}["Cash at bank"]
    stat = [ds.day_status(d) for d in lab]
    cashes = [r["cash_at_bank"] for r in days_]
    when = f"at {P.full_month}'s rate of spending"
    shows = (f"Unrestricted cash ({money(unres)}, after setting aside unspent grant money) would cover {FMT['months'](run)} of spending {when}, "
             + (f"short of the {FMT['months'](tgt)} target by {money(gap)}." if gap > 0 else f"above the {FMT['months'](tgt)} target by {money(-gap)}."))
    action = ("A reserves plan is the usual next step: how much of each month's surplus goes to reserves, and by when the gap is closed."
              if gap > 0 else "Reserves are above target: worth agreeing with the board how much to hold, and what the rest is for.")
    answer = f"{FMT['months'](run)} of spending in unrestricted cash, against a {FMT['months'](float(tgt))} reserves target."
    res_tgt = round(float(tgt) * spend + runway_numbers(D, P, P.mo)[1])     # cash at bank that would meet the target: grant money is held as well
    return report("runway", "nfp", "How many months of runway do we have?", "nfp", D, P,
                  "How long the organisation could keep going on its own money: cash at bank, less unspent grant money (which belongs to the funders' programs), divided by a month's spending.",
                  [{"label": None, "sections": [
                      kpis([kpi("Runway now", FMT["months"](run), f"target {FMT['months'](float(tgt))}", s_now, tone=ek.tone(run, "higher", float(tgt), 0.5)),
                            kpi("Target", FMT["months"](float(tgt)), "reserves target", sp3),
                            kpi("Gap" if gap > 0 else "Above target by", money(abs(gap)), "to reach the target" if gap > 0 else "unrestricted cash over the target", sp3,
                                tone="bad" if gap > 0 else "good"),
                            kpi(f"Runway in {P.prev_month}", FMT["months"](v(s_prev, 4)), f"at {mdate(runway_numbers(D, P, P.prev)[3]).strftime('%B')}'s rate of spending", s_prev,
                                tone=ek.tone(v(s_prev, 4), "higher", float(tgt), 0.5))]),
                      text(shows, action),
                      {"type": "series", "title": f"Cash at bank, every day ({ds.strf(lab[0], '%-d %b')} to {ds.strf(lab[-1], '%-d %b')})", "labels": [ds.strf(d, "%-d %b") for d in lab],
                       "months": [d.isoformat() for d in lab], "status": stat,
                       "views": {"All|cash": {"label": "Cash at bank $", "values": cashes, "format": "money0",
                                              "supports": [support(f"Cash at bank, {ds.strf(d, '%-d %b %Y')}", "Yesterday's closing cash + the day's money in less money out",
                                                                   [inp("Cash at bank, end of the day before", "money", [prev]), inp("Net money in (out) on the day", "money", [cur - prev]),
                                                                    calc("Cash at bank, end of the day", "money", "r0+r1")], cols=(ds.strf(d, "%-d %b"),))
                                                           for d, prev, cur in zip(lab, [opening] + cashes[:-1], cashes)]}},
                       "dims": {"line": ["All"], "measure": [("cash", "Cash at bank $")]},
                       "target": {"value": res_tgt, "label": f"Reserves target {money(res_tgt)}: {FMT['months'](float(tgt))} of spending + unspent grant money"},
                       "note": f"Cash at bank includes unspent grant money. The daily cash data starts {ds.strf(lab[0], '%-d %B %Y')} (after the opening balance)."}]}],
                  {"head": ["Date", "Status", "Cash at bank"], "kinds": ["text", "text", "money"],
                   "rows": [[d.isoformat(), s_, c] for d, s_, c in zip(lab, stat, cashes)]}, answer)


def board(D, P):
    tgt_end = D["_targets"]["Grants ending soon: window"]
    cur, prv = nfp_month(D, P.mo), nfp_month(D, P.prev)
    surplus = lambda x: x["income"] - x["expenses"]
    rows = [inp(f"Income, {mdate(m).strftime('%B')}", "money", [nfp_month(D, m)["income"]]) for m in P.fytd]
    n = len(P.fytd)
    rows += [calc("Income, year to date", "money", "+".join(f"r{i}" for i in range(n)))]
    rows += [inp(f"Expenses, {mdate(m).strftime('%B')}", "money", [nfp_month(D, m)["expenses"]]) for m in P.fytd]
    rows += [calc("Expenses, year to date", "money", "+".join(f"r{n + 1 + i}" for i in range(n))), calc("Surplus (deficit), year to date", "money", f"r{n}-r{2 * n + 1}")]
    sp = support(f"Year to date ({P.fytd_l})", "Income less expenses, financial year to date", rows,
                 "; ".join(f"{mdate(m).strftime('%B')} {P.status_of(m).lower()}" for m in P.fytd) + ".", cols=(f"{P.fy} to date",))
    surplus_ytd = sp["xl"]["rows"][-1]["values"][0]
    s_run = runway_support(D, P, P.mo)
    run = s_run["xl"]["rows"][-1]["values"][0]
    chart, sp_c, cpd, x = by_source_chart(D, P)
    raised, cost = src_totals(D, [P.mo], *GROUPS["All"])
    raised_p, cost_p = src_totals(D, [P.prev], *GROUPS["All"])
    s_ctr = support(f"Cost to raise a dollar, {P.month} and {P.prev_month}", "Fundraising costs ÷ money raised, in cents",
                    [inp("Fundraising costs", "money", [cost, cost_p]), inp("Money raised", "money", [raised, raised_p]), calc("Cents per dollar", "cents", "r0/r1*100")],
                    cols=(mlabel(P.mo), mlabel(P.prev)))
    G = grant_positions(D, P)
    live = [g for g in G if g["active"]]
    ending = sorted([g for g in live if g["months_left"] < tgt_end], key=lambda g: g["months_left"])
    grants = [[g["program"], money(g["spent_to_date"]), money(g["budget_to_date"]), pct(g["spent_to_date"] / g["budget_to_date"]),
               money(g["unspent"]), str(g["months_left"])] for g in sorted(live, key=lambda g: g["months_left"])]
    tgt = D["_targets"]["Reserves (unrestricted cash runway)"]
    notes = [f"Unrestricted cash covers {FMT['months'](run)} of spending, against a {FMT['months'](tgt)} reserves target."]
    decisions = []
    if ending:
        g0 = ending[0]
        need = g0["unspent"] / max(g0["months_left"], 1)
        notes.append(f"{len(ending)} grant{'s' if len(ending) != 1 else ''} end{'' if len(ending) != 1 else 's'} within {tgt_end} months with {money(sum(g['unspent'] for g in ending))} still to spend. {g0['program']}: "
                     f"{money(g0['unspent'])} left in {g0['months_left']} months ({money(need)} a month needed, against {money(g0['spent_now'])} spent in {P.when}).")
        decisions.append(f"{g0['program']}: lift spending to {money(need)} a month, or ask {g0['funder']} about carrying the balance over.")
    cheap, dear = min(cpd, key=cpd.get), max(cpd, key=cpd.get)
    notes.append(f"Fundraising cost {cents(cost, raised)} per dollar in {P.when}: {cheap.lower()} the cheapest ({half_up(cpd[cheap])}¢), {dear.lower()} the dearest ({half_up(cpd[dear])}¢).")
    decisions.append("Reserves: how much of each month's surplus goes to reserves, and by when the target is reached." if run < tgt else
                     "Reserves are above target: how much to hold, and what the rest is for.")
    decisions.append("Fundraising: where the next spare hours go, given what each source costs to raise.")
    answer = (f"A {money(surplus(cur))} {'surplus' if surplus(cur) >= 0 else 'deficit'} in {P.when}, {FMT['months'](run)} of runway, and "
              f"{len(ending)} grant{'s' if len(ending) != 1 else ''} ending within {tgt_end} months.")
    return report("board", "nfp", "What does the board need to see?", "nfp", D, P,
                  f"A one-page board summary for {P.label}: the result, the money, the risks, and the decisions to make. The full statements are in the downloads.",
                  [{"label": None, "sections": [
                      dict(kpis([kpi(f"Surplus, {P.when}", money(surplus(cur)), f"{P.prev_month} {money(surplus(prv))}",
                                support(f"Surplus, {P.month} and {P.prev_month}", "Income less expenses", [inp("Income", "money", [cur["income"], prv["income"]]),
                                        inp("Expenses", "money", [cur["expenses"], prv["expenses"]]), calc("Surplus", "money", "r0-r1")], P.part_note or None, cols=(mlabel(P.mo), mlabel(P.prev)))),
                            kpi("Surplus (deficit), year to date", money(surplus_ytd), P.fytd_l, sp),
                            kpi("Unrestricted cash runway", FMT["months"](run), f"reserves target {FMT['months'](tgt)}", s_run),
                            kpi(f"Cost to raise a dollar, {P.when}", cents(cost, raised), f"{P.prev_month} {cents(cost_p, raised_p)}", s_ctr)]), big=True),
                      {"type": "list", "title": "What the board should note", "items": notes},
                      dict(table("Grants", ["Program", "Spent to date", "Budget to date", "Against budget", "Still to spend", "Months left"], grants,
                                 ["text", "money", "money", "pct", "money", "int"],
                                 note="Against budget: red when spending is more than 1% over or under budget to date, amber within 1%."),
                           tones=[["", "", "", ("" if abs(g["spent_to_date"] / g["budget_to_date"] - 1) < 0.0005 else
                                                "warn" if abs(g["spent_to_date"] / g["budget_to_date"] - 1) < 0.01 else "bad"), "", ""]
                                  for g in sorted(live, key=lambda g: g["months_left"])]),
                      {"type": "list", "title": "Decisions to make", "items": decisions, "numbered": True}]}],
                  {"head": ["Program", "Spent to date", "Budget to date", "Against budget", "Still to spend", "Months left"],
                   "kinds": ["text", "money", "money", "pct", "money", "int"],
                   "rows": [[g["program"], g["spent_to_date"], g["budget_to_date"], "=B{r}/C{r}", g["unspent"], g["months_left"]]
                            for g in sorted(live, key=lambda g: g["months_left"])]}, answer)


# ======================================================================= the list

REPORTS = {"cost-to-win": cost_to_win, "job-margins": job_margins, "growth": growing, "cost-to-raise": cost_to_raise,
           "program-cost": program_cost, "runway": runway, "funding": funding, "board": board}
NEEDS_CASH = {"runway", "board"}       # need the balance sheet, which starts at the opening balance
