"""Tests for the fusion service's database logic (needs PostgreSQL; skipped if none)."""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db as fusion_db
from fusion import fuse


def cam(ts, node="cv-01", bearing=45):
    return {"schema": "ddds.event.v1", "node_id": node, "type": "camera", "ts_utc": ts,
            "class": "drone", "confidence": 0.8, "bearing_deg": bearing}


def rid(ts):
    return {"schema": "ddds.event.v1", "node_id": "rf-01", "type": "remote_id", "ts_utc": ts,
            "class": "DJI", "confidence": 0.95, "lat": 43.774, "lon": -79.502, "alt": 60,
            "rid_serial": "1581F5FJD239C00A1B2C"}


def alerts(db):
    return db.execute("SELECT alert_id, kind, sources FROM alerts ORDER BY alert_id").fetchall()


def test_camera_and_rf_within_3s_become_one_fused_alert(db):
    a = fusion_db.process_event(db, cam("2026-11-27T15:00:00Z"))
    b = fusion_db.process_event(db, rid("2026-11-27T15:00:01Z"))
    assert a == b
    assert alerts(db) == [(a, "fused", ["cv-01", "rf-01"])]


def test_events_far_apart_become_two_alerts(db):
    fusion_db.process_event(db, cam("2026-11-27T15:00:00Z"))
    fusion_db.process_event(db, rid("2026-11-27T15:00:10Z"))
    assert [k for _, k, _ in alerts(db)] == ["camera", "remote_id"]


def test_invalid_event_is_rejected_and_logged(db):
    bad = cam("2026-11-27T15:00:00Z")
    del bad["bearing_deg"]
    assert fusion_db.process_event(db, bad) is None
    assert alerts(db) == []
    assert db.execute("SELECT count(*) FROM rejected_events").fetchone()[0] == 1


def test_replay_gives_same_alerts_as_fusion_logic(db):
    """US-08: replaying a recorded session produces the same fused alerts."""
    sample = json.loads((Path(__file__).resolve().parent.parent / "sample_events.json").read_text())
    for event in sample:
        fusion_db.process_event(db, event)
    expected = [a["sources"] for a in fuse(sample)]
    assert [s for _, _, s in alerts(db)] == expected


def test_heartbeat_updates_sensor(db):
    assert fusion_db.record_heartbeat(db, {"node_id": "cv-01", "fps": 2.0})
    assert db.execute("SELECT fps FROM heartbeats WHERE node_id = 'cv-01'").fetchone()[0] == 2.0


def test_unknown_sensor_heartbeat_ignored_unless_it_registers(db):
    assert not fusion_db.record_heartbeat(db, {"node_id": "ac-01"})
    assert fusion_db.record_heartbeat(db, {"node_id": "ac-01", "type": "acoustic"})


def test_retention_deletes_events_older_than_30_days(db):
    fusion_db.process_event(db, rid("2026-01-01T00:00:00Z"))
    fusion_db.process_event(db, rid("2026-11-27T15:00:00Z"))
    now = datetime(2026, 11, 27, 16, tzinfo=timezone.utc)
    assert fusion_db.apply_retention(db, now) == 1
    old = db.execute("SELECT rid_serial FROM alerts ORDER BY first_seen LIMIT 1").fetchone()[0]
    assert old is None
