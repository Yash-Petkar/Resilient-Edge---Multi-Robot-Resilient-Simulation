"""Phase 19 baseline comparison: identical-condition, measurement-only benchmarking.

No synthetic multipliers or fabricated improvements are used. Each mode is executed
through the authoritative SimulationEngine with the same scenario, seed, robot/task
counts, duration, and fault schedules.
"""
from __future__ import annotations

import hashlib
import json
import math
import statistics
from typing import Any, Dict, List, Optional

from experiments.schema import build_definition, load_scenario_config
from experiments.runner import build_simulation


MODE_LABELS = {
    "baseline": "Baseline A (Stop/Wait)",
    "centralized": "Baseline B (Centralized Lock)",
    "resilient": "ResilientEdge (Proposed)",
}


def _initial_conditions(definition, sim) -> Dict[str, Any]:
    """Capture a comparable, deterministic initial-condition fingerprint."""
    payload = {
        "scenario_id": definition.scenario_id,
        "seed": definition.seed,
        "robot_count": definition.robot_count,
        "task_count": definition.task_count,
        "duration": definition.simulation_duration,
        "world": definition.world,
        "fault_schedule": definition.fault_schedule,
        "network_schedule": definition.network_schedule,
        "robots": sorted(
            ({"robot_id": r.robot_id, "position": list(r.position), "home": list(r.home_position or r.position)}
             for r in sim.robots.values()),
            key=lambda x: x["robot_id"],
        ),
        "tasks": sorted(
            ({"task_id": t.task_id, "pickup": list(t.pickup), "delivery": list(t.delivery), "priority": t.priority}
             for t in sim.tasks.values()),
            key=lambda x: x["task_id"],
        ),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    payload["fingerprint"] = hashlib.sha256(canonical.encode()).hexdigest()
    return payload


def _run_mode(scenario_id: str, config_name: str, seed: int = 42, run_index: int = 1) -> Dict[str, Any]:
    definition = build_definition(
        scenario_id, config_name, seed,
        experiment_id=f"PHASE19-{scenario_id}-{config_name.upper()}-{seed}-RUN-{run_index}",
    )
    sim = build_simulation(definition)
    conditions = _initial_conditions(definition, sim)
    steps = 0
    max_steps = max(1, math.ceil(definition.simulation_duration / sim.clock.time_step))
    while steps < max_steps and sim.clock.current_time < definition.simulation_duration:
        sim.step()
        steps += 1
        if sim.tasks and all(t.status.value == "COMPLETED" for t in sim.tasks.values()):
            break
    telemetry = sim.get_telemetry()
    metrics = dict(telemetry["metrics"])
    completed = int(metrics.get("completed_tasks", 0))
    total = len(sim.tasks)
    return {
        "system": MODE_LABELS[config_name],
        "architecture": config_name,
        "scenario_id": scenario_id,
        "seed": seed,
        "run_index": run_index,
        "robot_count": definition.robot_count,
        "task_count": definition.task_count,
        "duration_requested": definition.simulation_duration,
        "duration": telemetry["clock"]["current_time"],
        "steps": steps,
        "task_completion_rate": metrics.get("task_completion_rate", 0.0),
        "makespan": metrics.get("makespan", 0.0),
        "average_waiting_time": metrics.get("average_waiting_time", 0.0),
        "conflicts_detected": metrics.get("conflict_count", 0),
        "collision_count": metrics.get("collision_count", 0),
        "deadlocks_detected": metrics.get("deadlock_count", 0),
        "tasks_completed": completed,
        "tasks_failed": int(round(metrics.get("task_failure_rate", 0.0) * total / 100.0)),
        "resilience_recovery": config_name == "resilient",
        "resilience_recovery_enabled": bool(definition.configuration.get("resilience_enabled", False)),
        "dynamic_reassignment_enabled": bool(definition.configuration.get("dynamic_reassignment", False)),
        "deadlock_recovery_enabled": bool(definition.configuration.get("deadlock_recovery", False)),
        "network_resync_enabled": bool(definition.configuration.get("network_resync", False)),
        "coordination_mode": definition.configuration.get("coordination_mode"),
        "initial_conditions": conditions,
        "metrics": metrics,
    }


def run_baseline_a_stop_and_wait(scenario_id: str, seed: int = 42) -> Dict[str, Any]:
    return _run_mode(scenario_id, "baseline", seed)


def run_baseline_b_centralized_lock(scenario_id: str, seed: int = 42) -> Dict[str, Any]:
    return _run_mode(scenario_id, "centralized", seed)


def run_baseline_comparison(scenario_id: str = "S06", seed: int = 42) -> Dict[str, Any]:
    """Execute all three systems under identical initial conditions."""
    comparisons = [_run_mode(scenario_id, mode, seed) for mode in ("baseline", "centralized", "resilient")]
    fingerprints = {r["initial_conditions"]["fingerprint"] for r in comparisons}
    return {
        "scenario": scenario_id,
        "seed": seed,
        "common_initial_conditions": len(fingerprints) == 1,
        "initial_condition_fingerprints": [r["initial_conditions"]["fingerprint"] for r in comparisons],
        "comparisons": comparisons,
        "measurement_only": True,
        "note": "Results are measured from independent executions; no synthetic winner or multiplier is applied.",
    }


def _mean(values: List[float]) -> Optional[float]:
    return statistics.fmean(values) if values else None


def run_baseline_matrix(
    scenario_id: str,
    seeds: List[int],
) -> Dict[str, Any]:
    """Run a paired benchmark matrix across identical seeds."""
    if not seeds:
        raise ValueError("seeds must not be empty")
    runs = {mode: [_run_mode(scenario_id, mode, seed, i + 1) for i, seed in enumerate(seeds)]
            for mode in ("baseline", "centralized", "resilient")}
    fingerprints_by_seed = {
        seed: [runs[mode][i]["initial_conditions"]["fingerprint"] for mode in runs]
        for i, seed in enumerate(seeds)
    }
    common_conditions = all(len(set(v)) == 1 for v in fingerprints_by_seed.values())

    metric_keys = [
        "task_completion_rate", "makespan", "average_waiting_time",
        "conflicts_detected", "collision_count", "deadlocks_detected",
        "tasks_completed",
    ]
    summaries = {}
    for metric in metric_keys:
        summaries[metric] = {}
        for mode in runs:
            values = [float(r[metric]) for r in runs[mode]]
            summaries[metric][mode] = {
                "sample_count": len(values),
                "mean": round(_mean(values), 6),
                "minimum": min(values),
                "maximum": max(values),
            }
    return {
        "scenario": scenario_id,
        "seeds": list(seeds),
        "runs": runs,
        "common_initial_conditions": common_conditions,
        "fingerprints_by_seed": fingerprints_by_seed,
        "summaries": summaries,
        "measurement_only": True,
    }
