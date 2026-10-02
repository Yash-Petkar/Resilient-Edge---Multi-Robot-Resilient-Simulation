# Phase 14 Cleanup & Hardening Verification

## Scope

This pass only audits and hardens the existing Phase 14 implementation. It does not start Phase 15 and does not add ROS 2, Gazebo, Supabase, PostgreSQL, Redis, or a replacement persistence layer.

## Fixes

1. Removed the duplicate `messages_sent` metric assignment in `core/simulation/engine.py`.
2. Made persistent packet-loss and high-latency incidents edge-triggered. One active incident is retained while the condition persists and is marked `RESOLVED` when the condition clears.
3. Preserved partition edge-triggering.
4. Added `Robot.failed_at` so explicit FAILED transitions retain their simulation-time fault onset; snapshot/restore preserves it.
5. Failure detection now uses `failed_at` for explicit robot failures and heartbeat-timeout semantics for heartbeat failures.
6. Detection latency is clamped at zero and therefore cannot become negative.
7. Snapshot/restore rebinds active network incidents to the restored incident objects so persistence does not create duplicate incidents.
8. Added regression coverage for metric correctness, incident lifecycle, explicit FAILED timestamps, non-negative latency, and snapshot/restore.

## Verification

- `python -m compileall .` — PASS
- `python -m pytest -q` — PASS: 153 tests
- Phase 13 + Phase 14 cleanup tests — PASS
- Frontend dependency installation was attempted, but the environment timed out during `npm install`. Consequently `npm run lint` / `npm run build` could not be completed with a valid dependency tree. No frontend code was changed.

## Phase Status

Phase 14: CLEAN / PASS for the Python/core implementation.

Frontend build verification: NEEDS ATTENTION because dependencies could not be installed within the available execution window.

Phase 15: NOT STARTED.
