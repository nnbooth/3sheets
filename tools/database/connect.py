"""
connect.py — open a connection to the cloud database, signed in as you. No password exists.

Sign-in, tried in order (Microsoft's "default" chain):
  - the Azure command line (run `az login` once on each machine), then
  - a sign-in window in the browser.
The connection is always encrypted, and the server's certificate is checked (no TrustServerCertificate).
"""

from . import config


def connection_string(database=None, interactive=False):
    v = config.read()
    return (f"Server=tcp:{config.server_host(v)},1433;Database={database or v['SQL_DATABASE']};"
            f"Authentication={'ActiveDirectoryInteractive' if interactive else 'ActiveDirectoryDefault'};"
            "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=60")


def connect(database=None, interactive=False, autocommit=False):
    import mssql_python
    try:
        conn = mssql_python.connect(connection_string(database, interactive))
    except Exception as e:
        msg = str(e)
        hint = ""
        if "Client with IP address" in msg or "firewall" in msg.lower():
            hint = "\nThis machine isn't on the server's allowed list. Run:  python3 tools/database/azure_setup.py allow-this-machine"
        elif "login" in msg.lower() or "token" in msg.lower() or "credential" in msg.lower():
            hint = "\nSign in first:  az login   (or add --interactive to sign in through the browser)"
        elif "paused" in msg.lower() or "not currently available" in msg.lower():
            hint = "\nThe database was asleep (it pauses when idle to cost nothing). Try again in a minute."
        raise SystemExit(f"Couldn't connect to {config.server_host()}: {msg}{hint}")
    conn.autocommit = autocommit
    return conn


def whoami(conn):
    cur = conn.cursor()
    cur.execute("SELECT SUSER_SNAME(), DB_NAME(), @@VERSION")
    return cur.fetchone()
