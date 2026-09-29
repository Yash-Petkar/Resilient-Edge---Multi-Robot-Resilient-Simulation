"""Unit and integration tests for robot lifecycle, settings, snapshots, and scenarios."""
import unittest
from core.simulation.engine import SimulationEngine
from core.models.robot import RobotState
from core.models.task import TaskStatus
from core.models.fault import FaultType
from experiments.scenarios import SCENARIOS, run_scenario


class TestRobotLifecycleAndIntegration(unittest.TestCase):
    def setUp(self):
        self.sim = SimulationEngine(seed=42, time_step=0.1)
        self.sim.reset(robot_count=3, task_count=6)

    def test_robot_pause(self):
        """Test robot pause stops movement without creating faults."""
        r1 = self.sim.robots["R1"]
        initial_state = r1.state
        self.sim.pause_robot("R1")
        self.assertEqual(r1.state, RobotState.PAUSED)
        self.assertEqual(len(self.sim.fault_engine.active_faults), 0)

    def test_robot_resume(self):
        """Test robot resume transitions paused robot back without clearing unrelated faults."""
        # Inject fault on R3
        self.sim.fault_engine.inject_fault(FaultType.ROBOT_FAILURE, "R3", 0.0, 30.0)
        self.sim.robots["R3"].state = RobotState.FAILED
        self.sim.robots["R3"].health = 0.0

        # Pause and resume R1
        self.sim.pause_robot("R1")
        self.assertEqual(self.sim.robots["R1"].state, RobotState.PAUSED)
        self.sim.resume_robot("R1")
        self.assertIn(self.sim.robots["R1"].state, [RobotState.IDLE, RobotState.PLANNING])

        # R3 must remain FAILED (unrelated fault not cleared)
        self.assertEqual(self.sim.robots["R3"].state, RobotState.FAILED)
        self.assertGreater(len(self.sim.fault_engine.active_faults), 0)

    def test_robot_reset(self):
        """Test robot reset resets only the target robot."""
        # Inject fault on R3
        self.sim.fault_engine.inject_fault(FaultType.ROBOT_FAILURE, "R3", 0.0, 30.0)
        self.sim.robots["R3"].state = RobotState.FAILED

        # Reset R2
        self.sim.robots["R2"].battery = 45.0
        self.sim.reset_robot("R2")
        self.assertEqual(self.sim.robots["R2"].battery, 100.0)
        self.assertEqual(self.sim.robots["R2"].state, RobotState.IDLE)
        self.assertEqual(self.sim.robots["R2"].position, (6, 0))

        # R3 still failed
        self.assertEqual(self.sim.robots["R3"].state, RobotState.FAILED)

    def test_home_positions_are_consistent_across_lifecycle(self):
        self.assertEqual(self.sim.robots["R2"].position, (6, 0))
        self.assertEqual(self.sim.robots["R2"].home_position, (6, 0))

        snapshot = self.sim.save_snapshot()
        self.assertEqual(snapshot["home_positions"]["R2"], [6, 0])
        self.assertEqual(snapshot["robots"][1]["home_position"], [6, 0])

        robot = self.sim.robots["R2"]
        robot.position = (20, 10)
        robot.home_position = (99, 99)
        self.sim.restore_snapshot(snapshot)
        restored_robot = self.sim.robots["R2"]
        self.assertEqual(restored_robot.position, (6, 0))
        self.assertEqual(restored_robot.home_position, (6, 0))

        restored_robot.position = (20, 10)
        restored_robot.state = RobotState.FAILED
        self.sim.resume_robot("R2")
        self.assertEqual(restored_robot.position, (6, 0))
        self.assertEqual(restored_robot.state, RobotState.IDLE)

        self.sim.reset(robot_count=2, task_count=0)
        self.assertEqual(self.sim.robots["R2"].position, (6, 0))

    def test_robot_reassign(self):
        """Test robot reassign shifts active task to eligible idle robot."""
        # Step simulation to assign tasks
        self.sim.step(force=True)
        r1 = self.sim.robots["R1"]
        if not r1.current_task:
            task = list(self.sim.tasks.values())[0]
            self.sim.assign_task(task.task_id, "R1")

        active_task_id = r1.current_task
        self.assertIsNotNone(active_task_id)

        res = self.sim.reassign_robot("R1")
        self.assertEqual(res["status"], "REASSIGNED")
        self.assertEqual(res["task_id"], active_task_id)
        self.assertNotEqual(res["new_robot"], "R1")
        self.assertIsNone(r1.current_task)
        self.assertEqual(self.sim.tasks[active_task_id].assigned_robot, res["new_robot"])
        self.assertEqual(self.sim.tasks[active_task_id].status, TaskStatus.REASSIGNED)

    def test_settings_validation_and_application(self):
        """Test valid settings are applied and invalid ones raise ValueError."""
        updated = self.sim.update_settings({"time_step": 0.2, "time_scale": 2.0, "seed": 99})
        self.assertEqual(self.sim.clock.time_step, 0.2)
        self.assertEqual(self.sim.clock.time_scale, 2.0)
        self.assertEqual(self.sim.seed, 99)

        # Invalid settings must raise ValueError
        with self.assertRaises(ValueError):
            self.sim.update_settings({"time_step": -0.5})

        with self.assertRaises(ValueError):
            self.sim.update_settings({"default_robot_count": 0})

    def test_snapshot_save_and_restore(self):
        """Test complete simulation snapshot save and restore."""
        # Advance simulation and inject a fault
        for _ in range(5):
            self.sim.step(force=True)
        self.sim.fault_engine.inject_fault(FaultType.PACKET_LOSS, "network", self.sim.clock.current_time, 20.0, {"loss_rate": 0.5})

        saved_snapshot = self.sim.save_snapshot()
        saved_time = saved_snapshot["clock"]["current_time"]
        self.assertGreater(saved_time, 0.0)

        # Reset simulation
        self.sim.reset(robot_count=2, task_count=2)
        self.assertEqual(self.sim.clock.current_time, 0.0)
        self.assertEqual(len(self.sim.robots), 2)

        # Restore from snapshot
        self.sim.restore_snapshot(saved_snapshot)
        self.assertAlmostEqual(self.sim.clock.current_time, saved_time, places=2)
        self.assertEqual(len(self.sim.robots), len(saved_snapshot["robots"]))
        self.assertEqual(len(self.sim.fault_engine.active_faults), len(saved_snapshot["faults"]))

    def test_scenario_synchronization(self):
        """Test scenario benchmark execution and metric generation."""
        res = run_scenario("S01", seed=42)
        self.assertEqual(res["scenario_id"], "S01")
        self.assertIn("metrics", res)
        self.assertGreater(res["metrics"]["completed_tasks"], 0)
        self.assertGreater(res["metrics"]["makespan"], 0.0)


if __name__ == "__main__":
    unittest.main()
