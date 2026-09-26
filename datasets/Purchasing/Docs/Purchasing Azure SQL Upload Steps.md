# Purchasing → Azure SQL Upload — Steps

How the `purchasing` schema in Azure SQL gets created and (re)loaded from the CSVs in
[`datasets/Purchasing/Data`](../Data), using the scripts in
[`datasets/Purchasing/Scripts`](../Scripts). This is the template for the equivalent
Legal, Health, and Retail scripts — same shape, different schema name and source files.

## Target

- Server: `3sheets.database.windows.net` (Azure SQL logical server `3sheets`)
- Database: `3sheets.db.sql` (one database, shared across domains)
- Schema: `purchasing` (see [Purchasing schema.md](Purchasing%20schema.md) for table/column definitions,
  and [purchasing_schema_diagram.html](purchasing_schema_diagram.html) for the ER diagram)

## One-time machine setup

1. **Azure CLI** — installed via `winget install --id Microsoft.AzureCLI --exact`. Run `az login`
   and sign in with an account that has access to the `au.3sheets.qld` resource group.
2. **ODBC Driver 18 for SQL Server** — installed via `winget install --id Microsoft.msodbcsql.18
   --exact`. Required for `pyodbc` to connect to Azure SQL; the older built-in "SQL Server"
   driver is not sufficient.
3. **Firewall rule** — Azure SQL blocks all inbound connections by default. Your current public
   IP must be added to the `3sheets` server's allow list:
   ```
   az sql server firewall-rule create --resource-group "au.3sheets.qld" --server "3sheets" \
     --name "<your-name>-dev" --start-ip-address <your-ip> --end-ip-address <your-ip>
   ```
   Find your current IP with `Invoke-RestMethod -Uri "https://api.ipify.org"` (PowerShell) or
   any "what's my IP" service. **If a load fails with a firewall/access-denied error later, this
   is the most likely cause** — home/mobile connections often have a dynamic IP that changes
   over time and needs the rule re-added.
6. **Serverless auto-pause** — `3sheets.db.sql` runs on the Serverless tier (`GP_S_Gen5`,
   60-minute auto-pause). A `pyodbc.OperationalError` / SQLSTATE `08001` TCP timeout (not an
   auth error) on the *first* connection after a period of inactivity usually means the database
   was paused and is resuming — `azure_sql_connection.py` uses a 90s connection timeout to cover
   this, but if it still times out, just retry once; the resume continues in the background and
   the next attempt is fast. Check current status with:
   ```
   az sql db show --resource-group "au.3sheets.qld" --server "3sheets" --name "3sheets.db.sql" \
     --query "{status:status, autoPauseDelay:autoPauseDelay}"
   ```
4. **Credentials** — copy [`.env.example`](../../../.env.example) (repo root) to `.env` (repo
   root, gitignored) and fill in `AZURE_SQL_PASSWORD`. Server/database/user are already filled in.
5. **Python packages** — installed globally on this machine (no per-project venv):
   ```
   python -m pip install -r requirements.txt
   ```
   run from `datasets/Purchasing/Scripts`. See [requirements.txt](../Scripts/requirements.txt).

## Files

- [`purchasing_tables.py`](../Scripts/purchasing_tables.py) — single source of truth for every
  table's columns, SQL types, and Python cast functions. Manually defined and reviewed, never
  inferred from the CSVs. Edit this file to change a column's type; both scripts below read it.
- [`azure_sql_connection.py`](../Scripts/azure_sql_connection.py) — shared connection helper
  (reads `.env`, builds the pyodbc connection string). No table/type logic lives here.
- [`create_purchasing_schema.py`](../Scripts/create_purchasing_schema.py) — idempotent. Creates
  the `purchasing` schema, each table, and each `FOREIGN KEY` constraint **only if missing**.
  FKs are added in a second pass after every table exists, so table-creation order never has to
  match FK dependency order. Never drops or alters existing objects.
- [`load_purchasing_data.py`](../Scripts/load_purchasing_data.py) — destructive per table.
  Clears every table (children before parents, to respect the FK constraints), then reloads
  every row from its CSV. Tables nothing references (`vendor_bank_accounts`,
  `goods_receipt_applications`, `payments`) are `TRUNCATE`d; the 7 FK-referenced tables
  (`vendor_master`, `sku_master`, `purchase_orders`, `goods_receipts`,
  `supplier_invoices_head`, `supplier_invoices_detail`, `payment_batches`) use `DELETE` instead,
  since SQL Server refuses `TRUNCATE` on any table an FK constraint points at. No table in this
  schema has an `IDENTITY` column any more — every primary key is a natural business key, so
  `TRUNCATE`'s identity-seed reset is not a concern either way. Run `create_purchasing_schema.py`
  first if the tables don't exist yet.

## Running it

From `datasets/Purchasing/Scripts`:

```
python create_purchasing_schema.py
python load_purchasing_data.py
```

`create_purchasing_schema.py` prints which schema/tables it created vs. skipped (already
existing). `load_purchasing_data.py` prints a row count per table as it loads, then re-queries
Azure SQL to confirm the counts match.

## Known judgment calls

These were explicit decisions made while defining `purchasing_tables.py` — flagged here so
they're easy to revisit:

- `GST_Registered` (`vendor_master`) and `memo` (`purchase_orders`) are the only two
  True/False-shaped columns in this schema; both are stored as genuine `BIT`, matching what the
  source generator actually produces.
- Every table's primary key is a **natural business key generated by `Purchasing.py`** — there
  are no `IDENTITY` columns anywhere in this schema. `supplier_invoices_head` and
  `supplier_invoices_detail` used to need a SQL-generated surrogate key because
  `Invoice_Number` isn't unique; that was replaced 2026-08-20 by generating a real business key
  in Python instead (`Voucher_Number` for the head, `Invoice_Line_ID` for the detail), so
  CSV/SQL/Power BI can all reference the same stable ID without needing a post-insert
  `IDENTITY` value. See "Full P2P rebuild" below.
- All other tables use their natural single-column ID as primary key (`Vendor_ID`, `SKU_ID`,
  `Line_ID`, `Receipt_ID`, `Batch_ID`, `Payment_ID`), or a natural composite key where a single
  column isn't enough (`vendor_bank_accounts`: `Vendor_ID` + `Effective_Start_Date`;
  `goods_receipt_applications`: `Invoice_Line_ID` + `Receipt_ID`).
- **All 11 relationships in the schema are real, always-holding `FOREIGN KEY` constraints** —
  see the "Foreign keys" section in [Purchasing schema.md](Purchasing%20schema.md) for the full
  list. There is no business-key-only, FK-unenforceable link left in this schema; the old
  `Invoice_Number`-based head/detail link (which could never be a real FK, since
  `Invoice_Number` is intentionally non-unique) was replaced by the `Voucher_Number` FK as part
  of the rebuild below.
- **Full P2P rebuild (2026-08-20):** the schema went from 6 tables to 10, adding
  `vendor_bank_accounts`, `goods_receipt_applications`, `payment_batches`, and `payments`. This
  was a full architectural change, not an incremental patch — driven by the goal of making the
  Power BI reports demonstrate genuine procure-to-pay controls (three-way match, duplicate-invoice
  detection, bank-account-change fraud detection) backed by real matching/payment data, not
  synthetic labels. Details, rationale, and the exact new fields are in
  [Purchasing schema.md](Purchasing%20schema.md). Azure SQL was fully dropped and recreated
  against the new `purchasing_tables.py`; Power BI's semantic model was rebuilt table-by-table
  (old tables' M sources repointed, `Invoice_Number`-based relationship removed and replaced with
  `Voucher_Number`, 4 new tables and their relationships added) and verified refresh-clean with
  row counts matching Azure SQL exactly at every step.
- **Renamed and extended (2026-08-20, prior pass):** `purchase_orders_au_chaos` → `purchase_orders`.
  `sku_master` gained `Days_To_Deliver`; `purchase_orders` gained `Expected_Delivery_Date` —
  together these support a real DIFOT "on time" measure, not just "in full."
