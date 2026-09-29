# Phase 10 — Reservation System

## Status
PASS

## Objective
Implement an authoritative resource/time reservation lifecycle for multi-robot motion:

```text
REQUEST → EVALUATE → GRANT / REJECT → ACTIVE → RELEASE
```

## Implementation
- Extended the reservation model with explicit lifecycle states: `REQUESTED`, `GRANTED`, `REJECTED`, `ACTIVE`, `RELEASED`, `EXPIRED`, and `CANCELLED`.
- Added deterministic reservation IDs for reproducible simulation and tests.
- Added non-mutating `evaluate_request()` decisions with conflict IDs and reason text.
- Added explicit `activate()`, `release()`, and `cancel()` lifecycle operations.
- Added automatic expiry classification instead of silently deleting active reservations.
- Preserved cell and directed-edge reservations, including reverse-edge swap protection.
- Preserved the existing `request_cell_reservation()` and `request_edge_reservation()` APIs used by the simulation engine.
- Preserved snapshot/restore compatibility and deterministic reservation-ID sequencing.
- Added authoritative decision-log inspection for integration and testing.

## Safety invariant
No two incompatible active reservations may overlap the same resource/time window. Reverse directed-edge reservations are also mutually exclusive during overlapping intervals.

## Verification
Phase 10 tests cover:
- request/grant/activate/release lifecycle;
- conflict evaluation and rejection decisions;
- non-overlapping reservations;
- reverse-edge swap rejection;
- expiry and resource reuse;
- robot-wide release;
- snapshot restore and deterministic reservation IDs.

## Gate
A conflict scenario produces an explicit reservation decision and the existing execution-layer safety gate prevents the conflicting movement from being applied.
