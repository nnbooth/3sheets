# Purchasing Domain Documentation

## Overview
This document outlines best‑practice data engineering and financial‑controls documentation for the Purchasing domain. It covers table definitions, field‑level guidance, and recommended SQL data types based on the provided dataset. This documentation is intended to support ingestion into Azure SQL via Python.

**Rebuilt 2026-08-20** into a genuine procure-to-pay (P2P) model: raise PO → receive goods →
receive invoice → **apply goods receipts to the invoice** → pay the invoice. The previous
version stopped at "invoice references a PO line" — this pass added the actual matching,
payment, and vendor-banking layers so the checks and balances a real AP function relies on
(three-way match, duplicate-invoice detection, bank-account fraud detection) are backed by real
data, not a label.

---

## Schema: `purchasing`
All tables in this domain reside under the `purchasing` schema. This keeps procurement data logically separated from other business domains.

## Table list (dependency order)

1. `vendor_master`
2. `vendor_bank_accounts`
3. `sku_master`
4. `purchase_orders`
5. `goods_receipts`
6. `supplier_invoices_head`
7. `supplier_invoices_detail`
8. `goods_receipt_applications`
9. `payment_batches`
10. `payments`

---

## Table: `vendor_master`
Supplier master data. Bank account details were moved out of this table 2026-08-20 — see
`vendor_bank_accounts` below.

### Fields
- **Vendor_ID** — NVARCHAR(50), PRIMARY KEY
  Supplier identifier.
- **Vendor_Name** — NVARCHAR(255)
  Supplier name.
- **ABN** — NVARCHAR(20)
  Australian Business Number.
- **System_Currency** — NVARCHAR(10)
  Supplier currency.
- **Country** — NVARCHAR(50)
  Supplier country.
- **GST_Registered** — BIT
  GST registration status.

---

## Table: `vendor_bank_accounts`
**Added 2026-08-20.** An account master, not a static field — a vendor can change bank
accounts over time, and this is what makes that change auditable. Each row is one account that
was valid for a vendor over a date range; a vendor with a genuine account change has two rows
with adjoining `Effective_Start_Date`/`Effective_End_Date`. This is the primary fraud-detection
surface in the model: any `payments.Payment_Bank_Account` that doesn't match the account valid
*for that vendor, as of the payment date* is a red flag — either the account was **never** valid
for that vendor (redirection fraud) or it **was** valid once but has since been superseded
(stale/compromised details).

### Fields
- **Vendor_ID** — NVARCHAR(50), FOREIGN KEY → `vendor_master.Vendor_ID`, part of composite PK
- **Bank_Account** — NVARCHAR(50)
  The account reference on file for this vendor during this date range.
- **Effective_Start_Date** — DATE, part of composite PK
  When this account became the one on file.
- **Effective_End_Date** — DATE, nullable
  When this account stopped being current. `NULL` = still current.

**Primary key:** (`Vendor_ID`, `Effective_Start_Date`)

---

## Table: `sku_master`
Master data for SKUs, including intentional chaos.

Includes one placeholder row, `SKU_ID = "GENERAL"`, so that `purchase_orders.SKU_ID` can carry a
real, always-valid foreign key even for memo lines that have no catalog SKU.

### Fields
- **SKU_ID** — NVARCHAR(50), PRIMARY KEY
  SKU identifier. 250 catalog SKUs plus the `"GENERAL"` placeholder (251 rows total).
- **SKU_Description** — NVARCHAR(255)
  Description of the SKU.
- **Category** — NVARCHAR(100)
  Category grouping.
- **Typical_Unit_Price** — DECIMAL(18,4)
  Typical price. `0.0` for the placeholder row (unused).
- **Days_To_Deliver** — INT
  Agreed/standard lead time in days from PO date to expected delivery — the DIFOT "on time"
  benchmark. `14` (fixed) for the placeholder row.

---

## Table: `purchase_orders`
Core purchasing table containing PO lines, lifecycle chaos, FX anomalies, GST mismanagement, and vendor mismatches.

### Fields
- **Line_ID** — NVARCHAR(50), PRIMARY KEY
  Primary key for PO line.
- **PO_ID** — NVARCHAR(50)
  Purchase order identifier.
- **Date** — DATE
  PO creation date.
- **Vendor_ID** — NVARCHAR(50), FOREIGN KEY → `vendor_master.Vendor_ID`
  Supplier identifier.
- **SKU_ID** — NVARCHAR(50), FOREIGN KEY → `sku_master.SKU_ID`
  SKU identifier. Memo lines use `"GENERAL"`.
- **Line_Description** — NVARCHAR(255)
  Description of the purchased item.
- **memo** — BIT
  True when the line is a memo/ad-hoc entry not tied to a catalog SKU.
- **Qty** — DECIMAL(18,4)
  Quantity ordered. Supports fractional quantities.
- **Unit_Price** — DECIMAL(18,4)
  Price per unit.
- **Currency** — NVARCHAR(10)
  Currency code.
- **GST_Treatment** — NVARCHAR(50)
  GST classification.
- **Applied_FX_Rate** — DECIMAL(18,6)
  FX rate applied.
- **Expected_Delivery_Date** — DATE
  `Date` + the SKU's `Days_To_Deliver` — the promised-delivery benchmark actual receipts get
  measured against for DIFOT.

---

## Table: `goods_receipts`
Represents physical receipt of goods against purchase order lines. A single PO line can be
received across **multiple** receipt events on different dates (full receipt, partial receipt,
or two separate part-shipments) — this is what makes backorder/split-delivery invoicing
patterns possible downstream.

### Fields
- **Receipt_ID** — NVARCHAR(50), PRIMARY KEY
  Unique identifier for the goods receipt.
- **Line_ID** — NVARCHAR(50), FOREIGN KEY → `purchase_orders.Line_ID`
  References the purchase order line this receipt is against.
- **Receipt_Date** — DATE
  Date goods were received.
- **Qty_Received** — DECIMAL(18,4)
  Quantity received on this specific receipt event.

---

## Table: `supplier_invoices_head`
Header-level invoice data. **Restructured 2026-08-20:** the primary key is now
`Voucher_Number`, not `Invoice_Number` — this is how a real AP system works. The vendor's own
invoice number is a field on the voucher, never a guaranteed-unique identifier; the AP system
generates its own voucher number as each invoice is keyed in. `Invoice_Number` is deliberately
**not unique** here: the `DUPLICATE_INVOICE` fraud case is the same vendor invoice number keyed
into the AP system twice, as two different vouchers — exactly the pattern a voucher-numbering AP
system is designed to still let happen (and later catch) if a clerk doesn't check for it.

### Fields
- **Voucher_Number** — NVARCHAR(50), PRIMARY KEY
  System-generated AP voucher number. The real unique identifier of "an invoice entered into the
  system."
- **Invoice_Number** — NVARCHAR(50)
  The vendor's own invoice number. Not unique — see above.
- **Vendor_ID** — NVARCHAR(50), FOREIGN KEY → `vendor_master.Vendor_ID`
  Supplier identifier.
- **Invoice_Date** — DATE
  Invoice date.
- **Currency** — NVARCHAR(10)
  Currency code.
- **Goods_Total_Ex_GST** — DECIMAL(18,4)
  Goods total excluding GST.
- **Freight_Charged** — DECIMAL(18,4)
  Freight amount.
- **GST_Charged** — DECIMAL(18,4)
  GST charged.

---

## Table: `supplier_invoices_detail`
Line-level invoice detail. **Restructured 2026-08-20:** `Invoice_Line_ID` is a real business key
generated by `Purchasing.py` (not a SQL `IDENTITY` value), so it's portable and can be referenced
by `goods_receipt_applications` without depending on a load-time-assigned surrogate. The
head/detail link is now a real `FOREIGN KEY` on `Voucher_Number` — no more business-key-only
workaround.

### Fields
- **Invoice_Line_ID** — NVARCHAR(50), PRIMARY KEY
  Business key generated in the source data (`IL-NNNNNN`).
- **Voucher_Number** — NVARCHAR(50), FOREIGN KEY → `supplier_invoices_head.Voucher_Number`
  The voucher this line belongs to.
- **Invoice_Number** — NVARCHAR(50)
  Descriptive copy of the vendor's invoice number from the head — not a key.
- **Vendor_ID** — NVARCHAR(50)
  Supplier identifier.
- **PO_ID** — NVARCHAR(50)
  Purchase order identifier.
- **Line_ID** — NVARCHAR(50), FOREIGN KEY → `purchase_orders.Line_ID`
  PO line identifier.
- **Inv_Date** — DATE
  Invoice date.
- **Qty_Inv** — DECIMAL(18,4)
  Quantity invoiced. Supports fractional quantities.
- **Inv_Price** — DECIMAL(18,4)
  Price invoiced.
- **Inv_Currency** — NVARCHAR(10)
  Currency code.
- **Invoice_Error_Type** — NVARCHAR(50)
  Ground-truth chaos-case label (e.g. `NO_RECEIPT_INVOICE`, `QTY_OVER_RECEIVED`,
  `DUPLICATE_INVOICE`, `BACKORDER_SPLIT`). Kept for build-time verification; the intent is that
  reports surface the same findings **structurally**, from `goods_receipt_applications`, not from
  this label — see that table below.

---

## Table: `goods_receipt_applications`
**Added 2026-08-20.** The actual goods-receipt-to-invoice matching record a real AP clerk
produces — this is the piece the original design was missing entirely. Each row says "this
invoice line claims this quantity against this specific receipt." This is what makes the
three-way-match exception types **derivable facts** instead of a label with nothing backing
them:
- An invoice line with **zero** rows here is `NO_RECEIPT_INVOICE` — invoiced with no goods
  receipt behind it at all.
- An invoice line whose applied quantity is **less than** `Qty_Inv` is over-invoiced relative to
  what it actually matched.
- A receipt whose applied quantity (summed across all invoice lines that claim it) **exceeds**
  `Qty_Received` has been double-claimed — the structural fingerprint of `DUPLICATE_INVOICE`
  (confirmed 2026-08-20: 231 receipts show this, and 231 is the exact count of distinct receipts
  touched by duplicate-tagged invoice lines — not a bug, the intended fraud signature).

### Fields
- **Invoice_Line_ID** — NVARCHAR(50), FOREIGN KEY → `supplier_invoices_detail.Invoice_Line_ID`, part of composite PK
- **Receipt_ID** — NVARCHAR(50), FOREIGN KEY → `goods_receipts.Receipt_ID`, part of composite PK
- **Qty_Applied** — DECIMAL(18,4)
  Quantity from this invoice line matched against this specific receipt.

**Primary key:** (`Invoice_Line_ID`, `Receipt_ID`)

---

## Table: `payment_batches`
**Added 2026-08-20.** A payment run pays a batch of vouchers together on a given date — this is
the batch header. Deliberately has **no pre-computed total**: batches can span currencies, and
this project's convention is to compute currency-aware totals at report time, not bake a
misleading mixed-currency sum into the source data.

### Fields
- **Batch_ID** — NVARCHAR(50), PRIMARY KEY
- **Batch_Date** — DATE
  Date the batch was paid.

---

## Table: `payments`
**Added 2026-08-20.** Voucher-level payment detail — the last step of the P2P cycle.
`Payment_Bank_Account` is the account this specific payment actually went to; compare against
`vendor_bank_accounts` (effective-dated) to find payments sent somewhere that was never valid for
that vendor (redirection fraud) or that was valid once but has since been superseded. ~15% of
invoiced vouchers are deliberately left unpaid in the generated data (open AP).

### Fields
- **Payment_ID** — NVARCHAR(50), PRIMARY KEY
- **Batch_ID** — NVARCHAR(50), FOREIGN KEY → `payment_batches.Batch_ID`
- **Voucher_Number** — NVARCHAR(50), FOREIGN KEY → `supplier_invoices_head.Voucher_Number`
  The specific voucher this payment settles.
- **Vendor_ID** — NVARCHAR(50), FOREIGN KEY → `vendor_master.Vendor_ID`
- **Payment_Date** — DATE
- **Payment_Bank_Account** — NVARCHAR(50)
  The account actually paid into. Compare against `vendor_bank_accounts` for fraud detection.
- **Payment_Amount** — DECIMAL(18,4)
- **Payment_Currency** — NVARCHAR(10)

---

## Foreign keys

All 11 relationships below are real, always-holding `FOREIGN KEY` constraints, enforced in
`create_purchasing_schema.py`:

- `vendor_bank_accounts.Vendor_ID` → `vendor_master.Vendor_ID`
- `purchase_orders.Vendor_ID` → `vendor_master.Vendor_ID`
- `purchase_orders.SKU_ID` → `sku_master.SKU_ID` (holds because of the `"GENERAL"` placeholder row)
- `goods_receipts.Line_ID` → `purchase_orders.Line_ID`
- `supplier_invoices_head.Vendor_ID` → `vendor_master.Vendor_ID`
- `supplier_invoices_detail.Voucher_Number` → `supplier_invoices_head.Voucher_Number`
- `supplier_invoices_detail.Line_ID` → `purchase_orders.Line_ID`
- `goods_receipt_applications.Invoice_Line_ID` → `supplier_invoices_detail.Invoice_Line_ID`
- `goods_receipt_applications.Receipt_ID` → `goods_receipts.Receipt_ID`
- `payments.Batch_ID` → `payment_batches.Batch_ID`
- `payments.Voucher_Number` → `supplier_invoices_head.Voucher_Number`
- `payments.Vendor_ID` → `vendor_master.Vendor_ID`

This supersedes the pre-2026-08-20 design, where `Invoice_Number` (not a real key) was the only
way to connect header and detail, and there was no way at all to link an invoice to the specific
goods receipt(s) it claimed against.

## Notes
- All ID fields are stored as strings for consistency and flexibility.
- Dates use the DATE type for clean ingestion and reporting.
- Monetary values use DECIMAL(18,4) or DECIMAL(18,6) depending on precision requirements.
- Quantity fields use DECIMAL(18,4) to support fractional units.
- Text fields use NVARCHAR to support international characters.
