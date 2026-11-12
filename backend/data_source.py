"""Where the backend gets its data from.

This is the ONLY file that knows where data lives.
- Now:   reads fake data from JSON files in the data/ folder.
- Later: these two functions will read from PostgreSQL instead
         (filled by the fusion service). main.py won't need to change.
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"


def _read_json(filename):
    with open(DATA_DIR / filename) as f:
        return json.load(f)


def get_sensors():
    """Return a list of sensor nodes."""
    return _read_json("sensors.json")


def get_alerts():
    """Return a list of alerts."""
    return _read_json("alerts.json")
