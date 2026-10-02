"""Phase 11 — deterministic deadlock detection and recovery tests."""
import unittest

from core.coordination.deadlock import DeadlockDetector
from core.coordination.reservation_manager import ReservationManager
from core.models.robot import RobotState
from core.models.task import TaskStatus
from core.simulation.engine import SimulationEngine


class TestPhase11DeadlockRecovery(unittest.TestCase):
    def test_wait_for_graph_detects_three_robot_cycle(self):
        detector = DeadlockDetector()
        detector.build_graph({
            "R1": {"R2"},
            "R2": {"R3"},
            "R3": {"R1"},
        })
        cycles = detector.find_cycles()
        self.assertEqual(cycles, [["R1", "R2", "R3"]])

    def test_multiple_blockers_are_preserved(self):
        detector = DeadlockDetector()
        detector.build_graph({"R1": {"R2", "R3"}, "R2": None, "R3": None})
        self.assertEqual(detector.graph_snapshot(), {
            "R1": ["R2", "R3"],
            "R2": [],
            "R3": [],
        })
        self.assertEqual(detector.find_cycles(), [])

    def test_reservation_dependency_identifies_blocking_robot(self):
        manager = ReservationManager()
        owner = manager.request_cell_reservation("R2", (4, 4), 0.0, 1.0, priority=2)
        self.assertIsNotNone(owner)
        blockers = manager.get_cell_blockers("4,4" if False else (4, 4), 0.0, 0.5, exclude_robot="R1")
        self.assertEqual(blockers, ["R2"])

    def test_deterministic_victim_selection(self):
        detector = DeadlockDetector()
        victim, action = detector.resolve_deadlock(
            ["R1", "R2", "R3"],
            {"R1": 3, "R2": 1, "R3": 2},
        )
        self.assertEqual(victim, "R2")
        self.assertEqual(action, "BACKOFF_AND_REPLAN")

    def test_deadlock_recovery_state_survives_snapshot(self):
        engine = SimulationEngine(seed=12, time_step=0.1, deadlock_recovery=True)
        engine.reset(robot_count=3, task_count=0)
        engine.deadlock_backoff_until["R2"] = 4.5
        engine.deadlock_detector.build_graph({"R1": {"R2"}, "R2": {"R3"}, "R3": {"R1"}})
        engine.deadlock_detector.find_cycles()

        snapshot = engine.save_snapshot()
        restored = SimulationEngine(seed=99, time_step=0.5, deadlock_recovery=True)
        restored.restore_snapshot(snapshot)

        self.assertEqual(restored.deadlock_backoff_until, {"R2": 4.5})
        self.assertEqual(restored.deadlock_detector.graph_snapshot(), {
            "R1": ["R2"], "R2": ["R3"], "R3": ["R1"]
        })
        self.assertEqual(restored.deadlock_detector.last_cycles, [["R1", "R2", "R3"]])

    def test_engine_breaks_known_three_robot_deadlock(self):
        engine = SimulationEngine(seed=11, time_step=0.1, deadlock_recovery=True)
        engine.reset(robot_count=3, task_count=0)

        # A <- B <- C <- A occupancy cycle.
        positions = {"R1": (4, 0), "R2": (6, 0), "R3": (8, 0)}
        next_positions = {"R1": (6, 0), "R2": (8, 0), "R3": (4, 0)}
        for rid, pos in positions.items():
            engine.robots[rid].position = pos
            engine.robots[rid].state = RobotState.WAITING
            engine.robots[rid].current_path = [pos, next_positions[rid]]
            engine.robots[rid].path_progress = 0
            task_id = f"T-{rid}"
            engine.add_task(task_id, next_positions[rid], (10, 10), priority={"R1": 3, "R2": 1, "R3": 2}[rid])
            engine.robots[rid].current_task = task_id
            engine.tasks[task_id].assigned_robot = rid
            engine.tasks[task_id].status = TaskStatus.IN_PROGRESS

        telemetry = engine.force_step()
        self.assertEqual(telemetry["metrics"]["deadlock_count"], 1)
        self.assertEqual(engine.deadlock_detector.last_cycles, [["R1", "R2", "R3"]])
        self.assertIn("R2", engine.deadlock_backoff_until)
        self.assertEqual(engine.robots["R2"].state, RobotState.WAITING)
        self.assertEqual(engine.robots["R2"].current_path, [])
        self.assertTrue(any(i.fault == "DEADLOCK_RESOLVED" for i in engine.incidents))

        # A released reservation/dependency is not retained as an active blocker.
        self.assertEqual(engine.reservation_mgr.get_all_active(), [])


if __name__ == "__main__":
    unittest.main()
