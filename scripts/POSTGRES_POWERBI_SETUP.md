# Postgres + Power BI Setup

This is the Mac-to-laptop reporting setup for the Postgres-backed Legal reporting model.

## What this setup is for

- Postgres runs on the Mac as the reporting source of truth.
- Power BI Desktop runs on the Windows laptop and connects to that Postgres instance.
- The database is private; Power BI connects directly to it over the network.
- The report outputs can later be exported to Excel, PDF, and PowerPoint.

## Current state

- Postgres is already running on the Mac.
- The default reporting database name in this repo is `portfolio_data`.
- If reporting tables are missing, run the Legal load scripts before connecting Power BI.

## Recommended structure

1. Load the reporting tables into Postgres.
2. Create a read-only reporting user for Power BI.
3. Allow the Mac to accept network connections on port `5432`.
4. Connect Power BI Desktop from the laptop.
5. Build the report model in Power BI.
6. Publish the report and export the pack formats.

## Mac-side setup

### 1) Make Postgres reachable on the network

Postgres must listen on the Mac's LAN address, not only `localhost`.

Typical settings:

- `listen_addresses = '*'`
- `port = 5432`

### 2) Allow your laptop in `pg_hba.conf`

Add a rule for your laptop or VPN range.

Example for home LAN only:

```conf
host    all    all    192.168.0.0/24    scram-sha-256
```

If you use Tailscale or another VPN, allow the VPN subnet instead.

### 3) Open the firewall if needed

Allow inbound TCP port `5432` on the Mac.

## Power BI connection details

Use these values in Power BI Desktop on the laptop:

- Server: `192.168.0.127:5432` or your Mac's current LAN IP
- Database: `portfolio_data`
- Authentication: a dedicated read-only reporting user

## Next database step

If the database is still empty, the next step is to load the tables.

Recommended order:

1. Create the schema and tables.
2. Load the source data.
3. Verify row counts.
4. Create a reporting role/user.
5. Test the connection from Power BI.

## Suggested reporting user

Create a dedicated user that can only read the reporting tables.

Example intent:

- can `SELECT` from reporting tables/views
- cannot create, update, or delete data
- cannot change database structure

## Power BI workflow

1. Open Power BI Desktop.
2. Choose PostgreSQL as the source.
3. Enter the Mac IP and database name.
4. Sign in with the read-only reporting user.
5. Build measures, relationships, and visuals.
6. Publish the report.

## Deliverables

Once the Power BI model is built, you can use it to produce:

- Excel packs for tabular delivery
- PDF packs for management reporting
- PowerPoint packs for presentation

## Troubleshooting

- If Power BI cannot connect, check that the Mac IP is correct and that port `5432` is open.
- If the database connects but no tables appear, the load step has not run yet.
- If the laptop can connect on Wi-Fi but not outside the network, use VPN or Tailscale.

## Short version

- Mac hosts Postgres.
- Laptop connects with Power BI.
- Load or refresh reporting tables as needed.
- Use a read-only reporting user.
- Export the finished report into Excel, PDF, and PowerPoint.