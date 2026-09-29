"""Unit tests for recovery manager and task reassignment."""
import unittest
from core.models.robot import Robot, RobotState
from core.models.task import Task, TaskStatus
from core.coordination.reservation_manager import ReservationManager
from core.coordination.allocator import TaskAllocator
from core.planning.astar import AStarPlanner
from core.resilience.recovery_manager import RecoveryManager


class TestRecovery(unittest.TestCase):
    def test_robot_failure_and_task_reassignment(self):
        res_mgr = ReservationManager()
        allocator = TaskAllocator(seed=42)
        planner = AStarPlanner()
        recovery = RecoveryManager(res_mgr, allocator, planner)

        robots = {
            "R1": Robot(robot_id="R1", position=(0, 0), state=RobotState.MOVING, current_task="T01"),
            "R2": Robot(robot_id="R2", position=(5, 5), state=RobotState.IDLE),
        }
        tasks = {
            "T01": Task(task_id="T01", pickup=(2, 2), delivery=(8, 8), status=TaskStatus.IN_PROGRESS, assigned_robot="R1", priority=1)
        }

        # Place reservation for R1
        res_mgr.request_cell_reservation("R1", (2, 2), start_time=1.0, end_time=5.0)

        # R1 experiences fatal hardware failure
        incidents = recovery.handle_robot_failure(
            failed_robot_id="R1",
            robots=robots,
            tasks=tasks,
            current_time=5.0,
            failure_detected_time=5.0,
        )

        # 1. R1 marked FAILED
        self.assertEqual(robots["R1"].state, RobotState.FAILED)
        self.assertIsNone(robots["R1"].current_task)

        # 2. Reservations released
        active_res = res_mgr.get_all_active()
        self.assertEqual(len(active_res), 0)

        # 3. Task released and escalated
        self.assertEqual(tasks["T01"].status, TaskStatus.AVAILABLE)
        self.assertIsNone(tasks["T01"].assigned_robot)
        self.assertEqual(tasks["T01"].priority, 2)  # escalated priority from 1 to 2

        # 4. Allocator now assigns to R2
        allocation = allocator.allocate_next_task(list(tasks.values()), robots, current_time=6.0)
        self.assertIsNotNone(allocation)
        reassigned_task, replacement_robot = allocation
        self.assertEqual(replacement_robot.robot_id, "R2")


if __name__ == "__main__":
    unittest.main()
