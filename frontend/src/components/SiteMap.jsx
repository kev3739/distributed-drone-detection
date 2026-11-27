// Bird's-eye view of the site, drawn with SVG.
// - cameras: white dots with a grey cone showing what they can see
// - Remote ID receiver: blue diamond with its range ring
// - alerts with GPS: dots; camera-only alerts: a line in the direction the camera saw the drone
import { cameraFor, pointAlong, siteCenter, toMetres } from "../utils.js";

const W = 800, H = 520;          // drawing size
const SCALE = 1.4;               // pixels per metre
const CAMERA_RANGE = 180;        // metres
const CAMERA_FOV = 70;           // degrees
const RF_RANGE = 220;            // metres

export default function SiteMap({ sensors, alerts, selected, onSelect }) {
  const center = siteCenter(sensors);
  // metres -> screen pixels (north is up)
  const px = ({ x, y }) => ({ x: W / 2 + x * SCALE, y: H / 2 - y * SCALE });
  const at = (lat, lon) => px(toMetres(lat, lon, center));

  const cameraCone = (s) => {
    const o = toMetres(s.lat, s.lon, center);
    const a = px(pointAlong(o.x, o.y, s.facing_deg - CAMERA_FOV / 2, CAMERA_RANGE));
    const b = px(pointAlong(o.x, o.y, s.facing_deg + CAMERA_FOV / 2, CAMERA_RANGE));
    const p = px(o);
    return `M${p.x},${p.y} L${a.x},${a.y} A${CAMERA_RANGE * SCALE},${CAMERA_RANGE * SCALE} 0 0 1 ${b.x},${b.y} Z`;
  };

  const directionLine = (alert, length = 230) => {
    const cam = cameraFor(alert, sensors);
    if (!cam || alert.bearing_deg == null) return null;
    const o = toMetres(cam.lat, cam.lon, center);
    return { from: px(o), to: px(pointAlong(o.x, o.y, alert.bearing_deg, length)) };
  };

  const c = px({ x: 0, y: 0 });

  return (
    <div className="map">
      <div className="panel-head"><h2>Site map</h2>
        <span className="muted">York University · Lassonde (rings every 50 m)</span></div>
      <svg viewBox={`0 0 ${W} ${H}`} className="map-svg">
        {/* distance rings + site perimeter + buildings (decoration) */}
        {[50, 100, 150, 200].map((r) => (
          <circle key={r} cx={c.x} cy={c.y} r={r * SCALE} className="ring" />
        ))}
        <rect x={c.x - 230} y={c.y - 190} width={460} height={380} rx={10} className="perimeter" />
        <rect x={c.x - 150} y={c.y - 120} width={90} height={60} className="building" />
        <rect x={c.x + 40} y={c.y + 40} width={120} height={70} className="building" />
        <rect x={c.x - 40} y={c.y + 90} width={60} height={40} className="building" />
        <text x={W - 30} y={36} className="compass">N ↑</text>

        {/* sensors */}
        {sensors.map((s) => {
          const p = at(s.lat, s.lon);
          const off = s.status !== "online";
          if (s.type === "camera") {
            return (
              <g key={s.node_id}>
                <path d={cameraCone(s)} className={off ? "cone off" : "cone"} />
                <circle cx={p.x} cy={p.y} r={7} className={off ? "camera off" : "camera"} />
                {off && <text x={p.x - 6} y={p.y + 5} className="offline-x">✕</text>}
                <text x={p.x + 10} y={p.y - 10} className="label">{s.node_id}{off ? " (offline)" : ""}</text>
              </g>
            );
          }
          return (
            <g key={s.node_id}>
              <circle cx={p.x} cy={p.y} r={RF_RANGE * SCALE} className={off ? "rf-range off" : "rf-range"} />
              <rect x={p.x - 7} y={p.y - 7} width={14} height={14} transform={`rotate(45 ${p.x} ${p.y})`}
                    className={off ? "rf off" : "rf"} />
              <text x={p.x + 12} y={p.y + 18} className="label">{s.node_id}{off ? " (offline)" : ""}</text>
            </g>
          );
        })}

        {/* alerts (selected one is drawn last so it's on top) */}
        {[...alerts.filter((a) => a.alert_id !== selected?.alert_id), ...(selected ? [selected] : [])].map((a) => {
          const isSel = a.alert_id === selected?.alert_id;
          const line = directionLine(a, a.location ? undefined : 230);
          const dot = a.location ? at(a.location.lat, a.location.lon) : null;
          const cls = `${isSel ? "sel" : "old"} ${a.false_positive ? "fp" : ""}`;
          return (
            <g key={a.alert_id} onClick={() => onSelect(a.alert_id)} className="alert-mark">
              {line && <line x1={line.from.x} y1={line.from.y}
                             x2={dot ? dot.x : line.to.x} y2={dot ? dot.y : line.to.y}
                             className={`bearing ${cls}`} />}
              {dot && (
                <>
                  {isSel && <circle cx={dot.x} cy={dot.y} r={16} className="pulse" />}
                  <circle cx={dot.x} cy={dot.y} r={isSel ? 8 : 5} className={`drone ${cls}`} />
                  {isSel && <text x={dot.x + 12} y={dot.y - 10} className="drone-label">
                    #{a.alert_id} · {Math.round(a.location.alt_m)} m</text>}
                </>
              )}
              {!dot && isSel && line && (
                <text x={line.to.x + 6} y={line.to.y} className="drone-label">#{a.alert_id} · direction only</text>
              )}
            </g>
          );
        })}
      </svg>
      <div className="legend">
        <span><i className="lg camera" /> Camera</span>
        <span><i className="lg rf" /> Remote ID receiver</span>
        <span><i className="lg drone" /> Drone (GPS)</span>
        <span><i className="lg bearing" /> Camera direction</span>
      </div>
    </div>
  );
}
