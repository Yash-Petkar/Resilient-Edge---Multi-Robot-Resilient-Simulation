# Phase 11 — Deadlock Detection and Recovery

## Status
PASS

## Objective
Detect cyclic waiting between autonomous mobile robots and deterministically
break the cycle without allowing a conflicting movement to execute.

## Implementation

### Wait-for graph
The `DeadlockDetector` maintains a directed wait-for graph:

```text
R1 -> R2
R2 -> R3
R3 -> R1
```

An edge means the waiting robot depends on the blocking robot releasing a
resource or changing its trajectory.

The graph accepts multiple blockers per robot and normalizes traversal order,
so cycle detection is deterministic.

### Dependencies
Phase 11 builds dependencies from both:

- physical occupancy;
- active/granted spatial-temporal reservations;
- reverse directed-edge conflicts.

This prevents deadlock detection from depending only on the current physical
position of another robot.

### Recovery
The deterministic recovery policy is:

1. detect a cycle;
2. select the lowest task-priority robot as the victim;
3. use robot ID as the deterministic tie-breaker;
4. release all reservations owned by the victim;
5. clear its path;
6. enter `WAITING`;
7. apply a deterministic backoff of `max(2 * dt, 0.5s)`;
8. replan after the backoff window.

The public detector action remains `BACKOFF_AND_REPLAN` for compatibility with
the previous API; the simulation execution additionally releases reservations.

## Telemetry

The simulation telemetry now exposes:

```text
deadlock.wait_for_graph
deadlock.cycles
deadlock.backoff_until
```

These values are derived from the live simulation state.

## Snapshot compatibility

Phase 11 persists:

- deadlock backoff windows;
- wait-for graph;
- detected cycles.

Older snapshots without these fields remain valid.

## Verification

Phase 11 tests cover:

- three-robot cyclic wait detection;
- multiple blockers;
- reservation-derived blocking dependencies;
- deterministic victim selection;
- complete three-robot deadlock recovery.

Acceptance scenario:

```text
deadlock detected
      ↓
victim selected
      ↓
victim reservations released
      ↓
victim backs off
      ↓
path cleared
      ↓
replanning allowed
      ↓
cycle removed
```

No physical movement is applied while the victim is in recovery.
