# The cloud database (Azure SQL)

**No password, key or connection secret exists anywhere.** Everything signs in with your Microsoft account
(`az login`), the server refuses password logins, and only machines you've allowed can reach it. So there's nothing
to protect in files, nothing in git, and nothing to copy between machines.

## On any machine (Mac or Windows), once

```
python3 tools/setup_machine.py        # Windows: py tools\setup_machine.py
```

It installs the Python packages and the Azure command line, and switches on the git leak guard. It finds OneDrive and syncs `media/`.
It signs you in to Azure (browser), lets this machine through the database firewall, and tests the connection.
Run it again whenever something seems off, or after your internet address changes (a new network).

## Create the database (once, from either machine)

```
python3 tools/database/azure_setup.py            # the plan: what exists and what would be created (changes nothing)
python3 tools/database/azure_setup.py create     # create it, locked down
python3 tools/database/azure_setup.py status     # security check
```

What it creates: resource group `au.thefourthsheet.qld`, server `thefourthsheet.database.windows.net`, database `thefourthsheet`.
- **Region:** Australia East.
- **Cost:** the free serverless tier. It pauses when idle, and pauses instead of charging if the free monthly allowance runs out.
- **Sign-in:** Microsoft (Entra ID) only, with you as the only admin.
- **Encryption:** TLS 1.2 or newer.
- **Firewall:** no Azure-wide access; one rule per machine, at that machine's own address.

Settings (names and IDs only, never secrets) are saved to OneDrive `Config/database.env`, so both machines share them.

## Load the data

```
python3 tools/database/load.py --check     # stage and check everything; nothing live changes
python3 tools/database/load.py             # load: stage, check, then replace the live tables in one transaction
python3 tools/report.py --compare-sources  # every report from the database = the same report from the CSVs
python3 tools/report.py job-margins --period 2026-06 --source db
```

The load is safe by design:
- **Strict files:** each file's columns must match its table exactly.
- **Staged and checked:** every row lands in `stage` first, and row counts and a checksum of every number are compared with the files.
- **All or nothing:** only then are the live tables replaced, in one transaction. If anything fails, the live data is exactly as it was.
- **Logged:** every run goes in `ops.load_run` / `ops.load_table` (who, which machine, when, rows, result).
- **Parameters only:** values are always sent as parameters, so nothing in a file can run as SQL.

## Inside the database

| Schema | What | Who |
| --- | --- | --- |
| `dbo` | the tables in `schema.sql` (OneDrive, Data documentation) | `data_loader` writes, `report_reader` reads |
| `stage` | each load lands here first | `data_loader` |
| `ops` | load log | `data_loader` |
| `rpt` | reporting views (next: the star schema) | `report_reader` |

Add people and apps to a role, never one by one (`security.sql` has the commands, with placeholders). Apps in Azure (the
report API, a scheduled loader) use a managed identity, so they have no secret either.

## The star schema

`Data documentation/Database tables and star schema.md` (OneDrive) has every table: its file, rows, columns, types, keys
and an example. It also gives each table's best-practice place in a star schema, with a ready-to-paste prompt for Claude
through a SQL database MCP. Regenerate it with `python3 tools/database/document.py`.

## If something goes wrong

| Message | Fix |
| --- | --- |
| Client with IP address ... is not allowed | `python3 tools/database/azure_setup.py allow-this-machine` |
| Not signed in / token / credential | `az login` |
| database not currently available | it was paused (free tier); wait a minute and try again |
| COMMIT STOPPED | the leak guard found a secret or personal detail in what you're committing: remove it |
