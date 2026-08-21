"""Explicit column/type definitions for the `purchasing` schema.

Single source of truth used by both create_purchasing_schema.py and
load_purchasing_data.py, so the two can't drift out of sync. Types are
manually specified here (not inferred from the CSVs) — review before running
either script against real data.

Each Column has:
  name     - column name, matches the CSV header exactly
  sql_type - T-SQL type used in CREATE TABLE
  py_cast  - function applied to the raw CSV string value before insert
             (None means "pass the raw string through unchanged")
"""

from dataclasses import dataclass, field
from datetime import date, datetime

SCHEMA_NAME = "purchasing"


def to_date(value: str) -> date | None:
    if value in (None, ""):
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def to_decimal_str(value: str) -> str | None:
    # pyodbc accepts numeric strings for DECIMAL params; keep as str to avoid
    # float rounding on the way in.
    if value in (None, ""):
        return None
    return value


def to_bool(value: str) -> bool | None:
    if value in (None, ""):
        return None
    return value.strip().lower() in ("true", "1", "yes")


def to_int(value: str) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


@dataclass
class Column:
    name: str
    sql_type: str
    py_cast: object = None


@dataclass
class ForeignKey:
    columns: list[str]
    ref_table: str
    ref_columns: list[str]


@dataclass
class Table:
    name: str
    csv_file: str
    columns: list[Column]
    primary_key: list[str] = field(default_factory=list)
    # Set when the table has no natural unique key (or combination of one) in
    # the source data. SQL Server generates this value on insert - it is not
    # read from the CSV and load_purchasing_data.py must not supply it.
    identity_column: str | None = None
    foreign_keys: list[ForeignKey] = field(default_factory=list)


TABLES: list[Table] = [
    Table(
        name="vendor_master",
        csv_file="vendor_master.csv",
        primary_key=["Vendor_ID"],  # one row per vendor in the generator - safe as PK
        columns=[
            Column("Vendor_ID", "NVARCHAR(50)"),
            Column("Vendor_Name", "NVARCHAR(255)"),
            Column("ABN", "NVARCHAR(20)"),
            Column("System_Currency", "NVARCHAR(10)"),
            Column("Country", "NVARCHAR(50)"),
            # CSV writes GST_Registered as Python True/False -> "True"/"False" text
            Column("GST_Registered", "BIT", to_bool),
        ],
    ),
    Table(
        # Added 2026-08-20, replacing vendor_master.Approved_Bank_Account.
        # Bank details are effective-dated here specifically so a vendor can
        # have more than one over time - that's what makes a bank-account-
        # change fraud pattern detectable: comparing a payment's date against
        # which account was genuinely on file *then*, not just "now".
        name="vendor_bank_accounts",
        csv_file="vendor_bank_accounts.csv",
        primary_key=["Vendor_ID", "Effective_Start_Date"],
        foreign_keys=[
            ForeignKey(["Vendor_ID"], "vendor_master", ["Vendor_ID"]),
        ],
        columns=[
            Column("Vendor_ID", "NVARCHAR(50)"),
            Column("Bank_Account", "NVARCHAR(50)"),
            Column("Effective_Start_Date", "DATE", to_date),
            # NULL = still the current account. Nullable by default (no
            # NOT NULL applied anywhere in this schema).
            Column("Effective_End_Date", "DATE", to_date),
        ],
    ),
    Table(
        name="sku_master",
        csv_file="sku_master.csv",
        primary_key=["SKU_ID"],  # one row per SKU in the generator - safe as PK
        columns=[
            Column("SKU_ID", "NVARCHAR(50)"),
            Column("SKU_Description", "NVARCHAR(255)"),
            Column("Category", "NVARCHAR(100)"),
            Column("Typical_Unit_Price", "DECIMAL(18,4)", to_decimal_str),
            # Agreed/standard lead time in days - the DIFOT "on time" benchmark.
            # The placeholder SKU_ID="GENERAL" row gets a fixed default (14)
            # rather than a random value.
            Column("Days_To_Deliver", "INT", to_int),
        ],
    ),
    Table(
        # Renamed from purchase_orders_au_chaos 2026-08-20.
        name="purchase_orders",
        csv_file="purchase_orders.csv",
        primary_key=["Line_ID"],  # doc names this the PK; generator emits one row per line
        foreign_keys=[
            ForeignKey(["Vendor_ID"], "vendor_master", ["Vendor_ID"]),
            # Holds because Purchasing.py now writes a placeholder SKU_ID =
            # "GENERAL" row into sku_master for memo lines - see sku_master.
            ForeignKey(["SKU_ID"], "sku_master", ["SKU_ID"]),
        ],
        columns=[
            Column("Line_ID", "NVARCHAR(50)"),
            Column("PO_ID", "NVARCHAR(50)"),
            Column("Date", "DATE", to_date),
            Column("Vendor_ID", "NVARCHAR(50)"),
            Column("SKU_ID", "NVARCHAR(50)"),
            Column("Line_Description", "NVARCHAR(255)"),
            Column("memo", "BIT", to_bool),
            Column("Qty", "DECIMAL(18,4)", to_decimal_str),
            Column("Unit_Price", "DECIMAL(18,4)", to_decimal_str),
            Column("Currency", "NVARCHAR(10)"),
            Column("GST_Treatment", "NVARCHAR(50)"),
            Column("Applied_FX_Rate", "DECIMAL(18,6)", to_decimal_str),
            # PO Date + the SKU's Days_To_Deliver - promised delivery date,
            # supports the DIFOT "on time" measure.
            Column("Expected_Delivery_Date", "DATE", to_date),
        ],
    ),
    Table(
        name="goods_receipts",
        csv_file="goods_receipts.csv",
        primary_key=["Receipt_ID"],  # generator always suffixes -1/-2, unique per line
        foreign_keys=[
            ForeignKey(["Line_ID"], "purchase_orders", ["Line_ID"]),
        ],
        columns=[
            Column("Receipt_ID", "NVARCHAR(50)"),
            Column("Line_ID", "NVARCHAR(50)"),
            Column("Receipt_Date", "DATE", to_date),
            Column("Qty_Received", "DECIMAL(18,4)", to_decimal_str),
        ],
    ),
    Table(
        # Restructured 2026-08-20: Voucher_Number is now the primary key,
        # not Invoice_Number. This is how a real AP system actually works -
        # the vendor's own invoice number is just a field on the voucher,
        # never guaranteed unique. It's deliberately NOT unique here either:
        # the DUPLICATE_INVOICE case is the same Invoice_Number keyed into
        # the AP system twice, as two different vouchers.
        name="supplier_invoices_head",
        csv_file="supplier_invoices_head.csv",
        primary_key=["Voucher_Number"],
        foreign_keys=[
            ForeignKey(["Vendor_ID"], "vendor_master", ["Vendor_ID"]),
        ],
        columns=[
            Column("Voucher_Number", "NVARCHAR(50)"),
            Column("Invoice_Number", "NVARCHAR(50)"),  # intentionally not unique
            Column("Vendor_ID", "NVARCHAR(50)"),
            Column("Invoice_Date", "DATE", to_date),
            Column("Currency", "NVARCHAR(10)"),
            Column("Goods_Total_Ex_GST", "DECIMAL(18,4)", to_decimal_str),
            Column("Freight_Charged", "DECIMAL(18,4)", to_decimal_str),
            Column("GST_Charged", "DECIMAL(18,4)", to_decimal_str),
        ],
    ),
    Table(
        # Restructured 2026-08-20: Invoice_Line_ID is a real business key
        # generated in Purchasing.py (not a SQL-generated IDENTITY), so it's
        # portable and can be referenced by goods_receipt_applications
        # without depending on load-time-assigned surrogate values. Now that
        # supplier_invoices_head has a genuine unique PK (Voucher_Number),
        # the head/detail link is a real FOREIGN KEY too - no more
        # business-key-only workaround.
        name="supplier_invoices_detail",
        csv_file="supplier_invoices_detail.csv",
        primary_key=["Invoice_Line_ID"],
        foreign_keys=[
            ForeignKey(["Voucher_Number"], "supplier_invoices_head", ["Voucher_Number"]),
            ForeignKey(["Line_ID"], "purchase_orders", ["Line_ID"]),
        ],
        columns=[
            Column("Invoice_Line_ID", "NVARCHAR(50)"),
            Column("Voucher_Number", "NVARCHAR(50)"),
            Column("Invoice_Number", "NVARCHAR(50)"),  # descriptive copy from head, not a key
            Column("Vendor_ID", "NVARCHAR(50)"),
            Column("PO_ID", "NVARCHAR(50)"),
            Column("Line_ID", "NVARCHAR(50)"),
            Column("Inv_Date", "DATE", to_date),
            Column("Qty_Inv", "DECIMAL(18,4)", to_decimal_str),
            Column("Inv_Price", "DECIMAL(18,4)", to_decimal_str),
            Column("Inv_Currency", "NVARCHAR(10)"),
            Column("Invoice_Error_Type", "NVARCHAR(50)"),
        ],
    ),
    Table(
        # Added 2026-08-20 - the actual goods-receipt-to-invoice matching
        # record a real AP clerk produces. This is what makes
        # NO_RECEIPT_INVOICE / QTY_OVER_RECEIVED derivable facts (zero
        # application rows / invoiced qty exceeding applied qty) instead of
        # a label with nothing backing it.
        name="goods_receipt_applications",
        csv_file="goods_receipt_applications.csv",
        primary_key=["Invoice_Line_ID", "Receipt_ID"],
        foreign_keys=[
            ForeignKey(["Invoice_Line_ID"], "supplier_invoices_detail", ["Invoice_Line_ID"]),
            ForeignKey(["Receipt_ID"], "goods_receipts", ["Receipt_ID"]),
        ],
        columns=[
            Column("Invoice_Line_ID", "NVARCHAR(50)"),
            Column("Receipt_ID", "NVARCHAR(50)"),
            Column("Qty_Applied", "DECIMAL(18,4)", to_decimal_str),
        ],
    ),
    Table(
        # Added 2026-08-20. A payment run pays a batch of vouchers together
        # on a given date - this is the batch header. Deliberately has no
        # pre-computed total: batches can span currencies, and this project's
        # convention is to compute currency-aware totals at report time, not
        # bake a misleading mixed-currency sum into the source data.
        name="payment_batches",
        csv_file="payment_batches.csv",
        primary_key=["Batch_ID"],
        columns=[
            Column("Batch_ID", "NVARCHAR(50)"),
            Column("Batch_Date", "DATE", to_date),
        ],
    ),
    Table(
        # Added 2026-08-20 - voucher-level payment detail. Payment_Bank_Account
        # is the account this specific payment actually went to; compare
        # against vendor_bank_accounts (effective-dated) to find payments
        # sent somewhere that was never valid for that vendor (redirection
        # fraud) or that was valid once but has since been superseded.
        name="payments",
        csv_file="payments.csv",
        primary_key=["Payment_ID"],
        foreign_keys=[
            ForeignKey(["Batch_ID"], "payment_batches", ["Batch_ID"]),
            ForeignKey(["Voucher_Number"], "supplier_invoices_head", ["Voucher_Number"]),
            ForeignKey(["Vendor_ID"], "vendor_master", ["Vendor_ID"]),
        ],
        columns=[
            Column("Payment_ID", "NVARCHAR(50)"),
            Column("Batch_ID", "NVARCHAR(50)"),
            Column("Voucher_Number", "NVARCHAR(50)"),
            Column("Vendor_ID", "NVARCHAR(50)"),
            Column("Payment_Date", "DATE", to_date),
            Column("Payment_Bank_Account", "NVARCHAR(50)"),
            Column("Payment_Amount", "DECIMAL(18,4)", to_decimal_str),
            Column("Payment_Currency", "NVARCHAR(10)"),
        ],
    ),
]
