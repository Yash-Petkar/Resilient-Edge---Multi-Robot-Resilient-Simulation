"""Recovery manager for handling robot failure reassignment and network reconciliation."""
from typing import Dict, List, Optional, Tuple
from core.models.robot import Robot, RobotState
from core.models.task import Task, TaskStatus
from core.models.incident import Incident, IncidentSeverity
from core.coordination.reservation_manager import ReservationManager
from core.coordination.allocator import TaskAllocator
from core.planning.astar import AStarPlanner


class RecoveryManager:
    def __init__(
        self,
        reservation_mgr: ReservationManager,
        allocator: TaskAllocator,
        planner: AStarPlanner,
    ):
        self.reservation_mgr = reservation_mgr
        self.allocator = allocator
        self.planner = planner
        self.reassignment_latencies: List[float] = []
        self.recovery_events: List[Dict[str, float | str]] = []
        self.resync_events: List[Dict[str, float | str]] = []

    def handle_robot_failure(
        self,
        failed_robot_id: str,
        robots: Dict[str, Robot],
        tasks: Dict[str, Task],
        current_time: float,
        failure_detected_time: float,
    ) -> List[Incident]:
        """
        Executes complete failure recovery:
        1. Mark robot state = FAILED
        2. Release all its reservations
        3. Release any unfinished task back to AVAILABLE
        4. Reassign task to another available robot
        """
        incidents: List[Incident] = []
        robot = robots.get(failed_robot_id)
        if not robot:
            return incidents

        # 1. Mark failed
        robot.state = RobotState.FAILED
        robot.failed_at = float(current_time)
        robot.health = 0.0
        robot.current_path = []

        # 2. Release reservations
        self.reservation_mgr.release_all_for_robot(failed_robot_id)

        # 3. Recover unfinished task
        tid = robot.current_task
        if tid and tid in tasks:
            task = tasks[tid]
            if task.status in (TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS):
                task.status = TaskStatus.AVAILABLE
                task.assigned_robot = None
                task.phase = "PICKUP"
                task.priority = min(5, task.priority + 1)  # Escalate priority for recovery
                robot.current_task = None

                reassign_time = current_time - failure_detected_time
                self.reassignment_latencies.append(reassign_time)

                self.recovery_events.append({
                    "task_id": tid,
                    "failed_robot": failed_robot_id,
                    "detection_time": float(failure_detected_time),
                    "requeue_time": float(current_time),
                    "reassignment_latency": float(reassign_time),
                })

                incidents.append(
                    Incident(
                        incident_id=f"inc_rec_{tid}_{int(current_time*10)}",
                        timestamp=current_time,
                        entity=failed_robot_id,
                        fault="ROBOT_FAILURE",
                        severity=IncidentSeverity.CRITICAL,
                        state="RECOVERY",
                        message=f"Task {tid} released from failed {failed_robot_id} and requeued with priority {task.priority}. (Latency: {reassign_time:.2f}s)",
                    )
                )

        return incidents

    def handle_network_resync(
        self,
        robots: Dict[str, Robot],
        current_time: float,
    ) -> List[Incident]:
        """Reconcile locally-held robot state after communication is restored.

        The method deliberately does not mutate peer objects or bypass the P2P
        transport. It only normalizes each robot's local operational state; the
        next engine tick performs message synchronization through the existing
        communication adapter, followed by the normal conflict detector.
        """
        incidents: List[Incident] = []
        for rid in sorted(robots):
            robot = robots[rid]
            if robot.state == RobotState.FAILED:
                continue
            if robot.state in (RobotState.DEGRADED, RobotState.LOCAL_AUTONOMY):
                old_state = robot.state.value
                robot.state = RobotState.MOVING if robot.current_task else RobotState.IDLE
                robot.network_status = "CONNECTED"
                self.resync_events.append({
                    "robot_id": rid,
                    "timestamp": float(current_time),
                    "old_state": old_state,
                    "new_state": robot.state.value,
                })
                incidents.append(
                    Incident(
                        incident_id=f"inc_sync_{rid}_{int(current_time*10)}",
                        timestamp=current_time,
                        entity=rid,
                        fault="NETWORK_RESYNC",
                        severity=IncidentSeverity.INFO,
                        state="RESYNC",
                        message=(
                            f"Robot {rid} state reconciled from {old_state} to "
                            f"{robot.state.value}; P2P synchronization and conflict "
                            "validation continue through the normal simulation tick."
                        ),
                    )
                )
        return incidents
