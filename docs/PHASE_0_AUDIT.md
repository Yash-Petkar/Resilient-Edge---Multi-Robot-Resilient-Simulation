# ResilientEdge — Phase 0 Verification & Repository Audit Report

**Date:** September 26, 2026  
**Auditor:** Senior Software Architect & Verification Engineer  
**System:** ResilientEdge — Multi-Robot Resilience Simulation & Telemetry Platform  
**Target Development OS:** Windows 11 (PowerShell / cmd.exe)  
**Document:** `docs/PHASE_0_AUDIT.md`

---

## 1. Executive Summary

A comprehensive, ground-truth audit of the existing ResilientEdge codebase was conducted. Every subsystem—including `package.json`, frontend React components, backend FastAPI source, authoritative Python simulation core, SQLite persistence, legacy cloud provider schemas, experiment scripts, Windows batch/PowerShell scripts, and the test suite—was inspected, executed, and evaluated.

### Verification Highlights:
- **Unit Test Suite:** **38 of 38 tests PASSED** (`python -m unittest discover tests` completed in 0.523s).
- **Core Simulation Execution:** Verified live and deterministic via `core/simulation/engine.py` and `scripts/run_core_sim.py`.
- **Benchmark Experiment Suite (S01–S12):** All 12 scenarios executed cleanly via `scripts/run_experiment.py`, producing real mathematical metrics and baseline comparisons without fabricated multipliers.
- **FastAPI Backend:** Verified operational on `http://127.0.0.1:8000/health`, serving both REST endpoints and `/ws/telemetry` WebSockets.
- **Node/Express Host & IPC Bridge:** `server.ts` dual-mode architecture verified operational. It discovers FastAPI or transparently spawns `core/simulation/bridge.py` over stdio IPC.
- **Frontend Typecheck & Build:** TypeScript compiles with zero errors (`tsc --noEmit` exited code 0). Vite builds successfully into `dist/` (375 kB JS bundle, 50 kB CSS).

---

## 2. Current Architecture

```mermaid
graph TD
    subgraph Browser ["Frontend Client (React 19 + TypeScript + Vite)"]
        UI[TopBar / Sidebar / Views]
        SimMap[SimulationMap 2D Canvas]
        DBDash[DatabaseDashboard]
        SupSvc[ApiService / Offline Queue]
    end

    subgraph HostLayer ["Integration & Host Layer (server.ts / Express 4 + Vite)"]
        ExpServer[Express Port 3000]
        WSProxy[WebSocket /ws/telemetry]
        RBAC[RBAC Middleware: ADMIN, OPERATOR, OBSERVER]
        HealthCheck[FastAPI Discovery Probe]
    end

    subgraph BackendAPI ["FastAPI Service (backend/api/fastapi_app.py:8000)"]
        FastAPIApp[FastAPI App]
        FastAPIBroadcast[Async Telemetry Loop 10Hz]
    end

    subgraph SimulationCore ["Authoritative Python Simulation Core (core/)"]
        Bridge[stdio IPC Bridge: bridge.py]
        Engine[SimulationEngine: engine.py]
        Clock[SimulationClock 0.1s tick]
        World[WarehouseWorld 24x16 grid]
        AStar[AStarPlanner]
        Alloc[TaskAllocator]
        ResMgr[ReservationManager]
        Deadlock[DeadlockDetector]
        Faults[FaultEngine]
        NetSim[NetworkSimulator]
        StateMachine[ResilienceStateMachine]
        FailureDet[FailureDetector]
        Recovery[RecoveryManager]
        Metrics[MetricsCollector]
    end

    subgraph Persistence ["Persistence Layer"]
        SQLite[(SQLite: data/resilientedge.db)]
        legacy cloud provider[(SQLite + server-side RBAC Cloud)]
    end

    UI -->|HTTP REST /ws/telemetry| ExpServer
    ExpServer -->|Proxy if active| FastAPIApp
    ExpServer -->|stdio IPC fallback| Bridge
    FastAPIApp --> Engine
    Bridge --> Engine
    Engine --> SQLite
    FastAPIApp --> SQLite
    SupSvc -.->|Buffered async events| legacy cloud provider
```

The system employs an **authoritative simulation pattern**:
1. **Simulation Authority:** The single source of ground truth is Python's `SimulationEngine`. Movement, collisions, state machines, network drops, and pathfinding are calculated tick-by-tick in Python.
2. **Dual-Mode Host:**
   - **Mode A (FastAPI Active):** When FastAPI runs on `BACKEND_HOST:BACKEND_PORT` (`127.0.0.1:8000`), `server.ts` acts as a reverse proxy for all REST routes and multiplexes WebSockets to FastAPI.
   - **Mode B (Autonomous IPC Bridge):** If FastAPI is not running, `server.ts` automatically spawns `core/simulation/bridge.py` over stdio JSON streams, allowing the entire application to run from a single command (`npm start` or `tsx server.ts`) without separate Uvicorn orchestration.
3. **Dual Persistence Strategy:**
   - **Local Tier:** SQLite (`data/resilientedge.db`) writes ACID transactions synchronously for robots, tasks, incidents, experiments, and decision events.
   - **Local Persistence Tier:** SQLite with Row Level Security (server-side RBAC) is connected via `src/services/apiService.ts`. Telemetry and incidents are enqueued asynchronously in an offline buffer (`persistenceQueue`), preventing simulation frame drops during network outages.

---

## 3. Actual Repository Structure

```
resilientedge---multi-robot-resilience-simulation-&-telemetry-platform/
├── .env.example                               # Environment variable blueprint
├── .gitignore                                 # Git ignore patterns (node_modules, .venv, data/*.db)
├── bun.lock                                   # Bun lockfile (legacy; bun not on PATH)
├── index.html                                 # Vite HTML entry point
├── metadata.json                              # Applet metadata
├── package.json                               # Node dependencies and scripts
├── requirements.txt                           # Python dependencies
├── ResilientEdge_COMPLETE_FINAL.zip           # 204 KB root archive (redundant)
├── server.ts                                  # Express + Vite + IPC Bridge host
├── start.bat                                  # Master Windows startup batch script
├── start_backend.bat                          # Dedicated backend startup batch script
├── start_frontend.bat                         # Dedicated frontend startup batch script
├── stop.bat                                   # Windows stop batch script
├── tsconfig.json                              # TypeScript compiler configuration
├── vite.config.ts                             # Vite configuration with Tailwind CSS v4 plugin
├── backend/
│   ├── api/
│   │   └── fastapi_app.py                     # Authoritative FastAPI REST & WebSocket server
│   └── database/
│       └── sqlite_db.py                       # SQLite persistence implementation (ResilientEdgeDatabase)
├── core/
│   ├── coordination/
│   │   ├── allocator.py                       # Task allocation logic
│   │   ├── conflict.py                        # Spatial conflict detection
│   │   ├── deadlock.py                        # Cycle detection & deadlock breaking
│   │   └── reservation_manager.py             # Spatiotemporal reservation table
│   ├── faults/
│   │   └── fault_engine.py                    # Fault injection & duration lifecycle
│   ├── metrics/
│   │   └── collector.py                       # KPIs: makespan, waiting time, messages, energy
│   ├── models/
│   │   ├── experiment.py                      # Experiment data models
│   │   ├── fault.py                           # Fault and FaultType definitions
│   │   ├── incident.py                        # Incident severity and logging models
│   │   ├── reservation.py                     # Cell reservation models
│   │   ├── robot.py                           # Robot state and telemetry models
│   │   └── task.py                            # Task status and lifecycle models
│   ├── networking/
│   │   └── network_sim.py                     # Packet loss, latency, jitter, partitions
│   ├── planning/
│   │   └── astar.py                           # Grid-based A* pathfinder
│   ├── resilience/
│   │   ├── failure_detector.py                # Heartbeat and silence detector
│   │   ├── recovery_manager.py                # Autonomous handoff and recovery orchestrator
│   │   └── state_machine.py                   # Resilience state machine transitions
│   └── simulation/
│       ├── bridge.py                          # stdio IPC bridge for server.ts
│       ├── clock.py                           # Simulation clock with pause/step/scale
│       ├── engine.py                          # Core authoritative simulation engine
│       └── world.py                           # 24x16 Warehouse grid layout
├── data/
│   └── resilientedge.db                       # Local SQLite database
├── docs/
│   ├── API_SPEC.md                            # Comprehensive API documentation
│   ├── ARCHITECTURE.md                        # Architectural specification
│   ├── AUDIT_REPORT.md                        # Initial system audit
│   ├── BUILD_REPORT.md                        # Initial build report
│   ├── BUTTON_FUNCTIONALITY_AUDIT.md          # 40-button matrix audit
│   ├── FULL_SYSTEM_AUDIT.md                   # Full-system evaluation report
│   └── TRACEABILITY_MATRIX.md                 # Requirements traceability
├── experiments/
│   ├── baseline.py                            # Baseline A (Stop/Wait) vs B (Central Lock) vs ResilientEdge
│   ├── monte_carlo.py                         # Multi-seed Monte Carlo with 95% CI
│   ├── parameter_sweep.py                     # Sensitivity sweeps (robots, loss, latency)
│   └── scenarios.py                           # Benchmark scenarios S01 through S12
├── scripts/
│   ├── package.ps1                            # Packaging automation script
│   ├── run_backend.bat                        # Backend runner batch script
│   ├── run_backend.ps1                        # Backend runner PowerShell script
│   ├── run_core_sim.py                        # Standalone Python simulation runner
│   ├── run_experiment.py                      # Benchmark runner (S01–S12)
│   ├── run_frontend.bat                       # Frontend runner batch script
│   ├── run_frontend.ps1                       # Frontend runner PowerShell script
│   ├── setup_windows.bat                      # Windows setup batch script
│   ├── setup_windows.ps1                      # Windows setup PowerShell script
│   ├── start_resilientedge.bat                # Windows orchestrator batch script
│   └── start_resilientedge.ps1                # Windows orchestrator PowerShell script
├── src/
│   ├── App.tsx                                # Main application container and layout
│   ├── index.css                              # Tailwind CSS styles and custom scrollbars
│   ├── main.tsx                               # React root entry point
│   ├── types.ts                               # Central TypeScript interfaces
│   ├── components/
│   │   ├── BackupManager.tsx                  # Snapshot import/export and restore
│   │   ├── BaselineComparison.tsx             # Baseline A/B comparison charts
│   │   ├── CurrentTasksPanel.tsx              # Active task list and quick dispatch
│   │   ├── DatabaseDashboard.tsx              # SQLite / legacy cloud provider stats and event explorer
│   │   ├── ExperimentsRunner.tsx              # Scenario S01–S12 execution UI
│   │   ├── FaultInjectionPanel.tsx            # Chaos engineering fault injection
│   │   ├── FaultInjector.tsx                  # [UNUSED] Duplicate of FaultInjectionPanel
│   │   ├── FleetCards.tsx                     # [UNUSED] Superseded by inline cards in App.tsx
│   │   ├── Header.tsx                         # [UNUSED] Superseded by TopBar.tsx
│   │   ├── IncidentInvestigationModal.tsx     # [UNUSED] Decision evaluation modal
│   │   ├── IncidentTimeline.tsx               # [UNUSED] Superseded by IncidentTimelinePanel
│   │   ├── IncidentTimelinePanel.tsx          # Real-time incident stream and filter
│   │   ├── KpiCards.tsx                       # Fleet KPI strip
│   │   ├── MetricsDashboard.tsx               # Metric graphs and telemetry statistics
│   │   ├── NetworkTopologyView.tsx            # Network mesh latency / partition view
│   │   ├── ReplaySystemModal.tsx              # [UNUSED] Synthetic replay modal
│   │   ├── ResilienceStateMachine.tsx         # Resilience state transition diagram
│   │   ├── RobotDetailDrawer.tsx              # Robot inspect and control drawer
│   │   ├── RobotStatusPanel.tsx               # Right sidebar robot status strip
│   │   ├── SettingsModal.tsx                  # Simulation parameters modal
│   │   ├── Sidebar.tsx                        # Navigation sidebar
│   │   ├── SimulationCanvas.tsx               # [UNUSED] Superseded by SimulationMap
│   │   ├── SimulationMap.tsx                  # Primary 2D simulation canvas
│   │   ├── TaskDetailDrawer.tsx               # Task inspect, reassign, cancel drawer
│   │   ├── TaskDispatcherModal.tsx            # Task dispatch modal and queue
│   │   └── TopBar.tsx                         # Header with simulation clock controls
│   └── services/
│       └── apiService.ts                 # legacy cloud provider client with offline queue
├── legacy-cloud/
│   ├── migrations/
│   │   └── 20260926000000_initial_schema.sql  # Production SQLite schema with 10 server-side RBAC policies
│   └── seed/
│       └── seed.sql                           # Seed data for profiles, runs, robots, experiments
└── tests/
    ├── test_astar.py                          # A* algorithm unit tests
    ├── test_coordination.py                   # Conflict detection and allocation tests
    ├── test_database.py                       # SQLite persistence tests
    ├── test_deadlock.py                       # Deadlock cycle detection and breaking
    ├── test_deterministic.py                  # Seed reproducibility tests
    ├── test_e2e_simulation.py                 # Full lifecycle simulation tests
    ├── test_faults.py                         # Fault injection and heartbeat tests
    ├── test_models.py                         # Domain data model tests
    ├── test_network.py                        # Packet loss, latency, partition tests
    ├── test_production_and_baselines.py       # Baselines, Monte Carlo, explainability tests
    ├── test_recovery.py                       # Recovery and dynamic reassignment tests
    └── test_robot_lifecycle_and_integration.py# Pause, reset, reassign, settings tests
```

---

## 4. What Works

| Subsystem | Verified Behavior | Evidence |
|---|---|---|
| **Authoritative Simulation** | Full 24x16 grid simulation with A* pathfinding, spatial reservations, conflict avoidance, dynamic deadlock breaking, battery depletion, loading/unloading timers. | Verified via `scripts/run_core_sim.py` and live WebSocket telemetry. |
| **All 12 Experiment Scenarios** | S01 (Normal 3), S02 (Normal 10), S03 (Normal 20), S04 (Crossing), S05 (Blocked Aisle), S06 (Robot Failure), S07 (Low Battery), S08 (Packet Loss), S09 (Latency), S10 (Partition), S11 (Dynamic Obstacle), S12 (Combined). | `scripts/run_experiment.py` ran all 12 scenarios without crashing. |
| **Comparative Baselines** | Baseline A (Stop/Wait) and Baseline B (Centralized Lock) execute actual simulation steps and compare directly against ResilientEdge. | S06 benchmark verified: Baseline A = 0% comp, Baseline B = 0% comp, ResilientEdge = 66.7% comp. |
| **Monte Carlo Engine** | Runs scenarios across arbitrary seed counts with statistical computation of mean, median, standard deviation, min, max, and 95% confidence intervals. | Verified in `test_monte_carlo_execution`. |
| **Parameter Sweep Engine** | Sweeps `robot_count`, `packet_loss`, `latency`, and `fault_duration`, collecting sensitivity trends. | Verified in `test_parameter_sweep_execution`. |
| **SQLite Persistence** | Stores robots, tasks, faults, incidents, experiments, runs, reservations, decision events, metrics across 9 tables. | Verified in `test_database.py` (4 tests). |
| **FastAPI Backend Service** | REST endpoints (`/health`, `/robots`, `/tasks`, `/faults`, `/metrics`, `/scenarios`, `/settings`, `/backup`) and `/ws/telemetry` WebSocket. | Started on port 8000; probed via PowerShell `Invoke-RestMethod`. |
| **Node.js Host & IPC Bridge** | Discovers running FastAPI or seamlessly spawns `core/simulation/bridge.py` over stdio JSON streams. | Verified live at `http://localhost:3000/api/health`. |
| **TypeScript Typecheck** | Zero errors across all frontend source files. | `tsc --noEmit` exited code 0. |
| **Vite Production Build** | Compiles HTML, Tailwind CSS v4, and JS into `dist/`. | `node .\node_modules\vite\bin\vite.js build` built in 3.00s. |
| **Automated Unit Tests** | 38 automated test cases across 12 test files. | `python -m unittest discover tests` executed 38/38 OK. |

---

## 5. What Does Not Work & Known Bugs

### Bug 1: Windows Path Ampersand (`&`) Breaks npm CLI wrappers
- **Severity:** High (Windows Developer Experience)
- **Symptom:** Running `npm run dev` or `npm run build` from Windows `cmd.exe` fails with:
  `'-telemetry-platform\node_modules\.bin\' is not recognized as an internal or external command`
  `Error: Cannot find module '...\vite\bin\vite.js'`
- **Root Cause:** The workspace directory name contains an ampersand:
  `.../resilientedge---multi-robot-resilience-simulation-&-telemetry-platform`
  In Windows `cmd.exe`, `&` is a command separator. The npm `.bin/*.cmd` batch wrappers fail to quote `%~dp0` properly when expanding paths.
- **Workaround:** Invoking tools directly through Node works cleanly:
  - Development: `node ".\node_modules\tsx\dist\cli.mjs" server.ts`
  - Build: `node ".\node_modules\vite\bin\vite.js" build`
  - Typecheck: `node ".\node_modules\typescript\bin\tsc" --noEmit`

### Bug 2: npm Peer Dependency Conflict (`ERESOLVE`)
- **Severity:** Medium
- **Symptom:** Plain `npm install` fails with `ERESOLVE could not resolve`.
- **Root Cause:** `package.json` specifies `"vite": "^8.3.0"` and `"esbuild": "^0.25.0"`. `vite@8.3.1` has a peer dependency requirement of `esbuild@"^0.27.0 || ^0.28.0"`.
- **Workaround:** `npm install --legacy-peer-deps` resolves and installs all 191 packages cleanly.
- **Fix Needed:** Update `esbuild` dependency in `package.json` to `"^0.28.0"` or let Vite manage its internal esbuild version.

### Bug 3: SQLite Connection Resource Warnings in Unit Tests
- **Severity:** Low
- **Symptom:** `python -m unittest discover tests` outputs 15 warnings:
  `ResourceWarning: unclosed database in <sqlite3.Connection object>`
- **Root Cause:** In `backend/database/sqlite_db.py`, `with self.get_connection() as conn:` is used. In Python's `sqlite3`, the `with conn:` context manager only manages transaction commit/rollback—it does *not* close the database connection.
- **Fix Needed:** Add explicit `conn.close()` or implement a proper connection-closing context manager.

### Bug 4: Node.js Child Process Deprecation Warning
- **Severity:** Low (Security Warning)
- **Symptom:** `server.ts` outputs:
  `(node:5140) [DEP0190] DeprecationWarning: Passing args to a child process with shell option true can lead to security vulnerabilities`
- **Root Cause:** In `server.ts` line 102:
  `spawn(pythonExe, ['core/simulation/bridge.py'], { shell: process.platform === 'win32' })`
- **Fix Needed:** In Windows, executable resolution handles `.exe` directly; `shell: true` is not required when passing absolute or resolved executable paths.

### Bug 5: `TaskDispatcherModal` UX Inconsistency
- **Severity:** Low (UI Glitch)
- **Symptom:** In `App.tsx`, `{isDispatcherOpen && <TaskDispatcherModal ... />}` is rendered at the bottom of the page outside the main viewport, without an `onClose` prop. `TaskDispatcherModal` contains its own internal `[showModal, setShowModal]` state.
- **Fix Needed:** Connect `isDispatcherOpen` directly to the modal dialog visibility with an `onClose={() => setIsDispatcherOpen(false)}` prop.

---

## 6. Incomplete Functionality & Unused Files

### Unused / Duplicate Frontend Components
The following 7 components in `src/components/` are never imported by `App.tsx` or any active component:
1. `Header.tsx` (229 lines): Older navigation header; replaced by `TopBar.tsx`.
2. `FaultInjector.tsx` (249 lines): Earlier fault injection UI; replaced by `FaultInjectionPanel.tsx`.
3. `FleetCards.tsx` (119 lines): Earlier fleet card layout; fleet view in `App.tsx` renders its own cards inline.
4. `IncidentTimeline.tsx` (124 lines): Earlier incident list; replaced by `IncidentTimelinePanel.tsx`.
5. `SimulationCanvas.tsx` (426 lines): Earlier SVG canvas; replaced by `SimulationMap.tsx`.
6. `IncidentInvestigationModal.tsx` (199 lines): Detailed incident decision rationale modal. Fully coded with candidate evaluation comparisons, but not wired to row click events in `IncidentTimelinePanel.tsx`.
7. `ReplaySystemModal.tsx` (244 lines): Timeline scrubber modal. Contains placeholder synthetic position calculations `(offset = (t * 0.5 + idx * 4) % 18)` rather than querying recorded frames from `data/resilientedge.db`.

### Root Archive
- `ResilientEdge_COMPLETE_FINAL.zip` (204,766 bytes): Static zip archive in repository root. Should be moved to release artifacts or excluded from git tracking.

---

## 7. Security & Configuration Issues

1. **CORS Wildcard with Credentials:**
   In `backend/api/fastapi_app.py` lines 103–108:
   `allow_origins=["*"], allow_credentials=True`
   Browsers and security scanners reject wildcard origin when credentials are true. Origins should be restricted to `["http://localhost:3000", "http://127.0.0.1:3000"]`.
2. **Mock RBAC without Token Verification:**
   `server.ts` accepts `x-user-role` header without cryptographic validation. Fine for local simulation and demonstration, but requires legacy cloud provider JWT verification when deploying with cloud auth.
3. **Relative Database Path:**
   `backend/database/sqlite_db.py` uses `db_path="./data/resilientedge.db"`. If the application is launched from a subdirectory, SQLite will create a new database file in that subdirectory. It should resolve relative to the repository root.
4. **Environment Variables (.env):**
   `.env.example` provides complete configuration keys. A live `.env` file does not exist by default, which correctly causes `ApiService` to operate in safe local fallback mode.

---

## 8. Database Architecture & legacy cloud provider Status

### Local Persistence (Active: SQLite)
- **Database File:** `data/resilientedge.db`
- **Schema Management:** Automated table initialization in `ResilientEdgeDatabase.init_db()`
- **Tables (9):**
  1. `robots`: Fleet state, position `[x, y]`, battery, health, network status, updated timestamp.
  2. `tasks`: Tasks register with pickup, delivery, priority, deadline, status, timings.
  3. `faults`: Injected anomalies with duration and parameters.
  4. `incidents`: Chronological audit trail with severity (`INFO`, `WARNING`, `CRITICAL`).
  5. `experiments`: Benchmark scenario metadata and JSON metrics.
  6. `experiment_runs`: Run-by-run execution data.
  7. `reservations`: Spatiotemporal reservations.
  8. `decision_events`: Detailed rationale for dynamic task reassignments.
  9. `metrics`: Aggregate KPI records.

### Cloud Persistence (Standby: SQLite)
- **Status:** **STANDBY / OFFLINE BUFFERING**
- **Schema File:** `backend/database/20260926000000_initial_schema.sql` (382 lines)
  - Full relational schema mirroring the simulation model.
  - Row Level Security (server-side RBAC) policies configured for 3 roles:
    - `ADMIN`: Full read/write/truncate access.
    - `OPERATOR`: Read and insert/update telemetry, tasks, faults.
    - `OBSERVER`: Strict read-only access.
- **Seed File:** `backend/create_admin.py/seed.sql` (30 lines) with default profiles and benchmark runs.
- **Frontend Client:** `src/services/apiService.ts` detects lack of live credentials and falls back gracefully to local REST APIs. Any generated events are buffered in `persistenceQueue` and retried up to 5 times.

---

## 9. ROS 2 & Gazebo Integration Status

- **Status:** **NOT PRESENT (Decoupled Future Target)**
- **Verification:** Searched the entire codebase for ROS 2 (`rclpy`, `colcon`, `ros2`, `ament`) and Gazebo (`gz`, `sdf`, `urdf`).
- **Findings:**
  - Zero ROS 2 package definitions or Gazebo model descriptions exist in the repository.
  - The architecture is intentionally decoupled: `core/simulation/engine.py` maintains clean mathematical interfaces (`world.py`, `robot.py`, `clock.py`) designed to allow a future ROS 2 Node or Gazebo bridge to feed joint states/poses into the same resilience and coordination layer.
  - Documented as an optional roadmap phase in `docs/BUILD_REPORT.md`.

---

## 10. Testing & Verification Summary

### Automated Tests Executed:
1. **Command:** `python -m unittest discover tests`
   - **Result:** **PASSED** (Ran 38 tests in 0.523s)
   - **Status:** 38 passed, 0 failed, 0 errors.
   - **Breakdown:**
     - `test_astar.py`: 3 tests (straight line, obstacle avoidance, unreachable goal)
     - `test_coordination.py`: 3 tests (vertex conflict, reservation overlap, deterministic allocation)
     - `test_database.py`: 4 tests (init, save/retrieve telemetry, decision events, clear all)
     - `test_deadlock.py`: 2 tests (cycle detection, victim resolution)
     - `test_deterministic.py`: 1 test (reproducibility across seed 42)
     - `test_e2e_simulation.py`: 1 test (complete resilience lifecycle)
     - `test_faults.py`: 2 tests (fault lifecycle, heartbeat timeout)
     - `test_models.py`: 4 tests (robot, task, fault, reservation serialization)
     - `test_network.py`: 3 tests (packet loss, partition, state transitions)
     - `test_production_and_baselines.py`: 7 tests (decision explainability, low battery, Monte Carlo, jitter/reorder, parameter sweep, baseline comparison, snapshot determinism)
     - `test_recovery.py`: 1 test (robot failure and reassignment)
     - `test_robot_lifecycle_and_integration.py`: 7 tests (pause, resume, reset, reassign, scenarios, settings, snapshot save/restore)

2. **Pytest Attempt:**
   - **Command:** `pytest -q` / `python -m pytest -q`
   - **Result:** Failed with `No module named pytest` (pytest not installed in global Python 3.14 environment; standard `unittest` covers 100% of the suite).

3. **Frontend Build Verification:**
   - **Command:** `node ".\node_modules\vite\bin\vite.js" build`
   - **Result:** **PASSED** in 3.00s. Output:
     - `dist/index.html`: 1.39 kB
     - `dist/assets/index-XF5Ghw4U.css`: 50.24 kB
     - `dist/assets/index-Dx5jBDrS.js`: 375.47 kB

4. **Frontend Typecheck:**
   - **Command:** `node ".\node_modules\typescript\bin\tsc" --noEmit`
   - **Result:** **PASSED** (0 errors).

---

## 11. Recommended Implementation Order (Phased Roadmap)

Based on this audit, the recommended implementation plan to elevate ResilientEdge from working prototype to production-grade deployment is:

### Phase 1: Windows Scripting & Developer Experience Hardening
1. Patch `package.json` to resolve peer dependency issues (`esbuild` bump).
2. Fix Windows `.bat` and `.ps1` scripts (`start.bat`, `start_frontend.bat`, `run_frontend.bat`) to bypass cmd.exe ampersand parsing issues by invoking node CLI targets directly with quoted arguments.
3. Replace `"clean": "rm -rf dist server.js"` in `package.json` with a cross-platform rimraf command or Node script.

### Phase 2: Database Connection & Reliability Fixes
1. Fix connection closing in `backend/database/sqlite_db.py` to eliminate all 15 `ResourceWarning` unclosed database warnings.
2. Ensure database path resolves to absolute repository root path.
3. Fix CORS wildcard in `fastapi_app.py`.

### Phase 3: Component Cleanup & Missing Wire-ups
1. Clean up unused legacy components (`Header.tsx`, `FaultInjector.tsx`, `FleetCards.tsx`, `IncidentTimeline.tsx`, `SimulationCanvas.tsx`) into an archived directory or remove them cleanly.
2. Wire up `IncidentInvestigationModal.tsx` so clicking any row in `IncidentTimelinePanel.tsx` opens the explainable decision evaluation modal.
3. Clean up `TaskDispatcherModal.tsx` modal state management.
4. Replace synthetic replay calculation in `ReplaySystemModal.tsx` with true historical telemetry playback from SQLite.

### Phase 4: legacy cloud provider Production Integration (Optional Cloud Deployment)
1. Verify migrations against a live legacy cloud provider project.
2. Wire user authentication with local JWT authentication JWT verification in FastAPI / Express.
3. Enable live legacy cloud provider real-time broadcasting via SQLite publication channels.

### Phase 5: ROS 2 / Gazebo Bridge (Future Integration)
1. Implement a ROS 2 Nav2 / micro-ROS telemetry bridge node in `core/simulation/` subscribing to `/odom` and publishing to `/cmd_vel`.
2. Provide warehouse world URDF / SDF configuration.
