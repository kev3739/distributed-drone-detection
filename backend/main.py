"""DDDS backend API (Layer 3).

The web addresses (endpoints) the dashboard uses. It never touches the
database directly: it always asks data_source.py.

Run:   uvicorn main:app --reload     (or: docker compose up)
Docs:  http://localhost:8000/docs
"""
import asyncio
import json
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

import data_source

app = FastAPI(title="DDDS Backend", version="1.0.0")

# Let the React dashboard (running on another port) call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Is the API running, and can it reach the database?"""
    if not data_source.is_up():
        raise HTTPException(status_code=503, detail="database unavailable")
    return {"status": "ok"}


@app.get("/sensors")
def list_sensors():
    """All sensor nodes, where they are, and whether they're online (US-07, US-12)."""
    return data_source.get_sensors()


@app.get("/alerts")
def list_alerts(start: datetime | None = Query(None, alias="from"),
                end: datetime | None = Query(None, alias="to"),
                limit: int = Query(200, ge=1, le=1000)):
    """Alerts, newest first. Use ?from= and ?to= to search history (US-13)."""
    return data_source.get_alerts(start, end, limit)


@app.get("/alerts/{alert_id}")
def get_alert(alert_id: int):
    """One alert's details. Returns 404 if it doesn't exist."""
    alert = data_source.get_alert(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@app.get("/alerts/{alert_id}/events")
def get_alert_events(alert_id: int):
    """The raw sensor events that fusion merged into this alert."""
    get_alert(alert_id)  # 404 if it doesn't exist
    return data_source.get_alert_events(alert_id)


@app.post("/alerts/{alert_id}/false-positive")
def mark_false_positive(alert_id: int):
    """The operator says this alert was wrong (US-11)."""
    if not data_source.mark_false_positive(alert_id):
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"ok": True}


@app.get("/events")
def list_events(since: datetime | None = None, limit: int = Query(200, ge=1, le=1000)):
    """Raw sensor events, oldest first, optionally only after ?since= (IF-06)."""
    return data_source.get_events(since, limit)


@app.get("/stream/alerts")
async def stream_alerts():
    """Live feed (Server-Sent Events): sends the latest alerts every time they change."""
    async def updates():
        last_version = None
        while True:
            version = await asyncio.to_thread(data_source.get_version)
            if version != last_version:
                last_version = version
                alerts = await asyncio.to_thread(data_source.get_alerts)
                yield f"data: {json.dumps(alerts)}\n\n"
            await asyncio.sleep(0.5)
    return StreamingResponse(updates(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache"})
