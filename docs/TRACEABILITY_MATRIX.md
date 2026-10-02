# ResilientEdge Requirement Traceability Matrix

| Req ID | Requirement Description | Implementation Module | Automated Test | Scenario Evidence | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **FR-01** | Frontend Start & Offline Resilience | `src/App.tsx`, `Header.tsx` | UI Mount Test | Browser Load | **PASS** |
| **FR-02** | Robot Domain Models | `core/models/robot.py` | `tests/test_models.py` | Unit Test | **PASS** |
| **FR-03** | A* Path Planning & Obstacle Detour | `core/planning/astar.py` | `tests/test_astar.py` | S05 Blocked Aisle | **PASS** |
| **FR-04** | Continuous Simulation Loop | `core/simulation/engine.py` | `tests/test_e2e_simulation.py` | Standalone Runner | **PASS** |
| **FR-05** | Deterministic Task Allocation | `core/coordination/allocator.py` | `tests/test_coordination.py` | S01 Normal 3 Robots | **PASS** |
| **FR-06** | Spatial-Temporal Reservations | `core/coordination/reservation_manager.py` | `tests/test_coordination.py` | S04 Crossing Conflict | **PASS** |
| **FR-07** | Deadlock Cycle Resolution | `core/coordination/deadlock.py` | `tests/test_deadlock.py` | Cycle Backoff | **PASS** |
| **FR-08** | Heartbeat Failure Detection | `core/resilience/failure_detector.py`| `tests/test_faults.py` | S06 Robot Failure | **PASS** |
| **FR-09** | Autonomous Task Recovery & Handoff | `core/resilience/recovery_manager.py`| `tests/test_recovery.py` | S06, S12 Combined | **PASS** |
| **FR-10** | Wireless Network Simulation & Loss | `core/networking/network_sim.py` | `tests/test_network.py` | S08 Packet Loss | **PASS** |
| **FR-11** | Network Partition & Resynchronization| `core/resilience/state_machine.py` | `tests/test_network.py` | S10 Partition | **PASS** |
| **FR-12** | Event-Driven Metrics Calculation | `core/metrics/collector.py` | `tests/test_deterministic.py` | S01-S12 Benchmarks | **PASS** |
| **FR-13** | Benchmark Scenarios (S01 to S12) | `experiments/scenarios.py` | `scripts/run_experiment.py` | S01-S12 Output | **PASS** |
| **FR-14** | Baseline Comparison (A vs B vs Proposed)| `experiments/baseline.py` | `experiments/baseline.py` | S06 Comparison Table| **PASS** |
| **FR-15** | SQLite Database Persistence | `backend/database/sqlite_db.py` | `tests/test_models.py` | DB File Check | **PASS** |
| **FR-16** | FastAPI REST & WebSocket Backend | `backend/api/fastapi_app.py` | Local execution script | Windows Script | **PASS** |
| **FR-17** | Real-Time Web Telemetry Stream | `server.ts` (`/ws/telemetry`) | Server health curl check | Live UI Stream | **PASS** |
| **FR-18** | Role-Based Access Control (RBAC) | `src/types.ts`, `src/App.tsx` | UI Role Switcher | Admin/Op/Observer | **PASS** |
| **FR-19** | Critical Network Fluctuation Alerts | `src/App.tsx`, `Header.tsx` | Simulated loss threshold | Alert Banner | **PASS** |
| **FR-20** | Analytical Report Export (CSV & PDF) | `src/components/MetricsDashboard.tsx`| Export Function Calls | CSV & Print Trigger | **PASS** |
| **FR-21** | Dark Mode Theme Support | `src/components/Header.tsx` | Theme class toggling | Dark/Light CSS | **PASS** |
| **FR-22** | Windows Execution Scripts | `scripts/*.ps1`, `scripts/*.bat` | Script syntax validation | Windows Ready | **PASS** |
