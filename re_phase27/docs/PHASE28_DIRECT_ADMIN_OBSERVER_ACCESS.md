# Phase 28 — Direct Admin / Observer Access

## Scope

Replaced the previous multi-role/login entry flow for the demo package with a single direct-access selector containing only **Admin** and **Observer**.

## Public routes

- `/` — the single white/blue ResilientEdge landing page.
- `/access` — direct Admin / Observer access selection. No username, email, password, or login form is shown.
- `/app` and `/app/*` — the existing ResilientEdge application.

## Access behavior

1. Landing page `Access System`, `Launch Application`, and final application CTAs navigate to `/access`.
2. `/access` verifies frontend/backend demo-mode configuration.
3. Selecting **Admin** or **Observer** stores the existing demo role through `apiService.setDemoRole()`.
4. The user is sent directly to `/app`.
5. Existing backend `X-Demo-Role` and WebSocket `demo_role` enforcement remains active.
6. Admin keeps the existing ADMIN permissions.
7. Observer remains read-only through the existing permission model.

## Removed from the user flow

- Operator selection
- Viewer selection
- Email/password login page
- Public landing page nested inside another landing page

The backend JWT authentication implementation remains in the repository for authenticated deployments, but it is not exposed by the current demo UI.

## Demo configuration

The packaged `.env` enables:

```env
DEMO_MODE=true
VITE_DEMO_MODE=true
```

For a production deployment, replace the demo flow with authenticated access and use a production-grade JWT secret.
