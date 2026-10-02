# ResilientEdge — Full System Audit Report

**Audit Date:** 2026-09-26  
**Auditor:** ResilientEdge Engineering Team  
**Scope:** Full-stack codebase audit across Frontend, Backend, Simulation Engine, Networking, Faults, Database, and Deployment Scripts.

---

## 1. System Architecture & Entrypoints

### Frontend Entrypoints
- `index.html`: Entry HTML document referencing `/src/main.tsx`. Configured with Inter and JetBrains Mono typography.
- `src/main.tsx`: React DOM mount root with StrictMode.
- `src/App.tsx`: Central Dashboard & View Orchestrator. Manages WebSocket connection to `/ws/telemetry`, fallback polling to `/api/health`, active navigation tabs, modals, and telemetry state.

### Backend & API Entrypoints
- `server.ts`: Express + Vite full-stack server running on port 3000.
  - Detects Python executable (`python`, `py`, `python3`).
  - Spawns authoritative Python Simulation Bridge (`core/simulation/bridge.py`) or proxies to FastAPI (`BACKEND_HOST:BACKEND_PORT`) when available.
  - Implements REST endpoints matching both `/` and `/api/*`.
  - Hosts WebSocket telemetry server at `/ws/telemetry`.
- `backend/api/fastapi_app.py`: FastAPI authoritative server running on port 8000.
  - Lifespan background simulation loop at 10 Hz.
  - Exposes REST routes for simulation control, robots, tasks, faults, incidents, metrics, scenarios, settings, and snapshots.
  - Hosts native WebSocket server at `/ws/telemetry`.

### Python Simulation Core Entrypoints
- `core/simulation/engine.py`: Central Authoritative Simulation Engine (`SimulationEngine`).
  - Manages spatial warehouse model, robots, tasks, clock, faults, network, reservations, planning, conflict detection, deadlock resolution, metrics, and incident logging.
- `core/simulation/bridge.py`: Standard I/O IPC Bridge for communication between Node.js server and Python simulation.
- `core/simulation/clock.py`: Discrete simulation clock with single-step capability (`step`, `force_step`, `pause`, `resume`, `reset`).

---

## 2. Component & Dependency Map

| Module | Location | Purpose | Key Dependencies |
|---|---|---|---|
| **Simulation Engine** | `core/simulation/engine.py` | State authoritativeness, physics, step loop | `planner`, `allocator`, `fault_engine`, `network_sim` |
| **Path Planner** | `core/planning/astar.py` | Space-time A* grid path planning | Grid coordinates, obstacles, reservations |
| **Coordination** | `core/coordination/` | Reservation, conflict & deadlock detection | `engine`, `robot`, `task` |
| **Fault Engine** | `core/faults/fault_engine.py` | Chaos & fault lifecycle injection/resolution | `Fault`, `FaultType` |
| **Networking** | `core/networking/network_sim.py` | Packet loss, latency, jitter, partitions | In-flight message queue |
| **Resilience State** | `core/resilience/state_machine.py` | Resilience mode transitions (NORMAL, DEGRADED, LOCAL_AUTONOMY, etc.) | Timestamps, metrics |
| **Database** | `backend/database/sqlite_db.py` | SQLite persistent storage for telemetry & runs | `sqlite3`, JSON |
| **legacy cloud provider Layer** | `backend/database/` | SQLite persistent schemas, server-side RBAC, Auth profiles | SQLite 15+ |
| **Scenarios & Benchmarks**| `experiments/` | S01-S12 chaos scenarios & baseline comparison | `SimulationEngine` |

---

## 3. Audit Findings: TODOs, FIXMEs, and Stubs

1. **Baseline Benchmarks (`experiments/baseline.py`):**
   - **Finding:** Hardcoded multipliers (`makespan * 1.45`, `waiting_time * 2.8`) were used instead of real simulation runs for Stop-and-Wait and Centralized Lock.
   - **Resolution:** Replaced with actual execution of Baseline A (Stop-and-Wait) and Baseline B (Centralized Reservation) algorithms.

2. **Network Simulation (`core/networking/network_sim.py`):**
   - **Finding:** Jitter, message duplication, and message reordering were not fully simulated or exposed in telemetry.
   - **Resolution:** Implemented jitter perturbation, duplication rate, reordering queues, and real packet delivery accounting in `NetworkSimulator`.

3. **Battery Lifecycle (`core/simulation/engine.py`):**
   - **Finding:** Low battery was only clamped to 8% without executing the complete autonomous charging lifecycle.
   - **Resolution:** Implemented deterministic charging bay navigation (`C1`-`C4`), task handoff, charging state progression, and battery recovery.

4. **Database Dashboard View (`src/App.tsx`):**
   - **Finding:** Database stats cards displayed `telemetry.robots.length` rather than querying real database records.
   - **Resolution:** Added real database endpoints (`/api/database/stats`, `/api/database/*`) backed by legacy cloud provider and SQLite fallback.

5. **Role-Based Access Control (RBAC):**
   - **Finding:** Frontend components hardcoded `currentUserRole="ADMIN"`.
   - **Resolution:** Added interactive user/role switcher with `ADMIN`, `OPERATOR`, and `OBSERVER` roles and enforced RBAC permissions on both frontend and backend.

6. **Decision Explainability & Replay:**
   - **Finding:** Reassignment logged decisions but lacked candidate score breakdown and visual step-by-step incident replay.
   - **Resolution:** Added decision evaluation records (distance, battery, health, feasibility) and a deterministic incident replay modal.

---

## 4. API & Route Traceability

| Frontend Handler | API Route | HTTP Method | Backend Handler | Simulation Effect | Status |
|---|---|---|---|---|---|
| `TopBar.onClockAction('pause')` | `/api/simulation/pause` | POST | `simulation_pause()` | Clock paused, motion halted | Verified |
| `TopBar.onClockAction('resume')`| `/api/simulation/start` | POST | `simulation_start()` | Clock running, motion resumed | Verified |
| `TopBar.onClockAction('step')`  | `/api/simulation/step`  | POST | `simulation_step()`  | +0.1s tick while paused | Verified |
| `TopBar.onClockAction('reset')` | `/api/simulation/reset` | POST | `simulation_reset()` | Clock=0, robots & tasks reset | Verified |
| `TopBar.onClockAction(scale)`   | `/api/controls/clock`   | POST | `control_clock()`    | Updates time_scale | Verified |
| `RobotDetailDrawer.onAction('pause')` | `/api/robots/:id/pause` | POST | `pause_robot()` | Robot state=PAUSED | Verified |
| `RobotDetailDrawer.onAction('resume')`| `/api/robots/:id/resume`| POST | `resume_robot()`| Robot state=PLANNING/IDLE | Verified |
| `RobotDetailDrawer.onAction('reset')` | `/api/robots/:id/reset` | POST | `reset_robot()` | Restores home coordinates | Verified |
| `RobotDetailDrawer.onAction('reassign')`| `/api/robots/:id/reassign`| POST| `reassign_robot()`| Finds candidate, replans | Verified |
| `TaskDispatcherModal.onDispatch`| `/api/tasks`            | POST | `create_task()`      | Adds task to queue | Verified |
| `TaskDetailDrawer.onReassign`   | `/api/tasks/:id/assign` | POST | `assign_task_route()`| Rebinds task to robot | Verified |
| `TaskDetailDrawer.onCancel`     | `/api/tasks/:id/cancel` | POST | `cancel_task_route()`| Cancels task, frees robot | Verified |
| `FaultInjectionPanel.onInject`  | `/api/faults`           | POST | `inject_fault()`     | Injects 1 of 10 fault types | Verified |
| `FaultInjectionPanel.onClear`   | `/api/faults/:id`       | DELETE | `clear_fault()`    | Resolves target fault | Verified |
| `FaultInjectionPanel.onClearAll`| `/api/faults/clear-all` | POST | `clear_all_faults()` | Clears active faults | Verified |
| `SettingsModal.onSave`          | `/api/settings`         | POST | `set_settings()`     | Validates & applies config | Verified |
| `BackupManager.onSave`          | `/api/snapshot/save`    | POST | `export_snapshot()`  | Serializes full simulation state | Verified |
| `BackupManager.onRestore`       | `/api/snapshot/restore` | POST | `restore_snapshot()` | Restores full simulation state | Verified |
| `ExperimentsRunner.onRun`       | `/api/scenarios/run`    | POST | `execute_scenario()` | Runs isolated scenario S01-S12 | Verified |
| `BaselineComparison.onRun`     | `/api/baseline`         | GET  | `get_baseline_comparison()` | Runs real comparative simulations | Verified |
| `DatabaseView.fetchStats`       | `/api/database/stats`   | GET  | `get_database_stats()` | Returns table record counts | Verified |
