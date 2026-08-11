# DataPortfolio Scripts

Operational scripts for launching the local site and running dataset refresh workflows.

If you want the non-technical operating guide first, read `START_HERE.md` in this folder.

## Scripts in This Folder

- `run_project.bat`: Windows launcher for the static site at repository root.
- `run_project_mac.sh`: macOS launcher for the static site.
- `stop_project_mac.sh`: stops site processes started by macOS launcher.
- `operator_windows.bat`: Windows operator flow.
- `operator_mac.sh`: macOS operator flow.
- `POSTGRES_POWERBI_SETUP.md`: PostgreSQL and Power BI setup notes.

## Run Website - Windows

Run from repository root (`dataPortfolio`):

1. `scripts\\run_project.bat`
2. Open `http://127.0.0.1:8080`

What it does:

- Detects Python from PATH (`python` or `py -3`).
- Serves static files from repository root (where `index.html` lives).
- Opens the browser once the local port is reachable.

If it does not start:

1. Confirm Python is installed: `python --version` or `py -3 --version`
2. Check if port 8080 is in use: `netstat -ano | findstr :8080`
3. Stop the conflicting process and rerun the launcher

## Run Website - macOS

Run from repository root (`dataPortfolio`):

1. `./scripts/run_project_mac.sh`
2. Open `http://127.0.0.1:8080`

Stop services started by the launcher:

1. `./scripts/stop_project_mac.sh`

If it does not start:

1. Confirm Python is installed: `python3 --version`
2. Check logs: `tail -n 50 scripts/.runlogs/website.log`
3. Check port usage: `lsof -iTCP:8080 -sTCP:LISTEN -n -P`

## Data Workflows

- Health source files: `datasets/Health/data/`
- Legal source files: `datasets/Legal/data/`
- Legal build scripts: `datasets/Legal/scripts/`

Keep reporting table and view names stable when changing loader scripts so BI integrations stay compatible.