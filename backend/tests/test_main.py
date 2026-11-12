"""Tests for the backend API. Run from the backend folder:  pytest"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_sensors_have_status():
    r = client.get("/sensors")
    assert r.status_code == 200
    for sensor in r.json():
        assert sensor["status"] in ("online", "offline")


def test_alerts_newest_first():
    times = [a["time"] for a in client.get("/alerts").json()]
    assert times == sorted(times, reverse=True)


def test_every_alert_has_a_position_or_bearing():
    for alert in client.get("/alerts").json():
        assert alert["location"] is not None or alert["bearing_deg"] is not None


def test_get_one_alert():
    r = client.get("/alerts/1")
    assert r.status_code == 200
    assert r.json()["alert_id"] == 1


def test_missing_alert_returns_404():
    assert client.get("/alerts/999").status_code == 404
