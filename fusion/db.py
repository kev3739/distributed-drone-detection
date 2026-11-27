"""Everything the fusion service writes to PostgreSQL.

Kept separate from service.py so it can be tested without NATS.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "schemas"))

from fusion import WINDOW_SECONDS, make_alert  # our fusion logic
from validate import errors_for                # our event schema checker

RETENTION_DAYS = 30  # BL-21: Remote ID data is deleted after 30 days


def parse_time(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def process_event(conn, event):
    """Handle one detection event: check it, save it, and fuse it into an alert.

    Returns the alert_id it became part of, or None if the event was rejected.
    """
    problems = errors_for(event)
    if problems:
        conn.execute("INSERT INTO rejected_events (payload, problems) VALUES (%s, %s)",
                     (json.dumps(event), problems))
        return None

    ts = parse_time(event["ts_utc"])
    window = timedelta(seconds=WINDOW_SECONDS)
    with conn.transaction():
        # 1. Is there an alert that was active within 3 seconds of this event? -> same drone
        row = conn.execute(
            """SELECT alert_id FROM alerts
               WHERE last_seen BETWEEN %s AND %s
               ORDER BY last_seen DESC LIMIT 1 FOR UPDATE""",
            (ts - window, ts + window)).fetchone()
        if row:
            alert_id = row[0]
        else:
            # 2. No -> this is a new drone: create a new alert
            alert_id = conn.execute(
                "INSERT INTO alerts (first_seen, last_seen) VALUES (%s, %s) RETURNING alert_id",
                (ts, ts)).fetchone()[0]

        # 3. Save the event, linked to its alert
        conn.execute(
            "INSERT INTO events (node_id, type, ts_utc, payload, alert_id) VALUES (%s, %s, %s, %s, %s)",
            (event["node_id"], event["type"], ts, json.dumps(event), alert_id))

        # 4. Rebuild the alert from all of its events using the fusion logic
        group = [r[0] for r in conn.execute(
            "SELECT payload FROM events WHERE alert_id = %s ORDER BY ts_utc", (alert_id,))]
        _update_alert(conn, alert_id, group)
    return alert_id


def _update_alert(conn, alert_id, group):
    alert = make_alert(alert_id, group)
    types = {e["type"] for e in group}
    kind = "fused" if len(types) > 1 else types.pop()
    loc = alert["location"] or {}
    conn.execute(
        """UPDATE alerts SET first_seen = %s, last_seen = %s, kind = %s, sources = %s,
               drone_class = %s, confidence = %s, lat = %s, lon = %s, alt_m = %s,
               bearing_deg = %s, rid_serial = %s, updated_at = now()
           WHERE alert_id = %s""",
        (parse_time(group[0]["ts_utc"]), parse_time(group[-1]["ts_utc"]), kind, alert["sources"],
         alert["drone_class"], alert["confidence"], loc.get("lat"), loc.get("lon"), loc.get("alt_m"),
         alert["bearing_deg"], alert["rid_serial"], alert_id))


def record_heartbeat(conn, hb):
    """A sensor says 'I'm alive'. A new sensor is registered automatically if it says what type it is."""
    node_id = hb["node_id"]
    if hb.get("type"):
        conn.execute(
            """INSERT INTO sensors (node_id, type, lat, lon, facing_deg) VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT (node_id) DO NOTHING""",
            (node_id, hb["type"], hb.get("lat"), hb.get("lon"), hb.get("facing_deg")))
    known = conn.execute("SELECT 1 FROM sensors WHERE node_id = %s", (node_id,)).fetchone()
    if not known:
        return False
    conn.execute(
        """INSERT INTO heartbeats (node_id, last_heartbeat, fps) VALUES (%s, now(), %s)
           ON CONFLICT (node_id) DO UPDATE SET last_heartbeat = now(), fps = EXCLUDED.fps""",
        (node_id, hb.get("fps")))
    return True


def apply_retention(conn, now=None):
    """BL-21: delete events older than 30 days and wipe Remote ID details from old alerts."""
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=RETENTION_DAYS)
    deleted = conn.execute("DELETE FROM events WHERE ts_utc < %s", (cutoff,)).rowcount
    conn.execute(
        """UPDATE alerts SET rid_serial = NULL, lat = NULL, lon = NULL, alt_m = NULL
           WHERE last_seen < %s AND rid_serial IS NOT NULL""", (cutoff,))
    return deleted
