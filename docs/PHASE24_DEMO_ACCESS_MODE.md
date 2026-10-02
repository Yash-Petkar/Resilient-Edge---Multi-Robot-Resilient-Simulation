# Phase 24 — Judge/Demo Access Mode

## Purpose

The application now opens directly on the existing **Choose your access mode** screen when `DEMO_MODE` / `VITE_DEMO_MODE` is enabled (the packaged application defaults to demo mode). This removes the password/login dependency from the judge startup flow without removing the existing JWT authentication implementation.

## Preserved functionality

- Existing Administrator / Operator / Observer / Viewer permissions remain unchanged.
- Existing JWT login, refresh, logout, password hashing, sessions, and RBAC remain available when demo mode is disabled.
- Simulation, telemetry, WebSocket, persistence, experiments, fault injection, recovery, database, settings, and admin features are not replaced.
- Backend permission checks continue to run in demo mode using the selected role.

## Demo flow

`Run application -> Choose Access Mode -> Continue -> role-specific dashboard`

The demo frontend sends `X-Demo-Role` on HTTP API calls and `demo_role` on the telemetry WebSocket. The FastAPI middleware accepts those demo credentials only while `DEMO_MODE=true`; the normal JWT path remains the fallback.

## Production/authenticated flow

Set both variables to false:

```env
DEMO_MODE=false
VITE_DEMO_MODE=false
```

The original landing -> access mode -> login -> authenticated RBAC flow is then used.
