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

REPO = Path(__file__).resolve().parent.parent
LOCAL = REPO / "media"


def onedrive_root():
    if os.getenv("FOURTH_SHEET_DATA"):
        return Path(os.getenv("FOURTH_SHEET_DATA")).expanduser().parent
    for base in (os.getenv("OneDriveConsumer"), os.getenv("OneDrive"),
                 Path.home() / "Library/CloudStorage/OneDrive-Personal", Path.home() / "OneDrive"):
        if base and (Path(base) / "Projects/The 4th Sheet").exists():
            return Path(base) / "Projects/The 4th Sheet"
    raise SystemExit("Can't find the OneDrive folder 'Projects/The 4th Sheet'.")


def sync(quiet=False):
    remote = onedrive_root() / "Media" / "site media"
    up = down = 0
    names = {p.relative_to(LOCAL) for p in LOCAL.rglob("*") if p.is_file()} | \
            ({p.relative_to(remote) for p in remote.rglob("*") if p.is_file()} if remote.exists() else set())
    for rel in sorted(names):
        if rel.name == ".DS_Store":
            continue
        a, b = LOCAL / rel, remote / rel
        if a.exists() and (not b.exists() or a.stat().st_mtime > b.stat().st_mtime + 1):
            b.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(a, b)
            up += 1
        elif b.exists() and (not a.exists() or b.stat().st_mtime > a.stat().st_mtime + 1):
            a.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(b, a)
            down += 1
    if not quiet:
        print(f"media/ and OneDrive in step: {up} copied up, {down} copied down ({remote})")
    return up, down


if __name__ == "__main__":
    sync()
