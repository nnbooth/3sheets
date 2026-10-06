#!/usr/bin/env python3
"""report.py — build a report from the data for a period, as Excel, PDF and PowerPoint (from scratch, no templates).

    python3 tools/report.py job-margins --period 2026-06
    python3 tools/report.py --list

See tools/fourthsheet/cli.py for every option.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import winutf8; winutf8.ensure()   # Windows: run in UTF-8 mode (the tools write characters like ¢ and ▲)

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fourthsheet.cli import main  # noqa: E402

main(sys.argv[1:])
