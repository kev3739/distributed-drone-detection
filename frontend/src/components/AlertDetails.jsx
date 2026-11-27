// Everything about the selected alert, plus the raw sensor events fusion merged into it.
import { useEffect, useState } from "react";
import { getAlertEvents, markFalsePositive } from "../api.js";
import { KIND_LABEL, clockTime, percent, timeAgo } from "../utils.js";

export default function AlertDetails({ alert, now }) {
  const [events, setEvents] = useState([]);

  // Load the alert's events whenever a different alert is selected or it gets updated.
  useEffect(() => {
    if (!alert) return setEvents([]);
    getAlertEvents(alert.alert_id).then(setEvents).catch(() => setEvents([]));
  }, [alert?.alert_id, alert?.last_seen]);

  if (!alert) {
    return <div className="details"><div className="panel-head"><h2>Alert details</h2></div>
      <p className="empty">Select an alert to see its details.</p></div>;
  }

  const rows = [
    ["Detected", `${clockTime(alert.time)} (${timeAgo(alert.time, now)})`],
    ["Type", KIND_LABEL[alert.kind] ?? alert.kind],
    ["Sensors", alert.sources.join(", ")],
    ["Drone", alert.drone_class],
    ["Confidence", percent(alert.confidence)],
    ["Position", alert.location
      ? `${alert.location.lat.toFixed(5)}, ${alert.location.lon.toFixed(5)} · ${Math.round(alert.location.alt_m)} m`
      : "No GPS (camera only)"],
    ["Direction", alert.bearing_deg != null ? `${alert.bearing_deg}° from camera` : "–"],
    ["Remote ID serial", alert.rid_serial ?? "– (not broadcasting)"],
  ];

  return (
    <div className="details">
      <div className="panel-head">
        <h2>Alert #{alert.alert_id}</h2>
        <span className={`badge ${alert.kind}`}>{KIND_LABEL[alert.kind] ?? alert.kind}</span>
      </div>
      <dl className="fields">
        {rows.map(([k, v]) => (<div key={k}><dt>{k}</dt><dd>{v}</dd></div>))}
      </dl>

      <h3>Events in this sighting ({events.length})</h3>
      <table className="events">
        <thead><tr><th>Time</th><th>Sensor</th><th>Saw</th><th>Conf.</th></tr></thead>
        <tbody>
          {events.map((e, i) => (
            <tr key={i}>
              <td>{new Date(e.ts_utc).toLocaleTimeString([], { hour12: false })}.{String(new Date(e.ts_utc).getMilliseconds()).padStart(3, "0")}</td>
              <td>{e.node_id}</td>
              <td>{e.type === "camera" ? `${e.class}, ${e.bearing_deg}°` : `${e.class}, GPS`}</td>
              <td>{percent(e.confidence)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <button className="danger" disabled={alert.false_positive}
              onClick={() => markFalsePositive(alert.alert_id)}>
        {alert.false_positive ? "Marked as false positive" : "Mark false positive"}
      </button>
    </div>
  );
}
