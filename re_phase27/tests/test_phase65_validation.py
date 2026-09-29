"""Phase 6.5 validation gates derived from the master engineering instruction."""
import copy
import json

from core.coordination.reservation_manager import ReservationManager
from core.interfaces.ros2_adapter import ROS2RobotAdapter
from core.simulation.engine import SimulationEngine
from core.models.robot import RobotState
from experiments.runner import compare, run_experiment


def _authoritative_snapshot(snapshot):
    data = copy.deepcopy(snapshot)
    data.pop("incidents", None)  # restore itself appends a diagnostic incident
    data.pop("random_state", None)  # compared state is validated separately
    return data


def test_snapshot_round_trip_restores_authoritative_state():
    sim = SimulationEngine(seed=42, time_step=0.1)
    sim.reset(robot_count=3, task_count=3)
    sim.step(force=True)
    sim.reservation_mgr.request_cell_reservation("R1", (9, 9), 2.0, 3.0, priority=3)
    sim.reservation_mgr.request_edge_reservation("R1", (9, 8), (9, 9), 2.0, 3.0, priority=3)
    snapshot = sim.save_snapshot()
    before = _authoritative_snapshot(snapshot)
    sim.robots["R1"].position = (20, 14)
    sim.tasks["T01"].priority = 99
    sim.reservation_mgr.release_all_for_robot("R1")
    sim.restore_snapshot(snapshot)
    after = _authoritative_snapshot(sim.save_snapshot())
    assert before == after
    assert any(r.resource_id == "edge:(9,8)->(9,9)" for r in sim.reservation_mgr.get_all_active())


def test_reservation_manager_prevents_vertex_and_edge_swap_conflicts():
    mgr = ReservationManager()
    assert mgr.request_cell_reservation("R1", (5, 6), 1, 2)
    assert mgr.request_cell_reservation("R2", (5, 6), 1.5, 2.5) is None
    assert mgr.request_edge_reservation("R1", (5, 5), (5, 6), 2, 3)
    assert mgr.request_edge_reservation("R2", (5, 6), (5, 5), 2.2, 2.8) is None


def test_execution_layer_refuses_unsafe_moves_without_counting_physical_collision():
    sim = SimulationEngine(seed=42, time_step=0.1)
    sim.reset(robot_count=2, task_count=0)
    sim.robots["R1"].position = (5, 5)
    sim.robots["R2"].position = (5, 6)
    sim.robots["R1"].current_path = [(5, 5), (5, 6)]
    sim.robots["R1"].path_progress = 0
    from core.models.robot import RobotState
    sim.robots["R1"].state = RobotState.MOVING
    sim.step(force=True)
    assert sim.robots["R1"].position == (5, 5)
    assert sim.metrics.collision_count == 0


def test_deterministic_experiment_same_seed_same_metrics():
    a = run_experiment("S01", "resilient", seed=42, runs=1, robots=3, tasks=3, duration=10, persist=False)
    b = run_experiment("S01", "resilient", seed=42, runs=1, robots=3, tasks=3, duration=10, persist=False)
    ma = {k: v for k, v in a["runs"][0]["metrics"].items() if not k.startswith("planning_latency")}
    mb = {k: v for k, v in b["runs"][0]["metrics"].items() if not k.startswith("planning_latency")}
    assert ma == mb


def test_scalability_supports_3_10_20_robots_with_walkable_starts():
    for count in (3, 10, 20):
        sim = SimulationEngine(seed=42)
        sim.reset(robot_count=count, task_count=max(1, count // 2))
        assert len(sim.robots) == count
        assert len({r.position for r in sim.robots.values()}) == count
        assert all(sim.world.is_walkable(r.position) for r in sim.robots.values())
        sim.step(force=True)
        assert sim.metrics.collision_count == 0


def test_three_way_benchmark_api_shape_is_json_safe_for_default_five_runs():
    result = compare("S01", seed=42, runs=5, robots=3, tasks=3, duration=10)
    encoded = json.dumps(result, allow_nan=False)
    assert encoded


def test_three_way_benchmark_uses_common_simulation_infrastructure():
    result = compare("S01", seed=42, runs=2, robots=3, tasks=3, duration=10)
    assert set(("baseline", "centralized", "resilient")) <= set(result)
    seeds = {mode: [r["seed"] for r in result[mode]["runs"]] for mode in ("baseline", "centralized", "resilient")}
    assert seeds["baseline"] == seeds["centralized"] == seeds["resilient"] == [42, 43]
    assert all(r["configuration"]["robot_count"] == 3 for mode in seeds for r in result[mode]["runs"])


def test_ros2_boundary_has_no_local_ros_dependency():
    adapter = ROS2RobotAdapter("R1")
    assert adapter.available is False
    try:
        adapter.get_position()
    except NotImplementedError as exc:
        assert "ROS 2" in str(exc)
    else:
        raise AssertionError("ROS2 adapter must remain unimplemented locally")


def test_dynamic_rerouting_releases_old_path_and_uses_alternate_route():
    from core.models.fault import FaultType
    sim = SimulationEngine(seed=42, time_step=0.1)
    sim.reset(robot_count=1, task_count=0)
    sim.add_task("T", (4, 0), (10, 0))
    sim.assign_task("T", "R1")
    for _ in range(14):
        sim.step(force=True)
    robot = sim.robots["R1"]
    blocked = robot.current_path[robot.path_progress + 1]
    sim.fault_engine.inject_fault(FaultType.BLOCKED_AISLE, "test", sim.clock.current_time, 5.0, {"cells": [blocked]})
    old_path = list(robot.current_path)
    sim.step(force=True)
    assert sim.metrics.reroute_count >= 1
    assert robot.current_path != old_path
    assert blocked not in robot.current_path[robot.path_progress:]


def test_engine_delegates_per_robot_planning_to_agent(monkeypatch):
    sim = SimulationEngine(seed=42, time_step=0.1)
    sim.reset(robot_count=1, task_count=0)
    sim.add_task("T", (4, 0), (10, 0))
    sim.assign_task("T", "R1")
    agent = sim.agents["R1"]
    calls = []
    original = agent.plan_for_goal

    def wrapped(*args, **kwargs):
        calls.append((args, kwargs))
        return original(*args, **kwargs)

    monkeypatch.setattr(agent, "plan_for_goal", wrapped)
    sim.step(force=True)
    assert calls, "SimulationEngine bypassed the owning RobotAgent planner"


def test_conflict_resolution_is_owned_by_agents():
    sim = SimulationEngine(seed=42, time_step=0.1)
    sim.reset(robot_count=2, task_count=0)
    a1, a2 = sim.agents["R1"], sim.agents["R2"]
    a1.priority = 1
    a2.priority = 2
    assert a1.resolve_conflict(a2.robot_id, a2.priority) == "YIELD"
    assert a1.state == RobotState.WAITING
    assert a2.resolve_conflict(a1.robot_id, a1.priority) == "PROCEED"
    assert a2.state == RobotState.IDLE


def test_agent_local_move_is_the_only_robot_transition_api_used_by_execution():
    sim = SimulationEngine(seed=42, time_step=0.1)
    sim.reset(robot_count=1, task_count=0)
    agent = sim.agents["R1"]
    sim.add_task("T", (5, 0), (10, 0))
    sim.assign_task("T", "R1")
    agent.robot.current_path = [(4, 0), (5, 0)]
    agent.robot.path_progress = 0
    agent.robot.state = RobotState.MOVING
    calls = []
    original = agent.execute_local_move

    def wrapped(next_position):
        calls.append(next_position)
        return original(next_position)

    agent.execute_local_move = wrapped
    sim.step(force=True)
    assert calls == [(5, 0)]


def test_agents_have_independent_decision_sequences():
    sim = SimulationEngine(seed=42)
    sim.reset(robot_count=3, task_count=0)
    sim.agents["R1"].set_intent([(4, 0), (5, 0)], timestamp=1.0)
    assert sim.agents["R1"].decision_sequence == 1
    assert sim.agents["R2"].decision_sequence == 0
    assert sim.agents["R3"].decision_sequence == 0
