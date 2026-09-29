from experiments.schema import load_scenario_config, validate_all_scenarios
from experiments.runner import execute_scenario, execute_all_scenarios


def test_phase18_all_scenarios_have_required_executable_schema():
    errors = validate_all_scenarios()
    assert errors == {}


def test_phase18_every_catalog_scenario_executes():
    result = execute_all_scenarios(seed=42, persist=False)
    assert result["requested_scenarios"] == 12
    assert result["completed_scenarios"] == 12
    assert result["failed_scenarios"] == 0
    assert all(v["status"] == "COMPLETED" for v in result["scenarios"].values())


def test_phase18_scenario_execution_is_seed_reproducible():
    a = execute_scenario("S08", seed=123, persist=False)
    b = execute_scenario("S08", seed=123, persist=False)
    assert a["status"] == b["status"] == "COMPLETED"
    ignored = {"planning_latency_ms", "planning_latency_p95_ms"}
    assert {k: v for k, v in a["metrics"].items() if k not in ignored} == {k: v for k, v in b["metrics"].items() if k not in ignored}


def test_phase18_scenario_metadata_is_preserved():
    data = load_scenario_config("S12")
    assert data["world"]["map_id"] == "warehouse_default"
    assert data["robot_count"] == 3
    assert data["tasks"]["count"] == 6
    assert data["seed"] == 42
    assert data["duration"] == 60
    assert len(data["faults"]) == 3
    assert "expected_behavior" in data
