Synthetic Procurement Dataset Generator
A Python script that generates a complex, multi‑table synthetic dataset designed to simulate a high‑risk corporate procurement environment. It is engineered specifically for data auditing, financial reporting, and the development of internal control dashboards within a portfolio context.

📦 Overview
This script produces a relational database schema consisting of six interconnected CSV files:

sku_master

vendor_master

purchase_order_lines_au_chaos

goods_receipts

supplier_invoices

forex_rates

By programmatically linking these tables through unique identifiers, the script enables advanced analytical exercises such as three‑way matching—cross‑referencing purchase orders, receiving documents, and supplier invoices to verify payment accuracy.

🧠 Key Design Reasoning
To move beyond simplistic datasets, this script intentionally injects realistic “dirty data” and financial anomalies common in poorly managed purchasing departments. These inclusions allow a user to demonstrate their ability to detect and remediate systemic internal control weaknesses.

Financial & Compliance Auditing
GST Mismanagement  
In an Australian context, the script simulates errors in GST treatment, where items are incorrectly toggled between GST‑inclusive (price includes tax) and GST‑exclusive (tax not yet added). It also randomly injects 10% overpayments on invoices to simulate double‑counting of GST liabilities.

Bank Account Fraud  
To simulate phishing or internal fraud, a subset of invoices contains bank account numbers that differ from the system’s approved vendor master records.

Operational & Data Integrity
Master Data Chaos  
Intentional typos in product descriptions and fragmented spend categories (e.g., duplicated SKUs under varying names) test data‑cleaning skills.

Foreign Exchange (FX) Anomalies  
Using authentic 2026 AUD/USD historical exchange rate ranges, the script applies incorrect conversion rates on specific dates, reflecting manual entry errors and currency conversion exploits.

“Bag of Stuff” Procurement  
Generates vague, bulk‑pack descriptions (e.g., “Assorted Materials”) rather than unit‑based specifics, highlighting a common loss vector where goods received cannot be accurately verified.

Logistics & Reporting
Order Lifecycle Tracking  
The dataset includes various line statuses such as “Overdue,” “Partially Received,” and “Cancelled,” with associated reason codes (e.g., PORT_CONGESTION, SUPPLIER_STOCKOUT).

📊 Portfolio Value
By utilizing this script, a practitioner can build reports that surface critical corporate leakage points, such as:

DIFOT (Delivered In Full, On Time) failures

Price variances

Unauthorized payment diversions

This demonstrates a deep understanding of both technical data engineering and essential financial internal controls.

🚀 Getting Started
Requirements
Python 3.x

Standard libraries (e.g., csv, random, datetime)

Optional: pandas for analysis

Running the Script
bash
python generate_procurement_dataset.py
This will output all six CSV files into the working directory.

📁 Output Files
File Name	Description
sku_master.csv	SKU-level product metadata with intentional inconsistencies
vendor_master.csv	Supplier records including fraudulent bank account variations
purchase_order_lines_au_chaos.csv	PO lines with lifecycle statuses and anomalies
goods_receipts.csv	Receiving records including partial and overdue deliveries
supplier_invoices.csv	Invoices with GST errors and overpayment injections
forex_rates.csv	AUD/USD FX rates with intentional miscalculations


📝 Notes
This dataset is intentionally chaotic. It is designed for:

Internal audit simulations

Data engineering practice

Dashboard development

Fraud detection exercises

Master data cleanup demonstrations