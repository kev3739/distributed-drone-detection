// List of alerts (newest first). Click one to see it on the map and in the details panel.
import { KIND_LABEL, percent, timeAgo } from "../utils.js";

export default function AlertFeed({ alerts, selected, onSelect, now, title }) {
  const fused = alerts.filter((a) => a.kind === "fused").length;
  return (
    <div className="feed">
      <div className="panel-head">
        <h2>{title}</h2>
        <span className="muted">{alerts.length} total · {fused} fused</span>
      </div>
      {alerts.length === 0 && <p className="empty">Waiting for detections…</p>}
      <ul className="cards">
        {alerts.map((a) => (
          <li key={a.alert_id}
              className={`card ${a.alert_id === selected?.alert_id ? "selected" : ""} ${a.false_positive ? "fp" : ""}`}
              onClick={() => onSelect(a.alert_id)}>
            <div className="card-top">
              <span className={`badge ${a.kind}`}>{KIND_LABEL[a.kind] ?? a.kind}</span>
              <span className="muted">{timeAgo(a.time, now)}</span>
            </div>
            <div className="card-title">
              Alert #{a.alert_id} · {a.drone_class}
              {a.false_positive && <span className="badge fp-badge">False positive</span>}
            </div>
            <div className="card-meta">
              <span>{percent(a.confidence)} confidence</span>
              <span>{a.sources.join(" + ")}</span>
              {a.location && <span>{Math.round(a.location.alt_m)} m alt</span>}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
