#!/usr/bin/env python3
"""
sync_media.py — keep everything under media/ identical between this machine and OneDrive.

The Excel downloads (and anything else git ignores) only live on the machine that built them,
so they're mirrored to OneDrive (Projects/The 4th Sheet/Media/site media/), both ways:
whichever copy is newer wins, and files missing on one side are copied over. On a fresh
machine, running this pulls everything down.

Runs at the end of tools/sample_data.py, render_mockups.py and record_demo.py.
Run it yourself any time:   python3 tools/sync_media.py
"""

import os
import shutil
from pathlib import Path
import winutf8; winutf8.ensure()   # Windows: run in UTF-8 mode (the tools write characters like ¢ and ▲)

REPO = Path(__file__).resolve().parent.parent
LOCAL = REPO / "media"

# Files that have been retired: deleted on BOTH sides before syncing (otherwise "newer wins" would copy a
# deleted file straight back). Patterns are relative to media/.
RETIRED = [
    "exports/reports/*.xlsx", "exports/reports/*.pdf", "exports/reports/*.pptx",   # replaced by exports/reports/<period>/ (6 Oct 2026)
]


def onedrive_candidates():
    """Every place OneDrive can live, personal or business, on a Mac or a Windows PC. The one that holds
    'Projects/The 4th Sheet' wins, so moving the project to OneDrive for Business needs no code change."""
    home = Path.home()
    bases = [os.getenv("OneDriveConsumer"), os.getenv("OneDriveCommercial"), os.getenv("OneDrive"),
             home / "Library/CloudStorage/OneDrive-Personal", *sorted((home / "Library/CloudStorage").glob("OneDrive-*")),
             home / "OneDrive", *sorted(home.glob("OneDrive - *"))]
    return [Path(b) for b in bases if b]


PIN = Path.home() / ".fourthsheet" / "onedrive_root.txt"   # this machine's pinned project folder (not in git or OneDrive)


def pinned():
    return Path(PIN.read_text(encoding="utf-8").strip()).expanduser() if PIN.exists() and PIN.read_text(encoding="utf-8").strip() else None


def pin(path):
    """Pin this machine to one project folder: every tool then reads it, and stops (rather than looking elsewhere) if it's missing."""
    path = Path(path).expanduser()
    if not (path / "Data").is_dir():
        raise SystemExit(f"Not pinned: {path} doesn't have a Data folder. Is it the 'The 4th Sheet' folder, and has OneDrive synced it?")
    PIN.parent.mkdir(parents=True, exist_ok=True)
    PIN.write_text(str(path), encoding="utf-8")
    return path


def onedrive_root():
    """The project folder in OneDrive ('Projects/The 4th Sheet'). Order: FOURTH_SHEET_DATA (its parent), then this
    machine's pin (~/.fourthsheet/onedrive_root.txt), then a search of the usual OneDrive places (only if not pinned)."""
    if os.getenv("FOURTH_SHEET_DATA"):
        return Path(os.getenv("FOURTH_SHEET_DATA")).expanduser().parent
    p = pinned()
    if p:
        if not (p / "Data").is_dir():
            raise SystemExit(f"The pinned project folder isn't available: {p}\n"
                             "OneDrive may still be syncing or remapping. Wait for it to finish, or pin the new place with:\n"
                             "  python3 tools/setup_machine.py --onedrive \"<the 'The 4th Sheet' folder>\"   (Windows: py ...)")
        return p
    for base in onedrive_candidates():
        if (base / "Projects/The 4th Sheet").exists():
            return base / "Projects/The 4th Sheet"
    raise SystemExit("Can't find the OneDrive folder 'Projects/The 4th Sheet' (personal or business). "
                     "Sign in to OneDrive and let it sync, or pin it: python3 tools/setup_machine.py --onedrive \"<folder>\"")


def sync(quiet=False):
    remote = onedrive_root() / "Media" / "site media"
    gone = 0
    for pat in RETIRED:
        for side in (LOCAL, remote):
            for f in side.glob(pat):
                f.unlink()
                gone += 1
    up = down = 0
    names = {p.relative_to(LOCAL) for p in LOCAL.rglob("*") if p.is_file()} | \
            ({p.relative_to(remote) for p in remote.rglob("*") if p.is_file()} if remote.exists() else set())
    for rel in sorted(names):
        if rel.name == ".DS_Store":
            continue
        a, b = LOCAL / rel, remote / rel
        if a.exists() and b.exists() and a.stat().st_size == b.stat().st_size and abs(a.stat().st_mtime - b.stat().st_mtime) > 1 \
                and a.read_bytes() == b.read_bytes():
            t = min(a.stat().st_mtime, b.stat().st_mtime)      # same file, different dates (e.g. a fresh git clone):
            os.utime(a, (t, t)); os.utime(b, (t, t))           # line the dates up instead of copying
            continue
        if a.exists() and (not b.exists() or a.stat().st_mtime > b.stat().st_mtime + 1):
            b.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(a, b)
            up += 1
        elif b.exists() and (not a.exists() or b.stat().st_mtime > a.stat().st_mtime + 1):
            a.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(b, a)
            down += 1
    if not quiet:
        print(f"media/ and OneDrive in step: {up} copied up, {down} copied down" + (f", {gone} retired files removed" if gone else "") + f" ({remote})")
    return up, down


if __name__ == "__main__":
    sync()
