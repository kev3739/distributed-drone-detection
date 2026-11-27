// Everything the dashboard asks the backend for. All calls go to /api/...,
// which Vite forwards to the backend (see vite.config.js).
import { useEffect, useState } from "react";

const API = "/api";

async function getJson(path) {
  const res = await fetch(API + path);
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return res.json();
}

export const getSensors = () => getJson("/sensors");
export const getAlertEvents = (id) => getJson(`/alerts/${id}/events`);

export function searchAlerts(from, to) {
  const params = new URLSearchParams();
  if (from) params.set("from", new Date(from).toISOString());
  if (to) params.set("to", new Date(to).toISOString());
  return getJson(`/alerts?${params}`);
}

export async function markFalsePositive(id) {
  const res = await fetch(`${API}/alerts/${id}/false-positive`, { method: "POST" });
  if (!res.ok) throw new Error(`false positive -> ${res.status}`);
}

// Live alerts: the backend pushes the full list every time it changes (Server-Sent Events).
export function useLiveAlerts() {
  const [alerts, setAlerts] = useState([]);
  const [connected, setConnected] = useState(false);
  useEffect(() => {
    const source = new EventSource(`${API}/stream/alerts`);
    source.onopen = () => setConnected(true);
    source.onmessage = (msg) => {
      setAlerts(JSON.parse(msg.data));
      setConnected(true);
    };
    source.onerror = () => setConnected(false); // the browser reconnects by itself
    return () => source.close();
  }, []);
  return { alerts, connected };
}

// Sensors: asked for every 2 seconds so online/offline stays current.
export function useSensors() {
  const [sensors, setSensors] = useState([]);
  useEffect(() => {
    let stop = false;
    const load = () => getSensors().then((s) => !stop && setSensors(s)).catch(() => {});
    load();
    const timer = setInterval(load, 2000);
    return () => { stop = true; clearInterval(timer); };
  }, []);
  return sensors;
}
