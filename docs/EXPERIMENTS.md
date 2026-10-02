# ResilientEdge Phase 3 — Scientific Experiments

## Purpose

Phase 3 provides reproducible simulation experiments for comparing the existing ResilientEdge configuration with a deliberately resilience-disabled baseline. It does not alter the authoritative Python simulation model or fabricate measurements.

## Architecture

`CLI/UI -> experiment runner -> SimulationEngine -> MetricsCollector -> PersistenceRepository`

The runner reads scenario and algorithm configuration from `experiments/scenarios/*.yaml` and `experiments/configs/*.yaml`. The runner never talks directly to legacy cloud provider; persistence goes through the existing Phase 1 repository abstraction.

## Scenarios

- S01 normal baseline
- S02 single robot failure
- S03 multiple robot failure
- S04 communication latency
- S05 packet loss
- S06 network partition
- S07 task overload
- S08 path conflict
- S09 deadlock
- S10 failure during active task
- S11 failure during network degradation
- S12 combined multi-fault

Each scenario stores its version, robot/task counts, duration, fault schedule and network schedule.

## Baseline definition

`baseline.yaml` disables dynamic reassignment, deadlock recovery, network resynchronization and active resilience recovery while retaining the same simulation engine, task set, planner and random seed. `resilient.yaml` enables the existing resilience mechanisms.

For paired comparisons, the same seed sequence, scenario and initial configuration are used for both configurations. The algorithms are the experimental variable.

## Seeds and reproducibility

Every run stores its seed. Repeating a run with the same scenario, configuration and seed produces the same simulation-state metrics. Wall-clock measurements such as Python planning latency are intentionally excluded from deterministic-state checks because they depend on the host machine.

## Metrics

Primary metrics include task completion rate, makespan, mean task completion time, failure detection time, reassignment time, planning latency, conflicts, deadlocks, collisions, robot availability, task failure rate, network latency and packet loss. Secondary measurements include route length, idle/waiting time, throughput, energy model consumption and reassignments.

Energy is a simulated battery/energy model, not a physical measurement.

## Statistics

For completed runs the runner reports mean, median, minimum, maximum, standard deviation and sample count. Percentiles p50/p90/p95/p99 are reported when `n >= 5`; a 95% t-based confidence interval is reported when `n > 1`.

Paired effect size is Cohen's `d_z`. Significance testing is intentionally not reported for small samples. For `n >= 30`, a paired-t statistic with a normal-tail approximation is reported. This avoids presenting an unjustified p-value for the small validation suites.

A confidence interval or statistic is never reported as though failed runs were successful. Requested, completed and failed counts are retained.

## CLI

Windows PowerShell:

```powershell
python scripts/run_experiment.py --scenario S03 --config resilient --seed 12345 --runs 5 --output results/S03
python scripts/run_experiment.py --scenario S03 --compare --seed 12345 --runs 5
```

Supported options:

- `--scenario`
- `--config baseline|resilient`
- `--seed`
- `--runs`
- `--robots`
- `--tasks`
- `--duration`
- `--output`
- `--compare`

## Exports

A completed run produces:

- `experiment_summary.json`
- `experiment_runs.csv`
- `metrics.csv`

Generated result files are local artifacts and should not be committed as benchmark data unless intentionally curated.

## UI

The Experiments page supports scenario selection, baseline/resilient selection, repetitions, seed, robot/task overrides, execution and paired baseline comparison. Results show sample counts and numerical differences rather than an overall resilience score.

## Interpretation limits

These are software-simulation results. They do not establish physical robot performance, real network behavior, real battery consumption, or production-scale hardware scalability. Simulation scalability results are explicitly simulation scalability measurements.
