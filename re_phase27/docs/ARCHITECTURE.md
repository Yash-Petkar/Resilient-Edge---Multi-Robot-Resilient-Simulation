# ResilientEdge System Architecture Document

```
                    RESILIENTEDGE
                         │
          ┌──────────────┴──────────────┐
          │                             │
     CORE SOFTWARE                WEB APPLICATION
          │                             │
     Simulation Engine             Dashboard UI
     Robot Agents                  Visualization
     Task System                   Monitoring
     Path Planning (A*)            Fault Controls
     Coordination                  Metrics
     Fault Injection               Experiments
     Recovery Manager
     Network Simulation
          │
       FastAPI / Express
          │
       WebSocket (/ws/telemetry)
          │
       Frontend (React 19 + TypeScript)
```

---

## 1. Core Layers

### 1.1 Core Simulation Engine (`/core`)
- **Clock Subsystem (`core/simulation/clock.py`)**: Deterministic tick-driven simulation clock with discrete step $\Delta t = 0.1\text{s}$ and variable speed multiplier.
- **World Model (`core/simulation/world.py`)**: 24x16 grid warehouse representation containing physical storage pods, designated pickup stations (P1-P4), delivery stations (D1-D4), and charging docks (C1-C4).
- **A\* Path Planner (`core/planning/astar.py`)**: Optimal grid search with Manhattan distance heuristic, dynamic obstacle avoidance, and reserved cell checks.
- **Coordination & Conflict Detection (`core/coordination/`)**:
  - `allocator.py`: Deterministic greedy allocation with tie-breaking.
  - `conflict.py`: Trajectory collision checker (Vertex & Edge head-on conflicts).
  - `reservation_manager.py`: Spatial-temporal reservation window management.
  - `deadlock.py`: Wait-For Graph (WFG) cycle detection via DFS and victim priority preemption.
- **Chaos & Fault Engine (`core/faults/fault_engine.py`)**: Injects and manages robot hardware crashes, battery drain, blocked aisles, dynamic obstacles, packet loss, latency, and split-brain network partitions.
- **Resilience Engine (`core/resilience/`)**:
  - `state_machine.py`: 6-state resilience lifecycle (NORMAL, DEGRADED, LOCAL_AUTONOMY, RECOVERY, RESYNC, FAILED).
  - `failure_detector.py`: Heartbeat monitoring with 2.0s timeout threshold.
  - `recovery_manager.py`: Autonomous task reclamation, priority escalation, and replacement assignment.
- **Network Simulator (`core/networking/network_sim.py`)**: Simulates wireless packet loss, queuing latency, and network partition isolation.
- **Metrics Engine (`core/metrics/collector.py`)**: Event-driven calculation of makespan, waiting times, collision counts, message loss rates, and state durations.

### 1.2 Persistence Layer (`/backend/database/sqlite_db.py`)
- Standard SQLite3 database engine (`./data/resilientedge.db`).
- Tables: `robots`, `tasks`, `experiments`, `experiment_runs`, `faults`, `incidents`, `reservations`, `decision_events`, `metrics`.

### 1.3 Full-Stack Dev Server (`server.ts`)
- Express web server on port 3000.
- Native WebSocket server at `/ws/telemetry`.
- REST API matching FastAPI endpoints.
- Integrated Vite development middleware for instant AI Studio browser preview without external dependencies.

## Phase 1 Production Data Boundary

The authoritative Python `SimulationEngine` is isolated from database vendor APIs through `backend/database/repository.py`.

- `SQLiteRepository`: local transactional fallback.
- `LegacyCloudRepository`: server-side REST database client adapter using `REMOTE_DATABASE_SERVER_KEY` only on the backend.
- `ResilientPersistence`: selects legacy cloud provider when available and fails over to SQLite when database writes fail.
- `PersistenceWorker`: performs simulation writes asynchronously so database latency/outages cannot block the simulation tick loop.

Simulation telemetry is append-recorded in `telemetry_events`, while current robot/task/fault/incident state is upserted into their respective tables. Important state transitions are emitted as event types including simulation lifecycle, task lifecycle, robot state changes, fault events, incident creation, and network degradation/recovery.

## Authentication Boundary

With legacy cloud provider configured:

```text
Browser
  -> local JWT authentication session/JWT
  -> Node/Express transport boundary
  -> Python authoritative service
  -> JWT verification
  -> profiles.role
  -> server-side permission check
  -> SimulationEngine
```

The browser cannot choose its role. The previous client-side role-switch control has been removed. Local development without legacy cloud provider uses `JWT authentication`, defined on the server.

## Failure Semantics

- legacy cloud provider outage: database writes fail over to SQLite; simulation continues.
- WebSocket outage: telemetry broadcast fails only for the disconnected client; simulation continues.
- Browser refresh: reconnect receives the current authoritative Python snapshot.
- Invalid JWT: `401`.
- Valid JWT with insufficient role: `403`.
- Missing resource: `404`.
- Domain conflict: `409`.
- Unexpected backend failure: `500`.
