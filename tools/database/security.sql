-- security.sql — schemas and least-privilege roles inside the database. Safe to run again (every step checks first).
-- Run by: python3 tools/database/azure_setup.py database   (signed in as the server's Microsoft admin)
--
-- Schemas
--   dbo     the data (the tables in schema.sql)
--   stage   where each load lands first and is checked; the live tables only change once every check passes
--   ops     the load log: who loaded what, when, from where, how many rows, and whether it passed
--   rpt     reporting views (the website, the report builder and Power BI read these; next step)
--
-- Roles (people and apps are added to a role, never granted rights one by one)
--   report_reader  read-only: SELECT on dbo and rpt. For Power BI, the report builder, the website's API.
--   data_loader    loads data: write to stage, replace rows in dbo, write the load log. Can't change security.
-- Nobody signs in with a password: the server only accepts Microsoft (Entra ID) sign-in.

IF SCHEMA_ID('stage') IS NULL EXEC('CREATE SCHEMA stage');
IF SCHEMA_ID('ops') IS NULL EXEC('CREATE SCHEMA ops');
IF SCHEMA_ID('rpt') IS NULL EXEC('CREATE SCHEMA rpt');

IF OBJECT_ID('ops.load_run') IS NULL
CREATE TABLE ops.load_run (
    load_id        INT IDENTITY(1,1) PRIMARY KEY,
    started_at     DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    finished_at    DATETIME2(0) NULL,
    loaded_by      NVARCHAR(128) NOT NULL DEFAULT SUSER_SNAME(),
    machine        NVARCHAR(128) NULL,
    source         NVARCHAR(400) NULL,
    status         VARCHAR(20) NOT NULL DEFAULT 'Running',   -- Running, Loaded, Failed, Checked (dry run)
    tables_loaded  INT NULL,
    rows_loaded    INT NULL,
    message        NVARCHAR(4000) NULL
);

IF OBJECT_ID('ops.load_table') IS NULL
CREATE TABLE ops.load_table (
    load_id        INT NOT NULL REFERENCES ops.load_run(load_id),
    table_name     VARCHAR(128) NOT NULL,
    files          INT NOT NULL,
    csv_rows       INT NOT NULL,
    loaded_rows    INT NOT NULL,
    csv_checksum   DECIMAL(38,2) NULL,     -- sum of the numeric columns in the files
    loaded_checksum DECIMAL(38,2) NULL,    -- the same sum, read back from the database
    PRIMARY KEY (load_id, table_name)
);

IF DATABASE_PRINCIPAL_ID('report_reader') IS NULL CREATE ROLE report_reader;
IF DATABASE_PRINCIPAL_ID('data_loader') IS NULL CREATE ROLE data_loader;

GRANT SELECT ON SCHEMA::dbo TO report_reader;
GRANT SELECT ON SCHEMA::rpt TO report_reader;

GRANT SELECT, INSERT, DELETE ON SCHEMA::dbo TO data_loader;
GRANT SELECT, INSERT, DELETE, ALTER ON SCHEMA::stage TO data_loader;
GRANT SELECT, INSERT, UPDATE ON SCHEMA::ops TO data_loader;
GRANT CREATE TABLE TO data_loader;

-- People and apps: add each one to a role when it's needed. All sign in with Microsoft; none has a password.
-- Fill in and run one at a time (the server's admin does this):
--
--   A person who reads reports (e.g. in Power BI):
--     CREATE USER [[[READER_UPN]]] FROM EXTERNAL PROVIDER;           -- e.g. someone@yourdomain.com.au
--     ALTER ROLE report_reader ADD MEMBER [[[READER_UPN]]];
--
--   The report API, once it runs in Azure (its managed identity, so no secret exists anywhere):
--     CREATE USER [[[REPORT_API_IDENTITY_NAME]]] FROM EXTERNAL PROVIDER;
--     ALTER ROLE report_reader ADD MEMBER [[[REPORT_API_IDENTITY_NAME]]];
--
--   A scheduled loader (Power Automate, or a job in Azure), also by managed identity:
--     CREATE USER [[[LOADER_IDENTITY_NAME]]] FROM EXTERNAL PROVIDER;
--     ALTER ROLE data_loader ADD MEMBER [[[LOADER_IDENTITY_NAME]]];
