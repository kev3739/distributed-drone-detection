// The whole dashboard: holds the shared state and lays out the panels.
import { useEffect, useMemo, useRef, useState } from "react";
import { useLiveAlerts, useSensors, searchAlerts } from "./api.js";
import TopBar from "./components/TopBar.jsx";
import SiteMap from "./components/SiteMap.jsx";
import AlertFeed from "./components/AlertFeed.jsx";
import AlertDetails from "./components/AlertDetails.jsx";
import SensorHealth from "./components/SensorHealth.jsx";
import HistorySearch from "./components/HistorySearch.jsx";
import { beep } from "./sound.js";

export default function App() {
  const { alerts: liveAlerts, connected } = useLiveAlerts();
  const sensors = useSensors();
  const [view, setView] = useState("live");          // "live" or "history"
  const [historyAlerts, setHistoryAlerts] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [soundOn, setSoundOn] = useState(false);
  const [now, setNow] = useState(Date.now());

  // Tick every second so "5s ago" labels stay fresh.
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);

  // Beep when a brand-new alert arrives (if sound is on).
  const newestSeen = useRef(null);
  useEffect(() => {
    const newest = liveAlerts[0]?.alert_id;
    if (newest == null) return;
    if (newestSeen.current != null && newest > newestSeen.current && soundOn) beep();
    newestSeen.current = Math.max(newest, newestSeen.current ?? 0);
  }, [liveAlerts, soundOn]);

  const alerts = view === "live" ? liveAlerts : historyAlerts;

  // In live view, follow the newest alert until the operator clicks one.
  const selected = useMemo(() => {
    const picked = alerts.find((a) => a.alert_id === selectedId);
    return picked ?? (view === "live" ? alerts[0] : undefined);
  }, [alerts, selectedId, view]);

  const runSearch = async (from, to) => {
    setHistoryAlerts(await searchAlerts(from, to));
    setSelectedId(null);
  };

  return (
    <div className="app">
      <TopBar
        view={view}
        onView={(v) => { setView(v); setSelectedId(null); }}
        sensors={sensors}
        connected={connected}
        soundOn={soundOn}
        onSound={() => setSoundOn(!soundOn)}
        now={now}
      />
      <main className="grid">
        <section className="panel map-panel">
          <SiteMap sensors={sensors} alerts={alerts.slice(0, 12)} selected={selected}
                   onSelect={setSelectedId} />
        </section>

        <section className="panel feed-panel">
          {view === "history" && <HistorySearch onSearch={runSearch} />}
          <AlertFeed alerts={alerts} selected={selected} onSelect={setSelectedId}
                     now={now} title={view === "live" ? "Live alerts" : "Search results"} />
        </section>

        <section className="panel details-panel">
          <AlertDetails alert={selected} now={now} />
        </section>

        <section className="panel sensors-panel">
          <SensorHealth sensors={sensors} />
        </section>
      </main>
    </div>
  );
}
