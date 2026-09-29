# Phase 22 — WebSocket Telemetry

## Objective
Provide persistent real-time telemetry from the authoritative Python simulation to connected clients.

## Contract
`/ws/telemetry?access_token=<access-token>`

After authentication, the server sends the newest authoritative snapshot immediately and then streams subsequent simulation snapshots.

Each telemetry snapshot preserves the existing authoritative fields and adds:
- `message_type: "TELEMETRY"`
- monotonically increasing `sequence`
- `server_timestamp`

Expected state fields include `timestamp`, `robots`, `tasks`, `incidents`, `faults`, `metrics`, `simulation`, and `resilience`.

## Reliability
- The simulation continues when no clients are connected.
- Each client has a bounded queue.
- Slow clients do not block the simulation or other clients; stale queued snapshots may be dropped in favor of the newest state.
- Reconnecting clients immediately receive the latest cached snapshot.
- `PING` receives a `PONG`.
- Disconnects remove the client and cancel its sender task.

## Acceptance criteria
1. Authenticated client connects.
2. Initial authoritative snapshot is received.
3. Subsequent simulation ticks produce telemetry messages.
4. Sequence numbers increase monotonically.
5. Reconnection receives the current snapshot.
6. Slow clients cannot stall the simulation loop.
7. WebSocket disconnects are cleaned up.
