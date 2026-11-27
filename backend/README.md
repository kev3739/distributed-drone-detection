# backend

The API the dashboard uses (Layer 3). FastAPI, reading from PostgreSQL. Owner: Kevin.

| Endpoint | What it returns |
|---|---|
| `GET /health` | ok if the API and database are up |
| `GET /sensors` | every sensor node, its position, and online/offline (offline after 15 s without a heartbeat, US-07) |
| `GET /alerts?from=&to=` | fused alerts, newest first; `from`/`to` search history (US-13) |
| `GET /alerts/{id}` | one alert |
| `GET /alerts/{id}/events` | the raw sensor events fusion merged into that alert |
| `POST /alerts/{id}/false-positive` | operator marks an alert as wrong (US-11) |
| `GET /events?since=` | raw sensor events (IF-06) |
| `GET /stream/alerts` | live feed (Server-Sent Events): pushes the alert list whenever it changes |

Files: `main.py` (endpoints only), `data_source.py` (the only file that talks to the database).
Tests: `pytest` (needs PostgreSQL; see the main README).
