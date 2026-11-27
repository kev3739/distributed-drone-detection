"""Where the backend gets its data: the PostgreSQL database.

This is the ONLY file in the backend that talks to the database.
The fusion service writes alerts, events and heartbeats; this file only reads them
(plus marking an alert as a false positive).
"""
import os
from contextlib import contextmanager
from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://ddds:ddds-dev@localhost:5432/ddds")
OFFLINE_AFTER_SECONDS = 15  # US-07: 3 missed heartbeats (one every 5 s)


@contextmanager
def _db():
    with psycopg.connect(DATABASE_URL, row_factory=dict_row, autocommit=True) as conn:
        yield conn


def _iso(t):
    return t.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z") if t else None


def _alert(row):
    """Turn a database row into the JSON shape the dashboard expects."""
    return {
        "alert_id": row["alert_id"],
        "time": _iso(row["first_seen"]),
        "last_seen": _iso(row["last_seen"]),
        "kind": row["kind"],
        "sources": row["sources"],
        "drone_class": row["drone_class"],
        "confidence": row["confidence"],
        "location": ({"lat": row["lat"], "lon": row["lon"], "alt_m": row["alt_m"]}
                     if row["lat"] is not None else None),
        "bearing_deg": row["bearing_deg"],
        "rid_serial": row["rid_serial"],
        "false_positive": row["false_positive"],
    }


def is_up():
    try:
        with _db() as db:
            db.execute("SELECT 1")
        return True
    except psycopg.Error:
        return False


def get_sensors():
    with _db() as db:
        rows = db.execute(
            """SELECT s.*, h.last_heartbeat, h.fps,
                      EXTRACT(EPOCH FROM now() - h.last_heartbeat) AS seconds_ago
               FROM sensors s LEFT JOIN heartbeats h USING (node_id)
               ORDER BY s.node_id""").fetchall()
    sensors = []
    for r in rows:
        online = r["seconds_ago"] is not None and r["seconds_ago"] <= OFFLINE_AFTER_SECONDS
        sensors.append({
            "node_id": r["node_id"], "type": r["type"], "lat": r["lat"], "lon": r["lon"],
            "facing_deg": r["facing_deg"],
            "status": "online" if online else "offline",
            "last_heartbeat": _iso(r["last_heartbeat"]),
            "seconds_since_heartbeat": round(float(r["seconds_ago"]), 1) if r["seconds_ago"] is not None else None,
            "fps": r["fps"] if online else None,
        })
    return sensors


def get_alerts(start=None, end=None, limit=200):
    """Alerts newest first, optionally only between two times (US-13 history search)."""
    with _db() as db:
        rows = db.execute(
            """SELECT * FROM alerts
               WHERE kind IS NOT NULL
                 AND (%(start)s::timestamptz IS NULL OR first_seen >= %(start)s)
                 AND (%(end)s::timestamptz IS NULL OR first_seen <= %(end)s)
               ORDER BY first_seen DESC LIMIT %(limit)s""",
            {"start": start, "end": end, "limit": limit}).fetchall()
    return [_alert(r) for r in rows]


def get_alert(alert_id):
    with _db() as db:
        row = db.execute("SELECT * FROM alerts WHERE alert_id = %s AND kind IS NOT NULL",
                         (alert_id,)).fetchone()
    return _alert(row) if row else None


def get_alert_events(alert_id):
    """The raw sensor events that were fused into this alert."""
    with _db() as db:
        rows = db.execute("SELECT payload FROM events WHERE alert_id = %s ORDER BY ts_utc",
                          (alert_id,)).fetchall()
    return [r["payload"] for r in rows]


def get_events(since=None, limit=200):
    """Raw sensor events, oldest first, optionally only after a time (IF-06 /events?since=)."""
    with _db() as db:
        rows = db.execute(
            """SELECT payload FROM events
               WHERE %(since)s::timestamptz IS NULL OR ts_utc > %(since)s
               ORDER BY ts_utc LIMIT %(limit)s""",
            {"since": since, "limit": limit}).fetchall()
    return [r["payload"] for r in rows]


def mark_false_positive(alert_id):
    with _db() as db:
        n = db.execute("UPDATE alerts SET false_positive = TRUE, updated_at = now() WHERE alert_id = %s",
                       (alert_id,)).rowcount
    return n == 1


def get_version():
    """Changes whenever any alert is created or updated (the live stream watches this)."""
    with _db() as db:
        row = db.execute("SELECT count(*) AS n, max(updated_at) AS t FROM alerts").fetchone()
    return f"{row['n']}:{row['t']}"
