// Every sensor node: online/offline, when it last checked in, and camera frame rate.
export default function SensorHealth({ sensors }) {
  return (
    <div>
      <div className="panel-head"><h2>Sensor health</h2>
        <span className="muted">offline after 15 s without a heartbeat</span></div>
      <table className="sensors">
        <thead><tr><th></th><th>Node</th><th>Type</th><th>Last heartbeat</th><th>FPS</th></tr></thead>
        <tbody>
          {sensors.map((s) => (
            <tr key={s.node_id} className={s.status}>
              <td><span className={`status-dot ${s.status}`} /></td>
              <td>{s.node_id}</td>
              <td>{s.type === "remote_id" ? "Remote ID" : "Camera"}</td>
              <td>{s.seconds_since_heartbeat == null ? "never" : `${Math.round(s.seconds_since_heartbeat)}s ago`}</td>
              <td>{s.fps ?? "–"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
