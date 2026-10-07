#!/usr/bin/env python3
"""
setup_machine.py — get this machine (Mac or Windows) ready to work on The Fourth Sheet. Safe to run any time.

    Mac:      python3 tools/setup_machine.py
    Windows:  py tools\\setup_machine.py

It checks, and fixes what it can:
  1. Python packages (requirements.txt) and the PDF browser engine
  2. the Azure command line (installed into its own folder; no admin rights needed)
  3. git: commits use your private GitHub noreply address, and the leak guard (tools/githooks) is switched on
  4. OneDrive: the data, notes and media folders are found; media/ is synced both ways
  5. Azure: signed in (opens the browser if not), this machine allowed through the database firewall,
     and a test connection to the database (signed in as you: no password exists anywhere)
Nothing secret is stored by this script: sign-in tokens are kept by Azure's own tools in your user profile.
"""

import os
import platform
import shutil
import subprocess
import sys
import venv
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import winutf8; winutf8.ensure()   # Windows: run in UTF-8 mode (the tools write characters like ¢ and ▲)

REPO = Path(__file__).resolve().parent.parent
TOOLS = REPO / "tools"
sys.path.insert(0, str(TOOLS))
WIN = platform.system() == "Windows"
AZ_VENV = Path.home() / ".azure-cli-venv"
NOREPLY = "16619153+nnbooth@users.noreply.github.com"
OK, WARN, FAIL = "  ok ", "  !! ", "  XX "


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def ask(q):
    if not sys.stdin.isatty():
        return False
    return input(f"{q} [Y/n] ").strip().lower() in ("", "y", "yes")


def step(title):
    print(f"\n{title}")


def python_packages():
    step("1. Python packages")
    if sys.version_info < (3, 10):
        print(f"{FAIL}Python {platform.python_version()}: 3.10 or newer is needed (python.org/downloads).")
        sys.exit(1)
    if WIN and os.environ.get("PYTHONUTF8") != "1":
        run(["setx", "PYTHONUTF8", "1"])       # Windows: Python reads and writes files as UTF-8 from now on
        print(OK + "Python UTF-8 mode switched on for good (takes effect in new terminals; the tools cope meanwhile)")
    p = run([sys.executable, "-m", "pip", "install", "--quiet", "-r", str(REPO / "requirements.txt")])
    print((OK + "requirements.txt installed") if p.returncode == 0 else (FAIL + "pip failed:\n" + p.stderr[-800:]))
    has_chrome = any(Path(x).exists() for x in ("/Applications/Google Chrome.app", r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                                                 r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"))
    if not has_chrome:
        p = run([sys.executable, "-m", "playwright", "install", "chromium"])
        print((OK + "PDF browser engine installed (Chromium)") if p.returncode == 0 else (WARN + "couldn't install Chromium: " + p.stderr[-300:]))
    else:
        print(OK + "Google Chrome found (used for the PDFs)")


def az_exe():
    for p in (shutil.which("az"), shutil.which("az.cmd"), AZ_VENV / "bin" / "az", AZ_VENV / "Scripts" / "az.exe", AZ_VENV / "Scripts" / "az"):
        if p and Path(p).exists():
            return str(p)
    return None


def azure_cli():
    step("2. Azure command line")
    if az_exe():
        print(OK + f"found: {az_exe()}")
        return
    print("     installing into " + str(AZ_VENV) + " (a few minutes, no admin rights needed) ...")
    venv.create(AZ_VENV, with_pip=True)
    py = AZ_VENV / ("Scripts/python.exe" if WIN else "bin/python")
    p = run([str(py), "-m", "pip", "install", "--quiet", "--upgrade", "pip", "azure-cli"])
    print((OK + f"installed: {az_exe()}") if az_exe() else (FAIL + "install failed:\n" + p.stderr[-800:]))
    if az_exe() and not shutil.which("az"):
        hint = f'setx PATH "%PATH%;{AZ_VENV / "Scripts"}"' if WIN else f'echo \'export PATH="$PATH:{AZ_VENV / "bin"}"\' >> ~/.zshrc'
        print(WARN + f"to type 'az' yourself, add it to your PATH once:  {hint}")


def git_setup():
    step("3. git")
    run(["git", "-C", str(REPO), "config", "user.email", NOREPLY])
    print(OK + f"commits use your private GitHub address ({NOREPLY})")
    run(["git", "-C", str(REPO), "config", "core.hooksPath", "tools/githooks"])
    print(OK + "leak guard on: a commit with a password, key, data file or personal detail is stopped")


def onedrive():
    step("4. OneDrive")
    try:
        from sync_media import onedrive_root, sync
        root = onedrive_root()
    except SystemExit as e:
        print(FAIL + str(e) + " Sign in to OneDrive and let 'Projects/The 4th Sheet' sync, then run this again.")
        return False
    for sub in ("Data", "Data documentation", "Business", "Media/site media"):
        print((OK if (root / sub).exists() else WARN) + f"{sub}: {root / sub}")
    up, down = sync(quiet=True)
    print(OK + f"media/ synced with OneDrive ({up} up, {down} down)")
    return True


def azure_signin():
    step("5. Azure sign-in and the database")
    az = az_exe()
    if not az:
        print(WARN + "no Azure command line: skipped")
        return
    acct = run([az, "account", "show", "-o", "json"])
    if acct.returncode != 0:
        if ask("     Not signed in to Azure on this machine. Sign in now (opens the browser)?"):
            subprocess.run([az, "login"])
            acct = run([az, "account", "show", "-o", "json"])
        if acct.returncode != 0:
            print(WARN + "not signed in. Later:  az login   then run this again.")
            return
    import json
    a = json.loads(acct.stdout)
    print(OK + f"signed in as {a['user']['name']} (subscription {a['name']})")
    from database import config
    if not config.settings_file().exists():
        print(WARN + "the database isn't set up yet. Create it (once, from either machine):  python3 tools/database/azure_setup.py create")
        return
    v = config.read()
    if v["SQL_ADMIN_UPN"].startswith("[["):
        print(WARN + f"settings still have placeholders: {config.settings_file()}. Run: python3 tools/database/azure_setup.py create")
        return
    from database import azure_setup
    try:
        if ask(f"     Allow this machine through the database firewall (only its own internet address)?"):
            azure_setup.allow_this_machine(v)
        from database import connect
        conn = connect.connect()
        who, db, _ = connect.whoami(conn)
        conn.close()
        print(OK + f"connected to {config.server_host(v)} / {db} as {who} (encrypted, no password)")
    except SystemExit as e:
        print(WARN + str(e))


def main():
    print(f"Setting up {platform.node()} ({platform.system()}) for The Fourth Sheet, in {REPO}")
    python_packages()
    azure_cli()
    git_setup()
    have_onedrive = onedrive()
    azure_signin()
    print("\nReady. Everyday commands:")
    print("  python3 tools/serve.py                          preview the site at http://127.0.0.1:8765")
    print("  python3 tools/sample_data.py                    rebuild the data, reports and downloads")
    print("  python3 tools/report.py --list                  build any report for any period")
    print("  python3 tools/database/load.py --check          stage and check a database load (then without --check to load)")
    if WIN:
        print("  (on Windows, type py instead of python3)")
    if not have_onedrive:
        sys.exit(1)


if __name__ == "__main__":
    main()
