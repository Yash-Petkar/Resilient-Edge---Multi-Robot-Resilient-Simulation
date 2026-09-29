"""Experiment scenarios (S01 to S12) definition and runner."""
import time
from typing import Dict, List, Any, Callable
from core.simulation.engine import SimulationEngine
from core.models.fault import FaultType


class ScenarioDefinition:
    def __init__(
        self,
        scenario_id: str,
        name: str,
        description: str,
        robot_count: int,
        task_count: int,
        duration: float,
        setup_fn: Callable[[SimulationEngine], None],
    ):
        self.scenario_id = scenario_id
        self.name = name
        self.description = description
        self.robot_count = robot_count
        self.task_count = task_count
        self.duration = duration
        self.setup_fn = setup_fn


def setup_s01(sim: SimulationEngine):
    """S01: Normal baseline with 3 robots."""
    for i in range(1, 4):
        sim.add_robot(f"R{i}", (2 + i * 2, 0))
    for j in range(1, 7):
        p_station = list(sim.world.pickup_stations.values())[(j - 1) % 4]
        d_station = list(sim.world.delivery_stations.values())[(j - 1) % 4]
        sim.add_task(f"T{j:02d}", p_station, d_station, priority=(j % 3) + 1)


def setup_s02(sim: SimulationEngine):
    """S02: Normal scalability test with 10 robots."""
    for i in range(1, 11):
        sim.add_robot(f"R{i:02d}", (i * 2, (i % 2) * 15))
    for j in range(1, 16):
        p_station = list(sim.world.pickup_stations.values())[(j - 1) % 4]
        d_station = list(sim.world.delivery_stations.values())[(j - 1) % 4]
        sim.add_task(f"T{j:02d}", p_station, d_station, priority=(j % 5) + 1)


def setup_s03(sim: SimulationEngine):
    """S03: High-density fleet test with 20 robots."""
    for i in range(1, 21):
        sim.add_robot(f"R{i:02d}", (i % 22 + 1, 0 if i <= 10 else 15))
    for j in range(1, 25):
        p_station = list(sim.world.pickup_stations.values())[(j - 1) % 4]
        d_station = list(sim.world.delivery_stations.values())[(j - 1) % 4]
        sim.add_task(f"T{j:02d}", p_station, d_station, priority=(j % 5) + 1)


def setup_s04(sim: SimulationEngine):
    """S04: Crossing conflict coordination."""
    # Place R1 and R2 on opposite sides on intersecting trajectories
    sim.add_robot("R1", (2, 8))
    sim.add_robot("R2", (21, 8))
    sim.add_task("T01", (2, 8), (21, 8), priority=3)
    sim.add_task("T02", (21, 8), (2, 8), priority=2)


def setup_s05(sim: SimulationEngine):
    """S05: Blocked aisle dynamic detour and replanning."""
    setup_s01(sim)
    # Inject blocked aisle in central thoroughfare at t=3.0s
    sim.fault_engine.inject_fault(
        fault_type=FaultType.BLOCKED_AISLE,
        target="aisle_central",
        start_time=3.0,
        duration=25.0,
        parameters={"cells": [(8, 4), (8, 5), (9, 4), (9, 5)]},
    )


def setup_s06(sim: SimulationEngine):
    """S06: Robot failure detection and task reassignment."""
    setup_s01(sim)
    # Fail R2 at t=4.0s
    sim.fault_engine.inject_fault(
        fault_type=FaultType.ROBOT_FAILURE,
        target="R2",
        start_time=4.0,
        duration=60.0,
    )


def setup_s07(sim: SimulationEngine):
    """S07: Low battery threshold and graceful degradation."""
    setup_s01(sim)
    sim.fault_engine.inject_fault(
        fault_type=FaultType.LOW_BATTERY,
        target="R1",
        start_time=2.0,
        duration=30.0,
    )


def setup_s08(sim: SimulationEngine):
    """S08: Packet loss resilience (35% loss)."""
    setup_s01(sim)
    sim.fault_engine.inject_fault(
        fault_type=FaultType.PACKET_LOSS,
        target="network",
        start_time=2.0,
        duration=30.0,
        parameters={"rate": 0.35},
    )


def setup_s09(sim: SimulationEngine):
    """S09: Network latency jitter (1.2s synthetic lag)."""
    setup_s01(sim)
    sim.fault_engine.inject_fault(
        fault_type=FaultType.LATENCY,
        target="network",
        start_time=2.0,
        duration=30.0,
        parameters={"latency_seconds": 1.2},
    )


def setup_s10(sim: SimulationEngine):
    """S10: Network partition split-brain isolation and resync."""
    setup_s01(sim)
    sim.fault_engine.inject_fault(
        fault_type=FaultType.NETWORK_PARTITION,
        target="network",
        start_time=3.0,
        duration=15.0,
        parameters={"group_a": ["R1"], "group_b": ["R2", "R3"]},
    )


def setup_s11(sim: SimulationEngine):
    """S11: Dynamic obstacle avoidance."""
    setup_s01(sim)
    sim.fault_engine.inject_fault(
        fault_type=FaultType.DYNAMIC_OBSTACLE,
        target="pos:10,8",
        start_time=2.5,
        duration=20.0,
        parameters={"position": (10, 8)},
    )


def setup_s12(sim: SimulationEngine):
    """S12: Combined compound faults (R2 failure, packet loss, blocked aisle)."""
    setup_s01(sim)
    sim.fault_engine.inject_fault(
        fault_type=FaultType.ROBOT_FAILURE,
        target="R2",
        start_time=4.0,
        duration=40.0,
    )
    sim.fault_engine.inject_fault(
        fault_type=FaultType.BLOCKED_AISLE,
        target="aisle_central",
        start_time=2.0,
        duration=25.0,
        parameters={"cells": [(8, 4), (8, 5)]},
    )
    sim.fault_engine.inject_fault(
        fault_type=FaultType.PACKET_LOSS,
        target="network",
        start_time=3.0,
        duration=20.0,
        parameters={"rate": 0.30},
    )


SCENARIOS: Dict[str, ScenarioDefinition] = {
    "S01": ScenarioDefinition("S01", "Normal 3 Robots", "Baseline normal execution with 3 robots and 6 tasks", 3, 6, 45.0, setup_s01),
    "S02": ScenarioDefinition("S02", "Normal 10 Robots", "Scalability test with 10 robots across multiple aisle corridors", 10, 15, 60.0, setup_s02),
    "S03": ScenarioDefinition("S03", "Normal 20 Robots", "High-density fleet stress test with 20 robots", 20, 24, 75.0, setup_s03),
    "S04": ScenarioDefinition("S04", "Crossing Conflict", "Head-on and cross-intersection conflict resolution test", 2, 2, 30.0, setup_s04),
    "S05": ScenarioDefinition("S05", "Blocked Aisle", "Dynamic obstacle / aisle blockade triggering real-time detour replan", 3, 6, 45.0, setup_s05),
    "S06": ScenarioDefinition("S06", "Robot Failure", "R2 hardware failure with task reclamation and handoff to R1/R3", 3, 6, 50.0, setup_s06),
    "S07": ScenarioDefinition("S07", "Low Battery", "Sudden battery drop triggers degraded state and dock priority", 3, 6, 45.0, setup_s07),
    "S08": ScenarioDefinition("S08", "Packet Loss", "35% packet drop rate resilience verification", 3, 6, 45.0, setup_s08),
    "S09": ScenarioDefinition("S09", "Network Latency", "1.2s synthetic lag with delayed heartbeats and messages", 3, 6, 45.0, setup_s09),
    "S10": ScenarioDefinition("S10", "Network Partition", "Split-brain network isolation, local autonomy, and resynchronization", 3, 6, 50.0, setup_s10),
    "S11": ScenarioDefinition("S11", "Dynamic Obstacle", "Sudden obstacle appearing in active robot path triggering instant avoidance", 3, 6, 40.0, setup_s11),
    "S12": ScenarioDefinition("S12", "Combined Faults", "Compound failure scenario combining R2 crash, blocked corridor, and packet loss", 3, 6, 60.0, setup_s12),
}


def run_scenario(scenario_id: str, seed: int = 42, max_steps: int = 400) -> Dict[str, Any]:
    """Execute a scenario synchronously and return complete results."""
    defn = SCENARIOS.get(scenario_id)
    if not defn:
        raise ValueError(f"Unknown scenario ID: {scenario_id}")

    sim = SimulationEngine(seed=seed, time_step=0.2)
    defn.setup_fn(sim)

    steps_run = 0
    while steps_run < max_steps and sim.clock.current_time < defn.duration:
        sim.step()
        steps_run += 1
        # Stop early if all tasks completed
        if all(t.status == "COMPLETED" for t in sim.tasks.values()):
            break

    telemetry = sim.get_telemetry()
    return {
        "scenario_id": scenario_id,
        "name": defn.name,
        "seed": seed,
        "steps_run": steps_run,
        "duration": round(sim.clock.current_time, 2),
        "metrics": telemetry["metrics"],
        "incidents_count": len(sim.incidents),
        "tasks": telemetry["tasks"],
        "robots": telemetry["robots"],
    }
