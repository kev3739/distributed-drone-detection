"""Tests for fusion v0. Run from the fusion folder:  pytest"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fusion import fuse


def cam(ts, bearing=90, conf=0.8):
    return {"node_id": "cv-01", "type": "camera", "ts_utc": ts,
            "class": "drone", "confidence": conf, "bearing_deg": bearing}


def rid(ts, conf=0.95):
    return {"node_id": "rf-01", "type": "remote_id", "ts_utc": ts,
            "class": "DJI", "confidence": conf,
            "lat": 43.77, "lon": -79.50, "alt": 60, "rid_serial": "ABC123"}


def test_camera_and_rf_close_together_become_one_alert():
    alerts = fuse([cam("2026-11-13T15:00:00Z"), rid("2026-11-13T15:00:02Z")])
    assert len(alerts) == 1
    assert alerts[0]["sources"] == ["cv-01", "rf-01"]


def test_events_far_apart_stay_separate():
    alerts = fuse([cam("2026-11-13T15:00:00Z"), rid("2026-11-13T15:00:10Z")])
    assert len(alerts) == 2


def test_fused_alert_uses_rf_model_and_location_and_camera_bearing():
    alert = fuse([cam("2026-11-13T15:00:00Z", bearing=120), rid("2026-11-13T15:00:01Z")])[0]
    assert alert["drone_class"] == "DJI"
    assert alert["location"]["lat"] == 43.77
    assert alert["bearing_deg"] == 120


def test_confidence_is_the_highest():
    alert = fuse([cam("2026-11-13T15:00:00Z", conf=0.6), rid("2026-11-13T15:00:01Z", conf=0.9)])[0]
    assert alert["confidence"] == 0.9


def test_camera_only_alert_has_no_location():
    alert = fuse([cam("2026-11-13T15:00:00Z")])[0]
    assert alert["location"] is None
    assert alert["rid_serial"] is None


def test_order_of_events_does_not_matter():
    a = fuse([cam("2026-11-13T15:00:00Z"), rid("2026-11-13T15:00:01Z")])
    b = fuse([rid("2026-11-13T15:00:01Z"), cam("2026-11-13T15:00:00Z")])
    assert len(a) == len(b) == 1


def test_new_sensor_type_works_without_code_changes():
    """US-06: a mock third sensor (acoustic) is fused with no changes to fusion.py."""
    acoustic = {"node_id": "ac-01", "type": "acoustic", "ts_utc": "2026-11-13T15:00:00Z",
                "class": "drone", "confidence": 0.6}
    alerts = fuse([acoustic, cam("2026-11-13T15:00:01Z")])
    assert len(alerts) == 1
    assert alerts[0]["sources"] == ["ac-01", "cv-01"]
