# DataPortfolio

Portfolio repository for multi-domain analytics assets, sample datasets, and a lightweight static site.

## Repository Layout

- `index.html`, `styles.css`, `script.js`: root static site entrypoint and assets.
- `Assets/`: shared static assets.
- `datasets/Health/data/`: health operations star-schema CSV dataset and documentation.
- `datasets/Legal/data/`: legal and insurance finance star-schema CSV dataset and documentation.
- `datasets/Legal/scripts/`: Python data load and model build scripts for legal reporting.
- `datasets/Purchasing/`: purchasing data, docs, and scripts.
- `datasets/Retail/`: retail data and docs.
- `docs/`: project notes and planning artifacts.
- `scripts/`: operator and launcher scripts for Windows and macOS.

## Quick Start

Run from the repository root (`dataPortfolio`).

### Windows

1. Run `scripts\\run_project.bat`
2. Open `http://127.0.0.1:8080`

### macOS

1. Run `./scripts/run_project_mac.sh`
2. Open `http://127.0.0.1:8080`

## Prerequisites

- Python 3 available in PATH (`python`, `py -3`, or `python3` depending on platform).

## Data and Reporting Notes

- Legal reporting models target PostgreSQL `portfolio_data` and schema `legal`.
- Keep table and view names stable when modifying loaders or model scripts.
- Health and legal datasets are synthetic and intended for portfolio analytics/reporting demos.
