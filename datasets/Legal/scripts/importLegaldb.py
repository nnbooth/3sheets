"""Load legal finance CSVs into PostgreSQL database portfolio_data."""

import csv
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg import sql

SCRIPT_DIR = Path(__file__).resolve().parent
LEGAL_DIR = SCRIPT_DIR.parent
RAW_DIR = Path(os.getenv("LEGAL_DATA_DIR", LEGAL_DIR / "data"))

PGHOST = os.getenv("PGHOST", "127.0.0.1")
PGPORT = int(os.getenv("PGPORT", "5432"))
PGDATABASE = os.getenv("PGDATABASE", "portfolio_data")
PGUSER = os.getenv("PGUSER", os.getenv("USER", "postgres"))
PGPASSWORD = os.getenv("PGPASSWORD", "")
PGSCHEMA = os.getenv("PGSCHEMA", "legal")

TABLES = {
    "dim_office_location": "dim_office_location.csv",
    "dim_practice_area": "dim_practice_area.csv",
    "dim_fee_earner": "dim_fee_earner.csv",
    "dim_referral_source": "dim_referral_source.csv",
    "dim_date": "dim_date.csv",
    "dim_client": "dim_client.csv",
    "dim_matter": "dim_matter.csv",
    "fact_matter": "fact_matter.csv",
    "fact_work_performed": "fact_work_performed.csv",
    "fact_billing": "fact_billing.csv",
    "fact_disbursements": "fact_disbursements.csv",
    "fact_fee_earner_budget_monthly": "fact_fee_earner_budget_monthly.csv",
}


def load_csv(csv_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
INT_RE = re.compile(r"^-?\d+$")
NUMERIC_RE = re.compile(r"^-?\d+(\.\d+)?$")


def infer_pg_type(values: list[str]) -> str:
    non_empty = [v.strip() for v in values if v is not None and v.strip() != ""]
    if not non_empty:
        return "TEXT"

    if all(DATE_RE.match(v) for v in non_empty):
        return "DATE"
    if all(INT_RE.match(v) for v in non_empty):
        return "BIGINT"
    if all(NUMERIC_RE.match(v) for v in non_empty):
        return "NUMERIC"
    return "TEXT"


def infer_table_types(
    fieldnames: list[str],
    rows: list[dict[str, str]],
) -> dict[str, str]:
    inferred: dict[str, str] = {}
    for name in fieldnames:
        column_values = [row.get(name, "") for row in rows]
        inferred[name] = infer_pg_type(column_values)
    return inferred


def recreate_table(
    cur: psycopg.Cursor,
    table: str,
    fieldnames: list[str],
    column_types: dict[str, str],
) -> None:
    cur.execute(
        sql.SQL("DROP TABLE IF EXISTS {}.{}").format(
            sql.Identifier(PGSCHEMA),
            sql.Identifier(table),
        )
    )
    columns_sql = sql.SQL(", ").join(
        sql.SQL("{} {}").format(sql.Identifier(name), sql.SQL(column_types[name]))
        for name in fieldnames
    )
    cur.execute(
        sql.SQL("CREATE TABLE {}.{} ({})").format(
            sql.Identifier(PGSCHEMA),
            sql.Identifier(table),
            columns_sql,
        )
    )


def insert_rows(
    cur: psycopg.Cursor,
    table: str,
    fieldnames: list[str],
    column_types: dict[str, str],
    rows: list[dict[str, str]],
) -> None:
    if not rows:
        return
    placeholders = sql.SQL(", ").join(sql.SQL("%s") for _ in fieldnames)
    columns = sql.SQL(", ").join(sql.Identifier(name) for name in fieldnames)
    stmt = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
        sql.Identifier(PGSCHEMA),
        sql.Identifier(table),
        columns,
        placeholders,
    )

    def normalize(name: str, value: str | None):
        if value is None:
            return None
        trimmed = value.strip()
        if trimmed == "":
            return None if column_types.get(name, "TEXT") != "TEXT" else ""
        return trimmed

    cur.executemany(
        stmt,
        [[normalize(name, row.get(name, "")) for name in fieldnames] for row in rows],
    )


def main() -> None:
    print(f"Source dir: {RAW_DIR}")
    print(f"Target db:  {PGDATABASE} ({PGHOST}:{PGPORT})\n")

    with psycopg.connect(
        host=PGHOST,
        port=PGPORT,
        dbname=PGDATABASE,
        user=PGUSER,
        password=PGPASSWORD,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                    sql.Identifier(PGSCHEMA)
                )
            )
            cur.execute(
                sql.SQL(
                    """
                CREATE TABLE IF NOT EXISTS {}._ingestion_log (
                    table_name  TEXT PRIMARY KEY,
                    source_file TEXT,
                    row_count   INTEGER,
                    loaded_at   TEXT
                )
                """
                ).format(sql.Identifier(PGSCHEMA))
            )

            loaded_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

            for table, csv_name in TABLES.items():
                csv_path = RAW_DIR / csv_name
                if not csv_path.exists():
                    raise FileNotFoundError(f"Missing source file: {csv_path}")

                fieldnames, rows = load_csv(csv_path)
                column_types = infer_table_types(fieldnames, rows)
                recreate_table(cur, table, fieldnames, column_types)
                insert_rows(cur, table, fieldnames, column_types, rows)

                cur.execute(
                    sql.SQL(
                        """
                        INSERT INTO {}._ingestion_log (table_name, source_file, row_count, loaded_at)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT(table_name) DO UPDATE SET
                          source_file=excluded.source_file,
                          row_count=excluded.row_count,
                          loaded_at=excluded.loaded_at
                        """
                    ).format(sql.Identifier(PGSCHEMA)),
                    (table, f"legal_finance_dataset/{csv_name}", len(rows), loaded_at),
                )
                print(f"  loaded {table:<22} {len(rows):>7,} rows  <- {csv_name}")

            print("\nVerifying via PostgreSQL:")
            for table in TABLES:
                cur.execute(
                    sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
                        sql.Identifier(PGSCHEMA),
                        sql.Identifier(table),
                    )
                )
                print(f"  {table:<22} {cur.fetchone()[0]:>7,} rows")

        conn.commit()

    print(f"\nDone -> {PGDATABASE}.{PGSCHEMA}")


if __name__ == "__main__":
    main()
