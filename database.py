import os
import threading
from datetime import datetime
from decimal import Decimal

import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")

_SCHEMA_READY = False
_SCHEMA_LOCK = threading.Lock()

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS farmers (
    id BIGSERIAL PRIMARY KEY,
    token TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    mobile TEXT NOT NULL,
    farmer_id TEXT,
    crop TEXT NOT NULL,
    quantity DOUBLE PRECISION NOT NULL,
    slot TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    bank_name TEXT,
    account_holder TEXT,
    account_number TEXT,
    ifsc_code TEXT,
    tracking_id TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS shipment_tracking (
    id BIGSERIAL PRIMARY KEY,
    token TEXT NOT NULL UNIQUE REFERENCES farmers(token) ON DELETE CASCADE,
    tracking_id TEXT NOT NULL UNIQUE,
    stage TEXT NOT NULL DEFAULT 'At Procurement Centre',
    location_name TEXT NOT NULL DEFAULT 'Procurement Centre',
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    accuracy DOUBLE PRECISION,
    last_updated TEXT,
    gps_active BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS tracking_updates (
    id BIGSERIAL PRIMARY KEY,
    token TEXT NOT NULL REFERENCES farmers(token) ON DELETE CASCADE,
    stage TEXT,
    location_name TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    accuracy DOUBLE PRECISION,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS farmer_effort (
    token TEXT PRIMARY KEY REFERENCES farmers(token) ON DELETE CASCADE,
    visit_count INTEGER NOT NULL DEFAULT 1,
    first_registered_at TEXT,
    first_quality_at TEXT,
    last_updated TEXT
);

CREATE TABLE IF NOT EXISTS lot_trace (
    id BIGSERIAL PRIMARY KEY,
    token TEXT NOT NULL REFERENCES farmers(token) ON DELETE CASCADE,
    step_key TEXT NOT NULL,
    step_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pending',
    detail TEXT,
    updated_at TEXT,
    UNIQUE(token, step_key)
);

CREATE TABLE IF NOT EXISTS rejection_records (
    id BIGSERIAL PRIMARY KEY,
    token TEXT NOT NULL REFERENCES farmers(token) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    guidance TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS app_state (
    state_key TEXT PRIMARY KEY,
    current_queue_token INTEGER NOT NULL DEFAULT 97,
    next_token_number INTEGER NOT NULL DEFAULT 101,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_farmers_created_at ON farmers(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_farmers_mobile ON farmers(mobile);
CREATE INDEX IF NOT EXISTS idx_tracking_updates_token ON tracking_updates(token, id DESC);
CREATE INDEX IF NOT EXISTS idx_lot_trace_token ON lot_trace(token, id);
CREATE INDEX IF NOT EXISTS idx_rejections_token ON rejection_records(token, id DESC);

INSERT INTO app_state(state_key, current_queue_token, next_token_number, updated_at)
VALUES ('global', 97, 101, CURRENT_TIMESTAMP::text)
ON CONFLICT (state_key) DO NOTHING;
"""


def _adapt_sql(sql):
    # KisanGati's existing Flask code uses SQLite-style ? placeholders.
    # Psycopg/PostgreSQL uses %s, so adapt only the SQL passed to execute().
    return sql.replace("?", "%s")


def _normalize_db_value(value):
    """Convert PostgreSQL Decimal/numeric values to normal Python numbers.

    Supabase/PostgreSQL may return NUMERIC columns as decimal.Decimal while
    older SQLite-based KisanGati code expects float/int values. Normalizing
    values at the database boundary prevents float-vs-Decimal arithmetic
    errors throughout the application.
    """
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, tuple):
        return tuple(_normalize_db_value(v) for v in value)
    if isinstance(value, list):
        return [_normalize_db_value(v) for v in value]
    if isinstance(value, dict):
        return {k: _normalize_db_value(v) for k, v in value.items()}
    return value


class CursorAdapter:
    """Cursor wrapper that normalizes PostgreSQL numeric results."""

    def __init__(self, raw_cursor):
        self._raw = raw_cursor

    def execute(self, sql, params=None):
        self._raw.execute(_adapt_sql(sql), params or ())
        return self

    def executemany(self, sql, params_seq):
        self._raw.executemany(_adapt_sql(sql), params_seq)
        return self

    def fetchone(self):
        row = self._raw.fetchone()
        return _normalize_db_value(row) if row is not None else None

    def fetchall(self):
        rows = self._raw.fetchall()
        return _normalize_db_value(rows)

    def fetchmany(self, size=None):
        rows = self._raw.fetchmany() if size is None else self._raw.fetchmany(size)
        return _normalize_db_value(rows)

    def __iter__(self):
        for row in self._raw:
            yield _normalize_db_value(row)

    def __enter__(self):
        self._raw.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self._raw.__exit__(exc_type, exc_value, traceback)

    def __getattr__(self, name):
        return getattr(self._raw, name)


class DatabaseConnection:
    """Small compatibility wrapper around a psycopg connection."""

    def __init__(self, raw):
        self._raw = raw

    def execute(self, sql, params=None):
        cursor = self._raw.execute(_adapt_sql(sql), params or ())
        return CursorAdapter(cursor)

    def cursor(self, *args, **kwargs):
        return CursorAdapter(self._raw.cursor(*args, **kwargs))

    def commit(self):
        return self._raw.commit()

    def rollback(self):
        return self._raw.rollback()

    def close(self):
        # Routes in the original app call close() after each request.
        # Closing the actual socket is fine with Supavisor transaction pooling.
        return self._raw.close()

    def __getattr__(self, name):
        return getattr(self._raw, name)


def _connect():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not configured. Add the Supabase PostgreSQL "
            "Transaction Pooler connection string to Vercel Environment Variables."
        )
    return psycopg.connect(
        DATABASE_URL,
        sslmode=os.getenv("PGSSLMODE", "require"),
        prepare_threshold=None,
        connect_timeout=8,
    )


def _ensure_schema(conn):
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return
    with _SCHEMA_LOCK:
        if _SCHEMA_READY:
            return
        try:
            with conn.cursor() as cur:
                cur.execute(SCHEMA_SQL)

                # Backward-compatible migration for older KisanGati Supabase tables.
                # CREATE TABLE IF NOT EXISTS does not add columns to an existing table.
                legacy_columns = {
                    "farmers": {
                        "bank_name": "TEXT",
                        "account_holder": "TEXT",
                        "account_number": "TEXT",
                        "ifsc_code": "TEXT",
                        "tracking_id": "TEXT",
                    },
                    "shipment_tracking": {
                        "tracking_id": "TEXT",
                        "stage": "TEXT",
                        "location_name": "TEXT",
                        "latitude": "DOUBLE PRECISION",
                        "longitude": "DOUBLE PRECISION",
                        "accuracy": "DOUBLE PRECISION",
                        "last_updated": "TEXT",
                        "gps_active": "BOOLEAN DEFAULT FALSE",
                    },
                    "tracking_updates": {
                        "stage": "TEXT",
                        "location_name": "TEXT",
                        "latitude": "DOUBLE PRECISION",
                        "longitude": "DOUBLE PRECISION",
                        "accuracy": "DOUBLE PRECISION",
                        "updated_at": "TEXT",
                    },
                }

                for table, columns in legacy_columns.items():
                    for column, column_type in columns.items():
                        cur.execute(
                            f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS "{column}" {column_type}'
                        )

            conn.commit()
            _SCHEMA_READY = True
        except Exception:
            conn.rollback()
            raise


def db():
    """Return a short-lived PostgreSQL connection backed by Supabase.

    Vercel invokes Flask in serverless instances, so the application never
    stores business data on the local filesystem. The Supabase pooler keeps
    database connections manageable across short-lived invocations.
    """
    conn = _connect()
    try:
        _ensure_schema(conn)
        return DatabaseConnection(conn)
    except Exception:
        conn.close()
        raise


def allocate_token_number(conn):
    """Atomically allocate the next farmer token number."""
    with conn.cursor() as cur:
        # Keep the counter ahead of any imported/pre-seeded P-token records.
        cur.execute(
            """UPDATE app_state
               SET next_token_number = GREATEST(
                   next_token_number,
                   COALESCE((SELECT MAX(CAST(SUBSTRING(token FROM 2) AS INTEGER)) + 1
                             FROM farmers WHERE LEFT(token, 1) = 'P'), 101)
               ),
                   updated_at = %s
               WHERE state_key = 'global'""",
            (datetime.now().isoformat(),),
        )
        cur.execute(
            """UPDATE app_state
               SET next_token_number = next_token_number + 1,
                   updated_at = %s
               WHERE state_key = 'global'
               RETURNING next_token_number - 1""",
            (datetime.now().isoformat(),),
        )
        row = cur.fetchone()
    if not row:
        raise RuntimeError("KisanGati app state is not initialized.")
    return int(row[0])


def get_current_queue_token(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT current_queue_token FROM app_state WHERE state_key='global'")
        row = cur.fetchone()
    return int(row[0]) if row else 97


def advance_queue_token(conn):
    """Atomically advance the shared queue token and return its new value."""
    with conn.cursor() as cur:
        cur.execute(
            """UPDATE app_state
               SET current_queue_token = LEAST(999, current_queue_token + 1),
                   updated_at = %s
               WHERE state_key = 'global'
               RETURNING current_queue_token""",
            (datetime.now().isoformat(),),
        )
        row = cur.fetchone()
    if not row:
        raise RuntimeError("KisanGati app state is not initialized.")
    return int(row[0])
