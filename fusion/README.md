# fusion

The fusion service (Layer 2). Owner: Kevin.

It listens on the NATS event bus:
- `ddds.events.<type>.<node_id>`: checks each event against the schema, saves it, and merges events less than 3 s apart into one alert (US-09)
- `ddds.heartbeats.<node_id>`: records that the sensor is alive (US-07)

Events stay on the bus for 24 h (JetStream), so the service catches up after a restart and sessions can be replayed (US-08). Events older than 30 days are deleted and Remote ID details are wiped from old alerts (BL-21).

Files:
- `fusion.py`: the fusion rules (pure logic, no database)
- `db.py`: saving events, alerts and heartbeats to PostgreSQL
- `service.py`: connects to NATS and runs the above for every message
- `sample_events.json`: example events (`python fusion.py` fuses them and prints the result)
