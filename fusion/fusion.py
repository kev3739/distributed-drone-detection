"""Fusion service v0 (US-09).

Takes detection events from the sensors (camera and Remote ID) and
merges events that happen close together in time into ONE alert.

Rule (v0): events less than WINDOW_SECONDS apart = the same drone.

Run:  python fusion.py        (fuses sample_events.json and prints the alerts)
"""
import json
from datetime import datetime
from pathlib import Path

WINDOW_SECONDS = 3


def _time(event):
    """Turn the event's timestamp text into a real time we can compare."""
    return datetime.fromisoformat(event["ts_utc"].replace("Z", "+00:00"))


def group_events(events, window_seconds=WINDOW_SECONDS):
    """Put events that are close in time into the same group."""
    groups = []
    for event in sorted(events, key=_time):
        last_group = groups[-1] if groups else None
        if last_group and (_time(event) - _time(last_group[-1])).total_seconds() <= window_seconds:
            last_group.append(event)      # close in time -> same drone
        else:
            groups.append([event])        # too far apart -> new drone
    return groups


def make_alert(alert_id, group):
    """Combine one group of events into a single alert."""
    rf = next((e for e in group if e["type"] == "remote_id"), None)
    cv = next((e for e in group if e["type"] == "camera"), None)
    return {
        "alert_id": alert_id,
        "time": group[0]["ts_utc"],
        "sources": sorted({e["node_id"] for e in group}),
        # Remote ID knows the manufacturer, so prefer it; otherwise use the first event's class
        "drone_class": rf["class"] if rf else group[0]["class"],
        "confidence": max(e["confidence"] for e in group),
        # GPS position only comes from Remote ID; direction only from the camera
        "location": {"lat": rf["lat"], "lon": rf["lon"], "alt_m": rf["alt"]} if rf else None,
        "bearing_deg": cv["bearing_deg"] if cv else None,
        "rid_serial": rf["rid_serial"] if rf else None,
    }


def fuse(events, window_seconds=WINDOW_SECONDS):
    """Main function: events in, alerts out."""
    groups = group_events(events, window_seconds)
    return [make_alert(i + 1, g) for i, g in enumerate(groups)]


if __name__ == "__main__":
    events = json.loads((Path(__file__).parent / "sample_events.json").read_text())
    alerts = fuse(events)
    print(f"{len(events)} events in -> {len(alerts)} alerts out\n")
    print(json.dumps(alerts, indent=2))
