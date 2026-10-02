# Phase 18 — Experiment Engine

Phase 18 turns the S01-S12 scenario catalog into executable, reproducible experiments.

## Scenario contract

Every scenario YAML defines:

- `world`
- `robot_count`
- `tasks`
- `faults`
- `timing`
- `seed`
- `duration`
- `expected_behavior`

The runner validates this contract before execution.

## Catalog

S01 Normal / 3 robots
S02 Normal / 10 robots
S03 Normal / 20 robots
S04 Crossing conflict
S05 Blocked aisle
S06 Robot failure
S07 Low battery
S08 Packet loss
S09 Latency
S10 Network partition
S11 Dynamic obstacle
S12 Combined faults

## Execution

Run one scenario:

```powershell
python scripts/run_experiment.py --scenario S06 --seed 42
```

Run the complete catalog:

```powershell
python scripts/run_experiment.py --all --seed 42
```

Each run executes the authoritative `SimulationEngine`, captures actual telemetry-derived metrics, and records completed/failed status.

The seed is part of the experiment definition. Repeating a deterministic scenario with the same seed should produce identical simulation-state metrics.

## Gate

A Phase 18 build is complete only when all twelve scenarios execute successfully rather than merely existing as configuration files.
