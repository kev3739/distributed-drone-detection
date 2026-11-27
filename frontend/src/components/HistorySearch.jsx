// Search past alerts by time (US-13).
import { useState } from "react";

export default function HistorySearch({ onSearch }) {
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  return (
    <form className="history" onSubmit={(e) => { e.preventDefault(); onSearch(from, to); }}>
      <label>From <input type="datetime-local" value={from} onChange={(e) => setFrom(e.target.value)} /></label>
      <label>To <input type="datetime-local" value={to} onChange={(e) => setTo(e.target.value)} /></label>
      <button type="submit">Search</button>
    </form>
  );
}
