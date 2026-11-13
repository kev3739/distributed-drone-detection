"""DDDS backend API (Layer 3).

Defines the endpoints the dashboard calls. It does NOT know where the
data comes from: it just asks data_source.py. To switch from fake data
to the real database later, only data_source.py changes.

Run:   uvicorn main:app --reload
Docs:  http://localhost:8000/docs
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import data_source

app = FastAPI(title="DDDS Backend", version="0.1.0")

# Let the React dashboard (running on another port) call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Quick check that the API is running."""
    return {"status": "ok"}


@app.get("/sensors")
def list_sensors():
    """All sensor nodes and their status (for the sensor health panel)."""
    return data_source.get_sensors()


@app.get("/alerts")
def list_alerts():
    """All alerts, newest first (for the alert feed)."""
    return sorted(data_source.get_alerts(), key=lambda a: a["time"], reverse=True)


@app.get("/alerts/{alert_id}")
def get_alert(alert_id: int):
    """One alert's details. Returns 404 if it doesn't exist."""
    for alert in data_source.get_alerts():
        if alert["alert_id"] == alert_id:
            return alert
    raise HTTPException(status_code=404, detail="Alert not found")
