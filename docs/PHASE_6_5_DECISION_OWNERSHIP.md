# Phase 6.5 — Robot Decision Ownership

## Objective
Remove remaining per-robot planning, conflict-resolution, and movement-transition decisions from `SimulationEngine` and delegate them to each robot's `RobotAgent`.

## Implemented
- `RobotAgent.plan_for_goal()` owns per-robot A* planning and intent publication.
- `RobotAgent.resolve_conflict()` owns deterministic local conflict response.
- `RobotAgent.execute_local_move()` owns the robot state transition after the simulation world safety gate approves movement.
- Engine peer knowledge is populated between the participating agents before local conflict resolution.
- Charging navigation also uses the owning agent planner.
- Normal task navigation uses the owning agent planner.
- Unsafe reservation outcomes transition through the agent waiting API.
- Added Phase 6.5 tests for planning delegation, local conflict ownership, movement delegation, and independent decision sequences.

## Verification
- `python -m compileall -q core tests` — PASS
- `python -m pytest -q` — 95 passed
- No remaining `self.planner.plan(...)` calls in `core/simulation/engine.py` for per-robot planning.

## Boundary
`SimulationEngine` still owns world orchestration, task allocation, persistence-facing state, experiment control, and global safety checks. Those are intentionally not moved into `RobotAgent` in this phase.

## Status
PASS for the Phase 6.5 decision-ownership gate. Phase 8 P2P communication remains the next major requirement.
