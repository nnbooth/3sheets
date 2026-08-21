"""Shared Azure SQL connection helper for the purchasing create/load scripts.

Credentials come from a .env file at the repo root (see .env.example) via
python-dotenv's find_dotenv(), which walks up the directory tree from this
file so it works regardless of which domain's scripts/ folder calls it.
"""

import os

import pyodbc
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

REQUIRED_VARS = ("AZURE_SQL_SERVER", "AZURE_SQL_DATABASE", "AZURE_SQL_USER", "AZURE_SQL_PASSWORD")


def get_connection() -> pyodbc.Connection:
    values = {name: os.getenv(name) for name in REQUIRED_VARS}
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise RuntimeError(
            f"Missing env var(s): {', '.join(missing)}. Set them in the .env file "
            "at the repo root (see .env.example)."
        )

    # NOTE: the Azure SQL firewall only allows explicitly-listed client IPs.
    # If this connection fails with a "not allowed to access" error, your
    # public IP has likely changed (common on home/dynamic-IP connections) -
    # re-add it with:
    #   az sql server firewall-rule create --resource-group "au.3sheets.qld" \
    #     --server "3sheets" --name "<your-name>-dev" \
    #     --start-ip-address <new-ip> --end-ip-address <new-ip>
    #
    # NOTE: 3sheets.db.sql runs on the Serverless tier (GP_S_Gen5, 60-minute
    # auto-pause). A connection after a pause has to wait for the database to
    # resume, which can take well over 30s - that shows up as a TCP timeout
    # (SQLSTATE 08001), not an auth error. A generous Connection Timeout
    # covers this; if it still happens, retry - the resume itself continues
    # in the background once triggered, so the next attempt is fast.
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER=tcp:{values['AZURE_SQL_SERVER']},1433;"
        f"DATABASE={values['AZURE_SQL_DATABASE']};"
        f"UID={values['AZURE_SQL_USER']};"
        f"PWD={values['AZURE_SQL_PASSWORD']};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=90;"
    )
    return pyodbc.connect(conn_str)
