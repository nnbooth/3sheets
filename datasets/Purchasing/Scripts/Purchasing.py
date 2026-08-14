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
        round(random.uniform(8.0, 1200.0), 2)
    ])

df_sku = pd.DataFrame(sku_rows, columns=[
    "SKU_ID", "SKU_Description", "Category", "Typical_Unit_Price"
])

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
        f"ACC-APPROVED-{1000 + i}",
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
        f"ACC-APPROVED-{2000 + i}",
        source_abn,
        currency,
        currency_to_country(currency),
        currency == 'AUD'
    ])

df_vendor = pd.DataFrame(vendor_rows, columns=[
    'Vendor_ID', 'Vendor_Name', 'Approved_Bank_Account', 'ABN', 'System_Currency',
    'Country', 'GST_Registered'
])

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
            sku_row = df_sku.sample(1).iloc[0]
            sku_id = sku_row['SKU_ID']
            line_description = sku_row['SKU_Description']
            base_unit_price = round(
                float(sku_row['Typical_Unit_Price']) * random.uniform(0.85, 1.25),
                2
            )

        qty = random.randint(1, 50)

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
            daily_rate
        ])

        # --- RECEIPT LOGIC ---
        receipt_state_roll = random.random()
        qty_received_total = 0

        if receipt_state_roll < 0.12:
            qty_received_total = 0
        elif receipt_state_roll < 0.30:
            qty_received_total = random.randint(1, max(1, qty - 1))
            receipt_date = (po_date + timedelta(days=random.randint(5, 20))).strftime('%Y-%m-%d')
            receipt_rows.append([
                f"GR-{po_line_id}-1",
                po_line_id,
                receipt_date,
                qty_received_total
            ])
        else:
            qty_received_total = qty
            receipt_date = (po_date + timedelta(days=random.randint(5, 20))).strftime('%Y-%m-%d')
            receipt_rows.append([
                f"GR-{po_line_id}-1",
                po_line_id,
                receipt_date,
                qty_received_total
            ])

        # --- INVOICE CANDIDATE LOGIC (grouping/splitting happens in section 5) ---
        if po_date + timedelta(days=12) < current_date_anchor:
            error_roll = random.random()
            inv_error_type = "NONE"

            if error_roll < 0.06:
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
            elif error_roll < 0.32:
                inv_error_type = "BACKORDER_SPLIT"

            if qty_received_total > 0:
                invoice_qty = qty_received_total
            else:
                invoice_qty = qty if inv_error_type == "NO_RECEIPT_INVOICE" else 0

            if inv_error_type == "QTY_OVER_RECEIVED":
                invoice_qty = min(qty, max(qty_received_total + random.randint(1, 4), 1))
            elif inv_error_type == "OVER_PO_LIMIT":
                # Vendor bills beyond what was ever ordered on the line - a genuine matching exception
                invoice_qty = qty + random.randint(1, 10)

            if invoice_qty > 0:
                final_inv_price = po_price
                if random.random() < 0.05:
                    final_inv_price = round(po_price * 1.10, 2)

                if inv_error_type == "PRICE_VARIANCE":
                    final_inv_price = round(po_price * random.uniform(1.08, 1.25), 2)

                inv_curr = v_row['System_Currency']
                if inv_error_type == "CURRENCY_MISMATCH":
                    if inv_curr == 'AUD':
                        inv_curr = random.choice(['USD', 'EUR'])
                    elif inv_curr == 'USD':
                        inv_curr = 'AUD'
                    else:
                        inv_curr = 'AUD'

                inv_date = (po_date + timedelta(days=12)).strftime('%Y-%m-%d')

                pending_invoice_lines.append({
                    'Vendor_ID': v_row['Vendor_ID'],
                    'PO_ID': po_id,
                    'Line_ID': po_line_id,
                    'Inv_Date': inv_date,
                    'Qty_Inv': invoice_qty,
                    'Inv_Price': final_inv_price,
                    'Inv_Currency': inv_curr,
                    'Invoice_Error_Type': inv_error_type
                })

# --- 5. INVOICE HEAD / DETAIL ENGINE ---
# Real-world purchasing: invoices rarely map 1:1 to PO lines. Vendors bundle several
# PO lines (sometimes across multiple POs) onto one invoice, back-ordered lines get
# split across several invoices, and invoice numbers have no relationship to PO numbers.
detail_rows = []

vendor_lines = {}
for line in pending_invoice_lines:
    vendor_lines.setdefault(line['Vendor_ID'], []).append(line)

for vendor_id, lines in vendor_lines.items():
    random.shuffle(lines)

    # Duplicates and back-orders are always billed on their own invoice(s), pulled out first
    solo_lines = [l for l in lines if l['Invoice_Error_Type'] in ('DUPLICATE_INVOICE', 'OVER_PO_LIMIT')]
    split_lines = [l for l in lines if l['Invoice_Error_Type'] == 'BACKORDER_SPLIT']
    bundle_pool = [l for l in lines if l not in solo_lines and l not in split_lines]

    for line in solo_lines:
        inv_number = next_invoice_number(vendor_id)
        detail_rows.append([inv_number, vendor_id, line['PO_ID'], line['Line_ID'], line['Inv_Date'],
                             line['Qty_Inv'], line['Inv_Price'], line['Inv_Currency'], line['Invoice_Error_Type']])

        if line['Invoice_Error_Type'] == 'DUPLICATE_INVOICE':
            dup_date = (datetime.strptime(line['Inv_Date'], '%Y-%m-%d') + timedelta(days=random.randint(1, 5))).strftime('%Y-%m-%d')
            dup_number = next_invoice_number(vendor_id)
            detail_rows.append([dup_number, vendor_id, line['PO_ID'], line['Line_ID'], dup_date,
                                 line['Qty_Inv'], line['Inv_Price'], line['Inv_Currency'], line['Invoice_Error_Type']])

    for line in split_lines:
        first_qty = max(1, line['Qty_Inv'] // 2)
        second_qty = max(1, line['Qty_Inv'] - first_qty)
        first_date = line['Inv_Date']
        second_date = (datetime.strptime(first_date, '%Y-%m-%d') + timedelta(days=random.randint(7, 21))).strftime('%Y-%m-%d')

        first_number = next_invoice_number(vendor_id)
        second_number = next_invoice_number(vendor_id)
        detail_rows.append([first_number, vendor_id, line['PO_ID'], line['Line_ID'], first_date,
                             first_qty, line['Inv_Price'], line['Inv_Currency'], line['Invoice_Error_Type']])
        detail_rows.append([second_number, vendor_id, line['PO_ID'], line['Line_ID'], second_date,
                             second_qty, line['Inv_Price'], line['Inv_Currency'], line['Invoice_Error_Type']])

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
        inv_date = bundle[0]['Inv_Date']
        for line in bundle:
            detail_rows.append([inv_number, vendor_id, line['PO_ID'], line['Line_ID'], inv_date,
                                 line['Qty_Inv'], line['Inv_Price'], line['Inv_Currency'], line['Invoice_Error_Type']])

df_inv_detail = pd.DataFrame(detail_rows, columns=[
    'Invoice_Number', 'Vendor_ID', 'PO_ID', 'Line_ID', 'Inv_Date',
    'Qty_Inv', 'Inv_Price', 'Inv_Currency', 'Invoice_Error_Type'
])
df_inv_detail['Line_Amount_Ex_GST'] = round(df_inv_detail['Qty_Inv'] * df_inv_detail['Inv_Price'], 2)

# --- Invoice head: goods total mostly reconciles to the detail, freight is occasional,
# GST only applies for GST-registered (AUD) vendors ---
vendor_gst_lookup = df_vendor.set_index('Vendor_ID')['GST_Registered'].to_dict()

head_rows = []
for inv_number, group in df_inv_detail.groupby('Invoice_Number'):
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
        inv_number, vendor_id, inv_date, currency,
        goods_total_ex_gst, freight_charged, gst_charged
    ])

df_inv_head = pd.DataFrame(head_rows, columns=[
    'Invoice_Number', 'Vendor_ID', 'Invoice_Date', 'Currency',
    'Goods_Total_Ex_GST', 'Freight_Charged', 'GST_Charged'
])

df_inv_detail = df_inv_detail.drop(columns=['Line_Amount_Ex_GST'])

# --- 6. Convert to CSV ---
df_po = pd.DataFrame(po_lines, columns=[
    'Line_ID', 'PO_ID', 'Date', 'Vendor_ID', 'SKU_ID', 'Line_Description', 'memo', 'Qty',
    'Unit_Price', 'Currency', 'GST_Treatment', 'Applied_FX_Rate'
])

df_gr = pd.DataFrame(receipt_rows, columns=[
    'Receipt_ID', 'Line_ID', 'Receipt_Date', 'Qty_Received'
])

output_dir = Path(__file__).resolve().parent

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
    write_csv_with_fallback(df_sku, 'sku_master.csv'),
    write_csv_with_fallback(df_po, 'purchase_orders_au_chaos.csv'),
    write_csv_with_fallback(df_gr, 'goods_receipts.csv'),
    write_csv_with_fallback(df_inv_head, 'supplier_invoices_head.csv'),
    write_csv_with_fallback(df_inv_detail, 'supplier_invoices_detail.csv')
]

print("Australian purchasing chaos dataset generated for Power BI.")
print("Files written:", ", ".join(written_files))
