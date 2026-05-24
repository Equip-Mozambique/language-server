Write a Python file `<<filename.py>>` containing SQLite DDL + a typed helper for inserting rows. Output Python code only. No markdown fences. No commentary.

Module docstring: """SQLite schema for <<entity name>>."""

Imports:
    from __future__ import annotations
    import sqlite3
    from typing import Any
    from <<pydantic module>> import <<PydanticModel>>

Module-level constant `SCHEMA: str` containing CREATE TABLE statements.

Mapping rules from Pydantic → SQLite types:
- `int` → INTEGER
- `float` → REAL
- `str` → TEXT
- `bool` → INTEGER (0/1)
- `datetime` → TEXT (ISO 8601)
- `bytes` → BLOB
- Optional fields → nullable column (no NOT NULL)
- Required fields → NOT NULL

For the Pydantic model `<<PydanticModel>>` with fields:
    <<field_name>>: <<type>>   # <<primary key | unique | indexed>>
    <<...>>

Generate:
- `CREATE TABLE IF NOT EXISTS <<table_name>> (...)` with PRIMARY KEY and any
  UNIQUE / NOT NULL constraints derived from the rules above.
- One `CREATE INDEX IF NOT EXISTS` per indexed column.

Function `init_db(conn: sqlite3.Connection) -> None`:
    Executes `SCHEMA` via `conn.executescript(SCHEMA)`.

Function `insert_row(conn: sqlite3.Connection, row: <<PydanticModel>>) -> None`:
    Use `conn.execute("INSERT INTO <<table_name>> (...) VALUES (...)", row.model_dump())`.

No `__main__` block. No example usage.
