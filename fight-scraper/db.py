"""
Postgres access helpers

Thin data-access layer bridging the DataFrame / JSON based scraping and
parsing code with the Postgres database instance:

  * read_table       -> read an entire table into a DataFrame
  * read_json_docs   -> read a table of loosely-structured JSON docs
  * upsert_records   -> insert/update typed rows (keyed upsert)
  * upsert_json_doc  -> insert/update a single JSONB card row
  * delete_doc       -> delete a row by key

Uses SQLAlchemy to interact with the Postgres database using SQL queries
and ORM actions.
"""

import math
import os

from sqlalchemy import MetaData, Table, create_engine, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

_ENGINE = None
_TABLES = {}


def _sqlalchemy_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+psycopg2://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


def get_engine():
    """Return a process-wide SQLAlchemy engine built from DATABASE_URL."""
    global _ENGINE
    if _ENGINE is None:
        url = os.environ.get(
            "DATABASE_URL", "postgres://ufc:ufc@localhost:5432/ufc?sslmode=disable"
        )
        _ENGINE = create_engine(_sqlalchemy_url(url))
    return _ENGINE


def _reflect(table: str) -> Table:
    if table not in _TABLES:
        _TABLES[table] = Table(table, MetaData(), autoload_with=get_engine())
    return _TABLES[table]


def _clean(value):
    """Coerce pandas/numpy scalars to plain Python and NaN -> None."""
    if value is None:
        return None
    # numpy scalars expose .item(); use it without importing numpy directly.
    if hasattr(value, "item") and not isinstance(value, (str, bytes, dict, list)):
        value = value.item()
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def read_table(table: str):
    """Return an entire table as a DataFrame (mirrors collection.stream())."""
    import pandas as pd  # local import so JSON-only callers need not install pandas

    return pd.read_sql(f"SELECT * FROM {table}", get_engine())


def table_columns(table: str):
    """Return a table's column names (a schema template, no rows loaded)."""
    with get_engine().connect() as conn:
        result = conn.execute(text(f"SELECT * FROM {table} LIMIT 0"))
        return list(result.keys())


def read_json_docs(table: str):
    """Return [(doc_id, data_dict), ...] for a JSONB-backed card table."""
    with get_engine().connect() as conn:
        rows = conn.execute(text(f"SELECT doc_id, data FROM {table}")).fetchall()
    return [(row[0], row[1]) for row in rows]


def upsert_records(table: str, key_col: str, records):
    """Insert/update typed rows keyed on key_col (idempotent keyed upsert).

    Only columns that exist on the target table are written; any extra keys in
    the record are ignored, so callers can pass wider records safely.
    """
    if not records:
        return
    tbl = _reflect(table)
    valid = {c.name for c in tbl.columns}
    with get_engine().begin() as conn:
        for record in records:
            row = {k: _clean(v) for k, v in record.items() if k in valid}
            if key_col not in row:
                continue
            stmt = pg_insert(tbl).values(**row)
            update_cols = {c: stmt.excluded[c] for c in row if c != key_col}
            if update_cols:
                stmt = stmt.on_conflict_do_update(index_elements=[key_col], set_=update_cols)
            else:
                stmt = stmt.on_conflict_do_nothing(index_elements=[key_col])
            conn.execute(stmt)


def upsert_json_doc(table: str, doc_id: str, doc: dict):
    """Insert/update a single JSONB doc keyed by doc_id."""
    tbl = _reflect(table)
    clean_doc = {k: _clean(v) for k, v in doc.items()}
    stmt = pg_insert(tbl).values(doc_id=doc_id, data=clean_doc)
    stmt = stmt.on_conflict_do_update(index_elements=["doc_id"], set_={"data": clean_doc})
    with get_engine().begin() as conn:
        conn.execute(stmt)


def delete_doc(table: str, doc_id: str):
    """Delete a row by doc_id (mirrors document.delete())."""
    with get_engine().begin() as conn:
        conn.execute(text(f"DELETE FROM {table} WHERE doc_id = :id"), {"id": doc_id})
