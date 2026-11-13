"""Check that an event (or a list of events) follows the event schema v1.

Run:  python validate.py examples/camera_event.json
"""
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMA = json.loads((Path(__file__).parent / "event.v1.json").read_text())
_validator = Draft202012Validator(SCHEMA)


def errors_for(event):
    """Return a list of problems with this event (empty list = valid)."""
    return [e.message for e in _validator.iter_errors(event)]


if __name__ == "__main__":
    data = json.loads(Path(sys.argv[1]).read_text())
    events = data if isinstance(data, list) else [data]
    bad = 0
    for i, event in enumerate(events, start=1):
        problems = errors_for(event)
        if problems:
            bad += 1
            print(f"Event {i}: INVALID -> {'; '.join(problems)}")
        else:
            print(f"Event {i}: OK")
    sys.exit(1 if bad else 0)
