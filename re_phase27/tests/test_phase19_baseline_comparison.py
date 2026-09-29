from experiments.baseline import (
    run_baseline_comparison,
    run_baseline_matrix,
)


def test_phase19_uses_identical_initial_conditions():
    result = run_baseline_comparison("S01", seed=42)
    assert result["common_initial_conditions"] is True
    assert len(set(result["initial_condition_fingerprints"])) == 1
    assert len(result["comparisons"]) == 3


def test_phase19_executes_all_three_real_systems():
    result = run_baseline_comparison("S06", seed=42)
    systems = [r["system"] for r in result["comparisons"]]
    assert systems == [
        "Baseline A (Stop/Wait)",
        "Baseline B (Centralized Lock)",
        "ResilientEdge (Proposed)",
    ]
    for run in result["comparisons"]:
        assert run["steps"] > 0
        assert "metrics" in run
        assert run["coordination_mode"] in {"stop_and_wait", "centralized", "resilient"}


def test_phase19_matrix_pairs_same_seed_and_reports_measurements():
    result = run_baseline_matrix("S01", seeds=[11, 12])
    assert result["common_initial_conditions"] is True
    assert all(len(v) == 3 for v in result["fingerprints_by_seed"].values())
    for metric in ("task_completion_rate", "makespan", "collision_count"):
        assert set(result["summaries"][metric]) == {"baseline", "centralized", "resilient"}
        assert result["summaries"][metric]["baseline"]["sample_count"] == 2
    assert result["measurement_only"] is True
