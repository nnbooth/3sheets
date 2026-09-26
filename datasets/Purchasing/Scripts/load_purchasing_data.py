"""Clear and reload every table in the `purchasing` schema from its CSV.

Clear phase runs in reverse of TABLES order (children before parents), so
FK-referenced tables (vendor_master, sku_master, purchase_orders)
never have dangling child rows when they're cleared. SQL Server also refuses
TRUNCATE on any table an FK constraint references - regardless of whether
the referencing table is already empty - so those three use DELETE instead;
tables nothing references keep TRUNCATE (cheaper, resets IDENTITY seeds).

Reload phase runs in TABLES order (already parent-first, matching what the
FK constraints require) and inserts every row from the matching CSV using
the explicit column/type/cast definitions in purchasing_tables.py - nothing
is inferred from the CSV.

Run create_purchasing_schema.py first if the schema/tables don't exist yet.
"""

import csv
from pathlib import Path

from azure_sql_connection import get_connection
from purchasing_tables import SCHEMA_NAME, TABLES, Table

DATA_DIR = Path(__file__).resolve().parent.parent / "Data"

# Tables any foreign_keys entry points at - TRUNCATE is not allowed on these.
FK_REFERENCED_TABLES = {fk.ref_table for table in TABLES for fk in table.foreign_keys}


def load_rows(table: Table) -> list[dict[str, str]]:
    csv_path = DATA_DIR / table.csv_file
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing source file: {csv_path}")
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def cast_row(table: Table, row: dict[str, str]) -> list:
    values = []
    for column in table.columns:
        raw = row.get(column.name, "")
        raw = None if raw == "" else raw
        values.append(column.py_cast(raw) if column.py_cast else raw)
    return values


def clear_table(cursor, table: Table) -> None:
    if table.name in FK_REFERENCED_TABLES:
        cursor.execute(f"DELETE FROM [{SCHEMA_NAME}].[{table.name}]")
    else:
        cursor.execute(f"TRUNCATE TABLE [{SCHEMA_NAME}].[{table.name}]")


def load_table(cursor, table: Table) -> int:
    rows = load_rows(table)
    if not rows:
        return 0

    columns_sql = ", ".join(f"[{c.name}]" for c in table.columns)
    placeholders = ", ".join("?" for _ in table.columns)
    insert_sql = f"INSERT INTO [{SCHEMA_NAME}].[{table.name}] ({columns_sql}) VALUES ({placeholders})"

    cursor.fast_executemany = True
    cursor.executemany(insert_sql, [cast_row(table, row) for row in rows])
    return len(rows)


def main() -> None:
    conn = get_connection()
    try:
        cursor = conn.cursor()

        for table in reversed(TABLES):
            clear_table(cursor, table)
        conn.commit()

        for table in TABLES:
            count = load_table(cursor, table)
            conn.commit()
            print(f"  {table.name:<28} {count:>7,} rows  <- {table.csv_file}")

        print("\nVerifying via Azure SQL:")
        for table in TABLES:
            cursor.execute(f"SELECT COUNT(*) FROM [{SCHEMA_NAME}].[{table.name}]")
            print(f"  {table.name:<28} {cursor.fetchone()[0]:>7,} rows")

        print(f"\nDone -> {SCHEMA_NAME} schema reloaded.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
