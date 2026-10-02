# ResilientEdge Backend Deployment

The Vercel frontend can connect to this FastAPI service through `VITE_API_BASE_URL` and `VITE_WS_URL`.

## Production environment

Set:

- `HOST=0.0.0.0`
- `PORT=<platform supplied port>`
- `DATABASE_PATH=/data/resilientedge.db` when using a persistent mounted volume
- `JWT_SECRET=<strong random secret>`
- `DEMO_MODE=true` for the SIH/demo access flow, or `false` for password/JWT-only access
- `CORS_ORIGINS=https://resilient-edge-multi-robot-resilien.vercel.app`

## Render

`render.yaml` is included as a starting configuration. A persistent disk is required if SQLite data must survive service restarts/deploys.

## Docker

`Dockerfile.backend` runs only the FastAPI service and supports a platform-provided `PORT`.
