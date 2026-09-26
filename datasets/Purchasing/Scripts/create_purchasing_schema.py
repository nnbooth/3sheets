"""Create the `purchasing` schema and its tables in Azure SQL, if missing.

Idempotent: checks for the schema and each table before creating anything.
Never drops or alters existing objects - see load_purchasing_data.py for the
script that clears and reloads table data.

Table/column definitions live in purchasing_tables.py (reviewed manually,
not inferred from the CSVs) - edit that file, not this one, to change types.
"""

from azure_sql_connection import get_connection
from purchasing_tables import SCHEMA_NAME, TABLES, Table


def schema_exists(cursor) -> bool:
    cursor.execute("SELECT 1 FROM sys.schemas WHERE name = ?", SCHEMA_NAME)
    return cursor.fetchone() is not None


def table_exists(cursor, table_name: str) -> bool:
    cursor.execute(
        """
        SELECT 1 FROM sys.tables t
        JOIN sys.schemas s ON s.schema_id = t.schema_id
        WHERE s.name = ? AND t.name = ?
        """,
        SCHEMA_NAME,
        table_name,
    )
    return cursor.fetchone() is not None


def foreign_key_exists(cursor, table_name: str, constraint_name: str) -> bool:
    cursor.execute(
        """
        SELECT 1 FROM sys.foreign_keys fk
        JOIN sys.tables t ON t.object_id = fk.parent_object_id
        JOIN sys.schemas s ON s.schema_id = t.schema_id
        WHERE s.name = ? AND t.name = ? AND fk.name = ?
        """,
        SCHEMA_NAME,
        table_name,
        constraint_name,
    )
    return cursor.fetchone() is not None


def build_create_table_sql(table: Table) -> str:
    column_lines = []

    if table.identity_column:
        column_lines.append(f"[{table.identity_column}] INT IDENTITY(1,1) PRIMARY KEY")

    for column in table.columns:
        column_lines.append(f"[{column.name}] {column.sql_type}")

    if table.primary_key:
        pk_cols = ", ".join(f"[{name}]" for name in table.primary_key)
        column_lines.append(f"PRIMARY KEY ({pk_cols})")

    columns_sql = ",\n    ".join(column_lines)
    return f"CREATE TABLE [{SCHEMA_NAME}].[{table.name}] (\n    {columns_sql}\n)"


def build_add_fk_sql(table: Table, fk) -> tuple[str, str]:
    constraint_name = f"FK_{table.name}_{'_'.join(fk.columns)}"
    cols = ", ".join(f"[{c}]" for c in fk.columns)
    ref_cols = ", ".join(f"[{c}]" for c in fk.ref_columns)
    ddl = (
        f"ALTER TABLE [{SCHEMA_NAME}].[{table.name}] "
        f"ADD CONSTRAINT [{constraint_name}] FOREIGN KEY ({cols}) "
        f"REFERENCES [{SCHEMA_NAME}].[{fk.ref_table}] ({ref_cols})"
    )
    return constraint_name, ddl


def main() -> None:
    conn = get_connection()
    try:
        cursor = conn.cursor()

        if schema_exists(cursor):
            print(f"Schema [{SCHEMA_NAME}] already exists - skipping.")
        else:
            cursor.execute(f"CREATE SCHEMA [{SCHEMA_NAME}]")
            conn.commit()
            print(f"Created schema [{SCHEMA_NAME}].")

        for table in TABLES:
            if table_exists(cursor, table.name):
                print(f"  table {table.name:<28} already exists - skipping.")
                continue

            ddl = build_create_table_sql(table)
            cursor.execute(ddl)
            conn.commit()
            print(f"  table {table.name:<28} created.")

        # Added after every table exists, so table creation order above never
        # has to match FK dependency order.
        for table in TABLES:
            for fk in table.foreign_keys:
                constraint_name, ddl = build_add_fk_sql(table, fk)
                if foreign_key_exists(cursor, table.name, constraint_name):
                    print(f"  FK {constraint_name:<45} already exists - skipping.")
                    continue
                cursor.execute(ddl)
                conn.commit()
                print(f"  FK {constraint_name:<45} created.")

        print(f"\nDone -> {SCHEMA_NAME} schema is ready.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
