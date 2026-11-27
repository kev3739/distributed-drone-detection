"""Tests for the backend API (needs PostgreSQL; skipped if none). Run from backend/:  pytest"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

import data_source
from main import app
from conftest import TEST_DB

client = TestClient(app)


@pytest.fixture(autouse=True)
def use_test_db(db, monkeypatch):
    monkeypatch.setattr(data_source, "DATABASE_URL", TEST_DB)
    return db


def add_alert(db, first_seen, kind="fused", lat=43.774):
    return db.execute(
        """INSERT INTO alerts (first_seen, last_seen, kind, sources, drone_class, confidence,
                               lat, lon, alt_m, bearing_deg, rid_serial)
           VALUES (%s, %s, %s, ARRAY['cv-01','rf-01'], 'DJI', 0.9, %s, -79.502, 60, 45, '1581F5')
           RETURNING alert_id""", (first_seen, first_seen, kind, lat)).fetchone()[0]


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_alerts_newest_first(db):
    add_alert(db, "2026-11-27T15:00:00Z")
    add_alert(db, "2026-11-27T15:05:00Z")
    times = [a["time"] for a in client.get("/alerts").json()]
    assert times == sorted(times, reverse=True)


def test_history_search_by_time(db):
    add_alert(db, "2026-11-01T12:00:00Z")
    add_alert(db, "2026-11-27T15:00:00Z")
    found = client.get("/alerts", params={"from": "2026-11-20T00:00:00Z"}).json()
    assert len(found) == 1


def test_get_one_alert_and_404(db):
    alert_id = add_alert(db, "2026-11-27T15:00:00Z")
    body = client.get(f"/alerts/{alert_id}").json()
    assert body["location"]["lat"] == 43.774
    assert client.get("/alerts/999").status_code == 404


def test_camera_only_alert_has_no_location(db):
    alert_id = add_alert(db, "2026-11-27T15:00:00Z", kind="camera", lat=None)
    assert client.get(f"/alerts/{alert_id}").json()["location"] is None


def test_mark_false_positive(db):
    alert_id = add_alert(db, "2026-11-27T15:00:00Z")
    assert client.post(f"/alerts/{alert_id}/false-positive").status_code == 200
    assert client.get(f"/alerts/{alert_id}").json()["false_positive"] is True
    assert client.post("/alerts/999/false-positive").status_code == 404


def test_sensor_online_with_recent_heartbeat(db):
    db.execute("INSERT INTO heartbeats VALUES ('cv-01', now(), 2.0)")
    cv01 = next(s for s in client.get("/sensors").json() if s["node_id"] == "cv-01")
    assert cv01["status"] == "online" and cv01["fps"] == 2.0


def test_sensor_offline_after_15_seconds(db):
    """US-07: no heartbeat for more than 15 s -> offline."""
    db.execute("INSERT INTO heartbeats VALUES ('cv-01', now() - interval '16 seconds', 2.0)")
    cv01 = next(s for s in client.get("/sensors").json() if s["node_id"] == "cv-01")
    assert cv01["status"] == "offline"


def test_sensor_never_seen_is_offline():
    assert all(s["status"] == "offline" for s in client.get("/sensors").json())


def test_events_since(db):
    alert_id = add_alert(db, "2026-11-27T15:00:00Z")
    for ts in ("2026-11-27T15:00:00Z", "2026-11-27T15:00:01Z"):
        db.execute("INSERT INTO events (node_id, type, ts_utc, payload, alert_id) "
                   "VALUES ('cv-01', 'camera', %s, %s, %s)", (ts, f'{{"ts_utc": "{ts}"}}', alert_id))
    assert len(client.get("/events").json()) == 2
    assert len(client.get("/events", params={"since": "2026-11-27T15:00:00Z"}).json()) == 1
    assert len(client.get(f"/alerts/{alert_id}/events").json()) == 2
