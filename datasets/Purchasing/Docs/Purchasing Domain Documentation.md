# Purchasing Domain Documentation

## Overview
This document outlines best‑practice data engineering and financial‑controls documentation for the Purchasing domain. It covers table definitions, field‑level guidance, and recommended SQL data types based on the provided dataset. This documentation is intended to support ingestion into Azure SQL via Python.

**See also:** [Purchasing schema.md](Purchasing%20schema.md) is the authoritative, field-by-field
reference (including every `FOREIGN KEY` and the reasoning behind each key design decision) —
this document is a shorter overview of the same schema.

**Rebuilt 2026-08-20** into a genuine procure-to-pay model: raise PO → receive goods → receive
invoice → apply goods receipts to the invoice → pay the invoice. Four tables were added
(`vendor_bank_accounts`, `goods_receipt_applications`, `payment_batches`, `payments`) and the
invoice header/detail link was replaced with a real system-generated voucher key, so the
three-way match and fraud-detection story is backed by real data instead of a synthetic label.

---

## Schema: `purchasing`
All tables in this domain reside under the `purchasing` schema. This keeps procurement data logically separated from other business domains.

---

## Table: `vendor_master`
Supplier master data.

### Fields
- **Vendor_ID** — NVARCHAR(50), PRIMARY KEY
- **Vendor_Name** — NVARCHAR(255)
- **ABN** — NVARCHAR(20)
- **System_Currency** — NVARCHAR(10)
- **Country** — NVARCHAR(50)
- **GST_Registered** — BIT

---

## Table: `vendor_bank_accounts`
Effective-dated bank account history per vendor — a vendor can change accounts over time, and
this is what makes that change auditable and a payment to the wrong account detectable.

### Fields
- **Vendor_ID** — NVARCHAR(50), FOREIGN KEY → `vendor_master.Vendor_ID`, part of composite PK
- **Bank_Account** — NVARCHAR(50)
- **Effective_Start_Date** — DATE, part of composite PK
- **Effective_End_Date** — DATE, nullable (`NULL` = still current)

---

## Table: `sku_master`
Master data for SKUs, including intentional chaos. Includes one placeholder row,
`SKU_ID = "GENERAL"`, so `purchase_orders.SKU_ID` holds as a real foreign key even for memo
lines with no catalog SKU.

### Fields
- **SKU_ID** — NVARCHAR(50), PRIMARY KEY
- **SKU_Description** — NVARCHAR(255)
- **Category** — NVARCHAR(100)
- **Typical_Unit_Price** — DECIMAL(18,4)
- **Days_To_Deliver** — INT — agreed lead time; the DIFOT "on time" benchmark.

---

## Table: `purchase_orders`
Core purchasing table containing PO lines, lifecycle chaos, FX anomalies, GST mismanagement, and vendor mismatches.

### Fields
- **Line_ID** — NVARCHAR(50), PRIMARY KEY
- **PO_ID** — NVARCHAR(50)
- **Date** — DATE
- **Vendor_ID** — NVARCHAR(50), FOREIGN KEY → `vendor_master.Vendor_ID`
- **SKU_ID** — NVARCHAR(50), FOREIGN KEY → `sku_master.SKU_ID`
- **Line_Description** — NVARCHAR(255)
- **memo** — BIT
- **Qty** — DECIMAL(18,4)
- **Unit_Price** — DECIMAL(18,4)
- **Currency** — NVARCHAR(10)
- **GST_Treatment** — NVARCHAR(50)
- **Applied_FX_Rate** — DECIMAL(18,6)
- **Expected_Delivery_Date** — DATE — `Date` + the SKU's `Days_To_Deliver`.

---

## Table: `goods_receipts`
Physical receipt of goods against purchase order lines. A single PO line can be received across
multiple receipt events on different dates.

### Fields
- **Receipt_ID** — NVARCHAR(50), PRIMARY KEY
- **Line_ID** — NVARCHAR(50), FOREIGN KEY → `purchase_orders.Line_ID`
- **Receipt_Date** — DATE
- **Qty_Received** — DECIMAL(18,4)

---

## Table: `supplier_invoices_head`
Header-level invoice data. Primary key is `Voucher_Number` — the AP system's own
system-generated identifier, not the vendor's invoice number. `Invoice_Number` is deliberately
non-unique (the `DUPLICATE_INVOICE` case is the same vendor invoice keyed in twice, as two
different vouchers).

### Fields
- **Voucher_Number** — NVARCHAR(50), PRIMARY KEY
- **Invoice_Number** — NVARCHAR(50) — vendor's own number, not unique
- **Vendor_ID** — NVARCHAR(50), FOREIGN KEY → `vendor_master.Vendor_ID`
- **Invoice_Date** — DATE
- **Currency** — NVARCHAR(10)
- **Goods_Total_Ex_GST** — DECIMAL(18,4)
- **Freight_Charged** — DECIMAL(18,4)
- **GST_Charged** — DECIMAL(18,4)

---

## Table: `supplier_invoices_detail`
Line-level invoice detail used for three-way match, fraud detection, and GST/FX anomalies.

### Fields
- **Invoice_Line_ID** — NVARCHAR(50), PRIMARY KEY — business key, e.g. `IL-000123`
- **Voucher_Number** — NVARCHAR(50), FOREIGN KEY → `supplier_invoices_head.Voucher_Number`
- **Invoice_Number** — NVARCHAR(50) — descriptive copy only, not a key
- **Vendor_ID** — NVARCHAR(50)
- **PO_ID** — NVARCHAR(50)
- **Line_ID** — NVARCHAR(50), FOREIGN KEY → `purchase_orders.Line_ID`
- **Inv_Date** — DATE
- **Qty_Inv** — DECIMAL(18,4)
- **Inv_Price** — DECIMAL(18,4)
- **Inv_Currency** — NVARCHAR(10)
- **Invoice_Error_Type** — NVARCHAR(50) — ground-truth chaos-case label, kept for build-time
  verification; reports should surface the same findings structurally, from
  `goods_receipt_applications`, rather than reading this field.

---

## Table: `goods_receipt_applications`
The actual receipt-to-invoice matching record — one row per "this invoice line claims this
quantity against this specific receipt." Makes the three-way-match exceptions derivable facts:
an invoice line with no rows here has no receipt behind it at all; a receipt whose total applied
quantity exceeds what was received has been double-claimed (the structural signature of a
duplicate-invoice fraud).

### Fields
- **Invoice_Line_ID** — NVARCHAR(50), FOREIGN KEY → `supplier_invoices_detail.Invoice_Line_ID`, part of composite PK
- **Receipt_ID** — NVARCHAR(50), FOREIGN KEY → `goods_receipts.Receipt_ID`, part of composite PK
- **Qty_Applied** — DECIMAL(18,4)

---

## Table: `payment_batches`
A payment run paying a batch of vouchers together on one date. No pre-computed total — batches
can span currencies, and currency-aware totals are computed at report time.

### Fields
- **Batch_ID** — NVARCHAR(50), PRIMARY KEY
- **Batch_Date** — DATE

---

## Table: `payments`
Voucher-level payment detail. `Payment_Bank_Account` is compared against the effective-dated
`vendor_bank_accounts` history to detect payments to an account never valid for that vendor, or
one that was valid once but has since been superseded.

### Fields
- **Payment_ID** — NVARCHAR(50), PRIMARY KEY
- **Batch_ID** — NVARCHAR(50), FOREIGN KEY → `payment_batches.Batch_ID`
- **Voucher_Number** — NVARCHAR(50), FOREIGN KEY → `supplier_invoices_head.Voucher_Number`
- **Vendor_ID** — NVARCHAR(50), FOREIGN KEY → `vendor_master.Vendor_ID`
- **Payment_Date** — DATE
- **Payment_Bank_Account** — NVARCHAR(50)
- **Payment_Amount** — DECIMAL(18,4)
- **Payment_Currency** — NVARCHAR(10)

---

## Notes
- All ID fields are stored as strings for consistency and flexibility.
- Dates use the DATE type for clean ingestion and reporting.
- Monetary values use DECIMAL(18,4) or DECIMAL(18,6) depending on precision requirements.
- Quantity fields use DECIMAL(18,4) to support fractional units.
- Text fields use NVARCHAR to support international characters.
- No table in this schema has a SQL-generated `IDENTITY` key — every primary key is a natural
  business key, generated in `Purchasing.py` where the source data doesn't already carry one.

---

## Next Steps
This documentation supports the Python ingestion script (`create_purchasing_schema.py`,
`load_purchasing_data.py`) that creates the `purchasing` schema, all 10 tables and their 11
foreign keys, and loads each CSV into Azure SQL.
