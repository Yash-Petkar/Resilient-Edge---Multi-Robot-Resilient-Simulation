# ResilientEdge Phase 15 — Recovery Manager

Phase 15 turns failure detection and resilience state into an executable recovery workflow.

## Robot failure workflow

```text
failure
  -> detect
  -> mark robot failed
  -> release reservations
  -> release unfinished task
  -> find candidate robots
  -> select replacement
  -> replan / validate path
  -> execute
  -> complete
```

The existing `SimulationEngine.reassign_task()` remains the authoritative candidate-evaluation and handoff path. The RecoveryManager remains responsible for failure cleanup and network reconciliation; no second allocator or reservation system is introduced.

## Network recovery workflow

```text
partition
  -> local autonomy
  -> network restoration
  -> state reconciliation
  -> P2P message synchronization
  -> normal conflict detection/resolution
  -> RESYNC
  -> NORMAL
```

The network simulator and P2P adapter remain the transport boundary. Recovery does not directly share robot state between agents.

## Recovery metrics

The simulation records:

- `recovery_detection_time`
- `recovery_reassignment_time`
- `recovery_replanning_time`
- `recovery_time`

These are derived from simulation timestamps. They are not hard-coded.

## Determinism

Replacement selection remains deterministic: feasible path length, distance, battery reserve, and robot ID are used as stable tie-breakers.

## Persistence

Recovery context is included in simulation snapshots so a paused/restored recovery cannot silently lose its timing state.
