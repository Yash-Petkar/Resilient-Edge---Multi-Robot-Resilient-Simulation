# ResilientEdge Phase 1 Fix Report

Phase 1 addressed only the verified Phase 0 findings and runtime issues exposed
while validating those fixes. Existing active dashboard functionality remains
in place.

| Bug | Root cause | Fix | Files changed | Test proving the fix |
|---|---|---|---|---|
| Python packages and test discovery depended on implicit namespace-package behavior. | Several importable source and test directories had no `__init__.py`; pytest configuration did not state its minimum version or reporting defaults. | Added package markers to `backend`, `core` and its subpackages, `experiments`, `scripts`, and `tests`; retained the repository-root Python path and test directory in `pytest.ini`, and declared pytest 8+ with concise failure reporting. | `backend/__init__.py`, `backend/api/__init__.py`, `backend/database/__init__.py`, `core/__init__.py`, `core/coordination/__init__.py`, `core/faults/__init__.py`, `core/metrics/__init__.py`, `core/networking/__init__.py`, `core/planning/__init__.py`, `core/resilience/__init__.py`, `core/simulation/__init__.py`, `experiments/__init__.py`, `scripts/__init__.py`, `tests/__init__.py`, `pytest.ini` | `pytest -q` — **44 passed** without setting `PYTHONPATH`. |
| Robot home positions differed between initialization, reset, saved/restored state, and failure recovery. | Initial positions were repeated as literals and reset inferred a position separately from robot creation. | Added `robot_home_position()` as the deterministic source; robot creation/reset and failed-robot recovery use it. Robot and simulation snapshots record home coordinates; restore derives them from the same function rather than trusting snapshot-provided home values. | `core/models/robot.py`, `core/simulation/engine.py`, `backend/api/fastapi_app.py`, `core/simulation/bridge.py`, `tests/test_robot_lifecycle_and_integration.py` | `test_home_positions_are_consistent_across_lifecycle` verifies initialization, serialized snapshot data, restore, reset, and recovery for R2. |
| The task dispatcher always received the ADMIN role. | `App.tsx` passed a hardcoded role instead of the current role profile, while a reload could leave the UI role out of sync with the backend profile. | Load `/api/auth/me` at startup using OBSERVER as the fail-closed initial role; pass `currentUser.role` to the dispatcher; wait for backend role changes before updating the UI. A shared role-permission map is used by active controls, and both Node and FastAPI enforce the role held by the application profile. Observers can read only; operators can control simulation, dispatch tasks, inject faults, recover robots, and run experiments; settings, database writes/administration, snapshot restoration, and other destructive actions require ADMIN. | `src/App.tsx`, `src/permissions.ts`, `src/services/apiService.ts`, `src/components/TaskDispatcherModal.tsx`, `src/components/FaultInjectionPanel.tsx`, `src/components/TopBar.tsx`, `src/components/ExperimentsRunner.tsx`, `src/components/DatabaseDashboard.tsx`, `src/components/BackupManager.tsx`, `src/components/Sidebar.tsx`, `src/components/RobotDetailDrawer.tsx`, `src/components/TaskDetailDrawer.tsx`, `server.ts`, `backend/api/permissions.py`, `backend/api/fastapi_app.py`, `tests/test_permissions.py` | `tests/test_permissions.py` checks the role matrix and endpoint categories. Live API smoke test: operator task creation/read succeeded while settings returned **403**; an observer received **403** for task mutation even when sending `x-user-role: ADMIN`. |
| Old or unwired UI components were mixed with active source. | The Phase 0 audit found unused predecessor components and two components that were not connected to real data. | Isolated the unused/obsolete components under `src/legacy/components/`, excluded that directory from the active TypeScript project, and documented which files are predecessors versus unwired features. Current active components remain in `src/components/`. | `src/legacy/README.md`, `src/legacy/components/FaultInjector.tsx`, `src/legacy/components/FleetCards.tsx`, `src/legacy/components/Header.tsx`, `src/legacy/components/IncidentInvestigationModal.tsx`, `src/legacy/components/IncidentTimeline.tsx`, `src/legacy/components/ReplaySystemModal.tsx`, `src/legacy/components/SimulationCanvas.tsx`, `tsconfig.json` | `npm run lint` passes with isolated legacy files excluded; `npm run build` succeeds. |
| Settings navigation intercepted the Settings tab and opened a modal, leaving the existing backup/restore page unreachable. | The sidebar click handler never selected the `settings` tab that renders `BackupManager`. | Let the sidebar select the requested tab; retain the separate TopBar button for the settings modal. | `src/App.tsx` | `npm run build` verifies the route wiring compiles; ADMIN-only restore remains guarded by the shared permission map. |
| A generated ZIP archive was stored in the project source tree. | The root archive duplicated release/source material and could be included in source control. | Removed `ResilientEdge_COMPLETE_FINAL.zip` and added a `*.zip` ignore rule. No other ZIP archives remain outside dependencies. | `.gitignore`, `ResilientEdge_COMPLETE_FINAL.zip` (removed) | Filesystem search found no ZIP files in the project source outside `node_modules`. |
| UI copy made unsupported security/reliability claims. | Snapshot JSON was described as cryptographically verifiable without a signature/check; the local SQLite fallback was labeled as having active server-side RBAC and a zero-crash guarantee. | Describe snapshots as ordinary timestamped JSON; report legacy cloud provider connectivity versus local API role checks accurately and replace the crash guarantee with a factual offline-cache description. | `src/components/BackupManager.tsx`, `src/components/DatabaseDashboard.tsx` | Source search confirms those claims are gone; `npm run build` verifies the UI changes compile. |
| Windows npm script shims failed when the project path included `&`; the dependency tree also declared an incompatible direct esbuild peer. | npm's Windows `.cmd` wrappers misparsed the path, while the direct esbuild 0.25 dependency conflicted with Vite 8's optional peer range. | Changed npm scripts to invoke local Node entrypoints directly; removed the unnecessary direct esbuild dependency and synchronized the npm lockfile. Updated Vite's directory alias for the supported Node runtime. | `package.json`, `package-lock.json`, `bun.lock`, `vite.config.ts`, `tsconfig.json` | `npm install --package-lock-only --ignore-scripts` succeeds without a legacy peer override; `npm run build` and `npm run lint` pass from the attached path containing `&`. |
| SQLite connections stayed open after `with` blocks, and the default database location depended on the launch directory. | SQLite's connection context manager commits/rolls back but does not close the connection; the default DB path was relative to the process working directory. | Added an explicit closing transaction context and anchored the default database path at the project root. | `backend/database/sqlite_db.py`, `tests/test_database.py` | `test_connection_context_closes_connection` verifies use-after-close fails; `test_default_database_path_is_repository_relative` verifies the stable default path. Python test runs no longer emit unclosed-connection `ResourceWarning`s. |
| Host, port, and CORS defaults were inconsistent or unsafe for a local-first app. | The Node host bound to all interfaces with a fixed port; FastAPI allowed wildcard origins with credentials; Windows launch scripts hardcoded backend endpoints. | Added validated `HOST`/`PORT` and backend port configuration with loopback defaults, restricted default CORS origins to the local frontend, exposed values in `.env.example`, and wired Windows launch scripts to backend host/port environment variables. | `server.ts`, `backend/api/fastapi_app.py`, `.env.example`, `scripts/run_backend.ps1`, `scripts/run_backend.bat`, `start_backend.bat`, `start.bat`, `scripts/start_resilientedge.bat` | Python suite covers the API permission policy; application smoke test reported `/api/health` as ONLINE. Local launch defaults are `127.0.0.1:3000` and `127.0.0.1:8000`. |
| The app package was published internally as `react-example`. | Scaffold package metadata had not been renamed. | Renamed the npm package and synchronized the npm and Bun lockfile project names. | `package.json`, `package-lock.json`, `bun.lock` | `npm run build` identifies the project as `resilientedge`. |

## Verification

- `pytest -q` — **44 passed**.
- `python -m unittest discover tests` — **44 passed**.
- `npm run build` — **passed** (Vite transformed 1,724 modules).
- `npm run lint` — **passed** (`tsc --noEmit`).
- Live local API smoke test — **passed**: backend health was ONLINE; an operator could create/read tasks but received 403 for settings; an observer received 403 for task creation, including when attempting to override the role through a client-supplied `x-user-role: ADMIN` header.

The role selector remains the application's local profile-switching/demo
mechanism; it is not a substitute for verified external authentication.

## Reassignment regression fix (2026-09-27)

The production validation pass found a real reassignment edge case: the previous
implementation detached the source robot and released its reservations before it
knew whether another robot could accept the task. If every candidate was busy,
paused, failed, disconnected, or path-infeasible, the operation returned an error
with the original task already corrupted to an unassigned state.

The fix:

- makes `reassign_task(task_id)` the authoritative task-level operation;
- evaluates replacement candidates before mutating source/task state;
- keeps the original assignment intact on `NO_ELIGIBLE_ROBOT`;
- supports tasks already released to `AVAILABLE` by robot-failure recovery;
- rejects paused/non-operational/disconnected replacement robots;
- adds a `TASK_REASSIGN` Python IPC command;
- changes `/api/tasks/:id/reassign` to send the authoritative task ID instead of
  deriving a source robot from potentially stale Node telemetry;
- keeps the existing `/api/robots/:id/reassign` compatibility route;
- adds regression tests for successful, failed/atomic, and post-failure task
  reassignment.

Validation: `pytest -q` — **50 passed**.
