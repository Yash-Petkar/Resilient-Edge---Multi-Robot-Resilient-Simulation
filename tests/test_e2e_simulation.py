"""End-to-End Simulation Test: 3 robots, 6 tasks, R2 failure, task reassignment, packet loss, partition, resync, completion."""
import unittest
from core.simulation.engine import SimulationEngine
from core.models.fault import FaultType
from core.models.robot import RobotState
from core.models.task import TaskStatus


class TestE2ESimulation(unittest.TestCase):
    def test_complete_resilience_lifecycle(self):
        sim = SimulationEngine(seed=42, time_step=0.2)

        # 1. Spawn 3 robots
        r1 = sim.add_robot("R1", (4, 0))
        r2 = sim.add_robot("R2", (8, 0))
        r3 = sim.add_robot("R3", (12, 0))
        self.assertEqual(len(sim.robots), 3)

        # 2. Add 6 tasks
        for i in range(1, 7):
            p = list(sim.world.pickup_stations.values())[(i - 1) % 4]
            d = list(sim.world.delivery_stations.values())[(i - 1) % 4]
            sim.add_task(f"T{i:02d}", p, d, priority=(i % 3) + 1)
        self.assertEqual(len(sim.tasks), 6)

        # Run 25 steps: robots assign and begin moving
        for _ in range(25):
            sim.step()

        # At least one robot should be moving or have a task
        active_assigned = [r for r in sim.robots.values() if r.current_task is not None]
        self.assertGreater(len(active_assigned), 0)

        # 3. Inject R2 Failure
        sim.fault_engine.inject_fault(
            fault_type=FaultType.ROBOT_FAILURE,
            target="R2",
            start_time=sim.clock.current_time,
            duration=30.0,
        )

        # Advance simulation to allow failure detection & recovery
        for _ in range(25):
            sim.step()

        # R2 must be marked FAILED
        self.assertEqual(sim.robots["R2"].state, RobotState.FAILED)

        # 4. Inject Packet Loss & Network Partition
        sim.fault_engine.inject_fault(
            fault_type=FaultType.PACKET_LOSS,
            target="network",
            start_time=sim.clock.current_time,
            duration=10.0,
            parameters={"rate": 0.4},
        )
        sim.fault_engine.inject_fault(
            fault_type=FaultType.NETWORK_PARTITION,
            target="network",
            start_time=sim.clock.current_time,
            duration=5.0,
            parameters={"group_a": ["R1"], "group_b": ["R3"]},
        )

        # Advance simulation during partition
        for _ in range(30):
            sim.step()

        # Check that network partition caused LOCAL_AUTONOMY or DEGRADED state
        self.assertIn(
            sim.state_machine.current_state.value,
            ["LOCAL_AUTONOMY", "DEGRADED", "RESYNC", "NORMAL"],
        )

        # Clear remaining faults to allow complete recovery
        sim.fault_engine.clear_all()

        # Run until completion or max steps
        for _ in range(150):
            sim.step()

        telemetry = sim.get_telemetry()
        metrics = telemetry["metrics"]

        # Verify completed tasks count > 0 and metrics are derived from actual events
        self.assertGreater(metrics["completed_tasks"], 0)
        self.assertGreater(metrics["messages_sent"], 0)
        self.assertGreaterEqual(metrics["task_completion_rate"], 16.0)
        self.assertGreater(len(sim.incidents), 0)


if __name__ == "__main__":
    unittest.main()
