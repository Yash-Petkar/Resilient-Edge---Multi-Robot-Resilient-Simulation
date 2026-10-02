# Phase 13 — Failure Detection

## Objective

Detect failures from observable system behavior rather than directly reading the
fault-injection registry.

## Robot failure detection

The `FailureDetector` observes:

- robot heartbeat timestamps
- robot health/state
- battery state

Heartbeat timeout uses:

```text
fault_time = last_heartbeat + heartbeat_timeout
detection_time = current simulation time
detection_latency = detection_time - fault_time
```

Robot heartbeat detection runs before the current tick's P2P heartbeat publication,
preventing the detector from refreshing the evidence it is supposed to evaluate.

## Network failure detection

The detector observes the live `NetworkSimulator`:

- message delivery/drop counters
- measured latency
- partition state

It detects:

- `PACKET_LOSS_DETECTED`
- `HIGH_NETWORK_LATENCY`
- `NETWORK_PARTITION_DETECTED`

No `FaultEngine` state is read by the detector.

## Detection record

Every detected condition records:

```text
fault_time
detection_time
detection_latency
entity
fault
```

The timing fields are also attached to incident objects and serialized with
incident telemetry.

## Persistence

Failure-detector state is included in simulation snapshots:

- detected robot failures
- detection records
- network counters
- partition observation state
- network condition onset timestamps

Restoring a snapshot therefore does not silently lose detection history.

## Gate

Phase 13 is accepted when:

1. a robot heartbeat timeout creates a detection incident;
2. a robot failure is detected through observable robot state;
3. packet loss is detected from observed transport drops;
4. high latency is detected from observed latency;
5. a network partition is detected from transport state;
6. detection timing is recorded;
7. detector state survives snapshot/restore;
8. the complete regression suite remains green.

## Validation

```text
Full regression suite: 141 passed
Python compilation:    PASS
Phase 13 tests:        5 passed
```
