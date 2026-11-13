# Distributed Drone Detection System (DDDS)

Low-cost, fault-tolerant drone detection using camera and Remote ID sensor nodes, an event bus, and sensor fusion.
ENG 4000 Capstone, Team 31, Lassonde School of Engineering, York University.

## How it works

1. **Layer 1: Sensor nodes.** Camera nodes (Raspberry Pi 5 + YOLO) and Remote ID receivers (ESP32) detect drones and publish small JSON events. No video leaves the node.
2. **Layer 2: Event bus + fusion.** Events travel over NATS JetStream. The fusion service merges camera and RF events from the same drone into one alert.
3. **Layer 3: Application.** A FastAPI backend stores alerts in PostgreSQL and streams them to a React dashboard (REST + Server-Sent Events).

The system is receive-only. It never transmits, jams or interferes with drones.

## Repository layout

| Folder | What's in it | Owner |
|---|---|---|
| `edge-cv/` | Camera node: capture, YOLO detection, event publisher | Ekaterina |
| `edge-rf/` | Remote ID receiver and test emulator (ESP32) | Arshia |
| `schemas/` | Versioned event JSON schemas (v1) | Kevin |
| `fusion/` | Fusion service (merges CV + RF events into alerts) | Kevin |
| `backend/` | FastAPI backend, PostgreSQL, REST + SSE API | Kevin |
| `frontend/` | React operator dashboard | Kevin |
| `ml/` | Model training, RF classification, anomaly detection | Diego |
| `docs/` | Reports, diagrams, test results (`docs/test-results/`) | Everyone |

## How we work

- One branch per story: `feature/US-xx-short-name` (or `chore/...`, `fix/...`).
- `main` is protected: changes go through a pull request with 1 approval and passing CI.
- A story is **done** when it is merged through a reviewed PR, its tests pass, evidence is recorded (test log, screenshot or video), and the README/interfaces are updated.
- Tests: `pytest` (Python) and `Jest` (React), run on every PR.
- Releases use version tags (`v0.1.0` = R1 MVP). Model weights (`.pt`) go in GitHub Releases, not in Git.

## Team

Kevin Garg · Ekaterina Kozlovsky · Arshia Shaghayegh · Diego Alejandro Romero Rincon
Supervisor: Gene
