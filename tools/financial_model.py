#!/usr/bin/env python3
"""
financial_model.py — a small driver-based model for the home-page dashboard.

Three invented sample organisations:
  trades    SME: a field/trade services business (about $2.4M revenue)
  services  SME: a professional services consultancy (about $1.8M revenue)
  nfp       Not-for-profit: a community services charity (about $2.4M income)

For each: a P&L (income and expenditure for the NFP), balance sheet and
cash flow for FY2026 with FY2025 comparatives, plus "the fourth sheet"
(the numbers underneath). EVERY figure is calculated from the ASSUMPTIONS
below, in whole $'000, so every total adds up exactly as shown.

run_checks() proves it before anything is published:
  - every subtotal and total equals the sum of its lines
  - assets = liabilities + equity, at every balance date
  - opening cash + cash flow = closing cash on the balance sheet
  - profit (surplus) for the year = the movement in retained earnings
    (accumulated funds), after dividends
  - the "profit to cash" bridge ends at the change in cash
  - fourth-sheet metrics recalculate from the statements

Used by tools/sample_data.py (which writes the CSVs, dashboard-data.js and
the Excel/PDF exports). Australian financial years end 30 June.
"""

FY = ["FY2026", "FY2025"]          # display order: current, then prior
YEARS = ["FY2025", "FY2026"]       # calculation order
MONTHS = ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun"]


def half_up(x):
    return int(x + 0.5) if x >= 0 else -int(-x + 0.5)


def allocate(total, weights):
    """Split an integer total into integer parts that add back exactly (largest remainder)."""
    raw = [total * w / sum(weights) for w in weights]
    parts = [int(r) for r in raw]
    for i in sorted(range(len(raw)), key=lambda i: raw[i] - parts[i], reverse=True)[: total - sum(parts)]:
        parts[i] += 1
    return parts


# =============================================================== ASSUMPTIONS
# Money in $'000 unless the name says otherwise. Edit here, then run
# python3 tools/sample_data.py to regenerate everything.

TRADES = {
    "name": "SME · trades", "long_name": "Sample Trade Services Pty Ltd",
    "about": "A field/trade services business: maintenance contracts, installations and call-outs. About 14 staff.",
    "opening": {  # balance sheet at 30 June 2024
        "cash": 145, "debtors": 212, "stock": 58, "prepayments": 18, "fixed_assets": 240,
        "creditors": 128, "provisions": 96, "tax_payable": 4, "loan": 230, "share_capital": 10, "retained": 205,
    },
    "lines": ["Maintenance contracts", "Installations", "Call-outs and repairs"],
    "years": {
        "FY2025": {
            "revenue": [660, 1060, 490],
            "materials": [60, 350, 66], "subcontractors": [18, 125, 9], "direct_labour": [310, 280, 196],
            "opex": {"Office and admin wages": 310, "Marketing": 104, "Vehicles and fuel": 110, "Rent and occupancy": 80,
                     "Insurance": 33, "IT and software": 24, "Other overheads": 45},
            "depreciation": 48, "interest": 18,
            "debtor_days": 38, "stock": 62, "prepayments": 20, "creditor_days": 42, "provision_pct": 9,
            "capex": 70, "loan_drawn": 0, "loan_repaid": 60, "dividends": 0,
            "new_customers": 436, "staff_fte": 13,
        },
        "FY2026": {
            "revenue": [720, 1180, 540],
            "materials": [60, 380, 70], "subcontractors": [20, 140, 10], "direct_labour": [330, 300, 210],
            "opex": {"Office and admin wages": 330, "Marketing": 96, "Vehicles and fuel": 118, "Rent and occupancy": 84,
                     "Insurance": 36, "IT and software": 28, "Other overheads": 48},
            "depreciation": 52, "interest": 14,
            "debtor_days": 34, "stock": 66, "prepayments": 22, "creditor_days": 42, "provision_pct": 9,
            "capex": 40, "loan_drawn": 0, "loan_repaid": 60, "dividends": 40,
            "new_customers": 522, "staff_fte": 14,
        },
    },
    "tax_rate": 25,
    # how FY2026 marketing spend and new customers fall across the months (for the monthly chart)
    "monthly_marketing_weights": [9, 9, 8, 8, 8, 7, 9, 8, 8, 8, 7, 7],
    "monthly_customer_weights": [34, 36, 38, 40, 42, 40, 44, 46, 48, 50, 52, 52],
    "cac_target": 200,
}

SERVICES = {
    "name": "SME · professional services", "long_name": "Sample Advisory Pty Ltd",
    "about": "A professional services consultancy: projects, monthly retainers and training. About 12 staff.",
    "opening": {
        "cash": 96, "debtors": 248, "stock": 104, "prepayments": 14, "fixed_assets": 60,
        "creditors": 52, "provisions": 118, "tax_payable": 10, "loan": 40, "share_capital": 20, "retained": 282,
    },
    "lines": ["Projects", "Retainers", "Training"],
    "years": {
        "FY2025": {
            "revenue": [900, 560, 160],
            "materials": [0, 0, 0], "subcontractors": [110, 12, 28], "direct_labour": [450, 275, 60],
            "opex": {"Management and admin wages": 280, "Marketing and business development": 80, "Rent and occupancy": 92,
                     "IT and software": 48, "Professional indemnity insurance": 28, "Travel": 30, "Other overheads": 38},
            "depreciation": 22, "interest": 6,
            "debtor_days": 52, "stock": 98, "prepayments": 15, "creditor_days": 30, "provision_pct": 11,
            "capex": 20, "loan_drawn": 0, "loan_repaid": 20, "dividends": 30,
            "new_customers": 41, "staff_fte": 11.5,
            "billable_fte": 8.5, "available_hours_per_fte": 1600, "billable_hours": 9950,
        },
        "FY2026": {
            "revenue": [980, 620, 200],
            "materials": [0, 0, 0], "subcontractors": [90, 10, 30], "direct_labour": [470, 290, 70],
            "opex": {"Management and admin wages": 290, "Marketing and business development": 72, "Rent and occupancy": 96,
                     "IT and software": 54, "Professional indemnity insurance": 30, "Travel": 26, "Other overheads": 40},
            "depreciation": 24, "interest": 4,
            "debtor_days": 45, "stock": 89, "prepayments": 16, "creditor_days": 30, "provision_pct": 11,
            "capex": 30, "loan_drawn": 0, "loan_repaid": 20, "dividends": 80,
            "new_customers": 48, "staff_fte": 12,
            "billable_fte": 9, "available_hours_per_fte": 1600, "billable_hours": 10800,
        },
    },
    "tax_rate": 25,
    "monthly_billable_weights": [8, 9, 9, 9, 9, 6, 5, 9, 9, 8, 9, 10],
    "monthly_available_weights": [9, 9, 8, 9, 8, 7, 7, 8, 9, 8, 9, 9],
    "utilisation_target": 75,
    "stock_label": "Work in progress (unbilled)",
}

NFP = {
    "name": "Not-for-profit", "long_name": "Sample Community Services Ltd",
    "about": "A community services charity: government-funded programs, donations, events and program fees. About 18 staff. Registered charity, income-tax exempt.",
    "opening": {"cash": 820, "receivables": 64, "prepayments": 22, "fixed_assets": 150,
                "payables": 88, "grants_in_advance": 260, "provisions": 168, "accumulated": 540},
    "years": {
        "FY2025": {
            "income": {"Government grants": 1310, "Donations": 352, "Fundraising events": 188, "Program fees": 300, "Interest": 12},
            "program": {"Program delivery wages": 1120, "Program costs": 240},
            "fundraising": {"Grant writing and reporting": 80, "Event costs": 120, "Donor campaigns": 50},
            "admin": {"Administration wages": 230, "Occupancy": 116, "Other administration": 90},
            "depreciation": 30,
            "receivables": 70, "prepayments": 24, "payables": 92, "grants_in_advance": 300, "provision_pct": 12,
            "capex": 40, "program_hours": 22600, "staff_fte": 17,
        },
        "FY2026": {
            "income": {"Government grants": 1420, "Donations": 380, "Fundraising events": 210, "Program fees": 340, "Interest": 18},
            "program": {"Program delivery wages": 1180, "Program costs": 260},
            "fundraising": {"Grant writing and reporting": 85, "Event costs": 113, "Donor campaigns": 46},
            "admin": {"Administration wages": 220, "Occupancy": 120, "Other administration": 96},
            "depreciation": 34,
            "receivables": 76, "prepayments": 26, "payables": 101, "grants_in_advance": 340, "provision_pct": 12,
            "capex": 60, "program_hours": 23200, "staff_fte": 18,
        },
    },
    "reserves_target_months": 3,
}


# =============================================================== statement helpers

def row(label, level, values, note=None):
    """level: 'heading' (no numbers), 'detail', 'subtotal', 'total', 'key'."""
    return {"label": label, "level": level, "values": values, "note": note}


def by_year(fn):
    return [fn("FY2026"), fn("FY2025")]


# =============================================================== SME model

def sme(model):
    a = model["years"]
    o = model["opening"]
    rate = model["tax_rate"] / 100
    r = {}
    bs = {"FY2024": dict(o)}
    for y in YEARS:
        d = a[y]
        rev = sum(d["revenue"])
        mat, sub, lab = sum(d["materials"]), sum(d["subcontractors"]), sum(d["direct_labour"])
        cos = mat + sub + lab
        gp = rev - cos
        opex = sum(d["opex"].values())
        ebitda = gp - opex
        pbt = ebitda - d["depreciation"] - d["interest"]
        tax = half_up(pbt * rate) if pbt > 0 else 0
        npat = pbt - tax
        wages = lab + sum(v for k, v in d["opex"].items() if "wages" in k.lower())
        purchases = mat + sub + sum(v for k, v in d["opex"].items() if "wages" not in k.lower())
        prev = bs["FY2024" if y == "FY2025" else "FY2025"]
        cur = {
            "debtors": half_up(rev * d["debtor_days"] / 365),
            "stock": d["stock"],
            "prepayments": d["prepayments"],
            "fixed_assets": prev["fixed_assets"] + d["capex"] - d["depreciation"],
            "creditors": half_up(purchases * d["creditor_days"] / 365),
            "provisions": half_up(wages * d["provision_pct"] / 100),
            "tax_payable": tax,
            "loan": prev["loan"] + d["loan_drawn"] - d["loan_repaid"],
            "share_capital": prev["share_capital"],
            "retained": prev["retained"] + npat - d["dividends"],
        }
        # cash flow (direct method)
        wip = model.get("stock_label")  # services: unbilled work is a receipt timing item
        d_debt = cur["debtors"] - prev["debtors"]
        d_stock = cur["stock"] - prev["stock"]
        receipts = rev - d_debt - (d_stock if wip else 0)
        payments = cos + opex + (0 if wip else d_stock) + (cur["prepayments"] - prev["prepayments"]) \
            - (cur["creditors"] - prev["creditors"]) - (cur["provisions"] - prev["provisions"])
        tax_paid = prev["tax_payable"]
        operating = receipts - payments - d["interest"] - tax_paid
        investing = -d["capex"]
        financing = d["loan_drawn"] - d["loan_repaid"] - d["dividends"]
        cur["cash"] = prev["cash"] + operating + investing + financing
        bs[y] = cur
        r[y] = dict(rev=rev, mat=mat, sub=sub, lab=lab, cos=cos, gp=gp, opex=opex, ebitda=ebitda, pbt=pbt, tax=tax,
                    npat=npat, receipts=receipts, payments=payments, tax_paid=tax_paid, operating=operating,
                    investing=investing, financing=financing, wages=wages)

    def ca(y): b = bs[y]; return b["cash"] + b["debtors"] + b["stock"] + b["prepayments"]
    def cl(y): b = bs[y]; return b["creditors"] + b["provisions"] + b["tax_payable"]
    stock_label = model.get("stock_label", "Materials on hand")

    pnl = [row("Revenue", "heading", None)]
    for i, line in enumerate(model["lines"]):
        pnl.append(row(line, "detail", by_year(lambda y: a[y]["revenue"][i])))
    pnl.append(row("Total revenue", "subtotal", by_year(lambda y: r[y]["rev"])))
    pnl.append(row("Cost of sales", "heading", None))
    if any(r[y]["mat"] for y in YEARS):
        pnl.append(row("Materials", "detail", by_year(lambda y: -r[y]["mat"])))
    pnl.append(row("Subcontractors", "detail", by_year(lambda y: -r[y]["sub"])))
    pnl.append(row("Direct labour (incl. super)" if not model.get("stock_label") else "Consultant salaries (incl. super)", "detail", by_year(lambda y: -r[y]["lab"])))
    pnl.append(row("Total cost of sales", "subtotal", by_year(lambda y: -r[y]["cos"])))
    pnl.append(row("Gross profit", "total", by_year(lambda y: r[y]["gp"])))
    pnl.append(row("Operating expenses", "heading", None))
    for k in a["FY2026"]["opex"]:
        pnl.append(row(k, "detail", by_year(lambda y, k=k: -a[y]["opex"][k])))
    pnl.append(row("Total operating expenses", "subtotal", by_year(lambda y: -r[y]["opex"])))
    pnl.append(row("EBITDA", "total", by_year(lambda y: r[y]["ebitda"])))
    pnl.append(row("Depreciation", "subtotal", by_year(lambda y: -a[y]["depreciation"])))
    pnl.append(row("Interest", "subtotal", by_year(lambda y: -a[y]["interest"])))
    pnl.append(row("Profit before tax", "total", by_year(lambda y: r[y]["pbt"])))
    pnl.append(row(f"Income tax ({model['tax_rate']}%)", "subtotal", by_year(lambda y: -r[y]["tax"])))
    pnl.append(row("Net profit after tax", "key", by_year(lambda y: r[y]["npat"])))

    bsr = [row("Current assets", "heading", None),
           row("Cash at bank", "detail", by_year(lambda y: bs[y]["cash"])),
           row("Trade debtors", "detail", by_year(lambda y: bs[y]["debtors"])),
           row(stock_label, "detail", by_year(lambda y: bs[y]["stock"])),
           row("Prepayments", "detail", by_year(lambda y: bs[y]["prepayments"])),
           row("Total current assets", "subtotal", by_year(ca)),
           row("Vehicles and equipment" if not model.get("stock_label") else "Office equipment", "subtotal", by_year(lambda y: bs[y]["fixed_assets"])),
           row("Total assets", "total", by_year(lambda y: ca(y) + bs[y]["fixed_assets"])),
           row("Current liabilities", "heading", None),
           row("Trade creditors", "detail", by_year(lambda y: bs[y]["creditors"])),
           row("Employee leave provisions", "detail", by_year(lambda y: bs[y]["provisions"])),
           row("Income tax payable", "detail", by_year(lambda y: bs[y]["tax_payable"])),
           row("Total current liabilities", "subtotal", by_year(cl)),
           row("Equipment finance", "subtotal", by_year(lambda y: bs[y]["loan"])),
           row("Total liabilities", "total", by_year(lambda y: cl(y) + bs[y]["loan"])),
           row("Net assets", "key", by_year(lambda y: ca(y) + bs[y]["fixed_assets"] - cl(y) - bs[y]["loan"])),
           row("Equity", "heading", None),
           row("Share capital", "detail", by_year(lambda y: bs[y]["share_capital"])),
           row("Retained earnings", "detail", by_year(lambda y: bs[y]["retained"])),
           row("Total equity", "key", by_year(lambda y: bs[y]["share_capital"] + bs[y]["retained"]))]

    prevy = lambda y: "FY2024" if y == "FY2025" else "FY2025"
    cfr = [row("Operating activities", "heading", None),
           row("Receipts from customers", "detail", by_year(lambda y: r[y]["receipts"])),
           row("Payments to suppliers and employees", "detail", by_year(lambda y: -r[y]["payments"])),
           row("Interest paid", "detail", by_year(lambda y: -a[y]["interest"])),
           row("Income tax paid", "detail", by_year(lambda y: -r[y]["tax_paid"])),
           row("Net cash from operating activities", "subtotal", by_year(lambda y: r[y]["operating"])),
           row("Investing activities", "heading", None),
           row("Purchase of vehicles and equipment" if not model.get("stock_label") else "Purchase of equipment", "detail", by_year(lambda y: -a[y]["capex"])),
           row("Net cash from investing activities", "subtotal", by_year(lambda y: r[y]["investing"])),
           row("Financing activities", "heading", None),
           row("Equipment finance repaid", "detail", by_year(lambda y: -a[y]["loan_repaid"])),
           row("Dividends paid", "detail", by_year(lambda y: -a[y]["dividends"])),
           row("Net cash from financing activities", "subtotal", by_year(lambda y: r[y]["financing"])),
           row("Net change in cash", "total", by_year(lambda y: r[y]["operating"] + r[y]["investing"] + r[y]["financing"])),
           row("Cash at 1 July", "subtotal", by_year(lambda y: bs[prevy(y)]["cash"])),
           row("Cash at 30 June", "key", by_year(lambda y: bs[y]["cash"]))]

    # profit to cash bridge (FY2026)
    y, p = "FY2026", "FY2025"
    wc = -(bs[y]["debtors"] - bs[p]["debtors"]) - (bs[y]["stock"] - bs[p]["stock"]) - (bs[y]["prepayments"] - bs[p]["prepayments"]) \
        + (bs[y]["creditors"] - bs[p]["creditors"]) + (bs[y]["provisions"] - bs[p]["provisions"])
    taxt = bs[y]["tax_payable"] - bs[p]["tax_payable"]
    bridge = [["Net profit after tax", r[y]["npat"]], ["Add back depreciation", a[y]["depreciation"]],
              ["Working capital (debtors, stock, creditors)", wc], ["Tax owed but not yet paid", taxt],
              ["Vehicles and equipment bought", -a[y]["capex"]], ["Finance repaid", -a[y]["loan_repaid"]],
              ["Dividends paid", -a[y]["dividends"]]]
    change = bs[y]["cash"] - bs[p]["cash"]
    return dict(r=r, bs=bs, pnl=pnl, bsr=bsr, cfr=cfr, bridge=bridge, change=change)


# =============================================================== NFP model

def nfp(model):
    a = model["years"]
    bs = {"FY2024": dict(model["opening"])}
    r = {}
    for y in YEARS:
        d = a[y]
        prev = bs["FY2024" if y == "FY2025" else "FY2025"]
        income = sum(d["income"].values())
        program, fund, admin = sum(d["program"].values()), sum(d["fundraising"].values()), sum(d["admin"].values())
        expenses = program + fund + admin + d["depreciation"]
        surplus = income - expenses
        wages = sum(v for k, v in {**d["program"], **d["admin"]}.items() if "wages" in k.lower())
        cur = {"receivables": d["receivables"], "prepayments": d["prepayments"],
               "fixed_assets": prev["fixed_assets"] + d["capex"] - d["depreciation"],
               "payables": d["payables"], "grants_in_advance": d["grants_in_advance"],
               "provisions": half_up(wages * d["provision_pct"] / 100),
               "accumulated": prev["accumulated"] + surplus}
        grants_rec = d["income"]["Government grants"] + (cur["grants_in_advance"] - prev["grants_in_advance"]) - (cur["receivables"] - prev["receivables"])
        don_rec = d["income"]["Donations"] + d["income"]["Fundraising events"]
        fees_rec = d["income"]["Program fees"]
        int_rec = d["income"]["Interest"]
        payments = (expenses - d["depreciation"]) + (cur["prepayments"] - prev["prepayments"]) \
            - (cur["payables"] - prev["payables"]) - (cur["provisions"] - prev["provisions"])
        operating = grants_rec + don_rec + fees_rec + int_rec - payments
        investing = -d["capex"]
        cur["cash"] = prev["cash"] + operating + investing
        bs[y] = cur
        r[y] = dict(income=income, program=program, fund=fund, admin=admin, expenses=expenses, surplus=surplus,
                    grants_rec=grants_rec, don_rec=don_rec, fees_rec=fees_rec, int_rec=int_rec, payments=payments,
                    operating=operating, investing=investing, cash_expenses=expenses - d["depreciation"])

    pnl = [row("Income", "heading", None)]
    for k in a["FY2026"]["income"]:
        pnl.append(row(k, "detail", by_year(lambda y, k=k: a[y]["income"][k])))
    pnl.append(row("Total income", "subtotal", by_year(lambda y: r[y]["income"])))
    for head, key, total in [("Programs", "program", "Total program spend"), ("Fundraising", "fundraising", "Total fundraising costs"),
                             ("Administration", "admin", "Total administration")]:
        pnl.append(row(head, "heading", None))
        for k in a["FY2026"][key]:
            pnl.append(row(k, "detail", by_year(lambda y, k=k, key=key: -a[y][key][k])))
        rk = {"program": "program", "fundraising": "fund", "admin": "admin"}[key]
        pnl.append(row(total, "subtotal", by_year(lambda y, rk=rk: -r[y][rk])))
    pnl.append(row("Depreciation", "subtotal", by_year(lambda y: -a[y]["depreciation"])))
    pnl.append(row("Total expenses", "total", by_year(lambda y: -r[y]["expenses"])))
    pnl.append(row("Surplus for the year", "key", by_year(lambda y: r[y]["surplus"]), note="Income-tax exempt charity: no income tax."))

    def ca(y): b = bs[y]; return b["cash"] + b["receivables"] + b["prepayments"]
    def cl(y): b = bs[y]; return b["payables"] + b["grants_in_advance"] + b["provisions"]
    bsr = [row("Current assets", "heading", None),
           row("Cash at bank", "detail", by_year(lambda y: bs[y]["cash"])),
           row("Grants and fees receivable", "detail", by_year(lambda y: bs[y]["receivables"])),
           row("Prepayments", "detail", by_year(lambda y: bs[y]["prepayments"])),
           row("Total current assets", "subtotal", by_year(ca)),
           row("Vehicles and equipment", "subtotal", by_year(lambda y: bs[y]["fixed_assets"])),
           row("Total assets", "total", by_year(lambda y: ca(y) + bs[y]["fixed_assets"])),
           row("Current liabilities", "heading", None),
           row("Payables", "detail", by_year(lambda y: bs[y]["payables"])),
           row("Grants received in advance (unspent)", "detail", by_year(lambda y: bs[y]["grants_in_advance"])),
           row("Employee leave provisions", "detail", by_year(lambda y: bs[y]["provisions"])),
           row("Total liabilities", "total", by_year(cl)),
           row("Net assets", "key", by_year(lambda y: ca(y) + bs[y]["fixed_assets"] - cl(y))),
           row("Equity", "heading", None),
           row("Accumulated funds", "key", by_year(lambda y: bs[y]["accumulated"]))]

    prevy = lambda y: "FY2024" if y == "FY2025" else "FY2025"
    cfr = [row("Operating activities", "heading", None),
           row("Grants received", "detail", by_year(lambda y: r[y]["grants_rec"])),
           row("Donations and fundraising received", "detail", by_year(lambda y: r[y]["don_rec"])),
           row("Program fees received", "detail", by_year(lambda y: r[y]["fees_rec"])),
           row("Interest received", "detail", by_year(lambda y: r[y]["int_rec"])),
           row("Payments to suppliers and employees", "detail", by_year(lambda y: -r[y]["payments"])),
           row("Net cash from operating activities", "subtotal", by_year(lambda y: r[y]["operating"])),
           row("Investing activities", "heading", None),
           row("Purchase of vehicles and equipment", "detail", by_year(lambda y: -a[y]["capex"])),
           row("Net cash from investing activities", "subtotal", by_year(lambda y: r[y]["investing"])),
           row("Net change in cash", "total", by_year(lambda y: r[y]["operating"] + r[y]["investing"])),
           row("Cash at 1 July", "subtotal", by_year(lambda y: bs[prevy(y)]["cash"])),
           row("Cash at 30 June", "key", by_year(lambda y: bs[y]["cash"]))]

    y, p = "FY2026", "FY2025"
    wc = -(bs[y]["receivables"] - bs[p]["receivables"]) - (bs[y]["prepayments"] - bs[p]["prepayments"]) \
        + (bs[y]["payables"] - bs[p]["payables"]) + (bs[y]["provisions"] - bs[p]["provisions"])
    bridge = [["Surplus for the year", r[y]["surplus"]], ["Add back depreciation", a[y]["depreciation"]],
              ["Grants received in advance (unspent)", bs[y]["grants_in_advance"] - bs[p]["grants_in_advance"]],
              ["Working capital (receivables, payables)", wc], ["Vehicles and equipment bought", -a[y]["capex"]]]
    change = bs[y]["cash"] - bs[p]["cash"]
    return dict(r=r, bs=bs, pnl=pnl, bsr=bsr, cfr=cfr, bridge=bridge, change=change)


# =============================================================== the fourth sheet

def pct(n, d, places=1):
    return round(100 * n / d, places)


def fourth_trades(m, out):
    a, r, bs = m["years"], out["r"], out["bs"]
    cac = {y: a[y]["opex"]["Marketing"] * 1000 / a[y]["new_customers"] for y in YEARS}
    gm = {y: pct(r[y]["gp"], r[y]["rev"]) for y in YEARS}
    ddays = {y: half_up(bs[y]["debtors"] * 365 / r[y]["rev"]) for y in YEARS}
    fixed = {y: r[y]["opex"] + a[y]["depreciation"] + a[y]["interest"] for y in YEARS}
    breakeven = {y: fixed[y] / (r[y]["gp"] / r[y]["rev"]) for y in YEARS}
    mk = allocate(a["FY2026"]["opex"]["Marketing"] * 1000, m["monthly_marketing_weights"])
    cu = allocate(a["FY2026"]["new_customers"], m["monthly_customer_weights"])
    lines = [[ln, a["FY2026"]["revenue"][i], a["FY2026"]["revenue"][i] - a["FY2026"]["materials"][i] - a["FY2026"]["subcontractors"][i] - a["FY2026"]["direct_labour"][i]]
             for i, ln in enumerate(m["lines"])]
    return {
        "kpis": [
            {"label": "Cost to win a customer", "value": f"${half_up(cac['FY2026'])}", "sub": f"FY2025: ${half_up(cac['FY2025'])}", "cls": "good", "spine": True},
            {"label": "Gross margin", "value": f"{gm['FY2026']}%", "sub": f"FY2025: {gm['FY2025']}%", "cls": "good"},
            {"label": "Debtor days", "value": str(ddays["FY2026"]), "sub": f"FY2025: {ddays['FY2025']}", "cls": "good"},
            {"label": "Break-even revenue", "value": f"${breakeven['FY2026'] / 1000:.2f}M", "sub": f"{pct(breakeven['FY2026'], r['FY2026']['rev'], 0):.0f}% of revenue", "cls": ""},
        ],
        "chart": {"title": "Cost to win a customer, by month (FY2026)", "labels": MONTHS,
                  "values": [round(mk[i] / cu[i], 2) for i in range(12)], "target": m["cac_target"], "format": "money0",
                  "what": "cost to win a customer"},
        "table": {"title": "Profit by service line, FY2026 ($'000)", "head": ["Service line", "Revenue", "Gross profit", "Margin"],
                  "rows": [[ln, rv, g, f"{pct(g, rv)}%"] for ln, rv, g in lines],
                  "total": ["Total", r["FY2026"]["rev"], r["FY2026"]["gp"], f"{gm['FY2026']}%"]},
        "monthly": {"marketing_aud": mk, "new_customers": cu},
        "facts": dict(cac=cac, gm=gm, ddays=ddays, breakeven=breakeven, lines=lines),
    }


def fourth_services(m, out):
    a, r, bs = m["years"], out["r"], out["bs"]
    util = {y: pct(a[y]["billable_hours"], a[y]["billable_fte"] * a[y]["available_hours_per_fte"]) for y in YEARS}
    rate = {y: r[y]["rev"] * 1000 / a[y]["billable_hours"] for y in YEARS}
    lockup = {y: half_up((bs[y]["debtors"] + bs[y]["stock"]) * 365 / r[y]["rev"]) for y in YEARS}
    cac = {y: a[y]["opex"]["Marketing and business development"] * 1000 / a[y]["new_customers"] for y in YEARS}
    bh = allocate(a["FY2026"]["billable_hours"], m["monthly_billable_weights"])
    av = allocate(int(a["FY2026"]["billable_fte"] * a["FY2026"]["available_hours_per_fte"]), m["monthly_available_weights"])
    lines = [[ln, a["FY2026"]["revenue"][i], a["FY2026"]["revenue"][i] - a["FY2026"]["subcontractors"][i] - a["FY2026"]["direct_labour"][i]]
             for i, ln in enumerate(m["lines"])]
    return {
        "kpis": [
            {"label": "Utilisation", "value": f"{util['FY2026']:.0f}%", "sub": f"FY2025: {util['FY2025']:.0f}%", "cls": "good", "spine": True},
            {"label": "Revenue per billable hour", "value": f"${half_up(rate['FY2026'])}", "sub": f"FY2025: ${half_up(rate['FY2025'])}", "cls": "good"},
            {"label": "Lock-up days (debtors + WIP)", "value": str(lockup["FY2026"]), "sub": f"FY2025: {lockup['FY2025']}", "cls": "good"},
            {"label": "Cost to win a client", "value": f"${half_up(cac['FY2026']):,}", "sub": f"FY2025: ${half_up(cac['FY2025']):,}", "cls": "good"},
        ],
        "chart": {"title": "Utilisation by month (FY2026)", "labels": MONTHS,
                  "values": [round(100 * bh[i] / av[i], 1) for i in range(12)], "target": m["utilisation_target"], "format": "pct0",
                  "what": "utilisation"},
        "table": {"title": "Profit by service line, FY2026 ($'000)", "head": ["Service line", "Revenue", "Gross profit", "Margin"],
                  "rows": [[ln, rv, g, f"{pct(g, rv)}%"] for ln, rv, g in lines],
                  "total": ["Total", r["FY2026"]["rev"], r["FY2026"]["gp"], f"{pct(r['FY2026']['gp'], r['FY2026']['rev'])}%"]},
        "monthly": {"billable_hours": bh, "available_hours": av},
        "facts": dict(util=util, rate=rate, lockup=lockup, cac=cac, lines=lines),
    }


def fourth_nfp(m, out):
    a, r, bs = m["years"], out["r"], out["bs"]
    raised = {y: a[y]["income"]["Government grants"] + a[y]["income"]["Donations"] + a[y]["income"]["Fundraising events"] for y in YEARS}
    ctr = {y: r[y]["fund"] / raised[y] for y in YEARS}
    cph = {y: r[y]["program"] * 1000 / a[y]["program_hours"] for y in YEARS}
    unrestricted = {y: bs[y]["cash"] - bs[y]["grants_in_advance"] for y in YEARS}
    runway = {y: unrestricted[y] / (r[y]["cash_expenses"] / 12) for y in YEARS}
    d = a["FY2026"]
    sources = [["Government grants", d["income"]["Government grants"], d["fundraising"]["Grant writing and reporting"]],
               ["Donations", d["income"]["Donations"], d["fundraising"]["Donor campaigns"]],
               ["Fundraising events", d["income"]["Fundraising events"], d["fundraising"]["Event costs"]]]
    shares = allocate(100, [s[1] for s in sources])
    spend = [r["FY2026"]["program"], r["FY2026"]["fund"], sum(v for k, v in d["admin"].items() if k != "Occupancy"),
             d["admin"]["Occupancy"] + d["depreciation"]]
    cents = allocate(100, spend)
    return {
        "kpis": [
            {"label": "Cost to raise a dollar", "value": f"${ctr['FY2026']:.2f}", "sub": f"FY2025: ${ctr['FY2025']:.2f}", "cls": "good", "spine": True},
            {"label": "Spent on programs", "value": f"{cents[0]}c in $1", "sub": "of every dollar spent", "cls": ""},
            {"label": "Cost per program hour", "value": f"${half_up(cph['FY2026'])}", "sub": f"FY2025: ${half_up(cph['FY2025'])}", "cls": ""},
            {"label": "Cash runway (unrestricted)", "value": f"{runway['FY2026']:.1f} months", "sub": f"Target {m['reserves_target_months']} months", "cls": "good"},
        ],
        "chart": {"title": "Where each dollar goes (FY2026, cents)", "labels": ["Programs", "Fundraising", "Admin", "Occupancy"],
                  "values": cents, "target": None, "format": "cents_int", "what": "spending per dollar"},
        "table": {"title": "Funding sources, FY2026 ($'000)", "head": ["Source", "Raised", "Share", "Cost per $1"],
                  "rows": [[s[0], s[1], f"{shares[i]}%", f"${s[2] / s[1]:.2f}"] for i, s in enumerate(sources)],
                  "total": ["Total", raised["FY2026"], "100%", f"${ctr['FY2026']:.2f}"]},
        "monthly": {},
        "facts": dict(ctr=ctr, cph=cph, runway=runway, unrestricted=unrestricted, cents=cents, shares=shares, sources=sources),
    }


# =============================================================== assumptions (shown in the pop-up)

def sme_assumptions(m):
    a = m["years"]
    y, p = a["FY2026"], a["FY2025"]
    def both(k, fmt="{}"): return f"{fmt.format(y[k])} (FY2025: {fmt.format(p[k])})"
    groups = [
        ["The organisation", [["What it is", m["about"]], ["Staff (full-time equivalent)", both("staff_fte")],
                              ["Financial year", "1 July to 30 June; FY2026 = year to 30 June 2026"]]],
        ["Revenue", [[ln, f"${y['revenue'][i]:,}k (FY2025: ${p['revenue'][i]:,}k)"] for i, ln in enumerate(m["lines"])]
                    + [["New customers won", both("new_customers")]]],
        ["Costs", [["Direct costs by service line", "materials, subcontractors and labour set per line (see the P&L)"],
                   ["Overheads", "as listed in the P&L, set directly"],
                   ["Income tax", f"{m['tax_rate']}% of profit before tax (base rate entity); paid the following year"],
                   ["Superannuation", "included in wages"]]],
        ["Cash and balance sheet", [["Debtor days", both("debtor_days")],
                                    ["Creditor days", f"{y['creditor_days']} days of non-wage costs"],
                                    [m.get("stock_label", "Materials on hand"), f"${y['stock']}k at 30 June (FY2025: ${p['stock']}k)"],
                                    ["Employee leave provisions", f"{y['provision_pct']}% of wages"],
                                    ["Equipment bought", f"${y['capex']}k (FY2025: ${p['capex']}k)"],
                                    ["Equipment finance repaid", f"${y['loan_repaid']}k a year"],
                                    ["Dividends paid", f"${y['dividends']}k (FY2025: ${p['dividends']}k)"],
                                    ["GST", "excluded throughout, for simplicity"]]],
    ]
    if "billable_hours" in y:
        groups.append(["Utilisation", [["Billable staff", both("billable_fte")], ["Available hours per person", f"{y['available_hours_per_fte']:,} a year"],
                                       ["Billable hours", f"{y['billable_hours']:,} (FY2025: {p['billable_hours']:,})"]]])
    return groups


def nfp_assumptions(m):
    y, p = m["years"]["FY2026"], m["years"]["FY2025"]
    return [
        ["The organisation", [["What it is", m["about"]], ["Staff (full-time equivalent)", f"{y['staff_fte']} (FY2025: {p['staff_fte']})"],
                              ["Financial year", "1 July to 30 June; FY2026 = year to 30 June 2026"]]],
        ["Income", [[k, f"${v:,}k (FY2025: ${p['income'][k]:,}k)"] for k, v in y["income"].items()]],
        ["Spending", [["Program, fundraising and admin costs", "set directly (see Income and expenditure)"],
                      ["Program hours delivered", f"{y['program_hours']:,} (FY2025: {p['program_hours']:,})"],
                      ["Income tax", "none: registered charity, income-tax exempt"]]],
        ["Cash and balance sheet", [["Grants received in advance (unspent)", f"${y['grants_in_advance']}k at 30 June (FY2025: ${p['grants_in_advance']}k)"],
                                    ["Receivables / prepayments / payables", f"${y['receivables']}k / ${y['prepayments']}k / ${y['payables']}k at 30 June"],
                                    ["Employee leave provisions", f"{y['provision_pct']}% of wages"],
                                    ["Equipment bought", f"${y['capex']}k (FY2025: ${p['capex']}k)"],
                                    ["Unrestricted cash", "cash at bank less grants received in advance"],
                                    ["Reserves target", f"{m['reserves_target_months']} months of spending"],
                                    ["GST", "excluded throughout, for simplicity"]]],
    ]


# =============================================================== checks

def check_sections(rows, name):
    """Each subtotal/total must equal the sum of the lines above it in its block."""
    pending, problems = [], []
    for rw in rows:
        if rw["level"] == "heading":
            pending = []
        elif rw["level"] == "detail":
            pending.append(rw)
        elif rw["level"] == "subtotal" and pending:
            for i in range(2):
                if sum(p["values"][i] for p in pending) != rw["values"][i]:
                    problems.append(f"{name}: {rw['label']} {FY[i]}")
            pending = []
    return problems


def run_checks(org, model, out):
    bs, r, problems = out["bs"], out["r"], []
    problems += check_sections(out["pnl"], f"{org} P&L") + check_sections(out["bsr"], f"{org} BS") + check_sections(out["cfr"], f"{org} CF")
    rows = {rw["label"]: rw["values"] for rw in out["bsr"] if rw["values"]}
    cf = {rw["label"]: rw["values"] for rw in out["cfr"] if rw["values"]}
    pnl = {rw["label"]: rw["values"] for rw in out["pnl"] if rw["values"]}
    for i in range(2):
        if org == "nfp":
            if rows["Net assets"][i] != rows["Accumulated funds"][i]: problems.append(f"{org} balance {FY[i]}")
            if rows["Total current assets"][i] + rows["Vehicles and equipment"][i] != rows["Total assets"][i]: problems.append("nfp total assets")
            if rows["Total assets"][i] - rows["Total liabilities"][i] != rows["Net assets"][i]: problems.append("nfp net assets")
            if pnl["Total income"][i] + pnl["Total expenses"][i] != pnl["Surplus for the year"][i]: problems.append("nfp surplus")
            if (pnl["Total program spend"][i] + pnl["Total fundraising costs"][i] + pnl["Total administration"][i] + pnl["Depreciation"][i]) != pnl["Total expenses"][i]: problems.append("nfp expenses")
        else:
            if rows["Net assets"][i] != rows["Total equity"][i]: problems.append(f"{org} balance {FY[i]}")
            fa = [k for k in rows if k in ("Vehicles and equipment", "Office equipment")][0]
            if rows["Total current assets"][i] + rows[fa][i] != rows["Total assets"][i]: problems.append(f"{org} total assets")
            if rows["Total current liabilities"][i] + rows["Equipment finance"][i] != rows["Total liabilities"][i]: problems.append(f"{org} total liabilities")
            if rows["Total assets"][i] - rows["Total liabilities"][i] != rows["Net assets"][i]: problems.append(f"{org} net assets")
            chain = [("Total revenue", "Total cost of sales", "Gross profit"), ("Gross profit", "Total operating expenses", "EBITDA")]
            for x, yv, z in chain:
                if pnl[x][i] + pnl[yv][i] != pnl[z][i]: problems.append(f"{org} {z}")
            if pnl["EBITDA"][i] + pnl["Depreciation"][i] + pnl["Interest"][i] != pnl["Profit before tax"][i]: problems.append(f"{org} PBT")
            tax_label = [k for k in pnl if k.startswith("Income tax")][0]
            if pnl["Profit before tax"][i] + pnl[tax_label][i] != pnl["Net profit after tax"][i]: problems.append(f"{org} NPAT")
        # cash flow ties to the balance sheet
        if cf["Cash at 1 July"][i] + cf["Net change in cash"][i] != cf["Cash at 30 June"][i]: problems.append(f"{org} cash roll {FY[i]}")
        if cf["Cash at 30 June"][i] != rows["Cash at bank"][i]: problems.append(f"{org} cash ties to BS {FY[i]}")
        subs = [k for k in cf if k.startswith("Net cash from")]
        if sum(cf[k][i] for k in subs) != cf["Net change in cash"][i]: problems.append(f"{org} CF total")
    # profit ties to equity movement
    for y in YEARS:
        prev = "FY2024" if y == "FY2025" else "FY2025"
        if org == "nfp":
            if bs[y]["accumulated"] - bs[prev]["accumulated"] != r[y]["surplus"]: problems.append(f"nfp surplus to funds {y}")
        else:
            if bs[y]["retained"] - bs[prev]["retained"] != r[y]["npat"] - model["years"][y]["dividends"]: problems.append(f"{org} profit to RE {y}")
    # bridge ends at the change in cash
    if sum(v for _, v in out["bridge"]) != out["change"]: problems.append(f"{org} bridge")
    # cash never negative (it's a sample, keep it sensible)
    if min(bs[y]["cash"] for y in YEARS) < 0: problems.append(f"{org} negative cash")
    return problems


def build():
    """Run every model and check it. Returns {org: {...}} ready to publish."""
    result, problems = {}, []
    for org, m, fn, fourth, assum in [("trades", TRADES, sme, fourth_trades, sme_assumptions),
                                      ("services", SERVICES, sme, fourth_services, sme_assumptions),
                                      ("nfp", NFP, nfp, fourth_nfp, nfp_assumptions)]:
        out = fn(m)
        problems += run_checks(org, m, out)
        f4 = fourth(m, out)
        # fourth-sheet tables add up too
        t = f4["table"]
        for col in (1, 2):
            if isinstance(t["total"][col], int) and sum(rw[col] for rw in t["rows"]) != t["total"][col]:
                problems.append(f"{org} fourth-sheet table column {col}")
        if f4["chart"]["format"] == "cents_int" and sum(f4["chart"]["values"]) != 100:
            problems.append(f"{org} where-each-dollar-goes")
        result[org] = dict(model=m, out=out, fourth=f4, assumptions=assum(m))
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
                vals = "" if rw["values"] is None else "  ".join(f"{x:>7,}" for x in rw["values"])
                print(f"   {rw['level'][:3]:3} {rw['label'][:44]:44} {vals}")
        print("-- bridge", v["out"]["bridge"], "change", v["out"]["change"])
        print("-- fourth", [(k["label"], k["value"], k["sub"]) for k in v["fourth"]["kpis"]])
        print("-- chart", v["fourth"]["chart"]["values"])
    print("\nAll checks passed.")
