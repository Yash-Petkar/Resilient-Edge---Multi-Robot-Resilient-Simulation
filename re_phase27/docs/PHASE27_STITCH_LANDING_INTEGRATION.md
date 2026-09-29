# Phase 27 — Stitch Landing Page Integration

## Scope

Integrated the supplied Stitch landing-page design into the existing React/Vite ResilientEdge frontend without replacing the authenticated application.

## Routes

- `/` — public Stitch-inspired ResilientEdge landing page.
- `/app` — existing ResilientEdge application entry point.
- `/app/*` — existing application views with the existing client-side route mapping.
- Legacy application paths such as `/dashboard`, `/robots`, `/tasks`, etc. remain recognized by the existing application for compatibility.

## Preserved systems

No FastAPI, SQLite, Python simulation engine, WebSocket, authentication, JWT, RBAC, telemetry, task allocation, A*, conflict handling, fault injection, recovery, network simulation, metrics, or experiment implementation was replaced.

## Landing implementation

Landing components are under `src/components/landing/` and are isolated in `src/styles/landing.css`.

The landing page uses the existing `lucide-react` dependency and the existing Tailwind/Vite setup; no second CSS framework was added.

## Assets

The supplied Stitch package contained `code.html` and `screen.png`, while its HTML referenced externally hosted Google image URLs. Those external image URLs were not carried into the application. The supplied screenshot is retained locally as `public/assets/landing/stitch-reference.png` for design provenance/reference. Visual image-dependent areas were recreated with local React/CSS/SVG primitives so the public landing page does not depend on temporary external Stitch image URLs.

## Demo data boundary

Landing metrics, simulation previews, telemetry charts, task allocation examples, recovery logs, and network values are explicitly illustrative. They do not call the ResilientEdge backend or WebSocket and cannot mutate the live simulation.

## Validation

- TypeScript/TSX syntax transpilation: passed for all source TS/TSX files.
- Relative local import validation: passed.
- External Stitch image URL scan: no Google Stitch image URLs remain in application source.
- `npm run build`: not executable in the isolated build environment because dependencies were not installed and the environment could not retrieve the npm registry packages. `npm ci --offline` confirmed required package tarballs were not cached; an online `npm install` attempt timed out.


## Phase 28 follow-up

The landing-page CTA flow was subsequently changed to `/access`, with direct Admin/Observer selection and no login page in the demo UI. See `PHASE28_DIRECT_ADMIN_OBSERVER_ACCESS.md`.
