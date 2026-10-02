"""Backward-compatible Monte Carlo API backed by the Phase 3 runner."""
from typing import Any, Dict
from experiments.runner import run_experiment

def run_monte_carlo(scenario_id: str = "S06", num_runs: int = 10, start_seed: int = 100) -> Dict[str, Any]:
    result=run_experiment(scenario_id, "resilient", start_seed, num_runs, persist=True)
    # Preserve the Phase 1/2 response shape while exposing the richer Phase 3 schema.
    stats = {}
    for k,v in result.get("summary",{}).items():
        legacy = {"task_completion_rate":"completion_rate","average_waiting_time":"waiting_time","conflict_count":"conflicts","deadlock_count":"deadlocks"}.get(k,k)
        vv = dict(v)
        if "ci95_half_width" in vv:
            vv["ci_95"] = vv["ci95_half_width"]
        stats[legacy] = vv
    return {
        "scenario_id": scenario_id,
        "num_runs": num_runs,
        "runs": [{"run_index":r.get("run_index"),"seed":r.get("seed"),"completion_rate":r.get("metrics",{}).get("task_completion_rate"),"makespan":r.get("metrics",{}).get("makespan"),"waiting_time":r.get("metrics",{}).get("average_waiting_time"),"conflicts":r.get("metrics",{}).get("conflict_count"),"deadlocks":r.get("metrics",{}).get("deadlock_count")} for r in result.get("runs",[])],
        "statistics": {k:v for k,v in stats.items() if k in {"completion_rate","makespan","waiting_time","conflicts","deadlocks"}},
        "phase3_result": result,
    }
