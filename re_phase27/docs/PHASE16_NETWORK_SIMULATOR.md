# ResilientEdge Phase 16 — Network Simulator

Phase 16 makes the existing P2P transport an authoritative simulated message
transport rather than a direct state-sharing path.

## Transport pipeline

```text
RobotAgent
  -> CommunicationAdapter
  -> NetworkSimulator
  -> in-flight delivery queue
  -> CommunicationAdapter
  -> receiving RobotAgent
```

## Supported conditions

- configurable packet loss probability
- configurable latency
- seeded jitter
- seeded message duplication
- seeded message reordering
- explicit robot-group network partitions

Messages that are lost or blocked by a partition never enter the delivery
queue. Delayed messages remain in-flight until simulation time reaches their
delivery timestamp.

## Determinism

A seeded `random.Random` instance controls all stochastic transport effects.
Message IDs are deterministic (`msg_00000001`, ...), and same-time delivery
uses message ID as a stable tie-breaker.

## Persistence

The following transport state is snapshot-compatible:

- counters
- transport configuration
- random generator state
- next message ID
- in-flight messages
- message delivery timestamps
- partition groups
- latency samples

Restoring a snapshot therefore does not silently discard pending messages.

## Phase 15 boundary

The RecoveryManager remains responsible for failure recovery, task
reassignment, and network reconciliation. Phase 16 only controls how P2P
messages are transported. It does not directly modify peer state.

## Verification

The Phase 16 suite covers:

1. actual delayed delivery
2. partition isolation
3. duplicate delivery
4. deterministic reordering
5. in-flight snapshot/restore
6. adapter transport boundary
7. simulation reset of transport state

Full regression: 163 passed.
