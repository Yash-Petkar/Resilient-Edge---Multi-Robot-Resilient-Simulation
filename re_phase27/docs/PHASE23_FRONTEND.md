# Phase 23 — Frontend

## Scope

Phase 23 integrates the existing React + Vite frontend with the authoritative FastAPI backend and WebSocket telemetry layer. The Python `SimulationEngine` remains authoritative.

## Required views

- `/dashboard`
- `/simulation`
- `/robots`
- `/tasks`
- `/incidents`
- `/experiments`
- `/metrics`
- `/settings`

Additional operational views retained by the existing application:

- `/faults`
- `/recovery`
- `/baseline`
- `/network`
- `/database`
- `/admin/users`
- `/admin/audit`

## Integration

The frontend consumes:

- FastAPI REST endpoints under `/api/*`
- `/ws/telemetry` for live telemetry
- SQLite status through the backend
- Server-side authentication and RBAC

The browser does not become an alternate simulation authority.

## Routing hardening

All primary views now have stable browser paths. Refreshing or using browser back/forward navigation resolves the correct active view instead of falling back to Dashboard.

## Verification

- Backend regression suite: 181 passed.
- Frontend dependency installation/build could not be completed in the build environment because `npm install` timed out.
- Consequently, no claim is made that `npm run build` or `npm run lint` passed in this environment; those checks should be run after dependencies are installed locally.
