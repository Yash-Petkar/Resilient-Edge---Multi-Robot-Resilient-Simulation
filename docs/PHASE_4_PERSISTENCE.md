# ResilientEdge Phase 4 — Production Persistence + legacy cloud provider Integration

## Architecture

```text
React/Vite
   |
Node/Express host or FastAPI
   |
PersistenceRepository
   +--> LegacyCloudRepository (authoritative when configured + healthy)
   +--> SQLiteRepository (explicit/local development mode)
   |
SQLite / SQLite
```

The Python simulation remains authoritative. Database writes run through a bounded background worker so database latency/outages cannot terminate the simulation loop. WebSocket telemetry remains the live transport.

## Configuration

Server-only:
- `REMOTE_DATABASE_URL`
- `REMOTE_DATABASE_SERVER_KEY`

Browser-safe:
- `VITE_REMOTE_DATABASE_URL`
- `VITE_LEGACY_DATABASE_KEY`

Persistence controls:
- `PERSISTENCE_BACKEND=auto|local`
- `LOCAL_DB_FALLBACK=false|true`

## Health semantics

`GET /api/health` and `GET /api/database/status` report:
- `remote provider / online`
- `remote provider / offline`
- `remote provider / configuration_error`
- `sqlite / online`

Credentials are never returned.

## Persistence

Meaningful robot/task state is sampled from authoritative telemetry. Simulation control events, faults, incidents, recovery events, network degradation/restoration, telemetry snapshots, experiment runs, and metrics use the existing persistence abstraction. The worker retries legacy cloud provider connection establishment on a bounded interval.

## legacy cloud provider schema alignment

`backend/database/20260927120000_phase4_persistence.sql` adds only missing relationships/metadata: simulation-run parent linkage, network/recovery run IDs, experiment reproducibility fields, indexes, and required server-side RBAC read policies. Historical migrations are not modified.

## Security

The server key is read only by backend Python modules. It is not placed in `VITE_*`, React code, WebSocket messages, API responses, or logs. Browser access uses the anon/publishable key and authenticated legacy cloud provider sessions.

## Verification

Offline/local verification can run without legacy cloud provider credentials. A real legacy cloud provider connection can only be marked verified when valid project credentials are supplied and the backend's REST database client health check succeeds.
