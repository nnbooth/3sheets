import pandas as pd
import numpy as np
import random
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

vendor_rows = []
base_abns = []

for i in range(base_vendor_count):
    vendor_id = f"VEND-{i + 1:03d}"
    vendor_name = base_vendor_names[i % len(base_vendor_names)]
    abn = generate_abn()
    base_abns.append(abn)
    vendor_rows.append([
        vendor_id,
        vendor_name,
        f"ACC-APPROVED-{1000 + i}",
        abn,
        currency_pool[i % len(currency_pool)]
    ])

for i in range(duplicate_vendor_count):
    source_abn = random.choice(base_abns)
    vendor_id = f"VEND-{base_vendor_count + i + 1:03d}"
    vendor_rows.append([
        vendor_id,
        f"{base_vendor_names[(i + 3) % len(base_vendor_names)]} Pty Ltd",
        f"ACC-APPROVED-{2000 + i}",
        source_abn,
        random.choice(['AUD', 'USD'])
    ])

df_vendor = pd.DataFrame(vendor_rows, columns=[
    'Vendor_ID', 'Vendor_Name', 'Approved_Bank_Account', 'ABN', 'System_Currency'
])

# --- 4. TRANSACTION ENGINE ---
po_lines = []
inv_rows = []
receipt_rows = []
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

        # --- GST ERROR LOGIC ---
        gst_error = random.random() < 0.10
        po_price = round(base_unit_price / 1.1, 2) if gst_error else base_unit_price
        po_gst_type = "Inclusive" if gst_error else "Exclusive"

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

        # --- INVOICE LOGIC (mostly single PO line invoices, some errors) ---
        if po_date + timedelta(days=12) < current_date_anchor:
            error_roll = random.random()
            inv_error_type = "NONE"

            if error_roll < 0.07:
                inv_error_type = "NO_RECEIPT_INVOICE"
            elif error_roll < 0.13:
                inv_error_type = "QTY_OVER_RECEIVED"
            elif error_roll < 0.19:
                inv_error_type = "PRICE_VARIANCE"
            elif error_roll < 0.22:
                inv_error_type = "CURRENCY_MISMATCH"
            elif error_roll < 0.25:
                inv_error_type = "DUPLICATE_INVOICE"

            if qty_received_total > 0:
                invoice_qty = qty_received_total
            else:
                invoice_qty = qty if inv_error_type == "NO_RECEIPT_INVOICE" else 0

            if inv_error_type == "QTY_OVER_RECEIVED":
                invoice_qty = min(qty, max(qty_received_total + random.randint(1, 4), 1))

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

                inv_rows.append([
                    f"INV-{po_line_id}",
                    po_line_id,
                    inv_date,
                    invoice_qty,
                    final_inv_price,
                    inv_curr,
                    inv_error_type
                ])

                if inv_error_type == "DUPLICATE_INVOICE":
                    dup_date = (datetime.strptime(inv_date, "%Y-%m-%d") + timedelta(days=random.randint(1, 5))).strftime('%Y-%m-%d')
                    inv_rows.append([
                        f"INV-{po_line_id}-DUP",
                        po_line_id,
                        dup_date,
                        invoice_qty,
                        final_inv_price,
                        inv_curr,
                        inv_error_type
                    ])

# --- 5. Convert to CSV ---
df_po = pd.DataFrame(po_lines, columns=[
    'Line_ID', 'PO_ID', 'Date', 'Vendor_ID', 'SKU_ID', 'Line_Description', 'memo', 'Qty',
    'Unit_Price', 'Currency', 'GST_Treatment', 'Applied_FX_Rate'
])

df_gr = pd.DataFrame(receipt_rows, columns=[
    'Receipt_ID', 'Line_ID', 'Receipt_Date', 'Qty_Received'
])

df_inv = pd.DataFrame(inv_rows, columns=[
    'Inv_ID', 'Line_ID', 'Inv_Date', 'Qty_Inv', 'Inv_Price', 'Inv_Currency', 'Invoice_Error_Type'
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
    write_csv_with_fallback(df_inv, 'supplier_invoices.csv')
]

print("Australian purchasing chaos dataset generated for Power BI.")
print("Files written:", ", ".join(written_files))
