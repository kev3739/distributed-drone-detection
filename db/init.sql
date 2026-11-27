-- DDDS database (PostgreSQL). Runs automatically the first time the postgres container starts.

-- Sensor nodes on the site: where they are and which way cameras face.
CREATE TABLE sensors (
    node_id     TEXT PRIMARY KEY,
    type        TEXT NOT NULL,              -- camera, remote_id, ...
    lat         DOUBLE PRECISION,
    lon         DOUBLE PRECISION,
    facing_deg  DOUBLE PRECISION            -- cameras only
);

INSERT INTO sensors (node_id, type, lat, lon, facing_deg) VALUES
    ('cv-01', 'camera',    43.77300, -79.50250, 45),
    ('cv-02', 'camera',    43.77385, -79.50120, 225),
    ('rf-01', 'remote_id', 43.77330, -79.50200, NULL);

-- Last "I'm alive" message from each sensor (US-07).
CREATE TABLE heartbeats (
    node_id         TEXT PRIMARY KEY REFERENCES sensors(node_id),
    last_heartbeat  TIMESTAMPTZ NOT NULL,
    fps             DOUBLE PRECISION
);

-- Fused alerts: one row per drone sighting (US-09).
CREATE TABLE alerts (
    alert_id        SERIAL PRIMARY KEY,
    first_seen      TIMESTAMPTZ NOT NULL,
    last_seen       TIMESTAMPTZ NOT NULL,
    kind            TEXT,                   -- fused, camera, remote_id
    sources         TEXT[],
    drone_class     TEXT,
    confidence      DOUBLE PRECISION,
    lat             DOUBLE PRECISION,
    lon             DOUBLE PRECISION,
    alt_m           DOUBLE PRECISION,
    bearing_deg     DOUBLE PRECISION,
    rid_serial      TEXT,
    false_positive  BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX alerts_first_seen_idx ON alerts (first_seen);
CREATE INDEX alerts_last_seen_idx  ON alerts (last_seen);

-- Every valid detection event a sensor sent, and which alert it became part of.
CREATE TABLE events (
    id           BIGSERIAL PRIMARY KEY,
    node_id      TEXT NOT NULL,
    type         TEXT NOT NULL,
    ts_utc       TIMESTAMPTZ NOT NULL,
    payload      JSONB NOT NULL,
    received_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    alert_id     INTEGER REFERENCES alerts(alert_id) ON DELETE SET NULL
);
CREATE INDEX events_ts_idx ON events (ts_utc);
CREATE INDEX events_alert_idx ON events (alert_id);

-- Events that broke the schema (kept so we can debug bad sensors).
CREATE TABLE rejected_events (
    id           BIGSERIAL PRIMARY KEY,
    received_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    payload      JSONB NOT NULL,
    problems     TEXT[] NOT NULL
);
