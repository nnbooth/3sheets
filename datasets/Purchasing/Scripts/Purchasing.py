import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Set seed for reproducible audit targets
np.random.seed(42)
random.seed(42)

num_pos = 3500  
current_date_anchor = datetime(2026, 8, 1)

# --- 1. REAL 2026 FX RATES (AUD to USD) ---
# Data sourced from early 2026 market snapshots
fx_history = {
    '2026-02-01': 0.6945, '2026-02-09': 0.7083, '2026-03-25': 0.6942,
    '2026-04-16': 0.7158, '2026-05-13': 0.7259, '2026-06-20': 0.7006,
    '2026-07-29': 0.6959, '2026-08-01': 0.7017
}

def get_daily_rate(date_str):
    # Fallback to average if exact date not in history snapshot
    return fx_history.get(date_str, random.uniform(0.69, 0.72))

# --- 2. VENDOR MASTER (Australian Context) ---
vendors = [f"VEND-{i:d}" for i in range()]
df_vendor = pd.DataFrame({
    'Vendor_ID': vendors,
    'Vendor_Name': ["Apex Ind", "SteelWorks AU", "Global Log", "Vertex Mfg", "Office Depot AU", "TechCorp International"] + [f"Supplier {i}" for i in range()],
    'Approved_Bank_Account': [f"ACC-APPROVED-{ + i}" for i in range()],
    'System_Currency': ['AUD']*12 + ['USD']*5 + ['EUR']*3 
})

# --- 3. TRANSACTION ENGINE ---
po_lines, gr_rows, inv_rows =,,
po_line_counter = 10000

for po_idx in range(1, num_pos + 1):
    po_id = f"PO-2026-{po_idx:04d}"
    v_row = df_vendor.sample(1).iloc
    po_date = datetime(2026, 2, 1) + timedelta(days=random.randint(0, 175))
    date_str = po_date.strftime('%Y-%m-%d')
    
    for _ in range(random.randint(1, 3)):
        po_line_id = f"POL-{po_line_counter}"
        po_line_counter += 1
        
        # Base Unit Price (Ex-GST)
        base_unit_price = round(random.uniform(10.0, 1000.0), 2)
        qty = random.randint(1, 50)
        
        # --- GST FUCK UP LOGIC ---
        # 10% chance PO is entered as GST Inclusive (incorrectly lowering the base price)
        gst_error = random.random() < 0.10
        po_price = round(base_unit_price / 1.1, 2) if gst_error else base_unit_price
        po_gst_type = "Inclusive" if gst_error else "Exclusive"

        # --- FX FUCK UP LOGIC ---
        daily_rate = get_daily_rate(date_str)
        # Apply a plain wrong rate on Feb 9 or May 13 (simulating manual entry error)
        if date_str in ['--', '--'] and random.random() < 0.5:
            daily_rate = 0.85 # Massive error vs real 0.70 range
            
        po_lines.append([po_line_id, po_id, date_str, v_row['Vendor_ID'], f"SKU-{random.randint(1,100)}", qty, po_unit_price, v_row['System_Currency'], po_gst_type, daily_rate])

        # --- INVOICE FUCK UP LOGIC ---
        if po_date + timedelta(days=12) < current_date_anchor:
            # Overpay GST by 10% (simulating double GST application)
            final_inv_price = po_unit_price * 1.10 if random.random() < 0.05 else po_unit_price
            
            # Currency Flip: Vendor bills in USD despite AUD System agreement
            inv_curr = v_row['System_Currency']
            if inv_curr == 'AUD' and random.random() < 0.03:
                inv_curr = 'USD'
                
            inv_rows.append([f"INV-{po_line_id}", po_line_id, (po_date + timedelta(days=))strftime('%Y-%m-%d'), qty, final_inv_price, inv_curr])

# Convert to CSV
df_po = pd.DataFrame(po_lines, columns=['Line_ID', 'PO_ID', 'Date', 'Vendor_ID', 'SKU_ID', 'Qty', 'Unit_Price', 'Currency', 'GST_Treatment', 'Applied_FX_Rate'])
df_po.to_csv('purchase_orders_au_chaos.csv', index=False)
pd.DataFrame(inv_rows, columns=['Inv_ID', 'Line_ID', 'Inv_Date', 'Qty_Inv', 'Inv_Price', 'Inv_Currency']).to_csv('supplier_invoices.csv', index=False)

print("Australian Chaos Dataset Generated.")
