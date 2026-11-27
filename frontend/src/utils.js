// Small helper functions (no React here, so they're easy to test).

const M_PER_DEG_LAT = 110540;

// Turn latitude/longitude into metres east (x) and north (y) of a centre point.
export function toMetres(lat, lon, center) {
  const x = (lon - center.lon) * 111320 * Math.cos((center.lat * Math.PI) / 180);
  const y = (lat - center.lat) * M_PER_DEG_LAT;
  return { x, y };
}

// The point `distance` metres away from (x, y) in compass direction `bearingDeg` (0 = north).
export function pointAlong(x, y, bearingDeg, distance) {
  const rad = (bearingDeg * Math.PI) / 180;
  return { x: x + Math.sin(rad) * distance, y: y + Math.cos(rad) * distance };
}

// Middle of all the sensors: the map is centred here.
export function siteCenter(sensors) {
  const placed = sensors.filter((s) => s.lat != null && s.lon != null);
  if (!placed.length) return { lat: 43.7734, lon: -79.5019 };
  return {
    lat: placed.reduce((a, s) => a + s.lat, 0) / placed.length,
    lon: placed.reduce((a, s) => a + s.lon, 0) / placed.length,
  };
}

export const KIND_LABEL = { fused: "Fused", camera: "Camera only", remote_id: "Remote ID only" };

export function timeAgo(iso, now = Date.now()) {
  const s = Math.max(0, Math.round((now - new Date(iso).getTime()) / 1000));
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

export const clockTime = (iso) =>
  new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

export const percent = (x) => (x == null ? "–" : `${Math.round(x * 100)}%`);

// First camera that saw this alert (its direction line starts at that camera).
export function cameraFor(alert, sensors) {
  return sensors.find((s) => s.type === "camera" && alert.sources.includes(s.node_id));
}
