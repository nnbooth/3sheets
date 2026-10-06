"""
schema.py — the tables, read from the generated schema.sql (OneDrive, Data documentation/).

For each table: its CREATE TABLE statement, its columns and types, the CSV file(s) it loads from, and the
tables it references (so dimensions load before the facts that point at them).
"""

import re
from pathlib import Path

from . import config


def schema_file():
    return config.onedrive_project() / "Data documentation" / "schema.sql"


def data_root():
    return config.onedrive_project() / "Data"


class Table:
    def __init__(self, name, ddl, comment):
        self.name, self.ddl = name, ddl.strip()
        body = ddl[ddl.index("(") + 1:ddl.rindex(")")]
        self.columns = []
        for part in re.split(r",\s*\n", body):
            m = re.match(r"\s*([a-z_][a-z0-9_]*)\s+([A-Z]+(?:\([0-9, ]+\))?)", part)
            if m and m.group(1) not in ("primary", "foreign", "constraint", "unique"):
                self.columns.append((m.group(1), m.group(2)))
        self.refs = sorted(set(re.findall(r"REFERENCES\s+([a-z_]+)", ddl)) - {name})
        path = re.search(r"\[Data/([^\]]+?)(?: \(one file per organisation[^\]]*\))?\]", comment)
        self.pattern = path.group(1) if path else None

    def files(self):
        if not self.pattern:
            return []
        if "<organisation>" in self.pattern:
            return sorted(data_root().glob(self.pattern.replace("<organisation>", "*")))
        f = data_root() / self.pattern
        return [f] if f.exists() else []

    def ddl_in(self, schema):
        """The CREATE TABLE for another schema (e.g. stage), with keys and references dropped."""
        cols = ",\n".join(f"    [{c}] {t}" for c, t in self.columns)
        return f"CREATE TABLE {schema}.[{self.name}] (\n{cols}\n);"

    def ddl_dbo(self):
        return re.sub(r"REFERENCES ([a-z_]+)\(", r"REFERENCES dbo.\1(", re.sub(r"^CREATE TABLE ([a-z_]+)", r"CREATE TABLE dbo.\1", self.ddl))


def tables():
    text = schema_file().read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r"((?:--[^\n]*\n)*)(CREATE TABLE ([a-z_]+) \((?:.|\n)*?\n\);)", text):
        out[m.group(3)] = Table(m.group(3), m.group(2), m.group(1))
    return out


def load_order(ts):
    """Referenced tables first (a dimension before the facts that point at it)."""
    done, order = set(), []

    def visit(n, path=()):
        if n in done or n not in ts:
            return
        if n in path:
            raise SystemExit(f"Circular references in the schema: {' -> '.join(path + (n,))}")
        for r in ts[n].refs:
            visit(r, path + (n,))
        done.add(n)
        order.append(n)
    for n in sorted(ts):
        visit(n)
    return order
