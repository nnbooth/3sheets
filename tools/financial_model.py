#!/usr/bin/env python3
"""
financial_model.py — month-end sample model behind the home-page dashboard.

MONTH-END REPORTING, BUILT FROM THE TRANSACTIONS UP. We report September 2026
(the last closed month) against the PRIOR MONTH, August 2026. Three invented
organisations, each modelled at the most granular level:

  trades    SME: field/trade services. Every JOB (maintenance contract,
            installation, call-out) with its own revenue, materials,
            subcontractors, technician hours, invoice date and payment date.
  services  SME: professional services. Every client ENGAGEMENT (projects
            billed on milestones, monthly retainers, training) with hours,
            rates, contractors, billing, work in progress and invoices.
  nfp       Not-for-profit: community services charity. Every GRANT (funder,
            program, period, instalments, monthly spend against budget),
            plus donations, events and program fees.

The P&L, balance sheet and cash flow are ADDED UP FROM those records, in
whole dollars, so everything ties. run_checks() proves it before anything is
published (subtotals, balance sheet balances, cash ties, profit rolls into
equity, job/engagement/grant detail ties to the statements, debtors equal the
unpaid invoices, unspent grants equal grants received less income recognised).

Australian financial year: FY2027 runs 1 July 2026 to 30 June 2027. GST is
excluded for simplicity. All data is invented.

Used by tools/publish_dashboard.py (via tools/sample_data.py).
"""

import random
from datetime import date, timedelta

PERIODS = ["2026-09", "2026-08"]           # display order: this month, prior month
COLUMNS = ["Sep 2026", "Aug 2026"]
ALL_MONTHS = ["2026-05", "2026-06", "2026-07", "2026-08", "2026-09"]   # generated history (for invoices)
MONTH_END = {"2026-05": date(2026, 5, 31), "2026-06": date(2026, 6, 30), "2026-07": date(2026, 7, 31),
             "2026-08": date(2026, 8, 31), "2026-09": date(2026, 9, 30)}
WORKING_DAYS = {"2026-08": 20, "2026-09": 22}   # Brisbane: Ekka show holiday Wed 12 Aug 2026
HOURS_PER_DAY = 7.6


def ym(d):
    return d.strftime("%Y-%m")


def month_start(m):
    y, mm = map(int, m.split("-"))
    return date(y, mm, 1)


def prev_month(m):
    i = ALL_MONTHS.index(m)
    return ALL_MONTHS[i - 1]


def half_up(x):
    return int(x + 0.5) if x >= 0 else -int(-x + 0.5)


def split(total, weights):
    """Split an integer total in proportion to weights; the parts always add back exactly."""
    tw = sum(weights)
    raw = [total * w / tw for w in weights]
    parts = [int(x) for x in raw]
    for i in sorted(range(len(raw)), key=lambda i: raw[i] - parts[i], reverse=True)[: total - sum(parts)]:
        parts[i] += 1
    return parts


def row(label, level, values, note=None):
    """level: heading (no numbers) / detail / subtotal / total / key. values = [Sep, Aug]."""
    return {"label": label, "level": level, "values": values, "note": note}


def per(fn):
    return [fn(m) for m in PERIODS]


def unpaid_at(invoices, d):
    return sum(i["amount"] for i in invoices if i["invoice_date"] <= d and (i["paid_date"] is None or i["paid_date"] > d))


def paid_in(invoices, m):
    return sum(i["amount"] for i in invoices if i["paid_date"] is not None and ym(i["paid_date"]) == m)


# ======================================================================= TRADES

TRADES = {
    "name": "SME · trades", "long_name": "Sample Electrical & Air Pty Ltd",
    "about": "An electrical and air-conditioning contractor in Brisbane: maintenance contracts, installations and call-outs. 7 technicians, 3 office staff.",
    "technicians": 7, "tech_wages": {"2026-08": 54600, "2026-09": 54600}, "tech_cost_rate": 68,
    "callout_rate": 145, "materials_markup": 1.3, "target_margin": 35,
    "contracts": [  # [customer, monthly fee, technician hours a month, materials a month]
        ["Riverside Apartments (strata)", 3200, 18, 60], ["Southbank cafe group", 1800, 10, 40], ["Milton office tower", 4200, 24, 90],
        ["Ashgrove aged care", 3600, 20, 80], ["Newstead gym", 1600, 9, 30], ["Kangaroo Point townhouses", 2400, 14, 50],
        ["Rocklea factory", 3900, 22, 110], ["Wynnum medical centre", 2200, 12, 40], ["Bulimba school", 2800, 16, 60],
        ["Fortitude Valley hotel", 3400, 19, 70], ["Chermside retail centre", 4100, 23, 100], ["West End brewery", 2600, 15, 50],
        ["Carindale vet clinic", 1700, 9, 30], ["Wacol logistics depot", 3000, 17, 70],
    ],
    "contract_pay_days": 30,
    "installs": {  # [job id, job name, completion day, revenue, materials, subcontractors, tech hours, days to pay]
        "2026-08": [["J-2588", "Rocklea factory switchboard", 7, 38500, 15600, 4800, 92, 30],
                    ["J-2591", "Ashgrove hall LED lighting", 14, 21300, 8100, 0, 70, 30],
                    ["J-2594", "Newstead gym air-con", 19, 16800, 6700, 1200, 44, 21],
                    ["J-2597", "Wynnum house solar", 24, 19600, 9400, 2200, 36, 14],
                    ["J-2599", "Valley office cabling", 28, 13400, 3900, 1100, 48, 30]],
        "2026-09": [["J-2604", "Wacol warehouse switchboard", 4, 46800, 22900, 7400, 150, 45],
                    ["J-2607", "Milton office LED lighting", 9, 18600, 6900, 0, 64, 30],
                    ["J-2611", "Carindale solar and battery", 15, 27400, 13800, 3100, 46, 14],
                    ["J-2615", "West End cafe air-con", 18, 12900, 5100, 900, 38, 21],
                    ["J-2618", "Bulimba EV chargers", 23, 9800, 3600, 0, 26, 30],
                    ["J-2620", "Chermside clinic cabling", 29, 15200, 4300, 1800, 52, 30]],
    },
    "callouts": {"2026-05": 55, "2026-06": 57, "2026-07": 54, "2026-08": 58, "2026-09": 64},
    "history_installs": {"2026-05": 4, "2026-06": 5, "2026-07": 4},
    "opex": {"Office and admin wages": {"2026-08": 21900, "2026-09": 21900},
             "Marketing": {"2026-08": 8400, "2026-09": 7600},
             "Vehicles and fuel": {"2026-08": 7900, "2026-09": 8300},
             "Rent and occupancy": {"2026-08": 7000, "2026-09": 7000},
             "Insurance": {"2026-08": 3000, "2026-09": 3000},
             "IT and software": {"2026-08": 2300, "2026-09": 2300},
             "Other overheads": {"2026-08": 3600, "2026-09": 3900}},
    "new_customers": {"2026-08": 41, "2026-09": 47},
    "depreciation": {"2026-08": 4300, "2026-09": 4500}, "interest": {"2026-08": 1100, "2026-09": 1080},
    "loan_repaid": {"2026-08": 5000, "2026-09": 5000}, "capex": {"2026-08": 0, "2026-09": 12000},
    "provision_change": {"2026-08": 1100, "2026-09": 900}, "tax_rate": 25,
    "opening": {"cash": 88000, "stock": 66000, "prepayments": 21000, "fixed_assets": 252000,
                "provisions": 104000, "tax_payable": 31500, "loan": 105000, "share_capital": 10000},
}


def trades_jobs(m):
    """Every job and invoice for May-Sep (seeded, so it's identical every run)."""
    rng = random.Random(2604)
    jobs = []
    for month in ALL_MONTHS:
        start = month_start(month)
        for i, (cust, fee, hrs, mat) in enumerate(m["contracts"]):
            jobs.append({"month": month, "job": f"MC-{i + 1:02d}", "type": "Maintenance contract", "description": cust,
                         "revenue": fee, "materials": mat, "subcontractors": 0, "hours": hrs,
                         "invoice_date": start, "days_to_pay": m["contract_pay_days"] + rng.choice([-5, 0, 0, 3, 8])})
        if month in m["installs"]:
            for j, desc, day, rev, mat, sub, hrs, pay in m["installs"][month]:
                jobs.append({"month": month, "job": j, "type": "Installation", "description": desc, "revenue": rev, "materials": mat,
                             "subcontractors": sub, "hours": hrs, "invoice_date": start + timedelta(days=day - 1), "days_to_pay": pay})
        else:
            for k in range(m["history_installs"][month]):
                rev = rng.randrange(9000, 42000, 100)
                jobs.append({"month": month, "job": f"J-{2500 + ALL_MONTHS.index(month) * 20 + k}", "type": "Installation",
                             "description": f"Installation {k + 1}, {month_start(month).strftime('%B')}", "revenue": rev, "materials": int(rev * 0.38) // 100 * 100,
                             "subcontractors": int(rev * 0.08) // 100 * 100, "hours": rev // 260,
                             "invoice_date": start + timedelta(days=rng.randrange(0, 27)), "days_to_pay": rng.choice([14, 21, 30, 30, 45])})
        for k in range(m["callouts"][month]):
            hrs = rng.choice([1, 1.5, 2, 2, 2.5, 3, 3, 4])
            mat = rng.randrange(20, 240, 10)
            rev = half_up(hrs * m["callout_rate"] + mat * m["materials_markup"])
            jobs.append({"month": month, "job": f"C-{month[5:]}{k + 1:02d}", "type": "Call-out", "description": f"Call-out {k + 1}, {month_start(month).strftime('%B')}",
                         "revenue": rev, "materials": mat, "subcontractors": 0, "hours": hrs,
                         "invoice_date": start + timedelta(days=rng.randrange(0, 28)), "days_to_pay": rng.choice([0, 0, 0, 2, 7, 7, 14, 30])})
    for j in jobs:
        j["paid_date"] = j["invoice_date"] + timedelta(days=j["days_to_pay"])
        j["labour_cost"] = half_up(j["hours"] * m["tech_cost_rate"])
        j["gross_profit"] = j["revenue"] - j["materials"] - j["subcontractors"] - j["labour_cost"]
        j["amount"] = j["revenue"]
    return jobs


def trades(m):
    jobs = trades_jobs(m)
    inv = jobs
    purchases = {mo: sum(j["materials"] + j["subcontractors"] for j in jobs if j["month"] == mo) for mo in ALL_MONTHS}
    o = m["opening"]
    bs = {"2026-07": {**o, "debtors": unpaid_at(inv, MONTH_END["2026-07"]), "creditors": purchases["2026-07"]}}
    bs["2026-07"]["retained"] = (o["cash"] + bs["2026-07"]["debtors"] + o["stock"] + o["prepayments"] + o["fixed_assets"]
                                 - bs["2026-07"]["creditors"] - o["provisions"] - o["tax_payable"] - o["loan"] - o["share_capital"])
    r = {}
    for mo in ["2026-08", "2026-09"]:
        mj = [j for j in jobs if j["month"] == mo]
        by = lambda t, k: sum(j[k] for j in mj if j["type"] == t)
        rev = {t: by(t, "revenue") for t in ["Maintenance contract", "Installation", "Call-out"]}
        revenue = sum(rev.values())
        mat, sub = sum(j["materials"] for j in mj), sum(j["subcontractors"] for j in mj)
        techw = m["tech_wages"][mo]
        cos = mat + sub + techw
        gp = revenue - cos
        opex = {k: v[mo] for k, v in m["opex"].items()}
        ebitda = gp - sum(opex.values())
        pbt = ebitda - m["depreciation"][mo] - m["interest"][mo]
        tax = half_up(pbt * m["tax_rate"] / 100)
        npat = pbt - tax
        prev = bs[prev_month(mo)]
        wages = techw + opex["Office and admin wages"]
        nonwage = sum(v for k, v in opex.items() if "wages" not in k)
        receipts = paid_in(inv, mo)
        pay_sup = purchases[prev_month(mo)] + nonwage
        pay_emp = wages - m["provision_change"][mo]
        operating = receipts - pay_sup - pay_emp - m["interest"][mo]
        cur = {"cash": prev["cash"] + operating - m["capex"][mo] - m["loan_repaid"][mo],
               "debtors": unpaid_at(inv, MONTH_END[mo]), "stock": prev["stock"], "prepayments": prev["prepayments"],
               "fixed_assets": prev["fixed_assets"] + m["capex"][mo] - m["depreciation"][mo],
               "creditors": purchases[mo], "provisions": prev["provisions"] + m["provision_change"][mo],
               "tax_payable": prev["tax_payable"] + tax, "loan": prev["loan"] - m["loan_repaid"][mo],
               "share_capital": prev["share_capital"], "retained": prev["retained"] + npat}
        bs[mo] = cur
        hours = sum(j["hours"] for j in mj)
        avail = m["technicians"] * WORKING_DAYS[mo] * HOURS_PER_DAY
        r[mo] = dict(rev=rev, revenue=revenue, mat=mat, sub=sub, techw=techw, cos=cos, gp=gp, opex=opex, ebitda=ebitda, pbt=pbt,
                     tax=tax, npat=npat, receipts=receipts, pay_sup=pay_sup, pay_emp=pay_emp, operating=operating,
                     jobs_gp=sum(j["gross_profit"] for j in mj), allocated=sum(j["labour_cost"] for j in mj),
                     hours=hours, available=avail)

    pnl = [row("Revenue", "heading", None),
           row(f"Maintenance contracts ({len(m['contracts'])})", "detail", per(lambda mo: r[mo]["rev"]["Maintenance contract"])),
           row("Installations (jobs)", "detail", per(lambda mo: r[mo]["rev"]["Installation"])),
           row("Call-outs and repairs", "detail", per(lambda mo: r[mo]["rev"]["Call-out"])),
           row("Total revenue", "subtotal", per(lambda mo: r[mo]["revenue"])),
           row("Cost of sales", "heading", None),
           row("Materials", "detail", per(lambda mo: -r[mo]["mat"])),
           row("Subcontractors", "detail", per(lambda mo: -r[mo]["sub"])),
           row("Technician wages (incl. super)", "detail", per(lambda mo: -r[mo]["techw"])),
           row("Total cost of sales", "subtotal", per(lambda mo: -r[mo]["cos"])),
           row("Gross profit", "total", per(lambda mo: r[mo]["gp"])),
           row("Operating expenses", "heading", None)]
    for k in m["opex"]:
        pnl.append(row(k, "detail", per(lambda mo, k=k: -r[mo]["opex"][k])))
    pnl += [row("Total operating expenses", "subtotal", per(lambda mo: -sum(r[mo]["opex"].values()))),
            row("EBITDA", "total", per(lambda mo: r[mo]["ebitda"])),
            row("Depreciation", "subtotal", per(lambda mo: -m["depreciation"][mo])),
            row("Interest", "subtotal", per(lambda mo: -m["interest"][mo])),
            row("Profit before tax", "total", per(lambda mo: r[mo]["pbt"])),
            row(f"Income tax provision ({m['tax_rate']}%)", "subtotal", per(lambda mo: -r[mo]["tax"])),
            row("Net profit after tax", "key", per(lambda mo: r[mo]["npat"]))]
    bsr, cfr = sme_bs_cf(bs, r, m, "Materials on hand", "Vehicles and equipment", "Purchase of vehicles and equipment",
                         "Payments to suppliers", "Payments to employees")
    return dict(jobs=jobs, r=r, bs=bs, pnl=pnl, bsr=bsr, cfr=cfr)


def sme_bs_cf(bs, r, m, stock_label, fa_label, capex_label, sup_label, emp_label):
    def ca(mo): b = bs[mo]; return b["cash"] + b["debtors"] + b["stock"] + b["prepayments"]
    def cl(mo): b = bs[mo]; return b["creditors"] + b["provisions"] + b["tax_payable"]
    bsr = [row("Current assets", "heading", None),
           row("Cash at bank", "detail", per(lambda mo: bs[mo]["cash"])),
           row("Trade debtors (unpaid invoices)", "detail", per(lambda mo: bs[mo]["debtors"])),
           row(stock_label, "detail", per(lambda mo: bs[mo]["stock"])),
           row("Prepayments", "detail", per(lambda mo: bs[mo]["prepayments"])),
           row("Total current assets", "subtotal", per(ca)),
           row(fa_label, "subtotal", per(lambda mo: bs[mo]["fixed_assets"])),
           row("Total assets", "total", per(lambda mo: ca(mo) + bs[mo]["fixed_assets"])),
           row("Current liabilities", "heading", None),
           row("Trade creditors (bills due next month)", "detail", per(lambda mo: bs[mo]["creditors"])),
           row("Employee leave provisions", "detail", per(lambda mo: bs[mo]["provisions"])),
           row("Income tax payable", "detail", per(lambda mo: bs[mo]["tax_payable"])),
           row("Total current liabilities", "subtotal", per(cl)),
           row("Equipment finance", "subtotal", per(lambda mo: bs[mo]["loan"])),
           row("Total liabilities", "total", per(lambda mo: cl(mo) + bs[mo]["loan"])),
           row("Net assets", "key", per(lambda mo: ca(mo) + bs[mo]["fixed_assets"] - cl(mo) - bs[mo]["loan"])),
           row("Equity", "heading", None),
           row("Share capital", "detail", per(lambda mo: bs[mo]["share_capital"])),
           row("Retained earnings", "detail", per(lambda mo: bs[mo]["retained"])),
           row("Total equity", "key", per(lambda mo: bs[mo]["share_capital"] + bs[mo]["retained"]))]
    cfr = [row("Operating activities", "heading", None),
           row("Receipts from customers (invoices paid)", "detail", per(lambda mo: r[mo]["receipts"])),
           row(sup_label, "detail", per(lambda mo: -r[mo]["pay_sup"])),
           row(emp_label, "detail", per(lambda mo: -r[mo]["pay_emp"])),
           row("Interest paid", "detail", per(lambda mo: -m["interest"][mo])),
           row("Income tax paid", "detail", per(lambda mo: 0), note="Next PAYG instalment is due in October."),
           row("Net cash from operating activities", "subtotal", per(lambda mo: r[mo]["operating"])),
           row("Investing activities", "heading", None),
           row(capex_label, "detail", per(lambda mo: -m["capex"][mo])),
           row("Net cash from investing activities", "subtotal", per(lambda mo: -m["capex"][mo])),
           row("Financing activities", "heading", None),
           row("Equipment finance repaid", "detail", per(lambda mo: -m["loan_repaid"][mo])),
           row("Net cash from financing activities", "subtotal", per(lambda mo: -m["loan_repaid"][mo])),
           row("Net change in cash", "total", per(lambda mo: r[mo]["operating"] - m["capex"][mo] - m["loan_repaid"][mo])),
           row("Cash at start of month", "subtotal", per(lambda mo: bs[prev_month(mo)]["cash"])),
           row("Cash at end of month", "key", per(lambda mo: bs[mo]["cash"]))]
    return bsr, cfr


# ===================================================================== SERVICES

SERVICES = {
    "name": "SME · services", "long_name": "Sample Advisory Pty Ltd",
    "about": "A Brisbane finance and operations consultancy: projects billed on milestones, monthly retainers and training. 6 consultants, 3 management and admin staff.",
    "consultants": 6, "salaries": {"2026-08": 46500, "2026-09": 46500}, "cost_rate": 60, "target_margin": 40,
    # [code, type, client / description, rate or fee, days to pay]
    "engagements": [
        ["E-311", "Project", "Logistics systems rollout", 175, 30],
        ["E-314", "Project", "Retail pricing review", 190, 30],
        ["E-316", "Project", "Distributor cost-to-serve", 180, 45],
        ["E-318", "Project", "Health charity board pack", 165, 30],
        ["E-320", "Project", "Manufacturer process mapping", 170, 45],
        ["R-102", "Retainer", "Construction firm finance", 9500, 14],
        ["R-105", "Retainer", "Dental group reporting", 6800, 14],
        ["R-108", "Retainer", "Agribusiness CFO support", 12000, 30],
        ["R-110", "Retainer", "Hospitality payroll", 4200, 14],
        ["T-205", "Training", "Budgeting workshop", 6400, 30],
        ["T-207", "Training", "Excel for managers", 8800, 30],
        ["T-209", "Training", "Power BI basics", 4600, 30],
    ],
    # month -> code -> [hours, amount billed (projects only), contractors]
    "activity": {
        "2026-08": {"E-311": [180, 0, 4200], "E-314": [60, 0, 0], "E-316": [88, 15840, 0], "E-320": [100, 0, 1800],
                    "R-102": [56, 0, 0], "R-105": [42, 0, 0], "R-108": [68, 0, 0], "R-110": [34, 0, 0], "T-205": [20, 0, 900]},
        "2026-09": {"E-311": [210, 30000, 4800], "E-314": [96, 0, 0], "E-318": [64, 10560, 0], "E-320": [120, 24000, 2200],
                    "R-102": [58, 0, 0], "R-105": [44, 0, 0], "R-108": [70, 0, 0], "R-110": [36, 0, 0],
                    "T-207": [30, 0, 1500], "T-209": [14, 0, 0]},
    },
    "opening_wip": {"E-311": 12000, "E-314": 0, "E-316": 0, "E-318": 0, "E-320": 6000},
    "history_billing": {"2026-05": 118000, "2026-06": 126000, "2026-07": 121000},   # earlier months' invoices (for debtors)
    "history_contractors": {"2026-07": 3900},
    "opex": {"Management and admin wages": {"2026-08": 24000, "2026-09": 24000},
             "Marketing and business development": {"2026-08": 6500, "2026-09": 5800},
             "Rent and occupancy": {"2026-08": 8000, "2026-09": 8000},
             "IT and software": {"2026-08": 4500, "2026-09": 4500},
             "Professional indemnity insurance": {"2026-08": 2500, "2026-09": 2500},
             "Travel": {"2026-08": 2600, "2026-09": 1800},
             "Other overheads": {"2026-08": 3300, "2026-09": 3300}},
    "new_clients": {"2026-08": 3, "2026-09": 4},
    "depreciation": {"2026-08": 2000, "2026-09": 2000}, "interest": {"2026-08": 250, "2026-09": 240},
    "loan_repaid": {"2026-08": 1700, "2026-09": 1700}, "capex": {"2026-08": 0, "2026-09": 3200},
    "provision_change": {"2026-08": 700, "2026-09": 600}, "tax_rate": 25,
    "opening": {"cash": 158000, "prepayments": 15000, "fixed_assets": 61000,
                "provisions": 121000, "tax_payable": 48500, "loan": 18000, "share_capital": 20000},
}


def services_engagements(m):
    rng = random.Random(311)
    eng = {e[0]: e for e in m["engagements"]}
    rows, invoices = [], []
    for mo in ["2026-08", "2026-09"]:
        for code, (hours, billed, contractors) in m["activity"][mo].items():
            _, typ, desc, rate, pay = eng[code]
            if typ == "Project":
                revenue, bill = hours * rate, billed
            else:  # retainers and training: billed as delivered
                revenue = bill = rate
            rows.append({"month": mo, "code": code, "type": typ, "description": desc, "hours": hours,
                         "revenue": revenue, "billed": bill, "contractors": contractors,
                         "allocated_cost": hours * m["cost_rate"],
                         "contribution": revenue - contractors - hours * m["cost_rate"]})
            if bill:
                d = month_start(mo) + timedelta(days=(27 if typ == "Project" else rng.randrange(0, 20)))
                invoices.append({"invoice": f"INV-{mo[5:]}{code}", "code": code, "amount": bill, "invoice_date": d,
                                 "paid_date": d + timedelta(days=pay + rng.choice([-3, 0, 0, 5, 12]))})
    for mo, total in m["history_billing"].items():  # earlier months, in a few invoices each
        parts = [total // 4] * 3 + [total - 3 * (total // 4)]
        for k, amt in enumerate(parts):
            d = month_start(mo) + timedelta(days=6 + 6 * k)
            invoices.append({"invoice": f"INV-{mo[5:]}H{k}", "code": "earlier", "amount": amt, "invoice_date": d,
                             "paid_date": d + timedelta(days=rng.choice([14, 30, 30, 45, 52]))})
    return rows, invoices


def services(m):
    rows, invoices = services_engagements(m)
    o = m["opening"]
    wip0 = sum(m["opening_wip"].values())
    bs = {"2026-07": {**o, "debtors": unpaid_at(invoices, MONTH_END["2026-07"]), "stock": wip0,
                      "creditors": m["history_contractors"]["2026-07"]}}
    b0 = bs["2026-07"]
    b0["retained"] = (o["cash"] + b0["debtors"] + wip0 + o["prepayments"] + o["fixed_assets"]
                      - b0["creditors"] - o["provisions"] - o["tax_payable"] - o["loan"] - o["share_capital"])
    wip = dict(m["opening_wip"])
    r = {}
    for mo in ["2026-08", "2026-09"]:
        mr = [x for x in rows if x["month"] == mo]
        rev = {t: sum(x["revenue"] for x in mr if x["type"] == t) for t in ["Project", "Retainer", "Training"]}
        revenue = sum(rev.values())
        contractors = sum(x["contractors"] for x in mr)
        sal = m["salaries"][mo]
        cos = sal + contractors
        gp = revenue - cos
        opex = {k: v[mo] for k, v in m["opex"].items()}
        ebitda = gp - sum(opex.values())
        pbt = ebitda - m["depreciation"][mo] - m["interest"][mo]
        tax = half_up(pbt * m["tax_rate"] / 100)
        npat = pbt - tax
        for x in mr:
            if x["type"] == "Project":
                wip[x["code"]] = wip.get(x["code"], 0) + x["revenue"] - x["billed"]
        prev = bs[prev_month(mo)]
        wages = sal + opex["Management and admin wages"]
        nonwage = sum(v for k, v in opex.items() if "wages" not in k)
        receipts = paid_in(invoices, mo)
        pay_sup = prev["creditors"] + nonwage           # last month's contractor bills + this month's overheads
        pay_emp = wages - m["provision_change"][mo]
        operating = receipts - pay_sup - pay_emp - m["interest"][mo]
        bs[mo] = {"cash": prev["cash"] + operating - m["capex"][mo] - m["loan_repaid"][mo],
                  "debtors": unpaid_at(invoices, MONTH_END[mo]), "stock": sum(wip.values()), "prepayments": prev["prepayments"],
                  "fixed_assets": prev["fixed_assets"] + m["capex"][mo] - m["depreciation"][mo],
                  "creditors": contractors, "provisions": prev["provisions"] + m["provision_change"][mo],
                  "tax_payable": prev["tax_payable"] + tax, "loan": prev["loan"] - m["loan_repaid"][mo],
                  "share_capital": prev["share_capital"], "retained": prev["retained"] + npat}
        hours = sum(x["hours"] for x in mr)
        r[mo] = dict(rev=rev, revenue=revenue, contractors=contractors, sal=sal, cos=cos, gp=gp, opex=opex, ebitda=ebitda,
                     pbt=pbt, tax=tax, npat=npat, receipts=receipts, pay_sup=pay_sup, pay_emp=pay_emp, operating=operating,
                     hours=hours, available=m["consultants"] * WORKING_DAYS[mo] * HOURS_PER_DAY,
                     contribution=sum(x["contribution"] for x in mr), allocated=sum(x["allocated_cost"] for x in mr),
                     wip=dict(wip))
    pnl = [row("Revenue", "heading", None),
           row("Projects (hours worked)", "detail", per(lambda mo: r[mo]["rev"]["Project"])),
           row("Retainers", "detail", per(lambda mo: r[mo]["rev"]["Retainer"])),
           row("Training", "detail", per(lambda mo: r[mo]["rev"]["Training"])),
           row("Total revenue", "subtotal", per(lambda mo: r[mo]["revenue"])),
           row("Cost of sales", "heading", None),
           row("Consultant salaries (incl. super)", "detail", per(lambda mo: -r[mo]["sal"])),
           row("Contractors", "detail", per(lambda mo: -r[mo]["contractors"])),
           row("Total cost of sales", "subtotal", per(lambda mo: -r[mo]["cos"])),
           row("Gross profit", "total", per(lambda mo: r[mo]["gp"])),
           row("Operating expenses", "heading", None)]
    for k in m["opex"]:
        pnl.append(row(k, "detail", per(lambda mo, k=k: -r[mo]["opex"][k])))
    pnl += [row("Total operating expenses", "subtotal", per(lambda mo: -sum(r[mo]["opex"].values()))),
            row("EBITDA", "total", per(lambda mo: r[mo]["ebitda"])),
            row("Depreciation", "subtotal", per(lambda mo: -m["depreciation"][mo])),
            row("Interest", "subtotal", per(lambda mo: -m["interest"][mo])),
            row("Profit before tax", "total", per(lambda mo: r[mo]["pbt"])),
            row(f"Income tax provision ({m['tax_rate']}%)", "subtotal", per(lambda mo: -r[mo]["tax"])),
            row("Net profit after tax", "key", per(lambda mo: r[mo]["npat"]))]
    bsr, cfr = sme_bs_cf(bs, r, m, "Work in progress (unbilled project time)", "Office equipment", "Purchase of equipment",
                         "Payments to contractors and suppliers", "Payments to employees")
    return dict(engagements=rows, invoices=invoices, r=r, bs=bs, pnl=pnl, bsr=bsr, cfr=cfr)


# ========================================================================== NFP

NFP = {
    "name": "Not-for-profit", "long_name": "Sample Community Services Ltd",
    "about": "A Brisbane community services charity funded by six grants, donations, events and program fees. About 18 staff. Registered charity, income-tax exempt.",
    # [code, short name, program, funder, total, start, end, instalments [(date, amount)], received to 31 Jul, recognised to 31 Jul, spend Aug, spend Sep]
    "grants": [
        ["G-101", "Youth", "Youth outreach", "State Department of Families", 480000, date(2025, 7, 1), date(2027, 6, 30),
         [(date(2025, 7, 15), 60000), (date(2025, 10, 15), 60000), (date(2026, 1, 15), 60000), (date(2026, 4, 15), 60000), (date(2026, 7, 15), 60000), (date(2026, 10, 15), 60000)],
         262000, 21500, 22800],
        ["G-102", "Housing", "Housing support", "State Housing Program", 360000, date(2026, 1, 1), date(2026, 12, 31),
         [(date(2026, 1, 8), 180000), (date(2026, 7, 6), 180000)], 196000, 30500, 31200],
        ["G-103", "Meals", "Community meals", "Local council community grant", 48000, date(2026, 7, 1), date(2027, 6, 30),
         [(date(2026, 7, 10), 48000)], 3600, 4100, 4300],
        ["G-104", "Digital", "Digital literacy", "Philanthropic foundation", 90000, date(2025, 10, 1), date(2027, 3, 31),
         [(date(2025, 10, 20), 45000), (date(2026, 10, 20), 45000)], 49500, 5200, 4900],
        ["G-105", "Mind", "Mental health first aid", "Federal health program", 120000, date(2026, 4, 1), date(2027, 3, 31),
         [(date(2026, 4, 9), 60000), (date(2026, 10, 9), 60000)], 37000, 9400, 10800],
        ["G-106", "Volunteer", "Volunteer coordinator", "State volunteering grant", 36000, date(2026, 3, 1), date(2027, 2, 28),
         [(date(2026, 3, 3), 36000)], 15000, 3000, 3000],
    ],
    "grant_wage_share": 0.75,
    "untied_program": {"Program delivery wages (untied)": {"2026-08": 14000, "2026-09": 14500},
                       "Program costs (untied)": {"2026-08": 5500, "2026-09": 6100}},
    "income": {"Donations": {"2026-08": 18400, "2026-09": 27900},
               "Fundraising events": {"2026-08": 0, "2026-09": 41600},
               "Program fees": {"2026-08": 26800, "2026-09": 28300},
               "Interest": {"2026-08": 1450, "2026-09": 1380}},
    "fundraising": {"Grant writing and reporting": {"2026-08": 7100, "2026-09": 7100},
                    "Donor campaigns": {"2026-08": 2200, "2026-09": 5400},
                    "Event costs": {"2026-08": 2400, "2026-09": 16900}},
    "admin": {"Administration wages": {"2026-08": 18300, "2026-09": 18300},
              "Occupancy": {"2026-08": 10000, "2026-09": 10000},
              "Other administration": {"2026-08": 8000, "2026-09": 7600}},
    "depreciation": {"2026-08": 2900, "2026-09": 2900}, "capex": {"2026-08": 0, "2026-09": 0},
    "fees_receivable": {"2026-07": 9100, "2026-08": 9800, "2026-09": 10400},
    "provision_change": {"2026-08": 900, "2026-09": 700},
    "opening": {"cash": 610000, "prepayments": 21000, "fixed_assets": 178000, "payables": 36500, "provisions": 165000},
    "reserves_target_months": 3, "ending_within_months": 6,
}


def nfp(m):
    a = m
    g = a["grants"]
    received = lambda gr, d: sum(amt for dt, amt in gr[7] if dt <= d)
    recog = {gr[0]: {"2026-07": gr[8]} for gr in g}
    for gr in g:
        recog[gr[0]]["2026-08"] = gr[8] + gr[9]
        recog[gr[0]]["2026-09"] = gr[8] + gr[9] + gr[10]
    def grant_bal(mo):  # positive = received in advance (liability); negative = spent ahead (receivable)
        return {gr[0]: received(gr, MONTH_END[mo]) - recog[gr[0]][mo] for gr in g}
    def adv(mo): return sum(v for v in grant_bal(mo).values() if v > 0)
    def grec(mo): return -sum(v for v in grant_bal(mo).values() if v < 0)
    o = a["opening"]
    bs = {"2026-07": {**o, "grants_in_advance": adv("2026-07"), "grants_receivable": grec("2026-07"),
                      "fees_receivable": a["fees_receivable"]["2026-07"]}}
    b0 = bs["2026-07"]
    b0["accumulated"] = (o["cash"] + b0["fees_receivable"] + b0["grants_receivable"] + o["prepayments"] + o["fixed_assets"]
                         - o["payables"] - b0["grants_in_advance"] - o["provisions"])
    r = {}
    for mo in ["2026-08", "2026-09"]:
        k = 9 if mo == "2026-08" else 10
        gspend = {gr[0]: gr[k] for gr in g}
        grant_income = sum(gspend.values())
        other_income = {kk: v[mo] for kk, v in a["income"].items()}
        income = grant_income + sum(other_income.values())
        grant_wages = half_up(grant_income * a["grant_wage_share"])
        grant_costs = grant_income - grant_wages
        untied = {kk: v[mo] for kk, v in a["untied_program"].items()}
        program = grant_income + sum(untied.values())
        fund = {kk: v[mo] for kk, v in a["fundraising"].items()}
        admin = {kk: v[mo] for kk, v in a["admin"].items()}
        expenses = program + sum(fund.values()) + sum(admin.values()) + a["depreciation"][mo]
        surplus = income - expenses
        prev = bs[prev_month(mo)]
        wages = grant_wages + untied["Program delivery wages (untied)"] + fund["Grant writing and reporting"] + admin["Administration wages"]
        nonwage = expenses - a["depreciation"][mo] - wages
        grants_received = sum(amt for gr in g for dt, amt in gr[7] if ym(dt) == mo)
        fees_received = other_income["Program fees"] - (a["fees_receivable"][mo] - a["fees_receivable"][prev_month(mo)])
        don_received = other_income["Donations"] + other_income["Fundraising events"]
        pay_sup = prev["payables"]                 # suppliers are paid the following month
        pay_emp = wages - a["provision_change"][mo]
        operating = grants_received + don_received + fees_received + other_income["Interest"] - pay_sup - pay_emp
        bs[mo] = {"cash": prev["cash"] + operating - a["capex"][mo], "fees_receivable": a["fees_receivable"][mo],
                  "grants_receivable": grec(mo), "prepayments": prev["prepayments"],
                  "fixed_assets": prev["fixed_assets"] + a["capex"][mo] - a["depreciation"][mo],
                  "payables": nonwage, "grants_in_advance": adv(mo), "provisions": prev["provisions"] + a["provision_change"][mo],
                  "accumulated": prev["accumulated"] + surplus}
        r[mo] = dict(gspend=gspend, grant_income=grant_income, other_income=other_income, income=income,
                     grant_wages=grant_wages, grant_costs=grant_costs, untied=untied, program=program, fund=fund, admin=admin,
                     expenses=expenses, surplus=surplus, wages=wages, nonwage=nonwage, grants_received=grants_received,
                     fees_received=fees_received, don_received=don_received, pay_sup=pay_sup, pay_emp=pay_emp,
                     operating=operating, cash_expenses=expenses - a["depreciation"][mo])
    pnl = [row("Income", "heading", None)]
    for gr in g:
        pnl.append(row(f"{gr[2]} grant", "detail", per(lambda mo, c=gr[0]: r[mo]["gspend"][c])))
    for kk in a["income"]:
        pnl.append(row(kk, "detail", per(lambda mo, kk=kk: r[mo]["other_income"][kk])))
    pnl += [row("Total income", "subtotal", per(lambda mo: r[mo]["income"])),
            row("Programs", "heading", None),
            row("Grant-funded program wages", "detail", per(lambda mo: -r[mo]["grant_wages"])),
            row("Grant-funded program costs", "detail", per(lambda mo: -r[mo]["grant_costs"]))]
    for kk in a["untied_program"]:
        pnl.append(row(kk, "detail", per(lambda mo, kk=kk: -r[mo]["untied"][kk])))
    pnl.append(row("Total program spend", "subtotal", per(lambda mo: -r[mo]["program"])))
    for head, key, total in [("Fundraising", "fund", "Total fundraising costs"), ("Administration", "admin", "Total administration")]:
        pnl.append(row(head, "heading", None))
        for kk in a["fundraising" if key == "fund" else "admin"]:
            pnl.append(row(kk, "detail", per(lambda mo, kk=kk, key=key: -r[mo][key][kk])))
        pnl.append(row(total, "subtotal", per(lambda mo, key=key: -sum(r[mo][key].values()))))
    pnl += [row("Depreciation", "subtotal", per(lambda mo: -a["depreciation"][mo])),
            row("Total expenses", "total", per(lambda mo: -r[mo]["expenses"])),
            row("Surplus for the month", "key", per(lambda mo: r[mo]["surplus"]), note="Income-tax exempt charity: no income tax.")]

    def ca(mo): b = bs[mo]; return b["cash"] + b["fees_receivable"] + b["grants_receivable"] + b["prepayments"]
    def cl(mo): b = bs[mo]; return b["payables"] + b["grants_in_advance"] + b["provisions"]
    bsr = [row("Current assets", "heading", None),
           row("Cash at bank", "detail", per(lambda mo: bs[mo]["cash"])),
           row("Program fees receivable", "detail", per(lambda mo: bs[mo]["fees_receivable"])),
           row("Grants receivable (spent ahead of instalment)", "detail", per(lambda mo: bs[mo]["grants_receivable"])),
           row("Prepayments", "detail", per(lambda mo: bs[mo]["prepayments"])),
           row("Total current assets", "subtotal", per(ca)),
           row("Vehicles and equipment", "subtotal", per(lambda mo: bs[mo]["fixed_assets"])),
           row("Total assets", "total", per(lambda mo: ca(mo) + bs[mo]["fixed_assets"])),
           row("Current liabilities", "heading", None),
           row("Payables (bills due next month)", "detail", per(lambda mo: bs[mo]["payables"])),
           row("Grants received in advance (unspent)", "detail", per(lambda mo: bs[mo]["grants_in_advance"])),
           row("Employee leave provisions", "detail", per(lambda mo: bs[mo]["provisions"])),
           row("Total liabilities", "total", per(cl)),
           row("Net assets", "key", per(lambda mo: ca(mo) + bs[mo]["fixed_assets"] - cl(mo))),
           row("Equity", "heading", None),
           row("Accumulated funds", "key", per(lambda mo: bs[mo]["accumulated"]))]
    cfr = [row("Operating activities", "heading", None),
           row("Grant instalments received", "detail", per(lambda mo: r[mo]["grants_received"]), note="Next instalments arrive in October."),
           row("Donations and fundraising received", "detail", per(lambda mo: r[mo]["don_received"])),
           row("Program fees received", "detail", per(lambda mo: r[mo]["fees_received"])),
           row("Interest received", "detail", per(lambda mo: r[mo]["other_income"]["Interest"])),
           row("Payments to suppliers", "detail", per(lambda mo: -r[mo]["pay_sup"])),
           row("Payments to employees", "detail", per(lambda mo: -r[mo]["pay_emp"])),
           row("Net cash from operating activities", "subtotal", per(lambda mo: r[mo]["operating"])),
           row("Investing activities", "heading", None),
           row("Purchase of vehicles and equipment", "detail", per(lambda mo: -a["capex"][mo])),
           row("Net cash from investing activities", "subtotal", per(lambda mo: -a["capex"][mo])),
           row("Net change in cash", "total", per(lambda mo: r[mo]["operating"] - a["capex"][mo])),
           row("Cash at start of month", "subtotal", per(lambda mo: bs[prev_month(mo)]["cash"])),
           row("Cash at end of month", "key", per(lambda mo: bs[mo]["cash"]))]
    grant_rows = []
    hist_rng = random.Random(102)
    for gr in g:
        months = []
        d = gr[5]
        while d <= gr[6]:
            months.append(d.strftime("%Y-%m"))
            d = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
        budget = dict(zip(months, split(gr[4], [1] * len(months))))      # even monthly budget, adds to the grant
        before = [mo for mo in months if mo < "2026-08"]
        spend = dict(zip(before, split(gr[8], [hist_rng.uniform(0.8, 1.2) for _ in before]))) if before else {}
        spend["2026-08"], spend["2026-09"] = gr[9], gr[10]
        to_date = [mo for mo in months if mo <= "2026-09"]
        budget_to_date = sum(budget[mo] for mo in to_date)
        grant_rows.append({"code": gr[0], "short": gr[1], "program": gr[2], "funder": gr[3], "total": gr[4],
                           "start": gr[5].isoformat(), "end": gr[6].isoformat(),
                           "received_to_date": received(gr, MONTH_END["2026-09"]), "spent_to_date": recog[gr[0]]["2026-09"],
                           "spent_aug": gr[9], "spent_sep": gr[10], "budget_to_date": budget_to_date,
                           "spend_vs_budget_pct": round(100 * recog[gr[0]]["2026-09"] / budget_to_date, 1),
                           "unspent": gr[4] - recog[gr[0]]["2026-09"],
                           "balance_30_sep": grant_bal("2026-09")[gr[0]],
                           "months_left": max(0, (gr[6].year - 2026) * 12 + gr[6].month - 9),
                           "monthly": [{"month": mo, "spend": spend[mo], "budget": budget[mo]} for mo in to_date],
                           "budget_by_month": budget})
    return dict(r=r, bs=bs, pnl=pnl, bsr=bsr, cfr=cfr, grants=grant_rows, grant_bal=grant_bal)


# ============================================================ the fourth sheet
# Three headline numbers (this month vs last month) and one chart that drills
# into the detail. The full detail lists go to the Excel/PDF downloads and CSVs.

def chg(cur, prev, fmt, better="up"):
    up = cur > prev
    good = (up and better == "up") or (not up and better == "down")
    arrow = "▲" if up else ("▼" if cur < prev else "■")
    return f"{arrow} from {fmt(prev)} in Aug", "good" if (good and cur != prev) else ("" if cur == prev else "bad")


def money(v):
    """$1,234, with negatives in accounting brackets: ($1,234)."""
    v = half_up(v)
    return f"(${-v:,})" if v < 0 else f"${v:,}"


def support(title, formula, rows, note=None, series=None):
    """The workings behind a number: rows are [label, September, August] (already formatted)."""
    return {"title": title, "formula": formula, "head": ["", "Sep 2026", "Aug 2026"], "rows": rows, "note": note, "series": series}


def pct(v, dp=1):
    return f"{v:.{dp}f}%"


def hrs(v):
    return f"{v:,.1f}".rstrip("0").rstrip(".") + " h"


def fourth_trades(m, out):
    r = out["r"]
    gm = {mo: 100 * r[mo]["gp"] / r[mo]["revenue"] for mo in PERIODS}
    cac = {mo: m["opex"]["Marketing"][mo] / m["new_customers"][mo] for mo in PERIODS}
    util = {mo: 100 * r[mo]["hours"] / r[mo]["available"] for mo in PERIODS}
    installs = sorted([j for j in out["jobs"] if j["month"] == "2026-09" and j["type"] == "Installation"],
                      key=lambda j: -j["gross_profit"] / j["revenue"])     # bars sorted by value
    k1, c1 = chg(gm["2026-09"], gm["2026-08"], pct)
    k2, c2 = chg(cac["2026-09"], cac["2026-08"], money, "down")
    k3, c3 = chg(util["2026-09"], util["2026-08"], lambda v: pct(v, 0))
    P = lambda f: [f(mo) for mo in PERIODS]
    return {
        "kpis": [
            {"label": "Gross margin, September", "value": pct(gm["2026-09"]), "sub": k1, "cls": c1, "spine": True,
             "support": support("Gross margin", "Gross profit ÷ revenue", [
                 ["Revenue (every job invoiced in the month)", *P(lambda mo: money(r[mo]["revenue"]))],
                 ["Materials", *P(lambda mo: money(-r[mo]["mat"]))], ["Subcontractors", *P(lambda mo: money(-r[mo]["sub"]))],
                 ["Technician wages", *P(lambda mo: money(-r[mo]["techw"]))],
                 ["Gross profit", *P(lambda mo: money(r[mo]["gp"]))], ["Gross margin", *P(lambda mo: pct(gm[mo]))]],
                 "Technicians are on salary, so a quiet month for jobs lowers the margin even if every job is priced well.")},
            {"label": "Cost to win a customer", "value": money(cac["2026-09"]), "sub": k2, "cls": c2,
             "support": support("Cost to win a customer", "Marketing spend ÷ new customers", [
                 ["Marketing spend", *P(lambda mo: money(m["opex"]["Marketing"][mo]))],
                 ["New customers (first job ever)", *P(lambda mo: str(m["new_customers"][mo]))],
                 ["Cost per new customer", *P(lambda mo: money(cac[mo]))]])},
            {"label": "Technician time on jobs", "value": pct(util["2026-09"], 0), "sub": k3, "cls": c3,
             "support": support("Technician time on jobs", "Hours charged to jobs ÷ hours available", [
                 ["Hours charged to jobs (timesheets)", *P(lambda mo: hrs(r[mo]["hours"]))],
                 ["Technicians", *P(lambda mo: str(m["technicians"]))],
                 ["Working days", *P(lambda mo: str(WORKING_DAYS[mo]))],
                 ["Hours available (technicians × days × 7.6)", *P(lambda mo: hrs(r[mo]["available"]))],
                 ["Time on jobs", *P(lambda mo: pct(util[mo], 0))]],
                 "August had one fewer working day for the Ekka show holiday. The rest is travel, training, quoting and waiting time.")}],
        "chart": {"title": "Margin by installation job, September (%)", "labels": [j["description"] for j in installs],
                  "values": [round(100 * j["gross_profit"] / j["revenue"], 1) for j in installs],
                  "target": m["target_margin"], "format": "pct0", "what": "job margin",
                  "details": [support(j["description"], "Gross profit ÷ revenue for this job", [
                      ["Invoiced", j["invoice_date"].strftime("%-d %b"), ""], ["Revenue", money(j["revenue"]), ""],
                      ["Materials", money(-j["materials"]), ""], ["Subcontractors", money(-j["subcontractors"]), ""],
                      ["Technician time", f"{hrs(j['hours'])} × ${m['tech_cost_rate']} = {money(-j['labour_cost'])}", ""],
                      ["Gross profit", money(j["gross_profit"]), ""], ["Margin", pct(100 * j["gross_profit"] / j["revenue"]), ""]])
                      for j in installs]},
        "facts": dict(gm=gm, cac=cac, util=util),
    }


def fourth_services(m, out):
    r = out["r"]
    util = {mo: 100 * r[mo]["hours"] / r[mo]["available"] for mo in PERIODS}
    rate = {mo: r[mo]["revenue"] / r[mo]["hours"] for mo in PERIODS}
    lock = {mo: out["bs"][mo]["debtors"] + out["bs"][mo]["stock"] for mo in PERIODS}
    sep = sorted([x for x in out["engagements"] if x["month"] == "2026-09"], key=lambda x: -x["contribution"] / x["revenue"])
    k1, c1 = chg(util["2026-09"], util["2026-08"], lambda v: pct(v, 0))
    k2, c2 = chg(rate["2026-09"], rate["2026-08"], money)
    k3, c3 = chg(lock["2026-09"], lock["2026-08"], money, "down")
    P = lambda f: [f(mo) for mo in PERIODS]
    return {
        "kpis": [
            {"label": "Consultant utilisation, September", "value": pct(util["2026-09"], 0), "sub": k1, "cls": c1, "spine": True,
             "support": support("Consultant utilisation", "Billable hours ÷ hours available", [
                 ["Billable hours (timesheets)", *P(lambda mo: hrs(r[mo]["hours"]))],
                 ["Consultants", *P(lambda mo: str(m["consultants"]))], ["Working days", *P(lambda mo: str(WORKING_DAYS[mo]))],
                 ["Hours available (consultants × days × 7.6)", *P(lambda mo: hrs(r[mo]["available"]))],
                 ["Utilisation", *P(lambda mo: pct(util[mo], 0))]])},
            {"label": "Revenue per billable hour", "value": money(rate["2026-09"]), "sub": k2, "cls": c2,
             "support": support("Revenue per billable hour", "Revenue ÷ billable hours", [
                 ["Revenue", *P(lambda mo: money(r[mo]["revenue"]))], ["Billable hours", *P(lambda mo: hrs(r[mo]["hours"]))],
                 ["Revenue per hour", *P(lambda mo: money(rate[mo]))]],
                 "Retainers and training are fixed fees, so fewer hours on them raises the hourly figure.")},
            {"label": "Unbilled work + unpaid invoices", "value": money(lock["2026-09"]), "sub": k3, "cls": c3,
             "support": support("Cash tied up in work", "Work in progress + unpaid invoices at month end", [
                 ["Work in progress (project time not yet billed)", *P(lambda mo: money(out["bs"][mo]["stock"]))],
                 ["Unpaid client invoices", *P(lambda mo: money(out["bs"][mo]["debtors"]))],
                 ["Total tied up", *P(lambda mo: money(lock[mo]))]],
                 "Milestone billing on the logistics and manufacturer projects landed at the end of September, so it moved from unbilled to unpaid.")}],
        "chart": {"title": "Margin by engagement, September (%)", "labels": [x["description"] for x in sep],
                  "values": [round(100 * x["contribution"] / x["revenue"], 1) for x in sep],
                  "target": m["target_margin"], "format": "pct0", "what": "engagement margin",
                  "details": [support(x["description"], "Contribution ÷ revenue for this engagement", [
                      ["Type", x["type"], ""], ["Hours", hrs(x["hours"]), ""], ["Revenue", money(x["revenue"]), ""],
                      ["Contractors", money(-x["contractors"]), ""],
                      ["Consultant time", f"{hrs(x['hours'])} × ${m['cost_rate']} = {money(-x['allocated_cost'])}", ""],
                      ["Contribution", money(x["contribution"]), ""], ["Margin", pct(100 * x["contribution"] / x["revenue"]), ""]])
                      for x in sep]},
        "facts": dict(util=util, rate=rate, lock=lock),
    }


def fourth_nfp(m, out):
    r, bs = out["r"], out["bs"]
    raised = {mo: r[mo]["grant_income"] + r[mo]["other_income"]["Donations"] + r[mo]["other_income"]["Fundraising events"] for mo in PERIODS}
    fund = {mo: sum(r[mo]["fund"].values()) for mo in PERIODS}
    ctr = {mo: fund[mo] / raised[mo] for mo in PERIODS}
    unrestricted = {mo: bs[mo]["cash"] - bs[mo]["grants_in_advance"] for mo in PERIODS}
    runway = {mo: unrestricted[mo] / r[mo]["cash_expenses"] for mo in PERIODS}
    ending = [gr for gr in out["grants"] if gr["months_left"] < m["ending_within_months"]]
    cents = lambda v: f"{half_up(v * 100)}¢"
    k1, c1 = chg(ctr["2026-09"], ctr["2026-08"], cents, "down")
    k2, c2 = chg(runway["2026-09"], runway["2026-08"], lambda v: f"{v:.1f} months")
    P = lambda f: [f(mo) for mo in PERIODS]
    G = sorted(out["grants"], key=lambda gr: -gr["total"])     # biggest grants first, same order in both views
    mname = lambda mo: date(int(mo[:4]), int(mo[5:]), 1).strftime("%b %y")
    return {
        "kpis": [
            {"label": "Cost to raise a dollar, September", "value": cents(ctr["2026-09"]), "sub": k1, "cls": c1, "spine": True,
             "support": support("Cost to raise a dollar", "Fundraising costs ÷ money raised (grants, donations, events)", [
                 *[[k, *P(lambda mo, k=k: money(r[mo]["fund"][k]))] for k in m["fundraising"]],
                 ["Fundraising costs", *P(lambda mo: money(fund[mo]))],
                 ["Grant income", *P(lambda mo: money(r[mo]["grant_income"]))],
                 ["Donations", *P(lambda mo: money(r[mo]["other_income"]["Donations"]))],
                 ["Fundraising events", *P(lambda mo: money(r[mo]["other_income"]["Fundraising events"]))],
                 ["Money raised", *P(lambda mo: money(raised[mo]))], ["Cost per dollar raised", *P(lambda mo: cents(ctr[mo]))]],
                 "September's gala raised $41,600 but cost $16,900 to run, which lifts the month's figure.")},
            {"label": "Unrestricted cash runway", "value": f"{runway['2026-09']:.1f} months", "sub": k2, "cls": c2,
             "support": support("Unrestricted cash runway", "(Cash at bank − unspent grant money) ÷ this month's cash spending", [
                 ["Cash at bank", *P(lambda mo: money(bs[mo]["cash"]))],
                 ["Less unspent grant money (belongs to funders' programs)", *P(lambda mo: money(-bs[mo]["grants_in_advance"]))],
                 ["Unrestricted cash", *P(lambda mo: money(unrestricted[mo]))],
                 ["Cash spending in the month (expenses less depreciation)", *P(lambda mo: money(r[mo]["cash_expenses"]))],
                 ["Runway", *P(lambda mo: f"{runway[mo]:.1f} months")]],
                 f"Reserves target: {m['reserves_target_months']} months.")},
            {"label": f"Grants ending in {m['ending_within_months']} months", "value": f"{len(ending)} · {money(sum(gr['unspent'] for gr in ending))}",
             "sub": "still to spend before they end", "cls": "bad" if ending else "",
             "support": {"title": f"Grants ending in the next {m['ending_within_months']} months", "formula": "Grant total − spent to date",
                         "head": ["", "Ends", "Still to spend"],
                         "rows": [[gr["program"], date.fromisoformat(gr["end"]).strftime("%-d %b %Y"), money(gr["unspent"])] for gr in ending]
                                 + [["Total", "", money(sum(gr["unspent"] for gr in ending))]],
                         "note": "Unspent money usually has to be returned, or an extension negotiated, so plan the spending now.", "series": None}}],
        "chart": {"title": "Grant spend to date against budget", "labels": [gr["program"] for gr in G],
                  "values": [gr["spend_vs_budget_pct"] for gr in G], "target": 100, "format": "pct0", "what": "grant spend against budget",
                  "plain": True,
                  "views": [{"id": "pct", "label": "% of budget", "values": [gr["spend_vs_budget_pct"] for gr in G], "format": "pct0", "target": 100},
                            {"id": "spend", "label": "$ spent", "values": [gr["spent_to_date"] for gr in G], "format": "money_k",
                             "marks": [gr["budget_to_date"] for gr in G], "mark_label": "Budget to date"}],
                  "details": [support(gr["program"], f"{gr['funder']} · {money(gr['total'])} · {date.fromisoformat(gr['start']).strftime('%b %Y')} to {date.fromisoformat(gr['end']).strftime('%b %Y')}", [
                      ["Received from the funder", money(gr["received_to_date"]), ""], ["Still to spend", money(gr["unspent"]), ""],
                      ["Months left", str(gr["months_left"]), ""],
                      ["Spent to date", money(gr["spent_to_date"]), ""], ["Budget to date", money(gr["budget_to_date"]), ""],
                      ["Spent against budget", pct(gr["spend_vs_budget_pct"]), ""]], None,
                      {"title": "Spend by month against budget", "labels": [mname(x["month"]) for x in gr["monthly"]],
                       "values": [x["spend"] for x in gr["monthly"]], "budget": [x["budget"] for x in gr["monthly"]], "format": "money0"})
                      for gr in G]},
        "facts": dict(ctr=ctr, runway=runway, unrestricted=unrestricted, ending=ending),
    }


# ============================================================== assumptions

def trades_assumptions(m, out):
    sep = [j for j in out["jobs"] if j["month"] == "2026-09"]
    return [
        ["The business", [["What it is", m["about"]], ["Reporting month", "September 2026 (the last closed month), compared with August 2026"],
                          ["Financial year", "FY2027: 1 July 2026 to 30 June 2027"]]],
        ["Jobs (September)", [["Maintenance contracts", f"{len(m['contracts'])} customers, invoiced on the 1st, paid in about {m['contract_pay_days']} days"],
                              ["Installations", f"{len(m['installs']['2026-09'])} named jobs, each with its own quote, materials, subcontractors and hours"],
                              ["Call-outs", f"{m['callouts']['2026-09']} jobs at ${m['callout_rate']}/hour plus materials marked up {round((m['materials_markup'] - 1) * 100)}%"],
                              ["Jobs in September", f"{len(sep)} in total (every one is in the Excel download and CSV)"]]],
        ["Costs", [["Technicians", f"{m['technicians']} on salary: ${m['tech_wages']['2026-09']:,} a month incl. super"],
                   ["Job costing rate", f"${m['tech_cost_rate']}/hour for technician time charged to a job"],
                   ["Working days", "20 in August (Ekka show holiday), 22 in September; 7.6 hours a day"],
                   ["Overheads", "set month by month, as shown in the P&L"],
                   ["Income tax", f"{m['tax_rate']}% of profit, provided monthly; next PAYG instalment due October"]]],
        ["Cash and balance sheet", [["Customer payments", "each invoice is paid on its own date; unpaid invoices at month end = debtors"],
                                    ["Supplier bills", "materials and subcontractors are paid the following month"],
                                    ["Equipment finance", f"${m['loan_repaid']['2026-09']:,} repaid each month"],
                                    ["New equipment", f"a ${m['capex']['2026-09']:,} trailer bought in September"],
                                    ["GST", "excluded throughout, for simplicity"]]],
    ]


def services_assumptions(m, out):
    return [
        ["The business", [["What it is", m["about"]], ["Reporting month", "September 2026, compared with August 2026"],
                          ["Financial year", "FY2027: 1 July 2026 to 30 June 2027"]]],
        ["Engagements (September)", [["Projects", "hours worked at each project's rate; billed on milestones (unbilled time = work in progress)"],
                                     ["Retainers", "fixed monthly fee, billed monthly"], ["Training", "fixed fee, billed on delivery"],
                                     ["Engagements in September", f"{len(m['activity']['2026-09'])} (every one is in the Excel download and CSV)"]]],
        ["Costs", [["Consultants", f"{m['consultants']} on salary: ${m['salaries']['2026-09']:,} a month incl. super"],
                   ["Engagement costing rate", f"${m['cost_rate']}/hour for consultant time"],
                   ["Working days", "20 in August (Ekka show holiday), 22 in September; 7.6 hours a day"],
                   ["Income tax", f"{m['tax_rate']}% of profit, provided monthly"]]],
        ["Cash and balance sheet", [["Client payments", "each invoice is paid on its own date; unpaid invoices at month end = debtors"],
                                    ["Contractors", "paid the following month"], ["GST", "excluded throughout, for simplicity"]]],
    ]


def nfp_assumptions(m, out):
    return [
        ["The organisation", [["What it is", m["about"]], ["Reporting month", "September 2026, compared with August 2026"],
                              ["Financial year", "FY2027: 1 July 2026 to 30 June 2027"]]],
        ["Grants", [[gr['program'], f"{gr['funder']}: ${gr['total']:,}, {gr['start'][:7]} to {gr['end'][:7]}"] for gr in out["grants"]]
                   + [["Grant income", "recognised as the money is spent on the program"],
                      ["Unspent grants", "instalments received but not yet spent are a liability (grants received in advance)"]]],
        ["Other income and costs", [["Donations", "including the spring appeal in September"],
                                    ["Fundraising event", "September gala: income and costs in the same month"],
                                    ["Grant-funded spending", f"{round(m['grant_wage_share'] * 100)}% wages, the rest program costs"],
                                    ["Income tax", "none: registered charity, income-tax exempt"]]],
        ["Cash and balance sheet", [["Suppliers", "paid the following month"],
                                    ["Unrestricted cash", "cash at bank less unspent grant money"],
                                    ["Cash runway", "unrestricted cash ÷ this month's cash spending"],
                                    ["Reserves target", f"{m['reserves_target_months']} months of spending"],
                                    ["GST", "excluded throughout, for simplicity"]]],
    ]


# =================================================================== checks

def check_sections(rows, name):
    pending, problems = [], []
    for rw in rows:
        if rw["level"] == "heading":
            pending = []
        elif rw["level"] == "detail":
            pending.append(rw)
        elif rw["level"] == "subtotal" and pending:
            for i in range(2):
                if sum(p["values"][i] for p in pending) != rw["values"][i]:
                    problems.append(f"{name}: {rw['label']} {COLUMNS[i]}")
            pending = []
    return problems


def run_checks(org, model, out):
    problems = []
    for key in ("pnl", "bsr", "cfr"):
        problems += check_sections(out[key], f"{org} {key}")
    v = lambda key, label: next(rw["values"] for rw in out[key] if rw["label"] == label)
    pnl_labels = [rw["label"] for rw in out["pnl"]]
    for i, mo in enumerate(PERIODS):
        bs, prev = out["bs"][mo], out["bs"][prev_month(mo)]
        if org == "nfp":
            if v("bsr", "Net assets")[i] != v("bsr", "Accumulated funds")[i]: problems.append(f"nfp balance {mo}")
            if bs["accumulated"] - prev["accumulated"] != out["r"][mo]["surplus"]: problems.append(f"nfp surplus roll {mo}")
            if v("pnl", "Total income")[i] + v("pnl", "Total expenses")[i] != v("pnl", "Surplus for the month")[i]: problems.append("nfp surplus")
            grant_labels = {f"{gr[2]} grant" for gr in model["grants"]}
            grant_lines = sum(rw["values"][i] for rw in out["pnl"] if rw["label"] in grant_labels)
            if grant_lines != sum(out["r"][mo]["gspend"].values()): problems.append(f"nfp grant income {mo}")
            for gr_ in out["grants"]:
                if sum(x["spend"] for x in gr_["monthly"]) != gr_["spent_to_date"]: problems.append(f"nfp grant history {gr_['program']}")
                if sum(gr_["budget_by_month"].values()) != gr_["total"]: problems.append(f"nfp grant budget {gr_['program']}")
            bal = out["grant_bal"](mo)
            if bs["grants_in_advance"] - bs["grants_receivable"] != sum(bal.values()): problems.append(f"nfp grants in advance {mo}")
        else:
            if v("bsr", "Net assets")[i] != v("bsr", "Total equity")[i]: problems.append(f"{org} balance {mo}")
            if bs["retained"] - prev["retained"] != out["r"][mo]["npat"]: problems.append(f"{org} profit roll {mo}")
            for a, b, c in [("Total revenue", "Total cost of sales", "Gross profit"), ("Gross profit", "Total operating expenses", "EBITDA")]:
                if v("pnl", a)[i] + v("pnl", b)[i] != v("pnl", c)[i]: problems.append(f"{org} {c} {mo}")
            if v("pnl", "EBITDA")[i] + v("pnl", "Depreciation")[i] + v("pnl", "Interest")[i] != v("pnl", "Profit before tax")[i]: problems.append(f"{org} PBT")
            tax = next(l for l in pnl_labels if l.startswith("Income tax"))
            if v("pnl", "Profit before tax")[i] + v("pnl", tax)[i] != v("pnl", "Net profit after tax")[i]: problems.append(f"{org} NPAT")
            r = out["r"][mo]
            if org == "trades":
                mj = [j for j in out["jobs"] if j["month"] == mo]
                if sum(j["revenue"] for j in mj) != r["revenue"]: problems.append(f"trades job revenue {mo}")
                if sum(j["materials"] for j in mj) != r["mat"] or sum(j["subcontractors"] for j in mj) != r["sub"]: problems.append(f"trades job costs {mo}")
                if r["jobs_gp"] - (r["techw"] - r["allocated"]) != r["gp"]: problems.append(f"trades job GP to P&L {mo}")
                if bs["debtors"] != unpaid_at(out["jobs"], MONTH_END[mo]): problems.append(f"trades debtors {mo}")
            if org == "services":
                me = [x for x in out["engagements"] if x["month"] == mo]
                if sum(x["revenue"] for x in me) != r["revenue"]: problems.append(f"services engagement revenue {mo}")
                if r["contribution"] - (r["sal"] - r["allocated"]) != r["gp"]: problems.append(f"services engagement GP {mo}")
                if bs["stock"] != sum(r["wip"].values()): problems.append(f"services WIP {mo}")
                if bs["debtors"] != unpaid_at(out["invoices"], MONTH_END[mo]): problems.append(f"services debtors {mo}")
        cf = lambda label: v("cfr", label)[i]
        if cf("Cash at start of month") + cf("Net change in cash") != cf("Cash at end of month"): problems.append(f"{org} cash roll {mo}")
        if cf("Cash at end of month") != v("bsr", "Cash at bank")[i]: problems.append(f"{org} cash ties {mo}")
        if sum(rw["values"][i] for rw in out["cfr"] if rw["label"].startswith("Net cash from")) != cf("Net change in cash"): problems.append(f"{org} cf total {mo}")
        if bs["cash"] < 0: problems.append(f"{org} negative cash {mo}")
    return problems


def build():
    """Run every model and check it. Returns {org: {...}} ready to publish."""
    result, problems = {}, []
    for org, m, fn, fourth, assum in [("trades", TRADES, trades, fourth_trades, trades_assumptions),
                                      ("services", SERVICES, services, fourth_services, services_assumptions),
                                      ("nfp", NFP, nfp, fourth_nfp, nfp_assumptions)]:
        out = fn(m)
        problems += run_checks(org, m, out)
        result[org] = dict(model=m, out=out, fourth=fourth(m, out), assumptions=assum(m, out))
    if problems:
        raise SystemExit("Financial model checks FAILED:\n  " + "\n  ".join(problems))
    return result


if __name__ == "__main__":
    res = build()
    for org, v in res.items():
        print(f"\n=== {org}: {v['model']['long_name']} ===")
        for title, rows in [("P&L", v["out"]["pnl"]), ("Balance sheet", v["out"]["bsr"]), ("Cash flow", v["out"]["cfr"])]:
            print(f"-- {title}")
            for rw in rows:
                vals = "" if rw["values"] is None else "  ".join(f"{x:>10,}" for x in rw["values"])
                print(f"   {rw['level'][:3]:3} {rw['label'][:46]:46} {vals}")
        print("-- fourth", [(k["label"], k["value"], k["sub"]) for k in v["fourth"]["kpis"]])
        print("-- chart", list(zip(v["fourth"]["chart"]["labels"], v["fourth"]["chart"]["values"])))
    print("\nAll checks passed.")
