# Purchasing Power BI Model & Report Documentation

**Scope:** every table, column, calculated column, measure, relationship, and report page in
`datasets/Purchasing/Power BI/Purchasing.pbip`, as of 2026-08-21.

**Note on scope:** the `.pbip` project itself is intentionally excluded from git (see
`.gitignore`) — this document is the durable record of what it contains.

---

## 1. Overview

The model reports on a full procure-to-pay (P2P) cycle: **raise PO → receive goods → receive
invoice → apply goods receipts to the invoice (match) → pay the invoice**. It's built specifically
to demonstrate the checks and balances a real AP function relies on — three-way match, duplicate-
invoice detection, and vendor bank-account-change fraud detection — backed by real linked data
rather than a synthetic pass/fail label.

- **Source:** Azure SQL `3sheets.db.sql`, schema `purchasing`, server `3sheets.database.windows.net`.
- **Import mode:** all tables are Import (not DirectQuery); most use `Value.NativeQuery` against
  the source SQL rather than the folder-navigation connector, to avoid Power Query's stale-schema
  cache on tables whose structure changed during development.
- **Theme:** custom "3Sheets Consulting" theme, palette sourced from the site's `styles.css`
  (`#2f7a5d` accent, `#1f7a4a` good/green, `#b93a3a` bad/red).

## 2. Data Model Architecture

15 tables in total:

| Category | Tables |
|---|---|
| SQL source tables (10) | `vendor_master`, `vendor_bank_accounts`, `sku_master`, `purchase_orders`, `goods_receipts`, `supplier_invoices_head`, `supplier_invoices_detail`, `goods_receipt_applications`, `payment_batches`, `payments` |
| Calculated tables (2) | `PO_Summary`, `Invoice_Line_Reconciliation` |
| Supporting tables (2) | `Dim_Date` (calendar), `FX_Rates` (AUD/USD historical rates) |
| Hidden measures table (1) | `_Measures` |

**P2P flow through the tables:**

```
vendor_master ──┬── purchase_orders ──┬── goods_receipts ──┐
                 │  (Line_ID = PK)     │                    ├── goods_receipt_applications
                 │                     └── supplier_invoices_detail ──┘   (the match)
                 │                              │
                 ├── supplier_invoices_head ────┘ (Voucher_Number)
                 │         │
                 ├── payments ──── payment_batches
                 │
                 └── vendor_bank_accounts (effective-dated account history, for fraud detection)
```

`Voucher_Number` (system-generated, on `supplier_invoices_head`) is the real primary key of an
invoice, not the vendor's own `Invoice_Number` — mirroring how a real AP system works, and
deliberately allowing `Invoice_Number` to repeat (the `DUPLICATE_INVOICE` fraud case).

---

## 3. Tables

### 3.1 `vendor_master`
Supplier master data.

| Column | Type | Calculated? | Notes |
|---|---|---|---|
| Vendor_ID | string | No | **Key** |
| Vendor_Name | string | No | |
| ABN | string | No | |
| System_Currency | string | No | |
| Country | string | No | |
| GST_Registered | boolean | No | |

### 3.2 `vendor_bank_accounts`
Effective-dated bank account history per vendor — a vendor can change accounts over time; this is
the fraud-detection surface for payments.

| Column | Type | Calculated? | Notes |
|---|---|---|---|
| Vendor_ID | string | No | |
| Bank_Account | string | No | |
| Effective_Start_Date | dateTime | No | Format `dd-mmm-yy` |
| Effective_End_Date | dateTime | No | Nullable — blank = still current |

### 3.3 `sku_master`
SKU catalog, including one placeholder row (`SKU_ID = "GENERAL"`) so memo/ad-hoc PO lines still
carry a valid foreign key.

| Column | Type | Calculated? | Notes |
|---|---|---|---|
| SKU_ID | string | No | **Key** |
| SKU_Description | string | No | |
| Category | string | No | |
| Typical_Unit_Price | double | No | |
| Days_To_Deliver | int64 | No | Agreed lead time — the DIFOT "on time" benchmark |

### 3.4 `purchase_orders`
Core PO line table. Renamed from `purchase_orders_au_chaos` earlier in the build.

| Column | Type | Calculated? | DAX / Notes |
|---|---|---|---|
| Line_ID | string | No | **Key** |
| PO_ID | string | No | |
| Date | dateTime | No | |
| Vendor_ID | string | No | |
| SKU_ID | string | No | |
| Line_Description | string | No | |
| memo | boolean | No | True = ad-hoc line, no catalog SKU |
| Qty | double | No | |
| Unit_Price | double | No | |
| Currency | string | No | |
| GST_Treatment | string | No | |
| Applied_FX_Rate | double | No | Recorded rate, may contain deliberate entry errors |
| Expected_Delivery_Date | dateTime | No | `Date` + SKU's `Days_To_Deliver` |
| Effective_AUD_USD_Rate | decimal | **Yes** | `VAR TxDate = purchase_orders[Date] / VAR EffDate = CALCULATE(MAX(FX_Rates[Date]), FX_Rates[Date] <= TxDate, ALL(FX_Rates)) / RETURN CALCULATE(MAX(FX_Rates[AUD_USD_Rate]), FX_Rates[Date] = EffDate, ALL(FX_Rates))` — historical, transaction-date-effective FX rate |
| Line Value (Local) | decimal | **Yes** | `Qty * Unit_Price` |
| Line Value (AUD) | decimal | **Yes** | `SWITCH(Currency, "AUD", [Local], "USD", DIVIDE([Local], [Effective_AUD_USD_Rate]), BLANK())` |
| Total Qty Received (Line) | decimal | **Yes** | `CALCULATE(SUM(goods_receipts[Qty_Received]))`, defaulted to 0 |
| Total Qty Invoiced (Line) | decimal | **Yes** | `CALCULATE(SUM(supplier_invoices_detail[Qty_Inv]))`, defaulted to 0 |
| First Receipt Date | dateTime | **Yes** | `CALCULATE(MIN(goods_receipts[Receipt_Date]))` |
| Lead Time (Days) | int64 | **Yes** | `DATEDIFF(Date, First Receipt Date, DAY)` |
| Open Qty (Line) | decimal | **Yes** | `Qty - Total Qty Received (Line)` |
| Open Value (Local) | decimal | **Yes** | `Open Qty (Line) * Unit_Price` |
| Open Value (AUD) | decimal | **Yes** | Currency-switched version of Open Value |
| Three-Way Match Status | string | **Yes** | PO-line-level status: `"Open - Not Received/Invoiced"` / `"No Receipt Invoice (Exception)"` / `"Received - Not Yet Invoiced"` / `"Fully Matched"` / `"Qty Mismatch"`, from comparing ordered/received/invoiced quantities. **Note:** this is a coarser, PO-line-level proxy that predates the `goods_receipt_applications` rebuild — see §9. |
| Standard Price (SKU) | decimal | **Yes** | `RELATED(sku_master[Typical_Unit_Price])` |
| Received In Full | boolean | **Yes** | `Total Qty Received (Line) >= Qty` (over-delivery still counts) |
| PPV (Local) | decimal | **Yes** | `(Unit_Price - Standard Price (SKU)) * Qty`, blank for memo lines |
| PPV (AUD) | decimal | **Yes** | Currency-switched version |
| Delivered On Time | boolean | **Yes** | `First Receipt Date <= Expected_Delivery_Date` (never-received = not on time) |

### 3.5 `goods_receipts`
Physical receipt of goods against PO lines. A PO line can be received across multiple events.

| Column | Type | Calculated? | DAX / Notes |
|---|---|---|---|
| Receipt_ID | string | No | **Key** |
| Line_ID | string | No | |
| Receipt_Date | dateTime | No | |
| Qty_Received | double | No | |
| Applied_Qty_Total | decimal | **Yes** | `FILTER(ALL(goods_receipt_applications), Receipt_ID = ThisReceipt)` summed `Qty_Applied` — explicit `ALL()` filter, independent of the (inactive) direct relationship |
| Unapplied_Qty | decimal | **Yes** | `Qty_Received - Applied_Qty_Total` — signed; negative = over-applied (duplicate claim) |
| Effective_AUD_USD_Rate | decimal | **Yes** | Same historical-rate pattern, keyed on `Receipt_Date` |
| Unvouchered Qty | decimal | **Yes** | `MAX(0, Unapplied_Qty)` — clamped; the true "received but not yet invoiced" figure |
| Unvouchered Value (Local) | decimal | **Yes** | `Unvouchered Qty * RELATED(purchase_orders[Unit_Price])` |
| Unvouchered Value (AUD) | decimal | **Yes** | Currency-switched version |

### 3.6 `supplier_invoices_head`
Invoice header. **Voucher_Number is the real primary key** (system-generated AP voucher), not
`Invoice_Number` (the vendor's own number, deliberately non-unique — the `DUPLICATE_INVOICE` case
is the same invoice number keyed in twice as two vouchers).

| Column | Type | Calculated? | DAX / Notes |
|---|---|---|---|
| Voucher_Number | string | No | **Key** |
| Invoice_Number | string | No | Vendor's own number — not unique |
| Vendor_ID | string | No | |
| Invoice_Date | dateTime | No | |
| Currency | string | No | |
| Goods_Total_Ex_GST | double | No | |
| Freight_Charged | double | No | |
| GST_Charged | double | No | |
| Effective_AUD_USD_Rate | decimal | **Yes** | Keyed on `Invoice_Date` |
| Invoice Total Inc GST (Local) | decimal | **Yes** | `Goods_Total_Ex_GST + Freight_Charged + GST_Charged` |
| Invoice Total Inc GST (AUD) | decimal | **Yes** | Currency-switched version |
| Detail Total (Calc) | decimal | **Yes** | `SUMX(RELATEDTABLE(supplier_invoices_detail), Qty_Inv * Inv_Price)` via the `Voucher_Number` relationship |
| Head vs Detail Variance (Local) | decimal | **Yes** | `Goods_Total_Ex_GST - Detail Total (Calc)` |
| Head vs Detail Match | string | **Yes** | `"Matched"` / `"Mismatch (Currency)"` / `"Mismatch (Genuine)"` |
| Any Detail Currency Mismatch | boolean | **Yes** | TRUE if any related detail line's currency differs from the head's |
| Payment Date (Head) | dateTime | **Yes** | `CALCULATE(MIN(payments[Payment_Date]))` |
| Is Paid | boolean | **Yes** | `NOT ISBLANK(Payment Date (Head))` |
| Days To Pay | int64 | **Yes** | `DATEDIFF(Invoice_Date, Payment Date (Head), DAY)`, blank if unpaid |

### 3.7 `supplier_invoices_detail`
Invoice line detail.

| Column | Type | Calculated? | DAX / Notes |
|---|---|---|---|
| Invoice_Line_ID | string | No | **Key**, business key (e.g. `IL-000123`) |
| Voucher_Number | string | No | FK to head |
| Invoice_Number | string | No | Descriptive copy only, not a key |
| Vendor_ID | string | No | |
| PO_ID | string | No | |
| Line_ID | string | No | |
| Inv_Date | dateTime | No | |
| Qty_Inv | double | No | |
| Inv_Price | double | No | |
| Inv_Currency | string | No | |
| Invoice_Error_Type | string | No | Ground-truth chaos-case label — kept for build verification, not meant to be the surfaced fact (see §9) |
| Effective_AUD_USD_Rate | decimal | **Yes** | Keyed on `Inv_Date` |
| Detail Line Value (Local) | decimal | **Yes** | `Qty_Inv * Inv_Price` |
| Detail Line Value (AUD) | decimal | **Yes** | Currency-switched version |
| PO Qty | decimal | **Yes** | `RELATED(purchase_orders[Qty])` |
| PO Unit Price | decimal | **Yes** | `RELATED(purchase_orders[Unit_Price])` |
| PO Qty Received (Total) | decimal | **Yes** | `RELATED(purchase_orders[Total Qty Received (Line)])` |
| Price Variance (Local) | decimal | **Yes** | `Inv_Price - PO Unit Price` |
| Price Variance % | decimal | **Yes** | `DIVIDE(Price Variance (Local), PO Unit Price)` |
| Currency Matches Head | boolean | **Yes** | `Inv_Currency = RELATED(supplier_invoices_head[Currency])` |
| Applied_Qty_Total | decimal | **Yes** | `CALCULATE(SUM(goods_receipt_applications[Qty_Applied]))` via the active relationship |
| Has_Application | boolean | **Yes** | `Applied_Qty_Total > 0` |
| Qty_Unmatched | decimal | **Yes** | `Qty_Inv - Applied_Qty_Total` |

### 3.8 `goods_receipt_applications`
The real receipt-to-invoice matching record — one row per "this invoice line claims this quantity
against this specific receipt." This is what makes three-way-match exceptions derivable facts
instead of a synthetic label.

| Column | Type | Calculated? | Notes |
|---|---|---|---|
| Invoice_Line_ID | string | No | Composite key part |
| Receipt_ID | string | No | Composite key part |
| Qty_Applied | decimal | No | |

### 3.9 `payment_batches`
A payment run paying a batch of vouchers on one date. Deliberately no pre-computed total
(currency-aware totals are computed at report time).

| Column | Type | Calculated? | Notes |
|---|---|---|---|
| Batch_ID | string | No | **Key** |
| Batch_Date | dateTime | No | |

### 3.10 `payments`
Voucher-level payment detail — the fraud-detection payoff of the model.

| Column | Type | Calculated? | DAX / Notes |
|---|---|---|---|
| Payment_ID | string | No | **Key** |
| Batch_ID | string | No | |
| Voucher_Number | string | No | |
| Vendor_ID | string | No | |
| Payment_Date | dateTime | No | |
| Payment_Bank_Account | string | No | Account actually paid into |
| Payment_Amount | decimal | No | |
| Payment_Currency | string | No | |
| Effective_AUD_USD_Rate | decimal | **Yes** | Keyed on `Payment_Date` |
| Payment_Amount_AUD | decimal | **Yes** | Currency-switched version |
| Bank_Account_Status | string | **Yes** | See below — the fraud classification |

**`Bank_Account_Status` DAX** (full logic):
```dax
VAR ThisVendor = payments[Vendor_ID]
VAR ThisAccount = payments[Payment_Bank_Account]
VAR ThisDate = payments[Payment_Date]
VAR ValidNow =
    CALCULATE(
        COUNTROWS(vendor_bank_accounts),
        FILTER(
            ALL(vendor_bank_accounts),
            vendor_bank_accounts[Vendor_ID] = ThisVendor &&
            vendor_bank_accounts[Bank_Account] = ThisAccount &&
            vendor_bank_accounts[Effective_Start_Date] <= ThisDate &&
            (ISBLANK(vendor_bank_accounts[Effective_End_Date]) || vendor_bank_accounts[Effective_End_Date] >= ThisDate)
        )
    ) > 0
VAR EverValid =
    CALCULATE(
        COUNTROWS(vendor_bank_accounts),
        FILTER(
            ALL(vendor_bank_accounts),
            vendor_bank_accounts[Vendor_ID] = ThisVendor &&
            vendor_bank_accounts[Bank_Account] = ThisAccount
        )
    ) > 0
RETURN
    SWITCH(
        TRUE(),
        ValidNow, "Valid",
        EverValid, "Superseded Account",
        "Never Valid (Fraud Risk)"
    )
```
Classifies every payment as **Valid** (account on file for that vendor as of the payment date),
**Superseded Account** (was valid for that vendor once, but not any more), or **Never Valid
(Fraud Risk)** (never on file for that vendor at all). Verified: 4,190 Valid / 17 Superseded / 120
Never Valid across 4,327 payments.

### 3.11 `Dim_Date`
Standard calendar table, one row per day, generated from `MinMaxDates` (Power Query named
expression) spanning the full data range. Columns: `Date` (key), `Year`, `Quarter`, `Quarter
Name`, `Month Number`, `Month Name`, `Month Short Name`, `Year Month`, `Day of Month`, `Day of
Week`, `Day Name`, `Is Weekend`, `Financial Year`, `Financial Year Label`, `Financial Quarter`,
`Financial Quarter Label`, `Financial Month Number` (Australian FY, July–June). Marked as the
model's official Date Table (`dataCategory: Time`).

### 3.12 `FX_Rates`
Hardcoded AUD/USD historical rate table (8 rows, Feb–Aug 2026), sourced verbatim from
`Purchasing.py`'s `fx_history` dict. Effective-dated: every `Effective_AUD_USD_Rate` calculated
column across the model looks up the most recent rate on or before the transaction date.

### 3.13 `PO_Summary` (calculated table)
One row per `PO_ID`, rolling up all its lines. Built via `ADDCOLUMNS(SUMMARIZE(purchase_orders,
PO_ID, Vendor_ID, Date, Currency), ...)`.

| Column | Calculated? | DAX / Notes |
|---|---|---|
| PO_ID, Vendor_ID, Date, Currency | Grouping | From `SUMMARIZE` |
| Line Count | Added | `CALCULATE(COUNTROWS(purchase_orders))` |
| Lines Open | Added | Count where `Open Qty (Line) > 0` |
| Lines Fully Matched | Added | Count where `Three-Way Match Status = "Fully Matched"` |
| PO Value (Local) / (AUD) | Added | Summed line values |
| Open Value (AUD) | Added | Summed open value |
| PO Status | **Yes** | `IF(Lines Open = 0, "Closed - Fully Filled", "Open")` |
| Lines Received In Full | **Yes** | Count of lines where `Received In Full = TRUE` |
| PO Delivered In Full | **Yes** | `Lines Received In Full = Line Count` |
| Lines On Time | **Yes** | Count of lines where `Delivered On Time = TRUE` |
| PO Delivered On Time | **Yes** | `Lines On Time = Line Count` |
| PO DIFOT | **Yes** | `PO Delivered In Full && PO Delivered On Time` — true Delivered-In-Full-On-Time |

### 3.14 `Invoice_Line_Reconciliation` (calculated table)
One row per invoiced line (`supplier_invoices_detail`), enriched with PO/vendor/voucher context
via `SELECTCOLUMNS`. Combines the old PO-line-level proxy fields (`Qty Received (PO Line Total)`,
`Qty Outstanding`) with the new structural, invoice-line-specific match fields (`Qty Applied
(Structural)`, `Has Application (Structural)`, `Qty Unmatched (Structural)`) added in the P2P
rebuild.

Columns: `Vendor Number`, `Vendor Name`, `Voucher Number`, `PO Number`, `PO Line Number`, `SKU`,
`PO Unit Price`, `PO Currency`, `Qty Ordered`, `Qty Received (PO Line Total)`, `Qty Outstanding`,
`Qty Invoiced`, `PO Line Total`, `Invoice Number`, `Invoice Currency`, `Invoice Unit Price`,
`Invoice Line Total`, `Qty Applied (Structural)`, `Has Application (Structural)`, `Qty Unmatched
(Structural)`.

### 3.15 `_Measures`
Hidden table holding every general-purpose (non-table-specific) measure — see §5. Contains a
single hidden helper column (`Measures`) with no reporting purpose.

---

## 4. Relationships

18 relationships in total. All Many-to-One unless noted; direction is the standard "one side
filters many side" unless marked bothDirections.

| From (many) | To (one) | Active? | Cross-filter | Notes |
|---|---|---|---|---|
| purchase_orders.Vendor_ID | vendor_master.Vendor_ID | Yes | One direction | |
| purchase_orders.SKU_ID | sku_master.SKU_ID | Yes | One direction | Holds because of the `"GENERAL"` placeholder SKU |
| goods_receipts.Line_ID | purchase_orders.Line_ID | Yes | One direction | |
| supplier_invoices_detail.Line_ID | purchase_orders.Line_ID | Yes | One direction | |
| supplier_invoices_head.Vendor_ID | vendor_master.Vendor_ID | **No** | One direction | Deliberately inactive — see §9 |
| purchase_orders.Date | Dim_Date.Date | Yes | One direction | Only active date relationship |
| supplier_invoices_head.Invoice_Date | Dim_Date.Date | **No** | One direction | Inactive — see §9 |
| goods_receipts.Receipt_Date | Dim_Date.Date | **No** | One direction | Inactive — see §9 |
| supplier_invoices_detail.Inv_Date | Dim_Date.Date | **No** | One direction | Inactive — see §9 |
| purchase_orders.PO_ID | PO_Summary.PO_ID | Yes | **Both directions** | Needed so slicers on `vendor_master`/other dimensions reach `PO_Summary`-based measures (DIFOT %, etc.) |
| FX_Rates.Date | Dim_Date.Date | Yes | **Both directions** | 1:1 |
| supplier_invoices_detail.Voucher_Number | supplier_invoices_head.Voucher_Number | Yes | One direction | Real FK, replaces the old `Invoice_Number` business-key link |
| goods_receipt_applications.Invoice_Line_ID | supplier_invoices_detail.Invoice_Line_ID | Yes | One direction | |
| goods_receipt_applications.Receipt_ID | goods_receipts.Receipt_ID | **No** | One direction | Inactive — deactivated to avoid an ambiguous path via `purchase_orders`; `Applied_Qty_Total`/`Unvouchered Qty` columns use explicit `FILTER(ALL(...))` instead of relying on this |
| payments.Batch_ID | payment_batches.Batch_ID | Yes | One direction | |
| payments.Voucher_Number | supplier_invoices_head.Voucher_Number | Yes | One direction | |
| vendor_bank_accounts.Vendor_ID | vendor_master.Vendor_ID | Yes | One direction | |
| payments.Vendor_ID | vendor_master.Vendor_ID | Yes | One direction | |
| Invoice_Line_Reconciliation.'Vendor Number' | vendor_master.Vendor_ID | Yes | One direction | Added so the vendor slicer reaches the exception worklist table |

---

## 5. Measures

77 measures total, across 5 tables. Folder names below match the model's `displayFolder`
organization.

### 5.1 `_Measures` — "1. BAU Purchasing"
| Measure | DAX |
|---|---|
| Total PO Line Value | `SUMX(purchase_orders, Qty * Unit_Price)` |
| Total PO Count | `DISTINCTCOUNT(purchase_orders[PO_ID])` |
| Total PO Lines | `COUNTROWS(purchase_orders)` |
| Avg PO Line Value | `DIVIDE([Total PO Line Value], [Total PO Lines])` |
| Total Qty Ordered | `SUM(purchase_orders[Qty])` |
| Active Vendors | `DISTINCTCOUNT(purchase_orders[Vendor_ID])` |
| Total Qty Received | `SUM(goods_receipts[Qty_Received])` |
| Receipt Fulfilment % | `DIVIDE([Total Qty Received], [Total Qty Ordered])` |
| Memo Line % | `DIVIDE(CALCULATE(COUNTROWS(purchase_orders), memo = TRUE), [Total PO Lines])` |
| Total PO Line Value (AUD) | `SUM(purchase_orders[Line Value (AUD)])` — excludes EUR |
| Unconverted PO Value (EUR) | `CALCULATE(SUM(purchase_orders[Line Value (Local)]), Currency = "EUR")` |
| Top 5 Vendor Spend % | `DIVIDE(CALCULATE([Total PO Line Value (AUD)], TOPN(5, ALL(vendor_master[Vendor_ID]), CALCULATE([Total PO Line Value (AUD)]), DESC)), CALCULATE([Total PO Line Value (AUD)], ALL(vendor_master)))` |

### 5.2 `_Measures` — "2. Payables (AP)"
| Measure | DAX |
|---|---|
| Total Invoiced Ex GST | `CALCULATE(SUM(supplier_invoices_head[Goods_Total_Ex_GST]), USERELATIONSHIP(Invoice_Date, Dim_Date[Date]), USERELATIONSHIP(Vendor_ID, vendor_master[Vendor_ID]))` |
| Total Freight Charged | Same pattern, `SUM(Freight_Charged)` |
| Total GST Charged | Same pattern, `SUM(GST_Charged)` |
| Total Invoiced Inc GST | `[Total Invoiced Ex GST] + [Total Freight Charged] + [Total GST Charged]` |
| Invoice Count | `CALCULATE(COUNTROWS(supplier_invoices_head), USERELATIONSHIP(...) x2)` |
| Distinct Invoice Numbers | `CALCULATE(DISTINCTCOUNT(Invoice_Number), USERELATIONSHIP(...) x2)` |
| Avg Invoice Value | `DIVIDE([Total Invoiced Inc GST], [Invoice Count])` |
| Invoice Detail Lines | `COUNTROWS(supplier_invoices_detail)` |
| Avg Days PO to Invoice | `AVERAGEX(supplier_invoices_detail, DATEDIFF(RELATED(purchase_orders[Date]), Inv_Date, DAY))` |
| Total Invoiced (AUD, Inc GST) | `CALCULATE(SUM(Invoice Total Inc GST (AUD)), USERELATIONSHIP(...) x2)` — excludes EUR |
| Unconverted Invoice Value (EUR) | Same USERELATIONSHIP pattern, filtered to `Currency = "EUR"` |

> **Important pattern:** every AP measure that reads `supplier_invoices_head` and needs to respond
> to a vendor or date slicer explicitly invokes `USERELATIONSHIP` against the two relationships
> that are marked inactive in the model (§4) — this is how these measures correctly cross-filter
> despite the underlying relationships being off. See §9 for the three newer AP-aging measures
> that do **not** yet have this treatment.

### 5.3 `_Measures` — "3. Anomalies & Exceptions"
| Measure | DAX / Notes |
|---|---|
| Exception Line Count | `CALCULATE(COUNTROWS(supplier_invoices_detail), Invoice_Error_Type <> "NONE")` |
| Exception Rate % | `DIVIDE([Exception Line Count], [Invoice Detail Lines])` |
| Duplicate Invoice Line Count | `Invoice_Error_Type = "DUPLICATE_INVOICE"` count |
| Duplicate Invoice $ Exposure | Sum of `Qty_Inv * Inv_Price` for duplicate-tagged lines |
| Price Variance Line Count | `Invoice_Error_Type = "PRICE_VARIANCE"` count |
| Qty Over-Received Count | `Invoice_Error_Type = "QTY_OVER_RECEIVED"` count |
| No-Receipt Invoice Count | `Invoice_Error_Type = "NO_RECEIPT_INVOICE"` count |
| Currency Mismatch Count | `Invoice_Error_Type = "CURRENCY_MISMATCH"` count |
| Over PO Limit Count | `Invoice_Error_Type = "OVER_PO_LIMIT"` count |
| Backorder Split Count | `Invoice_Error_Type = "BACKORDER_SPLIT"` count |
| Vendors Sharing ABN (Count) | Vendors whose ABN appears more than once |
| GST Dropped Off Invoice Count | GST-registered vendor invoices with `GST_Charged = 0` |
| FX Rate Outlier PO Lines | `Applied_FX_Rate > 0.75` (outside the ~0.69–0.73 normal band) |
| GST Treatment Inclusive Flag Count | PO lines recorded `GST_Treatment = "Inclusive"` |
| FX Entry Error $ Impact (AUD) | Recorded-rate vs. correct-historical-rate AUD overstatement on USD lines |
| PO Data Quality Exception Count / Rate % | Composite: GST-inclusive flag OR FX outlier OR memo line |
| Total Price Variance $ (AUD) | `SUMX` of `(Invoiced Price - PO Price) x Qty`, AUD-converted |
| Head/Detail Mismatch Count / Rate % | Invoices where head total ≠ sum of detail lines |
| Head/Detail Variance $ (Local, Abs) | Sum of absolute head-vs-detail variance |
| Genuine Head/Detail Mismatch Count | Mismatch not explained by a currency difference |
| Currency-Caused Mismatch Count | Mismatch explained by a currency difference |

### 5.4 `_Measures` — "4. Three-Way Match & Outstanding"
| Measure | DAX / Notes |
|---|---|
| Fully Matched Lines % | `% of PO lines where Three-Way Match Status = "Fully Matched"` |
| Qty Mismatch Line Count | PO lines flagged `"Qty Mismatch"` |
| Received Not Yet Invoiced Count | PO lines flagged `"Received - Not Yet Invoiced"` (PO-line-level proxy — see §9 vs. `Fully Unvouchered Receipt Count`) |
| Open Lines Count | PO lines with any unreceived quantity |
| Fully Outstanding Lines Count | PO lines with zero receipts at all |
| Total Open Qty / Total Open Value (AUD) | Sums restricted to lines with open quantity |
| Unconverted Open Value (EUR) | EUR open value, unconverted |
| Avg Open Order Age (Days) | Average age (vs. today) of still-open lines |
| Open PO Count / Closed PO Count / Open PO % | PO-level rollup, from `PO_Summary[PO Status]` |

### 5.5 `_Measures` — "5. Vendor & Product Performance"
| Measure | DAX / Notes |
|---|---|
| Avg Lead Time (Days) | `AVERAGE(purchase_orders[Lead Time (Days)])` |
| Lead Time StdDev (Days) | `STDEV.P(purchase_orders[Lead Time (Days)])` |
| Total PPV (AUD) / Avg PPV % | Purchase Price Variance vs. SKU standard price |
| Delivered In Full % | `% of POs (PO_Summary) where PO Delivered In Full = TRUE` |
| On Time Delivery % | `% of POs where PO Delivered On Time = TRUE` |
| DIFOT % | `% of POs where PO DIFOT = TRUE` — true Delivered-In-Full-On-Time |

### 5.6 `goods_receipts` — "Three-Way Match"
`Over-Applied Receipt Count`, `Total Unapplied Receipt Qty` (net, signed), `Unvouchered Receipt
Count`, `Fully Unvouchered Receipt Count`, `Total Unvouchered Qty`, `Total Unvouchered Value
(AUD)`, `Unconverted Unvouchered Value (EUR)` — full DAX in §3.5.

### 5.7 `supplier_invoices_detail` — "Three-Way Match"
`Unmatched Invoice Lines (Structural)`, `Structural Over-Invoiced Line Count` — full DAX in §3.7.

### 5.8 `supplier_invoices_head` — "AP Aging"
`Unpaid Voucher Count`, `Outstanding Payable (AUD)`, `Avg Days To Pay` — full DAX in §3.6. **Note:**
these do not use `USERELATIONSHIP` — see §9.

### 5.9 `payments` — "Bank Account Fraud"
`Total Payments (AUD)`, `Bank Account Mismatch Count`, `Bank Account Fraud Count (Never Valid)`,
`Bank Account Superseded Count`, `$ At Risk (Bank Account Mismatch, AUD)` — full DAX in §3.10.

---

## 6. Report Pages

4 pages, each 1920×1080 ("Fit to Page"), sharing a common layout: a left filter rail (two stacked
slicers, 220px wide), a KPI card row, and a chart + table row.

### 6.1 Executive Overview
- **Slicers:** `Dim_Date[Financial Year Label]`, `vendor_master[Vendor_Name]`
- **Cards (6):** Total PO Line Value (AUD), Total Invoiced (AUD, Inc GST), Total Payments (AUD),
  Outstanding Payable (AUD), Active Vendors, Exception Rate %
- **Chart:** line chart, Category = `Dim_Date[Year Month]`, Y = Total PO Line Value (AUD) +
  Total Invoiced (AUD, Inc GST) — two series, coloured `#2f7a5d` / `#5ba882`

### 6.2 Three-Way Match & Exceptions
- **Slicers:** `vendor_master[Vendor_Name]`, `Invoice_Line_Reconciliation[Has Application (Structural)]`
- **Cards (5, red `#b93a3a`):** Unmatched Invoice Lines (Structural), Structural Over-Invoiced
  Line Count, Over-Applied Receipt Count, Unvouchered Receipt Count, Total Unvouchered Value (AUD)
- **Chart:** bar chart, Category = Vendor_Name, Y = Exception Line Count (red), sorted descending
- **Table:** `Invoice_Line_Reconciliation` — Vendor Name, Voucher Number, PO Number, Qty Invoiced,
  Qty Applied (Structural), Has Application (Structural), Qty Unmatched (Structural), sorted by
  Qty Unmatched descending (worst exceptions first)

### 6.3 Bank Account Fraud & Payments
- **Slicers:** `payments[Bank_Account_Status]`, `vendor_master[Vendor_Name]`
- **Cards (5):** Bank Account Mismatch Count, Bank Account Fraud Count (Never Valid), Bank
  Account Superseded Count, $ At Risk (Bank Account Mismatch, AUD) — all red; Total Payments
  (AUD) — default theme colour
- **Chart:** bar chart, Category = Vendor_Name, Y = $ At Risk (Bank Account Mismatch, AUD) (red),
  sorted descending
- **Table:** `payments` — Payment_ID, Vendor Name, Payment_Date, Payment_Bank_Account,
  Bank_Account_Status, Payment_Amount_AUD, sorted by status ascending (fraud/superseded float to
  top) then amount descending

### 6.4 AP Aging & Vendor Performance
- **Slicers:** `vendor_master[Vendor_Name]`, `Dim_Date[Financial Year Label]`
- **Cards (6):** Unpaid Voucher Count, Outstanding Payable (AUD), Avg Days To Pay — default
  colour; DIFOT %, On Time Delivery %, Delivered In Full % — green `#1f7a4a`
- **Chart:** bar chart, Category = Vendor_Name, Y = DIFOT % (green), sorted descending
- **Table:** `PO_Summary` — PO_ID, Vendor_ID, PO Status, PO Value (AUD), Open Value (AUD), PO
  DIFOT, sorted by PO Value descending

---

## 7. Theme & Styling

Palette sourced directly from the site's `styles.css` custom properties:

| Token | Hex | Source |
|---|---|---|
| Accent / good | `#2f7a5d` | `--accent` |
| Background | `#fbfdf9` | `--surface` |
| Secondary background | `#f4f7f2` | `--bg` |
| Border / light | `#dce8dc` | `--border` |
| Text | `#25342a` | `--text` |
| Muted text | `#5f6f63` | `--muted` |
| Accent soft | `#eaf6ee` | `--accent-soft` |
| Good (KPI) | `#1f7a4a` | `.metric-value.positive` |
| Bad (KPI) | `#b93a3a` | `.macro-status--error` |

Semantic colour convention applied across the report: **red** on exception/fraud-count cards and
charts, **green** on positive delivery-performance cards and charts, default theme accent on
purely informational totals.

---

## 8. Known Limitations

These are genuine, documented gaps in the current model, not oversights to be silently ignored:

1. **`supplier_invoices_head → vendor_master` relationship is inactive.** Reactivating it creates
   an ambiguous path (`supplier_invoices_detail → purchase_orders → vendor_master` vs.
   `supplier_invoices_detail → supplier_invoices_head → vendor_master`) that the Analysis Services
   engine hard-rejects at load time (confirmed by testing — Desktop refused to open the file).
   Most of the older AP measures work around this correctly via explicit `USERELATIONSHIP()` calls
   (see §5.2) — but the three newer AP-aging measures (`Unpaid Voucher Count`, `Outstanding
   Payable (AUD)`, `Avg Days To Pay` on `supplier_invoices_head`) do **not** yet have this
   treatment, so they don't respond to a vendor slicer. Applying the same `USERELATIONSHIP`
   pattern to these three measures is a safe, low-risk fix that doesn't touch the relationship
   graph at all — a good next step.

2. **`Dim_Date` is a role-playing dimension with only one active leg.** Four tables could
   reasonably relate to `Dim_Date` (PO date, invoice date, receipt date, invoice-line date), but
   only `purchase_orders.Date` is active — the other three are inactive for the same ambiguity
   reason as above. Slicers on `Dim_Date` (e.g. the Financial Year Label slicers on Executive
   Overview and AP Aging) therefore only filter PO-related figures directly; other date-based
   measures rely on their own explicit `USERELATIONSHIP` calls rather than slicer interaction. A
   full fix would mean building 2–3 dedicated role-playing date tables — a genuine modeling task,
   not a quick patch.

3. **`Three-Way Match Status` (on `purchase_orders`) is a PO-line-level proxy** that predates the
   `goods_receipt_applications` rebuild. It compares *cumulative* received/invoiced quantities per
   PO line, not the actual receipt a specific invoice line claims against — so it can call a line
   "invoiced" even if only one of several receipts against it has actually been matched. The
   newer, more precise structural facts (`Has_Application`, `Qty_Unmatched` on
   `supplier_invoices_detail`; `Unvouchered Qty` on `goods_receipts`) supersede it for exception
   reporting; it's retained because `PO_Summary`'s `Lines Fully Matched` column still depends on
   it for PO-level rollups.

4. **`Invoice_Error_Type` is a ground-truth label**, generated by the source Python script to mark
   which synthetic chaos case each invoice line represents. It's kept for build-time verification
   only — reports are designed to surface the same findings structurally (from
   `goods_receipt_applications`), not by reading this label, matching the original design intent.
