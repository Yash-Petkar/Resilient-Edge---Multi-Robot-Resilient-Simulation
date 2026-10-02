# Phase 12 — Fault Injection Engine

## Objective

Faults are authoritative simulation inputs. They must change the actual robot,
environment, coordination, and network behavior rather than merely appearing
in telemetry.

## Supported faults

### Robot
- `ROBOT_FAILURE`
- `LOW_BATTERY`

### Environment
- `BLOCKED_AISLE`
- `DYNAMIC_OBSTACLE`

### Network
- `PACKET_LOSS`
- `LATENCY`
- `JITTER`
- `MESSAGE_DUPLICATION`
- `MESSAGE_REORDERING`
- `NETWORK_PARTITION`

## Lifecycle

```text
PENDING -> ACTIVE -> RESOLVED
             |
             -> CLEARED
```

`inject_fault()` activates immediately for operator/API injection. `schedule_fault()`
creates a future fault and the simulation clock activates it when `start_time` is
reached.

## Real effects

- Robot failure sets the robot to `FAILED`, prevents participation in the
  movement/P2P loop, and releases its active reservations.
- Low battery drives the battery value down and enters the existing low-battery
  recovery/charging path.
- Blocked aisles and dynamic obstacles modify the authoritative world obstacle
  layer consumed by planning.
- Network faults configure the real `NetworkSimulator` used by P2P communication.
- Network partitions drive the resilience state machine into `LOCAL_AUTONOMY`.

## Determinism

Fault IDs are generated from a monotonic counter (`flt_000001`, ...), not UUIDs.
Multiple simultaneous network faults are combined deterministically by using the
maximum active value for loss, latency, jitter, duplication and reordering.

## Persistence

Fault state includes active and pending faults, history, and the next ID counter.
Snapshots restore fault IDs and lifecycle state without silently converting
pending faults into active faults.

## Gate

A fault scenario must produce an observable change in the actual simulation
state/behavior. A telemetry-only `FAULT: ...` message is not sufficient.
