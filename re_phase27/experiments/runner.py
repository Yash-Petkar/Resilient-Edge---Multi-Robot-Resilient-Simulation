"""Reproducible Phase 3 experiment runner, aggregation and export."""
from __future__ import annotations
import csv, json, math, statistics, time, uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from core.simulation.engine import SimulationEngine
from core.models.fault import FaultType
from backend.database.factory import persistence
from experiments.schema import ExperimentDefinition, build_definition, load_scenario_config, load_algorithm_config, validate_scenario_config, validate_all_scenarios

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


def _base_setup(sim: SimulationEngine, scenario_id: str, robots: int, tasks: int) -> None:
    """Build the authoritative world/task setup for the Phase 18 scenario catalog."""
    if scenario_id == "S04":
        sim.add_robot("R1", (2, 8)); sim.add_robot("R2", (21, 8))
        sim.add_task("T01", (2, 8), (21, 8), priority=3)
        sim.add_task("T02", (21, 8), (2, 8), priority=2)
        return
    sim.reset(robot_count=robots, task_count=tasks)
    # Phase 18 catalog runs explicitly mark active-failure scenarios so the
    # injected failure exercises real recovery without changing legacy baseline
    # experiment semantics.
    if cfg := getattr(sim, "_phase18_catalog", False):
        if scenario_id in {"S06", "S12"} and "R2" in sim.robots and "T01" in sim.tasks:
            sim.assign_task("T01", "R2")


def _apply_schedule(sim: SimulationEngine, schedule: Iterable[Dict[str, Any]]) -> None:
    for event in schedule:
        sim.fault_engine.inject_fault(
            fault_type=FaultType(str(event["type"])),
            target=str(event.get("target", "network")),
            start_time=float(event.get("start_time", 0.0)),
            duration=float(event.get("duration", 30.0)),
            parameters=dict(event.get("parameters") or {}),
        )


def build_simulation(defn: ExperimentDefinition) -> SimulationEngine:
    cfg = defn.configuration
    sim = SimulationEngine(
        seed=defn.seed,
        time_step=float(cfg.get("time_step", 0.1)),
        resilience_enabled=bool(cfg.get("resilience_enabled", True)),
        dynamic_reassignment=bool(cfg.get("dynamic_reassignment", True)),
        deadlock_recovery=bool(cfg.get("deadlock_recovery", True)),
        network_resync=bool(cfg.get("network_resync", True)),
        coordination_mode=str(cfg.get("coordination_mode", "resilient")),
    )
    sim._phase18_catalog = bool(defn.configuration.get("phase18_catalog", False))
    _base_setup(sim, defn.scenario_id, defn.robot_count, defn.task_count)
    _apply_schedule(sim, defn.fault_schedule)
    _apply_schedule(sim, defn.network_schedule)
    return sim


def run_one(defn: ExperimentDefinition, run_index: int = 1, persist: bool = True) -> Dict[str, Any]:
    # UUID5 keeps the identifier deterministic
    # for the same experiment definition and run index without relying on mutable state.
    run_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"resilientedge:{defn.experiment_id}:run:{run_index}"))
    run_key = f"{defn.experiment_id}-RUN-{run_index:04d}"
    started_wall = time.perf_counter()
    start_epoch = time.time()
    try:
        sim = build_simulation(defn)
        steps = 0
        max_steps = max(1, math.ceil(defn.simulation_duration / sim.clock.time_step))
        while steps < max_steps and sim.clock.current_time < defn.simulation_duration:
            sim.step()
            steps += 1
            if sim.tasks and all(t.status.value == "COMPLETED" for t in sim.tasks.values()):
                break
        telemetry = sim.get_telemetry()
        metrics = dict(telemetry["metrics"])
        result = {
            "run_id": run_id,
            "run_key": run_key,
            "experiment_id": defn.experiment_id,
            "scenario_id": defn.scenario_id,
            "status": "COMPLETED",
            "seed": defn.seed,
            "run_index": run_index,
            "requested_duration": defn.simulation_duration,
            "duration": telemetry["clock"]["current_time"],
            "steps": steps,
            "runtime_seconds": round(time.perf_counter() - started_wall, 6),
            "started_at": start_epoch,
            "configuration": defn.to_dict(),
            "metrics": metrics,
            "incidents_count": len(sim.incidents),
            "mode": defn.configuration.get("algorithm", "resilient"),
            "robot_count": defn.robot_count,
            "task_count": defn.task_count,
            "map_id": defn.scenario_id,
            "start_state": {r.robot_id: list(r.home_position or r.position) for r in sim.robots.values()},
            "tasks_completed": metrics.get("completed_tasks", 0),
            "tasks_failed": int(metrics.get("task_failure_rate", 0.0) * defn.task_count / 100.0),
            "collision_count": metrics.get("collision_count", 0),
            "conflict_count": metrics.get("conflict_count", 0),
            "deadlock_count": metrics.get("deadlock_count", 0),
            "average_wait_time": metrics.get("average_waiting_time", 0.0),
            "total_distance": metrics.get("total_distance", 0.0),
            "reroute_count": metrics.get("reroute_count", 0),
            "completion_time": metrics.get("makespan", telemetry["clock"]["current_time"]),
            "recovery_time": metrics.get("task_reassignment_time", 0.0),
            "utilization": metrics.get("robot_availability", 0.0),
        }
        if persist:
            persistence.create_experiment_run({"run_id": run_id, "experiment_id": defn.experiment_id, "scenario_id": defn.scenario_id, "status": "COMPLETED", "duration": result["duration"], "metrics": result, "configuration": defn.to_dict(), "mode": defn.configuration.get("algorithm", "resilient"), "scenario_version": defn.scenario_version, "algorithm_version": defn.algorithm_version, "configuration_version": defn.configuration_version, "start_time": start_epoch, "end_time": time.time()})
            persistence.store_metrics({"run_id": run_id, "timestamp": telemetry["clock"]["current_time"], **metrics})
        return result
    except Exception as exc:
        result = {
            "run_id": run_id, "experiment_id": defn.experiment_id, "scenario_id": defn.scenario_id,
            "status": "FAILED", "seed": defn.seed, "run_index": run_index,
            "error_type": type(exc).__name__, "error": str(exc), "runtime_seconds": round(time.perf_counter() - started_wall, 6),
            "configuration": defn.to_dict(), "metrics": {},
        }
        if persist:
            persistence.create_experiment_run({"run_id": run_id, "experiment_id": defn.experiment_id, "scenario_id": defn.scenario_id, "status": "FAILED", "duration": 0, "metrics": result, "configuration": defn.to_dict(), "mode": defn.configuration.get("algorithm", "resilient"), "scenario_version": defn.scenario_version, "algorithm_version": defn.algorithm_version, "configuration_version": defn.configuration_version, "start_time": start_epoch, "end_time": time.time(), "error_type": result.get("error_type"), "error": result.get("error")})
        return result


def _metric_values(runs: List[Dict[str, Any]], key: str) -> List[float]:
    return [float(r["metrics"][key]) for r in runs if r.get("status") == "COMPLETED" and key in r.get("metrics", {})]


def _t_critical_95(n: int) -> float:
    table = {2:12.706,3:4.303,4:3.182,5:2.776,6:2.571,7:2.447,8:2.365,9:2.306,10:2.262,11:2.228,12:2.201,13:2.179,14:2.160,15:2.145,16:2.131,17:2.120,18:2.110,19:2.101,20:2.093,21:2.086,22:2.080,23:2.074,24:2.069,25:2.064,26:2.060,27:2.056,28:2.052,29:2.048,30:2.045}
    return table.get(n, 1.96)


def summarize(values: List[float]) -> Dict[str, Any]:
    n = len(values)
    if not n:
        return {"sample_count": 0}
    vals = sorted(values)
    mean = statistics.fmean(vals)
    out = {
        "sample_count": n, "mean": mean, "median": statistics.median(vals),
        "minimum": min(vals), "maximum": max(vals),
        "std_dev": statistics.stdev(vals) if n > 1 else 0.0,
    }
    if n > 1:
        se = out["std_dev"] / math.sqrt(n)
        out["ci95_half_width"] = _t_critical_95(n) * se
        out["ci95_low"] = mean - out["ci95_half_width"]
        out["ci95_high"] = mean + out["ci95_half_width"]
        if n >= 5:
            for q, name in ((0.50,"p50"),(0.90,"p90"),(0.95,"p95"),(0.99,"p99")):
                pos=(n-1)*q; lo=math.floor(pos); hi=math.ceil(pos)
                out[name]=vals[lo] if lo==hi else vals[lo]+(vals[hi]-vals[lo])*(pos-lo)
    return {k: round(v, 6) if isinstance(v, float) else v for k,v in out.items()}


def paired_effect(baseline: List[float], resilient: List[float]) -> Dict[str, Any]:
    pairs = [(a,b) for a,b in zip(baseline,resilient) if math.isfinite(a) and math.isfinite(b)]
    diffs=[b-a for a,b in pairs]
    n=len(diffs)
    if n < 2: return {"sample_count": n, "method": "paired", "effect_size": None, "p_value": None}
    mean=statistics.fmean(diffs); sd=statistics.stdev(diffs)
    # Zero variance is a valid degenerate paired sample, but infinity/NaN are
    # not JSON-safe API values. Represent the undefined standardized effect
    # explicitly instead of leaking non-finite floats into FastAPI responses.
    zero_variance = sd == 0.0
    t = None if zero_variance else mean/(sd/math.sqrt(n))
    d = None if zero_variance else mean/sd
    result={
        "sample_count": n,
        "method": "paired_t",
        "mean_difference": round(mean,6),
        "effect_size_cohens_dz": round(d,6) if d is not None else None,
    }
    if n >= 30 and t is not None:
        p=math.erfc(abs(t)/math.sqrt(2.0))
        result.update({"test":"paired t; normal-tail approximation for n>=30","t_statistic":round(t,6),"p_value":round(p,8)})
    else:
        reason = "zero variance; standardized effect is undefined" if zero_variance else "sample size < 30; significance test omitted rather than using an unjustified normal approximation"
        result.update({"test":"not computed","t_statistic":None,"p_value":None,"reason":reason})
    return result


def aggregate_runs(runs: List[Dict[str, Any]], metric_keys: Optional[List[str]] = None) -> Dict[str, Any]:
    keys = metric_keys or sorted({k for r in runs for k in r.get("metrics", {})})
    return {key: summarize(_metric_values(runs, key)) for key in keys}


def execute_scenario(scenario_id: str, seed: Optional[int] = None, persist: bool = False) -> Dict[str, Any]:
    """Execute one catalog scenario end-to-end from its YAML definition."""
    scenario = load_scenario_config(scenario_id)
    issues = validate_scenario_config(scenario)
    if issues:
        raise ValueError(f"Invalid {scenario_id}: " + "; ".join(issues))
    actual_seed = int(scenario.get("seed", 42) if seed is None else seed)
    config_name = "resilient"
    defn = build_definition(
        scenario_id, config_name, actual_seed,
        robots=int(scenario["robot_count"]),
        tasks=int(scenario["tasks"]["count"]),
        duration=float(scenario["duration"]),
        experiment_id=f"EXP-{scenario_id}-SEED-{actual_seed}",
    )
    defn.configuration["phase18_catalog"] = True
    return run_one(defn, run_index=1, persist=persist)


def execute_all_scenarios(seed: Optional[int] = None, persist: bool = False) -> Dict[str, Any]:
    """Execute S01-S12 and retain pass/fail evidence for every scenario."""
    schema_errors = validate_all_scenarios()
    if schema_errors:
        return {"status": "FAILED", "schema_errors": schema_errors, "scenarios": {}}
    results = {}
    for sid in [f"S{i:02d}" for i in range(1, 13)]:
        try:
            results[sid] = execute_scenario(sid, seed=seed, persist=persist)
        except Exception as exc:
            results[sid] = {"status": "FAILED", "error_type": type(exc).__name__, "error": str(exc)}
    failed = [sid for sid, result in results.items() if result.get("status") != "COMPLETED"]
    return {
        "status": "COMPLETED" if not failed else "PARTIAL",
        "requested_scenarios": 12,
        "completed_scenarios": 12 - len(failed),
        "failed_scenarios": len(failed),
        "scenarios": results,
    }


def run_experiment(scenario: str, config: str = "resilient", seed: int = 42, runs: int = 1,
                   robots: Optional[int] = None, tasks: Optional[int] = None, duration: Optional[float] = None,
                   output: Optional[str] = None, persist: bool = True) -> Dict[str, Any]:
    if runs < 1: raise ValueError("runs must be >= 1")
    defn = build_definition(scenario, config, seed, robots, tasks, duration,
                            experiment_id=f"EXP-{scenario}-{config.upper()}-{seed}-{runs}")
    if persist:
        persistence.save_experiment({**defn.to_dict(), "status": "RUNNING", "metrics": {}})
    completed=[]; failed=[]
    for i in range(runs):
        run_def = ExperimentDefinition(**{**defn.to_dict(), "seed": seed+i, "experiment_id": defn.experiment_id})
        r=run_one(run_def, i+1, persist=persist)
        (completed if r["status"]=="COMPLETED" else failed).append(r)
    result={"experiment":defn.to_dict(),"requested_runs":runs,"completed_runs":len(completed),"failed_runs":len(failed),"runs":completed+failed,"summary":aggregate_runs(completed)}
    result["status"]="COMPLETED" if not failed else ("PARTIAL" if completed else "FAILED")
    if persist:
        persistence.save_experiment({**defn.to_dict(), "status": result["status"], "metrics": result["summary"], "end_time": time.time()})
    if output:
        export_results(result, Path(output))
    return result


def compare(scenario: str, seed: int = 42, runs: int = 5, **kwargs: Any) -> Dict[str, Any]:
    """Run equivalent simulation infrastructure for all benchmark modes."""
    modes = ("baseline", "centralized", "resilient")
    results = {mode: run_experiment(scenario, mode, seed, runs, persist=False, **kwargs) for mode in modes}
    comparisons: Dict[str, Any] = {}
    metric_keys = sorted(set(results["baseline"]["summary"]) & set(results["resilient"]["summary"]))
    for key in metric_keys:
        base_values = _metric_values(results["baseline"]["runs"], key)
        resilient_values = _metric_values(results["resilient"]["runs"], key)
        if not base_values or not resilient_values:
            continue
        baseline_mean = statistics.fmean(base_values)
        resilient_mean = statistics.fmean(resilient_values)
        comparisons[key] = {
            "baseline": summarize(base_values),
            "centralized": summarize(_metric_values(results["centralized"]["runs"], key)),
            "resilient": summarize(resilient_values),
            "absolute_difference": round(resilient_mean - baseline_mean, 6),
            "improvement_percent": round((baseline_mean - resilient_mean) / baseline_mean * 100.0, 6) if baseline_mean > 0 else None,
            "baseline_valid": baseline_mean > 0,
            "statistics": paired_effect(base_values, resilient_values),
        }
    return {"scenario": scenario, "seed": seed, "requested_runs": runs, **results, "comparisons": comparisons}


def export_results(result: Dict[str, Any], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output/"experiment_summary.json").write_text(json.dumps(result,indent=2,default=str),encoding="utf-8")
    rows=[]
    for r in result.get("runs",[]):
        row={"run_id":r.get("run_id"),"experiment_id":r.get("experiment_id"),"scenario_id":r.get("scenario_id"),"status":r.get("status"),"seed":r.get("seed"),"run_index":r.get("run_index"),"duration":r.get("duration"),"runtime_seconds":r.get("runtime_seconds")}
        row.update(r.get("metrics",{})); rows.append(row)
    if rows:
        fields=sorted({k for row in rows for k in row})
        with (output/"experiment_runs.csv").open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
        metric_rows=[]
        for row in rows:
            for k,v in row.items():
                if k not in {"run_id","experiment_id","scenario_id","status","seed","run_index"} and isinstance(v,(int,float)):
                    metric_rows.append({"run_id":row["run_id"],"seed":row["seed"],"metric":k,"value":v})
        with (output/"metrics.csv").open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=["run_id","seed","metric","value"]); w.writeheader(); w.writerows(metric_rows)
