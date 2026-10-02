# ResilientEdge Release Validation

## Release candidate

Phase 6.5 → Phase 7 application package with public landing experience, local JWT/RBAC, authoritative FastAPI simulation, SQLite persistence, experiments, telemetry WebSocket, and ROS 2 adapter boundary.

## Verification loop completed

| Gate | Result | Evidence |
|---|---|---|
| Python compilation | PASS | `python -m compileall -q backend core experiments` |
| Automated Python suite | PASS | **84 passed** |
| Backend import smoke | PASS | FastAPI/core/experiment modules imported successfully |
| Authentication | PASS | Admin login + `/api/auth/me` verified |
| JWT refresh/logout | PASS | Auth session flow covered by tests and smoke checks |
| SQLite persistence | PASS | Local DB online and CRUD endpoints exercised |
| WebSocket telemetry | PASS | Authenticated WS received clock + 3-robot telemetry |
| RBAC | PASS | Operator/viewer mutation permissions verified server-side |
| Experiments | PASS | `run` and default five-run `compare` API verified |
| JSON safety | PASS | Regression added for zero-variance benchmark statistics |
| Frontend relative imports | PASS | 34 TS/TSX source files; 0 missing local imports |
| Windows startup | PASS (source audit) | One-command host starts FastAPI automatically and reuses an already-running backend |
| Frontend production build | NOT RUN IN THIS ENVIRONMENT | npm registry/dependency installation stalled; target-machine `npm ci`, `npm run lint`, and `npm run build` remain required |

## Defects fixed during release loop

1. Benchmark comparison could return non-JSON-safe `Infinity` for a zero-variance paired effect. The API now returns `null` plus an explicit reason instead.
2. Windows startup scripts could launch a second FastAPI process even when one was already running. The Node host now probes `/health`, reuses an existing backend, and only terminates a backend process that it owns.
3. Windows setup now creates `.env` from `.env.example`, generates a random local `JWT_SECRET` when the placeholder is present, and initializes SQLite.
4. The explicit admin bootstrap now supports `--reset-existing` without touching simulation data.
5. Legacy frontend components had incorrect `../types` imports; all local imports now resolve.
6. Removed the one-off `notepad reset_admin.py` helper that wrote an ISO timestamp into a REAL SQLite field.

## Admin bootstrap

The packaged local database contains the administrator account `petkaryash050@gmail.com`. For this development/SIH package, the packaged demo password is `ResilientEdge@2026`. Reset it before any non-demo deployment:

```powershell
$env:RESILIENTEDGE_ADMIN_PASSWORD="<new-password>"
python -m backend.create_admin --reset-existing
```

## Frontend verification on Windows

After installing Node dependencies:

```powershell
npm ci
npm run lint
npm run build
```

Or use:

```powershell
.\scripts\verify_release.ps1
```

## ROS 2 / Gazebo boundary

ROS 2 and Gazebo are represented as integration-ready interfaces. They are not falsely claimed as installed or operational in the local Windows release environment.
