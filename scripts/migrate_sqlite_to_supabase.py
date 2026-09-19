"""One-time migration helper for an existing local KisanGati SQLite database.

Usage (PowerShell):
    $env:SQLITE_SOURCE="procurement.db"
    $env:DATABASE_URL="postgresql://..."
    python scripts/migrate_sqlite_to_supabase.py

The script preserves farmer, tracking, effort, lot-trace and rejection records.
It also advances the PostgreSQL token counter so new registrations continue
from the highest imported P-token.
"""

import os
import sqlite3
from datetime import datetime

import psycopg

from database import SCHEMA_SQL


SQLITE_SOURCE = os.getenv("SQLITE_SOURCE", "procurement.db")
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")

if not DATABASE_URL:
    raise SystemExit("Set DATABASE_URL to your Supabase PostgreSQL connection string.")


def rows(conn, table):
    try:
        return conn.execute(f"SELECT * FROM {table}").fetchall()
    except sqlite3.OperationalError:
        return []


def columns(conn, table):
    try:
        return [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    except sqlite3.OperationalError:
        return []


def as_dicts(conn, table):
    cols = columns(conn, table)
    return [dict(zip(cols, row)) for row in rows(conn, table)]


def main():
    if not os.path.exists(SQLITE_SOURCE):
        raise SystemExit(f"SQLite source not found: {SQLITE_SOURCE}")

    sqlite_conn = sqlite3.connect(SQLITE_SOURCE)
    sqlite_conn.row_factory = sqlite3.Row

    with psycopg.connect(
        DATABASE_URL,
        sslmode=os.getenv("PGSSLMODE", "require"),
        prepare_threshold=None,
        connect_timeout=10,
    ) as pg:
        with pg.cursor() as cur:
            cur.execute(SCHEMA_SQL)

            farmers = as_dicts(sqlite_conn, "farmers")
            tracking = as_dicts(sqlite_conn, "shipment_tracking")
            updates = as_dicts(sqlite_conn, "tracking_updates")
            effort = as_dicts(sqlite_conn, "farmer_effort")
            lot_trace = as_dicts(sqlite_conn, "lot_trace")
            rejections = as_dicts(sqlite_conn, "rejection_records")

            for r in farmers:
                cur.execute(
                    """INSERT INTO farmers
                    (token,name,mobile,farmer_id,crop,quantity,slot,status,created_at,
                     bank_name,account_holder,account_number,ifsc_code,tracking_id)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (token) DO UPDATE SET
                      name=EXCLUDED.name, mobile=EXCLUDED.mobile,
                      farmer_id=EXCLUDED.farmer_id, crop=EXCLUDED.crop,
                      quantity=EXCLUDED.quantity, slot=EXCLUDED.slot,
                      status=EXCLUDED.status, created_at=EXCLUDED.created_at,
                      bank_name=EXCLUDED.bank_name, account_holder=EXCLUDED.account_holder,
                      account_number=EXCLUDED.account_number, ifsc_code=EXCLUDED.ifsc_code,
                      tracking_id=EXCLUDED.tracking_id""",
                    (
                        r.get("token"), r.get("name"), r.get("mobile"), r.get("farmer_id"),
                        r.get("crop"), r.get("quantity"), r.get("slot"), r.get("status"),
                        r.get("created_at") or datetime.now().isoformat(), r.get("bank_name"),
                        r.get("account_holder"), r.get("account_number"), r.get("ifsc_code"),
                        r.get("tracking_id") or (f"KG-{r.get('token')}" if r.get("token") else None),
                    ),
                )

            for r in tracking:
                cur.execute(
                    """INSERT INTO shipment_tracking
                    (token,tracking_id,stage,location_name,latitude,longitude,accuracy,last_updated,gps_active)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (token) DO UPDATE SET
                      tracking_id=EXCLUDED.tracking_id, stage=EXCLUDED.stage,
                      location_name=EXCLUDED.location_name, latitude=EXCLUDED.latitude,
                      longitude=EXCLUDED.longitude, accuracy=EXCLUDED.accuracy,
                      last_updated=EXCLUDED.last_updated, gps_active=EXCLUDED.gps_active""",
                    (
                        r.get("token"), r.get("tracking_id") or f"KG-{r.get('token')}",
                        r.get("stage") or "At Procurement Centre", r.get("location_name") or "Procurement Centre",
                        r.get("latitude"), r.get("longitude"), r.get("accuracy"), r.get("last_updated"),
                        bool(r.get("gps_active") or 0),
                    ),
                )

            for r in updates:
                cur.execute(
                    """INSERT INTO tracking_updates
                    (token,stage,location_name,latitude,longitude,accuracy,updated_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    (r.get("token"), r.get("stage"), r.get("location_name"), r.get("latitude"),
                     r.get("longitude"), r.get("accuracy"), r.get("updated_at")),
                )

            for r in effort:
                cur.execute(
                    """INSERT INTO farmer_effort
                    (token,visit_count,first_registered_at,first_quality_at,last_updated)
                    VALUES (%s,%s,%s,%s,%s)
                    ON CONFLICT (token) DO UPDATE SET
                      visit_count=EXCLUDED.visit_count,
                      first_registered_at=EXCLUDED.first_registered_at,
                      first_quality_at=EXCLUDED.first_quality_at,
                      last_updated=EXCLUDED.last_updated""",
                    (r.get("token"), r.get("visit_count") or 1, r.get("first_registered_at"),
                     r.get("first_quality_at"), r.get("last_updated")),
                )

            for r in lot_trace:
                cur.execute(
                    """INSERT INTO lot_trace
                    (token,step_key,step_name,status,detail,updated_at)
                    VALUES (%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (token,step_key) DO UPDATE SET
                      step_name=EXCLUDED.step_name, status=EXCLUDED.status,
                      detail=EXCLUDED.detail, updated_at=EXCLUDED.updated_at""",
                    (r.get("token"), r.get("step_key"), r.get("step_name"), r.get("status") or "Pending",
                     r.get("detail"), r.get("updated_at")),
                )

            for r in rejections:
                cur.execute(
                    """INSERT INTO rejection_records
                    (token,reason,guidance,created_at)
                    VALUES (%s,%s,%s,%s)""",
                    (r.get("token"), r.get("reason"), r.get("guidance"),
                     r.get("created_at") or datetime.now().isoformat()),
                )

            cur.execute("""UPDATE app_state SET next_token_number = GREATEST(
                next_token_number,
                COALESCE((SELECT MAX(CAST(SUBSTRING(token FROM 2) AS INTEGER)) + 1
                          FROM farmers WHERE token LIKE 'P%'), 101)
            ), updated_at=%s WHERE state_key='global'""", (datetime.now().isoformat(),))

        pg.commit()

    sqlite_conn.close()
    print(f"Migration complete: {SQLITE_SOURCE} -> Supabase PostgreSQL")
    print(f"Imported farmers: {len(farmers)}")
    print(f"Imported tracking records: {len(tracking)}")
    print(f"Imported GPS updates: {len(updates)}")
    print(f"Imported effort records: {len(effort)}")
    print(f"Imported lot-trace rows: {len(lot_trace)}")
    print(f"Imported rejection records: {len(rejections)}")


if __name__ == "__main__":
    main()
