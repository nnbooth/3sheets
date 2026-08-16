# Purchasing Domain Documentation

## Overview
This document outlines best‑practice data engineering and financial‑controls documentation for the Purchasing domain. It covers table definitions, field‑level guidance, and recommended SQL data types based on the provided dataset. This documentation is intended to support ingestion into Azure SQL via Python.

---

## Schema: `purchasing`
All tables in this domain reside under the `purchasing` schema. This keeps procurement data logically separated from other business domains.

---

## Table: `goods_receipts`
Represents physical receipt of goods against purchase order lines.

### Fields
- **Receipt_ID** — NVARCHAR(50)  
  Unique identifier for the goods receipt. Often contains prefixes and non‑numeric characters.

- **Line_ID** — NVARCHAR(50)  
  Foreign key to purchase order lines.

- **Receipt_Date** — DATE  
  Date goods were received.

- **Qty_Received** — DECIMAL(18,4)  
  Quantity received for the line. Supports fractional receipts (e.g., partial pallets, partial bulk units).

---

## Table: `purchase_orders_au_chaos`
Core purchasing table containing PO lines, lifecycle chaos, FX anomalies, GST mismanagement, and vendor mismatches.

### Fields
- **Line_ID** — NVARCHAR(50)  
  Primary key for PO line.

- **PO_ID** — NVARCHAR(50)  
  Purchase order identifier.

- **Date** — DATE  
  PO creation date.

- **Vendor_ID** — NVARCHAR(50)  
  Supplier identifier.

- **SKU_ID** — NVARCHAR(50)  
  SKU identifier.

- **Line_Description** — NVARCHAR(255)  
  Description of the purchased item.

- **memo** — NVARCHAR(255)  
  Additional notes.

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

---

## Table: `sku_master`
Master data for SKUs, including intentional chaos.

### Fields
- **SKU_ID** — NVARCHAR(50)  
  SKU identifier.

- **SKU_Description** — NVARCHAR(255)  
  Description of the SKU.

- **Category** — NVARCHAR(100)  
  Category grouping.

- **Typical_Unit_Price** — DECIMAL(18,4)  
  Typical price.

---

## Table: `supplier_invoices_detail`
Line‑level invoice detail used for three‑way match, fraud detection, and GST/FX anomalies.

### Fields
- **Invoice_Number** — NVARCHAR(50)  
  Invoice identifier.

- **Vendor_ID** — NVARCHAR(50)  
  Supplier identifier.

- **PO_ID** — NVARCHAR(50)  
  Purchase order identifier.

- **Line_ID** — NVARCHAR(50)  
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
  Error classification.

---

## Table: `supplier_invoices_head`
Header‑level invoice data for financial reporting and fraud detection.

### Fields
- **Invoice_Number** — NVARCHAR(50)  
  Invoice identifier.

- **Vendor_ID** — NVARCHAR(50)  
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

## Table: `vendor_master`
Supplier metadata including fraud‑simulation bank accounts.

### Fields
- **Vendor_ID** — NVARCHAR(50)  
  Supplier identifier.

- **Vendor_Name** — NVARCHAR(255)  
  Supplier name.

- **Approved_Bank_Account** — NVARCHAR(50)  
  Approved bank account.

- **ABN** — NVARCHAR(20)  
  Australian Business Number.

- **System_Currency** — NVARCHAR(10)  
  Supplier currency.

- **Country** — NVARCHAR(50)  
  Supplier country.

- **GST_Registered** — NVARCHAR(10)  
  GST registration status.

---

## Notes
- All ID fields are stored as strings for consistency and flexibility.
- Dates use the DATE type for clean ingestion and reporting.
- Monetary values use DECIMAL(18,4) or DECIMAL(18,6) depending on precision requirements.
- Quantity fields use DECIMAL(18,4) to support fractional units.
- Text fields use NVARCHAR to support international characters.


