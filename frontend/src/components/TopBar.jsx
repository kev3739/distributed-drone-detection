// Top bar: name, Live/History switch, system status, sound toggle, clock.
export default function TopBar({ view, onView, sensors, connected, soundOn, onSound, now }) {
  const online = sensors.filter((s) => s.status === "online").length;
  const allOnline = sensors.length > 0 && online === sensors.length;
  return (
    <header className="topbar">
      <div className="brand">
        <span className="logo">◎</span> BeeWare <span className="brand-sub">Drone Detection</span>
      </div>
      <nav className="tabs">
        {["live", "history"].map((v) => (
          <button key={v} className={view === v ? "tab active" : "tab"} onClick={() => onView(v)}>
            {v === "live" ? "Live" : "History"}
          </button>
        ))}
      </nav>
      <div className="status">
        <span className={allOnline ? "pill ok" : "pill warn"}>
          {online} of {sensors.length} sensors online
        </span>
        <span className={connected ? "pill ok" : "pill bad"}>
          <span className="dot" /> {connected ? "Live feed" : "Reconnecting…"}
        </span>
        <button className={soundOn ? "pill btn on" : "pill btn"} onClick={onSound}>
          {soundOn ? "🔔 Sound on" : "🔕 Sound off"}
        </button>
        <span className="clock">{new Date(now).toLocaleTimeString()}</span>
      </div>
    </header>
  );
}
