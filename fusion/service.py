"""Fusion service (Layer 2).

Listens to the NATS event bus, and for every message:
- ddds.events.<type>.<node_id>  -> check it, save it, fuse it into an alert (db.process_event)
- ddds.heartbeats.<node_id>     -> mark that sensor as alive (db.record_heartbeat)

Events are kept on the bus for 24 hours (JetStream), so if this service restarts
it picks up where it left off, and a recorded session can be replayed (US-08).

Run:  python service.py      (normally started by docker compose)
"""
import asyncio
import json
import os

import nats
import psycopg
from nats.js.api import StreamConfig

import db

NATS_URL = os.environ.get("NATS_URL", "nats://ddds:ddds-dev@localhost:4222")
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://ddds:ddds-dev@localhost:5432/ddds")

STREAM = StreamConfig(name="DDDS_EVENTS", subjects=["ddds.events.>"], max_age=24 * 60 * 60)


async def connect_with_retry(connect, what):
    """Keep trying until the database / bus is up (they may start slower than us)."""
    for attempt in range(30):
        try:
            return await connect()
        except Exception as e:
            print(f"waiting for {what} ({e.__class__.__name__}), retry {attempt + 1}/30")
            await asyncio.sleep(2)
    raise SystemExit(f"could not connect to {what}")


async def main():
    conn = await connect_with_retry(
        lambda: psycopg.AsyncConnection.connect(DATABASE_URL), "PostgreSQL")
    await conn.close()  # just checking it's up; db.py uses a normal connection below
    pg = psycopg.connect(DATABASE_URL, autocommit=True)

    nc = await connect_with_retry(lambda: nats.connect(NATS_URL), "NATS")
    js = nc.jetstream()
    try:
        await js.add_stream(STREAM)
    except Exception:
        await js.update_stream(STREAM)

    async def on_event(msg):
        try:
            event = json.loads(msg.data)
            alert_id = db.process_event(pg, event)
            if alert_id is None:
                print(f"rejected event from {event.get('node_id', '?')} (doesn't match schema)")
            else:
                print(f"{event['node_id']:>6} {event['type']:<10} -> alert {alert_id}")
        except json.JSONDecodeError:
            print("rejected message that isn't JSON")
        await msg.ack()

    async def on_heartbeat(msg):
        try:
            db.record_heartbeat(pg, json.loads(msg.data))
        except Exception as e:
            print(f"bad heartbeat: {e}")

    await js.subscribe("ddds.events.>", durable="fusion", cb=on_event, manual_ack=True)
    await nc.subscribe("ddds.heartbeats.>", cb=on_heartbeat)
    print("Fusion service running: listening on ddds.events.> and ddds.heartbeats.>")

    while True:  # once an hour, delete old data (BL-21)
        removed = db.apply_retention(pg)
        if removed:
            print(f"retention: deleted {removed} events older than {db.RETENTION_DAYS} days")
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
