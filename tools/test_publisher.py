"""TEST TOOL ONLY: pretends to be our sensor nodes until the real hardware is ready.

It publishes to the NATS event bus in exactly the format the real nodes will use:
- ddds.heartbeats.<node_id>        every 5 s for each sensor
- ddds.events.<type>.<node_id>     a drone "sighting" every few seconds:
      fused      -> camera AND Remote ID both see it (1 s apart)
      camera     -> a drone with no Remote ID broadcast
      remote_id  -> Remote ID only (camera can't see it)
When Ekaterina's camera node and Arshia's receiver publish for real, stop this.

Run (with docker compose up running):
    python tools/test_publisher.py
    python tools/test_publisher.py --kill cv-02 --kill-after 40   # cv-02 "dies" after 40 s (US-07)
    python tools/test_publisher.py --send-invalid                  # also sends a broken event now and then
"""
import argparse
import asyncio
import json
import math
import os
import random
import time
from datetime import datetime, timezone

import nats

NATS_URL = os.environ.get("NATS_URL", "nats://ddds:ddds-dev@localhost:4222")

SENSORS = {  # same positions as db/init.sql
    "cv-01": ("camera", 43.77300, -79.50250),
    "cv-02": ("camera", 43.77385, -79.50120),
    "rf-01": ("remote_id", 43.77330, -79.50200),
}
SITE = (43.77340, -79.50190)
SERIALS = ["1581F5FJD239C00A1B2C", "1581F6GKB21AC0042D7E", "1596A9KX0034P0001"]


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def bearing(node, drone):
    """Compass direction (0 = north, 90 = east) from a sensor to the drone."""
    _, lat, lon = SENSORS[node]
    dy = (drone[0] - lat) * 110540
    dx = (drone[1] - lon) * 111320 * math.cos(math.radians(lat))
    return round(math.degrees(math.atan2(dx, dy)) % 360, 1)


def camera_event(node, drone):
    return {"schema": "ddds.event.v1", "node_id": node, "type": "camera", "ts_utc": now_iso(),
            "class": "drone", "confidence": round(random.uniform(0.70, 0.95), 2),
            "bearing_deg": bearing(node, drone)}


def remote_id_event(drone):
    serial = random.choice(SERIALS)
    return {"schema": "ddds.event.v1", "node_id": "rf-01", "type": "remote_id", "ts_utc": now_iso(),
            "class": "DJI" if serial.startswith("1581") else "Unknown manufacturer",
            "confidence": round(random.uniform(0.90, 0.99), 2),
            "lat": round(drone[0], 6), "lon": round(drone[1], 6), "alt": random.randint(30, 120),
            "rid_serial": serial}


async def publish_event(js, event):
    await js.publish(f"ddds.events.{event['type']}.{event['node_id']}", json.dumps(event).encode())


async def sighting(js, kind):
    drone = (SITE[0] + random.uniform(-0.0013, 0.0013), SITE[1] + random.uniform(-0.0018, 0.0018))
    camera = random.choice(["cv-01", "cv-02"])
    if kind in ("fused", "camera"):
        await publish_event(js, camera_event(camera, drone))
    if kind == "fused":
        await asyncio.sleep(1)
    if kind in ("fused", "remote_id"):
        await publish_event(js, remote_id_event(drone))
    if kind == "invalid":
        bad = camera_event(camera, drone)
        del bad["bearing_deg"]  # cameras must send a direction -> fusion rejects this
        await publish_event(js, bad)
    print(f"{now_iso()}  sighting: {kind}")


async def main(args):
    nc = await nats.connect(NATS_URL)
    js = nc.jetstream()
    plan = ["fused", "camera", "remote_id", "fused"] + (["invalid"] if args.send_invalid else [])
    start, next_hb, next_sighting, i = time.time(), 0.0, 3.0, 0
    print(f"Test publisher connected to NATS. Sighting every {args.every}s. Ctrl+C to stop.")
    while True:
        elapsed = time.time() - start
        if elapsed >= next_hb:
            for node, (ntype, *_) in SENSORS.items():
                if node == args.kill and elapsed >= args.kill_after:
                    continue  # this node has "died": no more heartbeats
                hb = {"node_id": node, "fps": 2.0 if ntype == "camera" else None}
                await nc.publish(f"ddds.heartbeats.{node}", json.dumps(hb).encode())
            next_hb += 5
        if elapsed >= next_sighting:
            await sighting(js, plan[i % len(plan)])
            i += 1
            next_sighting += args.every
        await asyncio.sleep(0.2)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--every", type=float, default=8, help="seconds between sightings (keep above 4)")
    p.add_argument("--kill", help="sensor that stops sending heartbeats, e.g. cv-02")
    p.add_argument("--kill-after", type=int, default=40)
    p.add_argument("--send-invalid", action="store_true")
    try:
        asyncio.run(main(p.parse_args()))
    except KeyboardInterrupt:
        print("\nStopped.")
