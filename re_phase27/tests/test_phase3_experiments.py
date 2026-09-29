import json
from pathlib import Path

from experiments.schema import build_definition, load_scenario_config
from experiments.runner import run_one, run_experiment, compare


def test_all_phase3_scenarios_have_formal_configs():
    for sid in [f"S{i:02d}" for i in range(1,13)]:
        cfg = load_scenario_config(sid)
        assert cfg["scenario_id"] == sid
        assert cfg["version"]
        assert cfg["duration"] > 0
        assert isinstance(cfg["fault_schedule"], list)
        assert isinstance(cfg["network_schedule"], list)


def test_same_seed_reproduces_state_metrics():
    definition = build_definition("S03", "resilient", 12345)
    a = run_one(definition, persist=False)
    b = run_one(definition, persist=False)
    ignored = {"planning_latency_ms", "planning_latency_p95_ms"}
    assert {k:v for k,v in a["metrics"].items() if k not in ignored} == {k:v for k,v in b["metrics"].items() if k not in ignored}


def test_phase3_runner_exports_actual_runs(tmp_path):
    result = run_experiment("S01", "resilient", seed=7, runs=2, output=str(tmp_path), persist=False)
    assert result["requested_runs"] == 2
    assert result["completed_runs"] == 2
    assert result["failed_runs"] == 0
    assert (tmp_path / "experiment_summary.json").exists()
    assert (tmp_path / "experiment_runs.csv").exists()
    assert (tmp_path / "metrics.csv").exists()
    data=json.loads((tmp_path/"experiment_summary.json").read_text())
    assert len(data["runs"]) == 2


def test_baseline_and_resilient_use_same_seed_sequence():
    result = compare("S02", seed=10, runs=2)
    assert result["requested_runs"] == 2
    assert [r["seed"] for r in result["baseline"]["runs"]] == [10,11]
    assert [r["seed"] for r in result["resilient"]["runs"]] == [10,11]
    assert result["comparisons"]["task_completion_rate"]["baseline"]["sample_count"] == 2
    assert result["comparisons"]["task_completion_rate"]["resilient"]["sample_count"] == 2

def test_failed_run_is_retained_as_failed():
    from dataclasses import replace
    d = build_definition("S01", "resilient", 99)
    bad = replace(d, fault_schedule=[{"type":"NOT_A_REAL_FAULT","target":"R1","start_time":0,"duration":1}])
    r = run_one(bad, persist=False)
    assert r["status"] == "FAILED"
    assert r["error_type"] in {"ValueError", "KeyError"}
