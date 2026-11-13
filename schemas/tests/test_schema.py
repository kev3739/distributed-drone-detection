"""Tests for event schema v1. Run from the schemas folder:  pytest"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from validate import errors_for


def load(path):
    return json.loads(Path(path).read_text())


def test_camera_example_is_valid():
    assert errors_for(load(HERE / "examples/camera_event.json")) == []


def test_remote_id_example_is_valid():
    assert errors_for(load(HERE / "examples/remote_id_event.json")) == []


def test_fusion_sample_events_are_valid():
    for event in load(HERE.parent / "fusion/sample_events.json"):
        assert errors_for(event) == []


def test_missing_required_field_is_rejected():
    event = load(HERE / "examples/camera_event.json")
    del event["node_id"]
    assert errors_for(event) != []


def test_camera_without_bearing_is_rejected():
    event = load(HERE / "examples/camera_event.json")
    del event["bearing_deg"]
    assert errors_for(event) != []


def test_remote_id_without_gps_is_rejected():
    event = load(HERE / "examples/remote_id_event.json")
    del event["lat"]
    assert errors_for(event) != []


def test_confidence_above_1_is_rejected():
    event = load(HERE / "examples/camera_event.json")
    event["confidence"] = 1.5
    assert errors_for(event) != []


def test_new_sensor_type_is_allowed():
    """US-06: a new sensor type can publish without changing the schema."""
    event = {"schema": "ddds.event.v1", "node_id": "ac-01", "type": "acoustic",
             "ts_utc": "2026-11-13T15:00:00Z", "class": "drone", "confidence": 0.6}
    assert errors_for(event) == []
