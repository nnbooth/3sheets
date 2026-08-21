import pandas as pd
import numpy as np
import random
import string
from datetime import datetime, timedelta
from pathlib import Path

# Set seed for reproducible audit targets
np.random.seed(42)
random.seed(42)

num_pos = 3500
current_date_anchor = datetime(2026, 8, 1)

# --- 1. REAL 2026 FX RATES (AUD to USD) ---
fx_history = {
    '2026-02-01': 0.6945, '2026-02-09': 0.7083, '2026-03-25': 0.6942,
    '2026-04-16': 0.7158, '2026-05-13': 0.7259, '2026-06-20': 0.7006,
    '2026-07-29': 0.6959, '2026-08-01': 0.7017
}

def get_daily_rate(date_str):
    """Return FX rate for date, falling back to most recent prior rate."""
    if date_str in fx_history:
        return fx_history[date_str]

    target_date = datetime.strptime(date_str, "%Y-%m-%d")

    # Find all historical dates <= target date
    prior_dates = [
        (datetime.strptime(d, "%Y-%m-%d"), rate)
        for d, rate in fx_history.items()
        if datetime.strptime(d, "%Y-%m-%d") <= target_date
    ]

    if prior_dates:
        prior_dates.sort(key=lambda x: x[0], reverse=True)
        return prior_dates[0][1]

    # If nothing earlier exists, return earliest available
    earliest_date = min(
        (datetime.strptime(d, "%Y-%m-%d"), rate)
        for d, rate in fx_history.items()
    )
    return earliest_date[1]

# --- 2. SKU MASTER ---
sku_count = 250
sku_categories = [
    "MRO", "Packaging", "Electrical", "Safety", "IT", "Office", "Mechanical"
]

def make_sku_description(category):
    prefixes = {
        "MRO": ["Bearing", "Coupling", "Seal", "Lubricant"],
        "Packaging": ["Carton", "Shrink Wrap", "Label Roll", "Pallet Film"],
        "Electrical": ["Relay", "Cable", "Switch", "Connector"],
        "Safety": ["Glove", "Helmet", "Barrier", "Signage"],
        "IT": ["Dock", "Monitor Arm", "Keyboard", "Cable Adapter"],
        "Office": ["Paper", "Toner", "Chair Mat", "Notebook"],
        "Mechanical": ["Valve", "Gasket", "Fastener Kit", "Drive Belt"]
    }
    return f"{random.choice(prefixes[category])} - {category}"

sku_rows = []
for i in range(1, sku_count + 1):
    category = random.choice(sku_categories)
    sku_rows.append([
        f"SKU-{i:03d}",
        make_sku_description(category),
        category,
        round(random.uniform(8.0, 1200.0), 2),
        random.randint(5, 20)
    ])

# Catalog SKUs only - this is what section 4 samples from for genuine
# (non-memo) PO lines. Keep the placeholder row (below) out of this pool so
# it can never be drawn as if it were a real catalog item.
df_sku_catalog = pd.DataFrame(sku_rows, columns=[
    "SKU_ID", "SKU_Description", "Category", "Typical_Unit_Price", "Days_To_Deliver"
])

# sku_master.csv output = catalog + one placeholder row for memo/ad-hoc PO
# lines (SKU_ID == "GENERAL", see section 4). Lets SKU_ID carry a real
# foreign key to sku_master instead of being unenforceable for the ~8% of PO
# lines that are memo entries with no catalog SKU. Days_To_Deliver on the
# placeholder is a fixed default (not random) since there's no real catalog
# item to base a lead time on.
df_sku = pd.concat([df_sku_catalog, pd.DataFrame([{
    "SKU_ID": "GENERAL",
    "SKU_Description": "Ad hoc / non-catalog item (memo line placeholder)",
    "Category": "General",
    "Typical_Unit_Price": 0.0,
    "Days_To_Deliver": 14
}])], ignore_index=True)

# SKU_ID -> agreed/standard lead time (days), used below to compute each PO
# line's Expected_Delivery_Date. This is the "promised" delivery date that
# actual receipts get measured against for on-time performance (DIFOT).
sku_lead_time = dict(zip(df_sku["SKU_ID"], df_sku["Days_To_Deliver"]))

# --- 3. VENDOR MASTER (with duplicate ABN setups) ---
def generate_abn():
    return ''.join(str(random.randint(0, 9)) for _ in range(11))

base_vendor_names = [
    "Apex Industrial", "SteelWorks AU", "Global Logistics", "Vertex Manufacturing",
    "Office Depot AU", "TechCorp International", "Coastal Supplies", "Nexus Components",
    "Metro Wholesale", "Southern Plant Services", "Prime Industrial", "Pacific Traders",
    "Clearwater Safety", "ForgeLine", "Harbour Tools", "BluePeak Distribution",
    "Summit Engineering", "RapidProcure", "Alpha Trade Hub", "IronBridge"
]

base_vendor_count = 24
duplicate_vendor_count = 6
currency_pool = ['AUD'] * 15 + ['USD'] * 6 + ['EUR'] * 3

# Non-AUD vendors are assumed not GST-registered; country is informational for AP review
eur_countries = ['Germany', 'France', 'Netherlands', 'Italy']

def currency_to_country(currency):
    if currency == 'AUD':
        return 'Australia'
    if currency == 'USD':
        return 'United States'
    return random.choice(eur_countries)

vendor_rows = []
base_abns = []

for i in range(base_vendor_count):
    vendor_id = f"VEND-{i + 1:03d}"
    vendor_name = base_vendor_names[i % len(base_vendor_names)]
    abn = generate_abn()
    base_abns.append(abn)
    currency = currency_pool[i % len(currency_pool)]
    vendor_rows.append([
        vendor_id,
        vendor_name,
        abn,
        currency,
        currency_to_country(currency),
        currency == 'AUD'
    ])

for i in range(duplicate_vendor_count):
    source_abn = random.choice(base_abns)
    vendor_id = f"VEND-{base_vendor_count + i + 1:03d}"
    currency = random.choice(['AUD', 'USD'])
    vendor_rows.append([
        vendor_id,
        f"{base_vendor_names[(i + 3) % len(base_vendor_names)]} Pty Ltd",
        source_abn,
        currency,
        currency_to_country(currency),
        currency == 'AUD'
    ])

df_vendor = pd.DataFrame(vendor_rows, columns=[
    'Vendor_ID', 'Vendor_Name', 'ABN', 'System_Currency',
    'Country', 'GST_Registered'
])

# --- 3b. VENDOR BANK ACCOUNT MASTER ---
# Bank details live here, not on vendor_master, specifically so a vendor can
# have more than one over time (Effective_Start/End_Date). That's what makes
# a bank-account-change fraud pattern detectable at all: you compare a
# payment's date against which account was genuinely valid *then*, not just
# whatever's on file "now".
bank_account_counter = 1000


def _next_bank_account():
    global bank_account_counter
    bank_account_counter += 1
    return f"ACC-APPROVED-{bank_account_counter}"


def _fraud_bank_account():
    return f"ACC-DIVERTED-{random.randint(10000, 99999)}"


bank_account_rows = []
bank_account_history = {}  # Vendor_ID -> [(start_date_str, end_date_str_or_None, account), ...]

for vendor_id in df_vendor['Vendor_ID']:
    first_account = _next_bank_account()
    changes_account = random.random() < 0.15

    if not changes_account:
        bank_account_rows.append([vendor_id, first_account, '2025-06-01', None])
        bank_account_history[vendor_id] = [('2025-06-01', None, first_account)]
    else:
        change_date = datetime(2026, 2, 1) + timedelta(days=random.randint(30, 150))
        change_date_str = change_date.strftime('%Y-%m-%d')
        end_of_first = (change_date - timedelta(days=1)).strftime('%Y-%m-%d')
        second_account = _next_bank_account()
        bank_account_rows.append([vendor_id, first_account, '2025-06-01', end_of_first])
        bank_account_rows.append([vendor_id, second_account, change_date_str, None])
        bank_account_history[vendor_id] = [
            ('2025-06-01', end_of_first, first_account),
            (change_date_str, None, second_account),
        ]

df_bank_accounts = pd.DataFrame(bank_account_rows, columns=[
    'Vendor_ID', 'Bank_Account', 'Effective_Start_Date', 'Effective_End_Date'
])


def _account_valid_on(vendor_id, as_of_date_str):
    """The bank account genuinely on file for this vendor on this date."""
    for start, end, acct in bank_account_history.get(vendor_id, []):
        if start <= as_of_date_str and (end is None or as_of_date_str <= end):
            return acct
    return bank_account_history[vendor_id][-1][2]


def _superseded_account(vendor_id):
    """An account that WAS valid for this vendor once, but no longer is -
    None if the vendor never changed accounts."""
    history = bank_account_history.get(vendor_id, [])
    old = [acct for start, end, acct in history if end is not None]
    return random.choice(old) if old else None

# Consistent-ish but random invoice number style per vendor, unrelated to PO numbering
vendor_invoice_style = {}
for v in df_vendor['Vendor_ID']:
    vendor_invoice_style[v] = {
        'style': random.randint(0, 4),
        'tag': ''.join(random.choices(string.ascii_uppercase, k=3)),
        'seq': random.randint(100, 9000)
    }

def next_invoice_number(vendor_id):
    info = vendor_invoice_style[vendor_id]
    info['seq'] += random.randint(1, 4)
    n = info['seq']
    tag = info['tag']
    if info['style'] == 0:
        return f"INV{n:06d}"
    if info['style'] == 1:
        return f"{tag}-{n:05d}"
    if info['style'] == 2:
        return f"SI/{n:04d}/26"
    if info['style'] == 3:
        return f"{n:07d}"
    return f"IN-{n:05d}-{tag}"

# --- 4. PO / RECEIPT ENGINE ---
po_lines = []
receipt_rows = []
# Per PO line: ordered list of receipt events, each tracking how much of that
# receipt hasn't yet been applied (matched) to an invoice. Consumed in
# section 5 to build genuine goods-receipt-to-invoice matches, instead of a
# random label standing in for a matching process that never happened.
line_receipts = {}
pending_invoice_lines = []  # candidate detail lines, grouped into invoices in section 5
po_line_counter = 10000

memo_descriptions = [
    "Ad hoc maintenance items",
    "Urgent workshop consumables",
    "General project sundries",
    "Miscellaneous warehouse supplies",
    "Emergency plant materials"
]

for po_idx in range(1, num_pos + 1):
    po_id = f"PO-2026-{po_idx:04d}"
    v_row = df_vendor.sample(1).iloc[0]
    gst_registered = bool(v_row['GST_Registered'])

    po_date = datetime(2026, 2, 1) + timedelta(days=random.randint(0, 175))
    date_str = po_date.strftime('%Y-%m-%d')

    for _ in range(random.randint(1, 3)):
        po_line_id = f"POL-{po_line_counter}"
        po_line_counter += 1

        memo_flag = random.random() < 0.08
        if memo_flag:
            sku_id = "GENERAL"
            line_description = random.choice(memo_descriptions)
            base_unit_price = round(random.uniform(50.0, 5000.0), 2)
        else:
            sku_row = df_sku_catalog.sample(1).iloc[0]
            sku_id = sku_row['SKU_ID']
            line_description = sku_row['SKU_Description']
            base_unit_price = round(
                float(sku_row['Typical_Unit_Price']) * random.uniform(0.85, 1.25),
                2
            )

        qty = random.randint(1, 50)

        # Promised delivery date, from the SKU's agreed lead time - the DIFOT
        # "on time" benchmark actual receipts get measured against.
        expected_delivery_date = (po_date + timedelta(days=int(sku_lead_time[sku_id]))).strftime('%Y-%m-%d')

        # --- GST ERROR LOGIC (only relevant for GST-registered / AUD vendors) ---
        if gst_registered:
            gst_error = random.random() < 0.10
            po_price = round(base_unit_price / 1.1, 2) if gst_error else base_unit_price
            po_gst_type = "Inclusive" if gst_error else "Exclusive"
        else:
            po_price = base_unit_price
            po_gst_type = "Not Registered"

        # --- FX ERROR LOGIC ---
        daily_rate = get_daily_rate(date_str)

        # Catastrophic manual FX entry error
        if date_str in ['2026-02-09', '2026-05-13'] and random.random() < 0.5:
            daily_rate = 0.85

        po_lines.append([
            po_line_id,
            po_id,
            date_str,
            v_row['Vendor_ID'],
            sku_id,
            line_description,
            memo_flag,
            qty,
            po_price,
            v_row['System_Currency'],
            po_gst_type,
            daily_rate,
            expected_delivery_date
        ])

        # --- RECEIPT LOGIC ---
        # A line can now receive across one or two genuinely separate events
        # (goods arriving on different days) - the real-world case the model
        # previously had no way to represent, since only one goods_receipts
        # row was ever created per PO line.
        receipt_state_roll = random.random()
        line_receipts[po_line_id] = []

        def _log_receipt(seq, rcv_qty, rcv_date):
            receipt_id = f"GR-{po_line_id}-{seq}"
            receipt_rows.append([receipt_id, po_line_id, rcv_date.strftime('%Y-%m-%d'), rcv_qty])
            line_receipts[po_line_id].append({
                'Receipt_ID': receipt_id, 'Qty_Available': rcv_qty, 'Receipt_Date': rcv_date
            })

        if receipt_state_roll < 0.12:
            pass  # never received - line stays fully open
        elif receipt_state_roll < 0.30:
            partial_qty = random.randint(1, max(1, qty - 1))
            _log_receipt(1, partial_qty, po_date + timedelta(days=random.randint(5, 20)))
        elif receipt_state_roll < 0.75:
            _log_receipt(1, qty, po_date + timedelta(days=random.randint(5, 20)))
        else:
            first_qty = max(1, round(qty * random.uniform(0.3, 0.7)))
            second_qty = max(1, qty - first_qty)
            first_date = po_date + timedelta(days=random.randint(5, 15))
            second_date = first_date + timedelta(days=random.randint(5, 15))
            _log_receipt(1, first_qty, first_date)
            _log_receipt(2, second_qty, second_date)

        total_available = sum(r['Qty_Available'] for r in line_receipts[po_line_id])
        has_two_receipts = len(line_receipts[po_line_id]) == 2

        def _apply_receipts(target_qty):
            """Consume up to target_qty from this line's receipts, oldest
            first. Returns the (receipt, qty_applied) matches actually made -
            short of target_qty if not enough was ever received. This *is*
            the matching process; NO_RECEIPT_INVOICE / QTY_OVER_RECEIVED are
            now facts you can derive from its output, not labels."""
            applications = []
            remaining = target_qty
            for r in line_receipts[po_line_id]:
                if remaining <= 0:
                    break
                take = min(r['Qty_Available'], remaining)
                if take > 0:
                    applications.append({'Receipt_ID': r['Receipt_ID'], 'Qty_Applied': take})
                    r['Qty_Available'] -= take
                    remaining -= take
            return applications

        def _price_for(error_type):
            p = po_price
            if random.random() < 0.05:
                p = round(po_price * 1.10, 2)
            if error_type == "PRICE_VARIANCE":
                p = round(po_price * random.uniform(1.08, 1.25), 2)
            return p

        # --- INVOICE CANDIDATE LOGIC (grouping happens in section 5) ---
        if po_date + timedelta(days=12) < current_date_anchor:
            error_roll = random.random()
            inv_error_type = "NONE"

            # Each error type is only selectable when the receipt state
            # actually supports it - e.g. NO_RECEIPT_INVOICE only when
            # nothing has arrived, BACKORDER_SPLIT only when goods genuinely
            # arrived in two batches. Otherwise it falls through to NONE.
            if error_roll < 0.06 and total_available == 0:
                inv_error_type = "NO_RECEIPT_INVOICE"
            elif error_roll < 0.11:
                inv_error_type = "QTY_OVER_RECEIVED"
            elif error_roll < 0.16:
                inv_error_type = "PRICE_VARIANCE"
            elif error_roll < 0.19:
                inv_error_type = "CURRENCY_MISMATCH"
            elif error_roll < 0.22:
                inv_error_type = "DUPLICATE_INVOICE"
            elif error_roll < 0.26:
                inv_error_type = "OVER_PO_LIMIT"
            elif error_roll < 0.32 and has_two_receipts:
                inv_error_type = "BACKORDER_SPLIT"

            inv_curr = v_row['System_Currency']
            if inv_error_type == "CURRENCY_MISMATCH":
                if inv_curr == 'AUD':
                    inv_curr = random.choice(['USD', 'EUR'])
                elif inv_curr == 'USD':
                    inv_curr = 'AUD'
                else:
                    inv_curr = 'AUD'

            if inv_error_type == "BACKORDER_SPLIT":
                # Vendor invoices each physical batch separately, as it
                # arrives - two real invoice candidates, each matched to its
                # own receipt event.
                for r in line_receipts[po_line_id]:
                    apps = _apply_receipts(r['Qty_Available'])
                    inv_qty = sum(a['Qty_Applied'] for a in apps)
                    if inv_qty <= 0:
                        continue
                    inv_date = (r['Receipt_Date'] + timedelta(days=random.randint(3, 10))).strftime('%Y-%m-%d')
                    pending_invoice_lines.append({
                        'Vendor_ID': v_row['Vendor_ID'], 'PO_ID': po_id, 'Line_ID': po_line_id,
                        'Inv_Date': inv_date, 'Qty_Inv': inv_qty, 'Inv_Price': _price_for(inv_error_type),
                        'Inv_Currency': inv_curr, 'Invoice_Error_Type': inv_error_type,
                        'Applications': apps
                    })
                continue

            if inv_error_type == "NO_RECEIPT_INVOICE":
                invoice_qty = qty
                applications = []
            elif inv_error_type == "QTY_OVER_RECEIVED":
                invoice_qty = total_available + random.randint(1, 4)
                applications = _apply_receipts(total_available)
            elif inv_error_type == "OVER_PO_LIMIT":
                # Vendor bills beyond what was ever ordered on the line - a genuine matching exception
                invoice_qty = qty + random.randint(1, 10)
                applications = _apply_receipts(total_available)
            else:
                invoice_qty = total_available
                applications = _apply_receipts(total_available)

            if invoice_qty > 0:
                inv_date = (po_date + timedelta(days=12)).strftime('%Y-%m-%d')
                pending_invoice_lines.append({
                    'Vendor_ID': v_row['Vendor_ID'],
                    'PO_ID': po_id,
                    'Line_ID': po_line_id,
                    'Inv_Date': inv_date,
                    'Qty_Inv': invoice_qty,
                    'Inv_Price': _price_for(inv_error_type),
                    'Inv_Currency': inv_curr,
                    'Invoice_Error_Type': inv_error_type,
                    'Applications': applications
                })

# --- 5. INVOICE HEAD / DETAIL ENGINE ---
# Real-world purchasing: invoices rarely map 1:1 to PO lines. Vendors bundle several
# PO lines (sometimes across multiple POs) onto one invoice, and invoice numbers have
# no relationship to PO numbers. Each final detail row gets its own natural
# Invoice_Line_ID (a real business key, not a SQL-generated surrogate) and writes its
# goods-receipt matches out to goods_receipt_applications.
#
# Voucher_Number, not Invoice_Number, is the AP system's own primary key -
# exactly like a real ERP: the vendor's invoice number is just a field on the
# voucher, not guaranteed unique. That's what makes DUPLICATE_INVOICE
# realistic: the *same* Invoice_Number gets keyed into the AP system twice,
# as two different vouchers - not two different fabricated invoice numbers.
detail_rows = []
gra_rows = []  # goods_receipt_applications: Invoice_Line_ID, Receipt_ID, Qty_Applied
invoice_line_counter = 0
voucher_counter = 0


def _next_invoice_line_id():
    global invoice_line_counter
    invoice_line_counter += 1
    return f"IL-{invoice_line_counter:06d}"


def _next_voucher_number():
    global voucher_counter
    voucher_counter += 1
    return f"V-{voucher_counter:06d}"


def _emit_detail_row(inv_number, voucher_number, line, applications=None):
    line_id_for_invoice = _next_invoice_line_id()
    apps = line['Applications'] if applications is None else applications
    detail_rows.append([
        line_id_for_invoice, voucher_number, inv_number, line['Vendor_ID'], line['PO_ID'], line['Line_ID'],
        line['Inv_Date'], line['Qty_Inv'], line['Inv_Price'], line['Inv_Currency'], line['Invoice_Error_Type']
    ])
    for a in apps:
        gra_rows.append([line_id_for_invoice, a['Receipt_ID'], a['Qty_Applied']])


vendor_lines = {}
for line in pending_invoice_lines:
    vendor_lines.setdefault(line['Vendor_ID'], []).append(line)

for vendor_id, lines in vendor_lines.items():
    random.shuffle(lines)

    # Duplicates, over-limit and backorder-batch invoices are always billed
    # on their own invoice, pulled out first.
    solo_lines = [l for l in lines if l['Invoice_Error_Type'] in ('DUPLICATE_INVOICE', 'OVER_PO_LIMIT', 'BACKORDER_SPLIT')]
    bundle_pool = [l for l in lines if l not in solo_lines]

    for line in solo_lines:
        inv_number = next_invoice_number(vendor_id)
        voucher_number = _next_voucher_number()
        _emit_detail_row(inv_number, voucher_number, line)

        if line['Invoice_Error_Type'] == 'DUPLICATE_INVOICE':
            # Same Invoice_Number, entered into the AP system a second time
            # by mistake - a fresh Voucher_Number, and the *same* receipt
            # applications as the original (two vouchers both claiming the
            # same receipt is exactly how this gets caught in real life).
            dup_date = (datetime.strptime(line['Inv_Date'], '%Y-%m-%d') + timedelta(days=random.randint(1, 5))).strftime('%Y-%m-%d')
            dup_voucher = _next_voucher_number()
            dup_line = dict(line)
            dup_line['Inv_Date'] = dup_date
            _emit_detail_row(inv_number, dup_voucher, dup_line, applications=line['Applications'])

    # Bundle remaining lines: mostly solo, some multi-line/multi-PO invoices
    idx = 0
    while idx < len(bundle_pool):
        bundle_roll = random.random()
        if bundle_roll < 0.78:
            bundle_size = 1
        elif bundle_roll < 0.93:
            bundle_size = 2
        else:
            bundle_size = 3

        bundle = bundle_pool[idx: idx + bundle_size]
        idx += bundle_size

        inv_number = next_invoice_number(vendor_id)
        voucher_number = _next_voucher_number()
        inv_date = bundle[0]['Inv_Date']
        for line in bundle:
            line_for_emit = dict(line)
            line_for_emit['Inv_Date'] = inv_date
            _emit_detail_row(inv_number, voucher_number, line_for_emit)

df_inv_detail = pd.DataFrame(detail_rows, columns=[
    'Invoice_Line_ID', 'Voucher_Number', 'Invoice_Number', 'Vendor_ID', 'PO_ID', 'Line_ID', 'Inv_Date',
    'Qty_Inv', 'Inv_Price', 'Inv_Currency', 'Invoice_Error_Type'
])
df_inv_detail['Line_Amount_Ex_GST'] = round(df_inv_detail['Qty_Inv'] * df_inv_detail['Inv_Price'], 2)

df_gra = pd.DataFrame(gra_rows, columns=['Invoice_Line_ID', 'Receipt_ID', 'Qty_Applied'])

# --- Invoice head: goods total mostly reconciles to the detail, freight is occasional,
# GST only applies for GST-registered (AUD) vendors ---
vendor_gst_lookup = df_vendor.set_index('Vendor_ID')['GST_Registered'].to_dict()

head_rows = []
for voucher_number, group in df_inv_detail.groupby('Voucher_Number'):
    inv_number = group['Invoice_Number'].iloc[0]
    vendor_id = group['Vendor_ID'].iloc[0]
    inv_date = group['Inv_Date'].min()
    currency = group['Inv_Currency'].mode().iloc[0]
    goods_total = round(group['Line_Amount_Ex_GST'].sum(), 2)

    # A few invoices have a head total that doesn't tie back to the detail lines
    head_error_roll = random.random()
    if head_error_roll < 0.05:
        goods_total_ex_gst = round(goods_total + random.uniform(-150.0, 150.0), 2)
    else:
        goods_total_ex_gst = goods_total

    freight_charged = round(random.uniform(20.0, 380.0), 2) if random.random() < 0.30 else 0.0

    gst_registered = bool(vendor_gst_lookup.get(vendor_id, False))
    if gst_registered:
        gst_base = goods_total_ex_gst + freight_charged
        if random.random() < 0.05:
            gst_charged = 0.0  # GST dropped off the invoice entirely - a compliance chaos case
        else:
            gst_charged = round(gst_base * 0.10, 2)
    else:
        gst_charged = 0.0

    head_rows.append([
        voucher_number, inv_number, vendor_id, inv_date, currency,
        goods_total_ex_gst, freight_charged, gst_charged
    ])

df_inv_head = pd.DataFrame(head_rows, columns=[
    'Voucher_Number', 'Invoice_Number', 'Vendor_ID', 'Invoice_Date', 'Currency',
    'Goods_Total_Ex_GST', 'Freight_Charged', 'GST_Charged'
])

df_inv_detail = df_inv_detail.drop(columns=['Line_Amount_Ex_GST'])

# --- 7. PAYMENTS (batch header + voucher-level detail) ---
# Real AP doesn't pay one invoice at a time - a payment RUN goes out on a
# cadence (here, weekly) and settles a batch of vouchers together. Each
# payment line still resolves its own bank account, since a batch spans many
# vendors: normally whatever's genuinely on file for that vendor as of the
# payment date, occasionally a fabricated account that was never valid for
# that vendor at all (outright redirection fraud), and occasionally an
# account that WAS valid once but has since been superseded (a process
# failure around the bank-detail-change event, not necessarily fraud).
# Neither needs a label - both are a plain comparison against
# vendor_bank_accounts, discoverable exactly the way a real AP controls
# review would find them. Some invoices are never paid at all (genuinely
# outstanding, not just a proxy - real AP aging is possible now).
batch_dates = []
_d = datetime(2026, 2, 15)
while _d <= datetime(2026, 10, 1):
    batch_dates.append(_d)
    _d += timedelta(days=7)


def _next_batch_date(target_date):
    for bd in batch_dates:
        if bd >= target_date:
            return bd
    return batch_dates[-1]


payment_rows = []
payment_counter = 0
batches_used = {}  # Batch_ID -> Batch_Date, only the ones actually used

for _, inv in df_inv_head.iterrows():
    if random.random() < 0.15:
        continue  # genuinely unpaid / still outstanding

    payment_counter += 1
    payment_id = f"PMT-{payment_counter:06d}"

    inv_total = round(inv['Goods_Total_Ex_GST'] + inv['Freight_Charged'] + inv['GST_Charged'], 2)
    target_date = datetime.strptime(inv['Invoice_Date'], '%Y-%m-%d') + timedelta(days=random.randint(10, 45))
    batch_date = _next_batch_date(target_date)
    batch_id = f"BATCH-{batch_date.strftime('%Y%m%d')}"
    batches_used[batch_id] = batch_date.strftime('%Y-%m-%d')
    payment_date = batch_date.strftime('%Y-%m-%d')

    fraud_roll = random.random()
    if fraud_roll < 0.03:
        bank_account = _fraud_bank_account()  # never valid for this vendor, at any time
    elif fraud_roll < 0.05:
        bank_account = _superseded_account(inv['Vendor_ID']) or _account_valid_on(inv['Vendor_ID'], payment_date)
    else:
        bank_account = _account_valid_on(inv['Vendor_ID'], payment_date)

    payment_rows.append([
        payment_id, batch_id, inv['Voucher_Number'], inv['Vendor_ID'], payment_date,
        bank_account, inv_total, inv['Currency']
    ])

df_payments = pd.DataFrame(payment_rows, columns=[
    'Payment_ID', 'Batch_ID', 'Voucher_Number', 'Vendor_ID', 'Payment_Date',
    'Payment_Bank_Account', 'Payment_Amount', 'Payment_Currency'
])

df_payment_batches = pd.DataFrame(
    sorted(batches_used.items(), key=lambda kv: kv[0]),
    columns=['Batch_ID', 'Batch_Date']
)

# --- 8. Convert to CSV ---
df_po = pd.DataFrame(po_lines, columns=[
    'Line_ID', 'PO_ID', 'Date', 'Vendor_ID', 'SKU_ID', 'Line_Description', 'memo', 'Qty',
    'Unit_Price', 'Currency', 'GST_Treatment', 'Applied_FX_Rate', 'Expected_Delivery_Date'
])

df_gr = pd.DataFrame(receipt_rows, columns=[
    'Receipt_ID', 'Line_ID', 'Receipt_Date', 'Qty_Received'
])

output_dir = Path(__file__).resolve().parent.parent / "Data"

def write_csv_with_fallback(df, filename):
    target = output_dir / filename
    try:
        df.to_csv(target, index=False)
        return target.name
    except PermissionError:
        fallback = output_dir / f"new_{filename}"
        df.to_csv(fallback, index=False)
        return fallback.name

written_files = [
    write_csv_with_fallback(df_vendor, 'vendor_master.csv'),
    write_csv_with_fallback(df_bank_accounts, 'vendor_bank_accounts.csv'),
    write_csv_with_fallback(df_sku, 'sku_master.csv'),
    write_csv_with_fallback(df_po, 'purchase_orders.csv'),
    write_csv_with_fallback(df_gr, 'goods_receipts.csv'),
    write_csv_with_fallback(df_inv_head, 'supplier_invoices_head.csv'),
    write_csv_with_fallback(df_inv_detail, 'supplier_invoices_detail.csv'),
    write_csv_with_fallback(df_gra, 'goods_receipt_applications.csv'),
    write_csv_with_fallback(df_payment_batches, 'payment_batches.csv'),
    write_csv_with_fallback(df_payments, 'payments.csv'),
]

print("Australian purchasing chaos dataset generated for Power BI.")
print("Files written:", ", ".join(written_files))
