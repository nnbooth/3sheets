"""
config.py — where the database is. Names only: NOTHING SECRET goes in this file, in git, or in OneDrive.

Settings are read from, in order:
  1. environment variables (e.g. FOURTH_SHEET_SQL_SERVER), handy for a one-off;
  2. OneDrive: Projects/The 4th Sheet/Config/database.env, so the Mac and the PC share one copy;
  3. the defaults below.
A value still showing [[PLACEHOLDER]] stops anything that needs it, with a message saying what to fill in.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DEFAULTS = {
    "AZURE_SUBSCRIPTION_ID": "[[AZURE_SUBSCRIPTION_ID]]",   # az account show --query id   (filled in by azure_setup.py)
    "AZURE_TENANT_ID": "[[AZURE_TENANT_ID]]",               # az account show --query tenantId
    "AZURE_RESOURCE_GROUP": "au.thefourthsheet.qld",
    "AZURE_LOCATION": "australiaeast",
    "SQL_SERVER": "thefourthsheet",                          # becomes thefourthsheet.database.windows.net
    "SQL_DATABASE": "thefourthsheet",
    "SQL_ADMIN_UPN": "[[SQL_ADMIN_UPN]]",                   # your Microsoft sign-in (the server's only admin)
    "SQL_ADMIN_OBJECT_ID": "[[SQL_ADMIN_OBJECT_ID]]",       # az ad signed-in-user show --query id
}
FILE_HEADER = """# The Fourth Sheet: where the cloud database is. Shared by every machine through OneDrive.
# NAMES ONLY. Never put a password, key, secret or connection string with a password in this file:
# sign-in is with your Microsoft account (az login), so none is needed.
"""


def onedrive_project():
    from sync_media import onedrive_root
    return onedrive_root()


def settings_file():
    return onedrive_project() / "Config" / "database.env"


def read():
    vals = dict(DEFAULTS)
    f = settings_file()
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip()
    for k in vals:
        if os.getenv("FOURTH_SHEET_" + k):
            vals[k] = os.getenv("FOURTH_SHEET_" + k)
    return vals


def write(vals):
    f = settings_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(FILE_HEADER + "".join(f"{k}={vals[k]}\n" for k in DEFAULTS), encoding="utf-8")
    return f


def need(*keys):
    vals = read()
    missing = [k for k in keys if vals[k].startswith("[[")]
    if missing:
        raise SystemExit(f"Fill in {', '.join(missing)} in {settings_file()} (or run: python3 tools/database/azure_setup.py)")
    return vals


def server_host(vals=None):
    return f"{(vals or read())['SQL_SERVER']}.database.windows.net"
