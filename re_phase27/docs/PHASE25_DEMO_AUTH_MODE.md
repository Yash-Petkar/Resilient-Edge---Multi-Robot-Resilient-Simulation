# ResilientEdge — Phase 25
## Environment-Controlled Demo Mode + Production Authentication

Phase 25 removes the Phase 24 hard-coded demo-mode behavior. The frontend now reads `VITE_DEMO_MODE` through `ApiService.isDemoMode()`, while the backend reads `DEMO_MODE`.

### Demo deployment

```env
DEMO_MODE=true
VITE_DEMO_MODE=true
```

Flow:

```text
Access Mode → Role → Dashboard
```

The selected role is sent through the existing demo-role mechanism. Backend RBAC and WebSocket demo authentication remain enforced.

### Authenticated deployment

```env
DEMO_MODE=false
VITE_DEMO_MODE=false
```

Flow:

```text
Normal Authentication → JWT → Backend RBAC → Dashboard
```

The frontend clears stale demo-role state and does not treat a demo role as authentication.

### Configuration mismatch

The backend health response reports its active `demo_mode`. The frontend compares it with `VITE_DEMO_MODE`. If they differ, the UI blocks entry and displays the mismatch instead of silently producing an insecure or unusable state.

### Startup

The launcher scripts no longer force `DEMO_MODE=true`. Configuration comes from the environment / `.env`.

For a demo package, copy `.env.example` to `.env` and use:

```env
DEMO_MODE=true
VITE_DEMO_MODE=true
```

For an authenticated deployment:

```env
DEMO_MODE=false
VITE_DEMO_MODE=false
```

Do not put JWT secrets, passwords, API keys, or private tokens in `VITE_*` variables.

### Verification

Run:

```powershell
npm run test:mode
npm run lint
npm run build
```

and:

```powershell
python -m pytest -q
```

The complete repository should preserve the existing simulation, telemetry, persistence, task allocation, A* planning, conflict handling, fault injection, recovery, network simulation, metrics, experiments, RBAC, JWT, and WebSocket behavior.
