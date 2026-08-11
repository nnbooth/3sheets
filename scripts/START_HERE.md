# START HERE (Non-Technical Operating Guide)

This is your simplified control panel for the whole project.

## What This Project Actually Does

- Keeps one legal reporting dataset up to date.
- Loads that data into PostgreSQL.
- Builds reporting views used by BI tools.
- Serves the website and revenue snapshot page.

## What You Should Focus On

- Sales work.
- Building Power BI reports.
- Building Looker Studio reports.
- Exporting to Excel / Google Sheets.

## What To Ignore Unless Something Breaks

- Code internals in `Legal/scripts/*.py`
- Active site files in `simple-reporting-site/`
- Legacy website folder `website/` is deprecated and retained only for reference
- Most generated CSV internals in `Health/data` and `Legal/data`

## Your 4 Commands (macOS)

Run from the `dataPortfolio` folder.

1) Start website

```bash
./run_project_mac.sh
```

2) Refresh Legal reporting data end-to-end

```bash
./scripts/operator_mac.sh refresh-legal
```

3) Refresh Legal data and start website

```bash
./scripts/operator_mac.sh full-refresh
```

4) Stop website

```bash
./stop_project_mac.sh
```

## One-Line Workflow You Can Repeat

1. Run `./scripts/operator_mac.sh refresh-legal`
2. Open Power BI and refresh model from PostgreSQL `portfolio_data` (schema `legal`)
3. Build report outputs
4. Share/export packs

## Where Your Reporting Inputs Live

- Legal dataset CSVs: `Legal/data/`
- Postgres target DB: `portfolio_data`
- Postgres schema: `legal`
- Business reporting views: built by `Legal/scripts/build_legal_models.py`

## If Something Fails

Run:

```bash
./scripts/operator_mac.sh status
```

That gives a quick health check for Node, npm, Python, website process, and launcher logs.
