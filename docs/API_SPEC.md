# ResilientEdge REST & WebSocket API Specification

## Authentication

When legacy cloud provider server configuration is enabled, `/api/*` operational endpoints require `Authorization: Bearer <legacy cloud provider access token>`. The backend validates the JWT and loads the role from `profiles`.

Local Windows development without legacy cloud provider uses the server-defined `JWT authentication`; the browser cannot change the role.

### Roles

| Role | Permissions |
|---|---|
| OBSERVER | Read simulation state, robots, tasks, metrics, incidents, experiment results |
| OPERATOR | Observer + simulation control, task dispatch, permitted fault/recovery actions, experiments |
| ADMIN | Operator + settings, database administration, destructive snapshot operations |

## Core endpoints

| Method | Path | Authorization | Purpose |
|---|---|---|---|
| GET | `/api/health` | Public | Service + database + WebSocket health |
| GET | `/api/auth/me` | Authenticated | Current authenticated profile/role |
| GET | `/api/simulation/state` | Authenticated | Current authoritative state summary |
| POST | `/api/simulation/start` | Operator | Resume simulation |
| POST | `/api/simulation/pause` | Operator | Pause simulation |
| POST | `/api/simulation/step` | Operator | Advance one deterministic step |
| POST | `/api/simulation/reset` | Operator | Reset simulation |
| POST | `/api/controls/clock` | Operator | Pause/resume/step/reset/scale |
| GET | `/api/robots` | Authenticated | Robot telemetry |
| GET | `/api/robots/:id` | Authenticated | Single robot |
| GET | `/api/tasks` | Authenticated | Tasks |
| POST | `/api/tasks` | Operator | Create task |
| POST | `/api/tasks/:id/assign` | Operator | Assign task |
| POST | `/api/tasks/:id/reassign` | Operator | Reassign task |
| POST | `/api/tasks/:id/cancel` | Operator | Cancel task |
| GET | `/api/faults` | Authenticated | Active faults |
| POST | `/api/faults` | Operator | Inject fault |
| DELETE | `/api/faults/:id` | Operator | Resolve/clear fault |
| POST | `/api/faults/clear-all` | Operator | Clear active faults |
| GET | `/api/incidents` | Authenticated | Incident history |
| GET | `/api/metrics` | Authenticated | Current metrics |
| GET | `/api/scenarios` | Authenticated | Scenario catalog |
| POST | `/api/scenarios/run` | Operator | Run scenario |
| GET | `/api/experiments` | Authenticated | Experiment history |
| POST | `/api/experiments/monte-carlo` | Operator | Run Monte Carlo experiment |
| POST | `/api/experiments/parameter-sweep` | Operator | Run parameter sweep |
| GET | `/api/baseline` | Authenticated | Baseline comparison |
| GET | `/api/settings` | Authenticated | Simulation settings |
| POST | `/api/settings` | Admin | Update settings |
| GET | `/api/database/status` | Public | Actual persistence backend/health state |
| GET | `/api/database/stats` | Authenticated | Persistence statistics |
| GET | `/api/database/robots` | Authenticated | Persisted robots |
| GET | `/api/database/tasks` | Authenticated | Persisted tasks |
| GET | `/api/database/incidents` | Authenticated | Persisted incidents |
| GET | `/api/database/events` | Authenticated | Persisted decision events |
| POST | `/api/database/clear` | Admin | Clear local administrative database |
| GET | `/api/backup` | Authenticated | Export snapshot |
| POST | `/api/snapshot/restore` | Admin | Restore snapshot |

## Request/response examples

### Create task

```json
POST /api/tasks
{
  "pickup": [2, 2],
  "delivery": [21, 2],
  "priority": 3,
  "deadline": 300
}
```

### Inject fault

```json
POST /api/faults
{
  "type": "ROBOT_FAILURE",
  "target": "R2",
  "duration": 30,
  "parameters": {}
}
```

### Error contract

- `400` malformed/invalid request or domain operation
- `401` missing/invalid/expired authentication
- `403` authenticated but insufficient role
- `404` resource not found
- `409` valid request conflicts with current simulation state
- `500` unexpected server error
- `503/504` transport/backend unavailable where applicable

## WebSocket telemetry

`ws://<host>:<port>/ws/telemetry?access_token=<legacy cloud providerAccessToken>`

The initial message is the newest authoritative snapshot. Subsequent messages are telemetry snapshots from the Python simulation engine. Each telemetry message preserves the authoritative state fields and adds `message_type: "TELEMETRY"`, a monotonically increasing `sequence`, and `server_timestamp`. Each client has a bounded queue so slow browsers cannot block the simulation loop; stale queued snapshots may be dropped in favor of newer state. A disconnected browser does not stop the simulation; reconnect receives the newest cached snapshot. Clients may send `{"type":"PING"}` and receive a `PONG` response.
