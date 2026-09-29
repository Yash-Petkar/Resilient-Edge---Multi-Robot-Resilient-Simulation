"""Deterministic task allocation for multi-robot fleets."""
import math
from typing import List, Dict, Optional, Tuple
from core.models.robot import Robot, RobotState
from core.models.task import Task, TaskStatus


class TaskAllocator:
    def __init__(self, seed: int = 42):
        self.seed = seed

    def allocate_next_task(
        self,
        tasks: List[Task],
        robots: Dict[str, Robot],
        current_time: float,
    ) -> Optional[Tuple[Task, Robot]]:
        """
        Deterministically selects the highest-priority pending task and assigns
        it to the best suited available robot based on distance, battery, and workload.
        """
        # Filter available tasks
        available_tasks = [t for t in tasks if t.status == TaskStatus.AVAILABLE]
        if not available_tasks:
            return None

        # Sort tasks by priority descending, then deadline ascending, then creation_time ascending, then task_id
        sorted_tasks = sorted(
            available_tasks,
            key=lambda t: (-t.priority, t.deadline, t.creation_time, t.task_id),
        )

        # Filter eligible robots (IDLE or DEGRADED with battery > 15%, not FAILED)
        eligible_robots = [
            r for r in robots.values()
            if r.state in (RobotState.IDLE, RobotState.DEGRADED)
            and r.battery > 15.0
            and r.current_task is None
        ]
        if not eligible_robots:
            return None

        # Evaluate each task against eligible robots
        for task in sorted_tasks:
            best_robot: Optional[Robot] = None
            best_score = float("inf")

            # Deterministic sorting of robots to break ties consistently
            for r in sorted(eligible_robots, key=lambda x: x.robot_id):
                # Score = Euclidean distance to pickup + battery penalty + health penalty
                dx = r.position[0] - task.pickup[0]
                dy = r.position[1] - task.pickup[1]
                distance = math.hypot(dx, dy)

                # Battery penalty (favors higher battery)
                battery_factor = (100.0 - r.battery) * 0.1
                # Health penalty
                health_factor = (1.0 - r.health) * 20.0
                # Network penalty
                network_factor = 10.0 if r.network_status == "DEGRADED" else 0.0

                score = distance + battery_factor + health_factor + network_factor

                if score < best_score:
                    best_score = score
                    best_robot = r

            if best_robot:
                return (task, best_robot)

        return None
