"""Unit tests for task allocation, reservations, and conflict detection."""
import unittest
from core.models.robot import Robot, RobotState
from core.models.task import Task, TaskStatus
from core.coordination.allocator import TaskAllocator
from core.coordination.reservation_manager import ReservationManager
from core.coordination.conflict import ConflictDetector


class TestCoordination(unittest.TestCase):
    def test_deterministic_allocation(self):
        allocator = TaskAllocator(seed=42)
        robots = {
            "R1": Robot(robot_id="R1", position=(0, 0), battery=100.0),
            "R2": Robot(robot_id="R2", position=(10, 10), battery=100.0),
        }
        task = Task(task_id="T1", pickup=(1, 0), delivery=(5, 5), priority=1, status=TaskStatus.AVAILABLE)

        res = allocator.allocate_next_task([task], robots, current_time=0.0)
        self.assertIsNotNone(res)
        allocated_task, allocated_robot = res
        # R1 is at (0,0), distance to (1,0) is 1. R2 is at (10,10), distance is much greater.
        self.assertEqual(allocated_robot.robot_id, "R1")

    def test_reservation_overlap(self):
        res_mgr = ReservationManager()
        # Robot 1 requests cell (5,5) from t=1.0 to t=3.0
        r1 = res_mgr.request_cell_reservation("R1", (5, 5), start_time=1.0, end_time=3.0)
        self.assertIsNotNone(r1)

        # Robot 2 requests same cell during overlapping interval [2.0, 4.0] -> Rejected
        r2 = res_mgr.request_cell_reservation("R2", (5, 5), start_time=2.0, end_time=4.0)
        self.assertIsNone(r2)

        # Robot 2 requests non-overlapping interval [3.5, 5.0] -> Granted
        r3 = res_mgr.request_cell_reservation("R2", (5, 5), start_time=3.5, end_time=5.0)
        self.assertIsNotNone(r3)

    def test_vertex_conflict_detection(self):
        # R1 and R2 planned to be at (3,3) at step 2
        trajectories = {
            "R1": [(1, 3), (2, 3), (3, 3)],
            "R2": [(5, 3), (4, 3), (3, 3)],
        }
        conflicts = ConflictDetector.detect_trajectory_conflicts(trajectories, current_time=0.0, dt=1.0)
        self.assertTrue(any(c.conflict_type.value == "VERTEX" and c.location == (3, 3) for c in conflicts))


if __name__ == "__main__":
    unittest.main()
