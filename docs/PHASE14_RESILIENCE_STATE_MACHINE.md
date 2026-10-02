# Phase 14 — Resilience State Machine

## Objective

Provide one authoritative, deterministic global resilience state machine:

```text
NORMAL
  -> DEGRADED
  -> LOCAL_AUTONOMY
  -> RECOVERY
  -> RESYNC
  -> NORMAL

FAILED is available for unrecoverable global service loss and can re-enter
RECOVERY when recovery begins.
```

## Transition audit

Every state transition records:

```text
timestamp
entity
old_state
new_state
reason
```

No-op transitions are ignored and invalid transitions are rejected. Recovery
code may explicitly use `force=True` only when a safety-critical transition is
known to be valid outside the normal transition graph.

## Persistence

The state machine snapshot contains:

- current state
- accumulated state durations
- recent transition events
- last transition timestamp

Restore reconstructs the same state and transition history.

## Integration

Phase 13 detection and the simulation engine continue to drive the machine for
network degradation, network partition, recovery, and resynchronization. The
state machine is the authoritative source for the global resilience state.

## Gate

Phase 14 passes when:

1. the required states exist;
2. the normal degradation/autonomy/resync path works;
3. transition events contain all five audit fields;
4. invalid transitions are rejected;
5. FAILED and recovery are represented;
6. snapshot/restore preserves the state machine;
7. the complete regression suite remains green.
