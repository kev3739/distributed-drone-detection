# frontend

The BeeWare operator dashboard (Layer 3). React + Vite. Owner: Kevin.

Run (with the backend running: `docker compose --profile test up --build` from the repo root):

```bash
cd frontend
npm install      # first time only
npm run dev      # then open http://localhost:5173
npm test         # unit tests
```

What's on the screen:
- **Top bar**: Live / History, how many sensors are online, live-feed status, alert sound on/off
- **Site map**: cameras (with what they can see), the Remote ID receiver and its range, drones with GPS (dots) and camera-only detections (direction lines). Offline sensors turn red.
- **Live alerts**: new alerts appear instantly (Server-Sent Events from `/stream/alerts`), labelled Fused / Camera only / Remote ID only
- **Alert details**: everything about the selected alert, the raw sensor events fusion merged into it, and "Mark false positive" (US-11)
- **Sensor health**: online/offline (offline after 15 s without a heartbeat, US-07), last heartbeat, FPS (US-12)
- **History**: search past alerts by time (US-13)

Files: `src/App.jsx` (layout + shared state), `src/api.js` (all calls to the backend), `src/utils.js` (map maths and formatting, tested in `utils.test.js`), `src/components/` (one file per panel).
