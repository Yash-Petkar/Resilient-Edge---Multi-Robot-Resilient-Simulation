# ResilientEdge

Multi-Robot Resilience Simulation & Telemetry Platform.

## Architecture

```text
React + Vite
      |
Node/Express development host + proxy :3000
      |
FastAPI :8000
      |
SQLite persistent database
      |
Authoritative Python SimulationEngine
```

The Python simulation engine remains authoritative for robot state, task state, faults, recovery, simulation time, planning, coordination, and resilience behavior. FastAPI is the authoritative application backend. SQLite is the only persistence provider. Node is transport/development hosting only.

## Requirements

- Python 3.11+
- Node.js 20+
- npm
- Windows PowerShell supported

## Windows setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
npm install
```

Initialize the database:

```powershell
python -m backend.init_db
```

Create the initial administrator interactively, or set `RESILIENTEDGE_ADMIN_PASSWORD` for a non-interactive bootstrap:

```powershell
python -m backend.create_admin
```

If the administrator already exists and its password must be intentionally replaced:

```powershell
python -m backend.create_admin --reset-existing
```

Start the complete application (FastAPI + React/Vite host) with one command:

```powershell
npm run dev
```

`server.ts` starts FastAPI automatically when port 8000 is free. If FastAPI is already running, it reuses that instance instead of starting a duplicate process. The normal development URL is `http://127.0.0.1:3000`; FastAPI is available at `http://127.0.0.1:8000`.

Windows one-click startup:

```powershell
.\scripts\setup_windows.ps1
.\scripts\start_resilientedge.ps1
```

## Environment

Copy `.env.example` to `.env`.

Required production-style configuration:

```text
APP_URL=http://127.0.0.1:3000
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
HOST=127.0.0.1
PORT=3000
JWT_SECRET=<random secret, at least 32 characters>
DATABASE_PATH=./data/resilientedge.db
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
NODE_ENV=development
```

`JWT_SECRET` is server-only and must never use a `VITE_` prefix.

For the packaged judge/demo configuration, `.env` enables direct access with:

```text
DEMO_MODE=true
VITE_DEMO_MODE=true
```

## Demo Access

The public entry flow is intentionally direct for the demo deployment:

```text
Landing Page (/)
      ↓
Access System (/access)
      ↓
Admin OR Observer
      ↓
Application (/app)
```

There is no username, password, email, or login page in this demo UI. The selected role is still sent to FastAPI through the existing demo-role mechanism, and server-side RBAC remains authoritative.

The demo selector exposes only **Admin** and **Observer**. Operator and Viewer are not presented in the UI.

## Authentication

FastAPI implements email/password authentication using SQLite and JWT.

Endpoints:

- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/logout`
- `POST /api/auth/refresh`

Passwords are stored as salted `scrypt` hashes. Access tokens contain `sub`, `email`, `role`, `iat`, `exp`, and a token type.

The backend JWT authentication implementation remains available for authenticated deployments, but it is not exposed by the current demo UI. Protected demo requests use the selected `X-Demo-Role`, and FastAPI re-checks permissions server-side on every protected request.

## RBAC

| Role | Read | Simulation | Tasks | Faults | Recovery | Experiments | Settings | DB Admin | User Admin |
|---|---|---|---|---|---|---|---|---|---|
| ADMIN | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| OPERATOR | Yes | Yes | Yes | Yes | Yes | Yes | No | No | No |
| OBSERVER | Yes | No | No | No | No | No | No | No | No |
| VIEWER | Yes | No | No | No | No | No | No | No | No |

Server-side authorization is authoritative. Frontend role state is only for presentation and control visibility.

## Database

The SQLite database preserves the existing simulation tables and adds:

- `users`
- `profiles`
- `audit_logs`

Indexes are created for user email, profile email/role, audit timestamp, and audit user ID. Foreign keys are enabled on each SQLite connection.

`python -m backend.init_db` is idempotent and never deletes existing simulation data.

## Admin account

The bootstrap command creates:

- Email: `petkaryash050@gmail.com`
- Full name: `Fleet Administrator`
- Role: `ADMIN`

The password is supplied through `RESILIENTEDGE_ADMIN_PASSWORD` or an interactive prompt. It is never embedded in frontend source.

The backend prevents demoting the last administrator.

## Audit logging

Administrative and authentication events are stored in `audit_logs`. Passwords, JWTs, and secrets are never written to audit records.

Current administration endpoints:

- `GET /api/admin/users`
- `PATCH /api/admin/users/{id}/role`
- `GET /api/admin/audit`

## API and WebSocket

Existing simulation API contracts remain under `/api/*`, including robots, tasks, faults, scenarios, experiments, metrics, settings, database status, and simulation controls.

Health:

- `GET /api/health`
- `GET /api/database/status`

Telemetry:

- `GET /ws/telemetry` through the Node development proxy
- FastAPI authoritative WebSocket: `/ws/telemetry`

The simulation advances independently of connected browsers. Disconnecting a browser does not stop the simulation.

## Persistence worker

Simulation writes are asynchronous. The simulation loop does not wait on SQLite writes. The worker uses a bounded queue and bounded exponential retry behavior so a transient database error does not terminate the simulation.

## Experiments

The existing S01-S12 scientific experiment system remains in `experiments/`. Scenario definitions, deterministic seeds, baseline/resilient configurations, metrics, replay, and result persistence are preserved.

## Testing

Python validation:

```powershell
python -m compileall -q backend core experiments
python -m pytest -q
```

Frontend validation:

```powershell
npm run lint
npm run build
```

## Troubleshooting

### Database offline

Check that `DATABASE_PATH` points to a writable location and that the process has permission to create the SQLite file.

### 401 Unauthorized

The access token is missing, expired, invalid, or the corresponding local account is inactive/missing.

### 403 Forbidden

The authenticated account does not have the server-side permission required by the endpoint.

### WebSocket authentication failure

Verify that the browser has a valid JWT and that the Node proxy can reach FastAPI on `BACKEND_HOST:BACKEND_PORT`.

### Frontend dependencies

Run `npm install` on the target machine. Do not copy a platform-specific `node_modules` directory between operating systems.

## Security notes

- Never commit `.env` or real secrets.
- Never expose `JWT_SECRET` to browser code.
- Never trust a role supplied by React, localStorage, query parameters, or request bodies.
- Never log passwords or JWTs.
- Keep FastAPI and SQLite behind the deployment's normal process, network, and filesystem controls.

## Later phases

ROS 2, Gazebo, decentralized coordination, and additional physical-robot integrations are intentionally outside this migration.


## Phase 17 — Metrics Engine

The metrics layer is authoritative and event/state derived. It does not fabricate
performance values. `SimulationEngine.get_telemetry()` finalizes current
resilience-state duration and synchronizes transport counters from the
`NetworkSimulator` before producing the metrics summary.

Metrics include task completion rate, makespan, waiting/execution/route metrics,
planning latency, conflicts, collisions, deadlocks and recovery timing, robot
availability/utilization, task reassignment, network delivery/drop/duplicate/
reorder/stale counters, packet-loss rate, latency percentiles, and resilience
state durations.

Network counters are copied from the authoritative transport layer, while
simulation events record task, conflict, failure, deadlock, recovery and
planning measurements. Metric state is snapshot/restorable.
\n## Phase 19 — Baseline Comparison\n\nPhase 19 executes Baseline A (Stop/Wait), Baseline B (Centralized Lock), and ResilientEdge using the same scenario definition, seed, robot/task counts, duration, world, and fault/network schedules. Initial-condition fingerprints are compared before metrics are reported. Results are measurement-only: no synthetic multipliers or fabricated winner are introduced.\n\nExample:\n\n```powershell\npython -c "from experiments.baseline import run_baseline_comparison; import json; print(json.dumps(run_baseline_comparison('S06', 42), indent=2))"\n```\n\nMulti-seed matrix:\n\n```powershell\npython -c "from experiments.baseline import run_baseline_matrix; import json; print(json.dumps(run_baseline_matrix('S06', [42,43,44]), indent=2))"\n```\n

## Phase 20 — SQLite Database Persistence

Phase 20 makes SQLite the authoritative local persistence layer for the completed
simulation stack. The database is initialized idempotently and preserves existing
records on restart.

Required scientific/persistence entities are stored in:

- `robots`
- `tasks`
- `experiments`
- `experiment_runs`
- `faults`
- `incidents`
- `reservations`
- `decision_events`
- `metrics`

Additional application tables retain simulation, telemetry, network, recovery,
authentication, and audit history.

Schema initialization maintains a `schema_migrations` ledger with Phase 20 version
`20`, enables SQLite foreign-key enforcement, and creates indexes for experiment
runs, incidents, reservations, decision events, metrics, and fault queries.

Initialize with:

```powershell
python -m backend.init_db
```

The command is safe to run repeatedly and does not delete existing simulation data.

## Judge / Demo startup (Phase 24–28)

The packaged demo opens on the white/blue ResilientEdge landing page. The public flow is:

```text
Landing Page (/)
      ↓
Access System (/access)
      ↓
Admin OR Observer
      ↓
Application (/app)
```

There is no username, password, email, or login page in the demo UI. The existing JWT authentication and RBAC implementation remains available in the backend for authenticated deployments. Demo requests use the explicit demo role, and FastAPI still enforces permissions server-side. The Node WebSocket proxy forwards the selected demo role to FastAPI.

The packaged `.env` enables `DEMO_MODE=true` and `VITE_DEMO_MODE=true`. This is intentional for local/judge/demo use; do not use the demo configuration as a production authentication configuration.

See `docs/PHASE24_DEMO_ACCESS_MODE.md`, `docs/PHASE25_DEMO_AUTH_MODE.md`, and `docs/PHASE28_DIRECT_ADMIN_OBSERVER_ACCESS.md`.

## Current Windows startup (Phase 28 light-theme build)

From the project root, run `start.bat`. It creates `.venv` when missing, installs Python dependencies, initializes SQLite, installs Node dependencies when `node_modules` is absent, and starts the combined UI/FastAPI process. The backend is configured for `DEMO_MODE=true` and the frontend for `VITE_DEMO_MODE=true`.

Access flow:
- `/` — white/blue landing page
- `/access` — Admin or Observer selection; no login screen
- `/app` — existing application with the selected demo role

The application is light-only. Legacy dark utility classes are overridden in `src/index.css`, and the simulation canvas was changed to a light warehouse visualization. Backend startup prefers `.venv\Scripts\python.exe` on Windows.
