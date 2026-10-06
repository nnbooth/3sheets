# The Fourth Sheet

Website and tooling for **The Fourth Sheet**, Nathan Booth's Brisbane consultancy for SMEs and not-for-profits:
*"Your accountant gives you three sheets. I give you the fourth."* Live at https://nnbooth.github.io/thefourthsheet/.

The site is plain HTML, CSS and JavaScript (no framework, no build step) on GitHub Pages. Python in `tools/` generates
everything data-driven: the month-end sample model behind the home dashboard (checked to add up), the daily star schema
for a cloud database, the deliveries map data, the Excel and PDF downloads, the mock-up images and the game video.
Business decisions, placeholders and the go-live checklist are in the private project notes: OneDrive, `The 4th Sheet/Business/Project notes.md`.

Ground rules: sample data is labelled and adds up; no client results claimed; copy is technology agnostic; every report
gets Excel and PDF downloads; data lives in OneDrive, not git.

## Repository layout

This repo is **public** and the website is served straight from it. Private notes and data live in OneDrive, never here.

```
index.html  sme.html  not-for-profit.html  examples.html  services.html  about.html  numbers-explained.html  report-*.html
styles.css  script.js
data/                       generated data the pages read (dashboard-data.js, deliveries-data.js)
assets/brand/               the 4th mark, wordmark, share image
assets/tools/               tool logos       assets/people/   headshot
media/mockups/              mock-up images   media/game/      game video and poster
media/exports/              the Excel and PDF downloads (generated)
game/                       the playable game
tools/                      Python that generates everything (kept in git, not published)
_config.yml                 tells GitHub Pages not to publish README.md and tools/
```

## Where the private files and data live

Everything private is in OneDrive (`Projects/The 4th Sheet/`), backed up to the cloud and kept out of git:

```
Business/           Project notes.md (decisions, to-do, go-live checklist), business and project plans
Data/               data only (CSV, Excel), one folder per task:
                      Common/  Month-end dashboard/{SME trades, SME services, Not-for-profit}/
                      Deliveries map/  Live displays/  Reports/  Management pack template/
                      Health/  Legal/  Purchasing/  Retail/   (the dataset projects)
Data documentation/ schema.sql and what each table holds (generated), dataset READMEs
Dataset projects/   the Health, Legal and Purchasing scripts and docs (a separate project from the website)
Brand/  Media/  Archive/
```

Scripts find the Data folder automatically on the Mac (`~/Library/CloudStorage/OneDrive-Personal/...`) and on a Windows PC (`%OneDrive%\Projects\The 4th Sheet`). To use another location, set `FOURTH_SHEET_DATA` to the `Data` folder.
The only spreadsheets kept in git are the website's own downloads in `media/exports/`.

## Quick Start

Run from the repository root (`dataPortfolio`):

```
python3 tools/serve.py             # then open http://127.0.0.1:8765 (no caching)
python3 tools/sample_data.py       # regenerate the sample model, downloads and CSVs
```

## Prerequisites

- Python 3 available in PATH (`python`, `py -3`, or `python3` depending on platform).
