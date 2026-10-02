from core.models.robot import Robot, RobotState
from core.models.task import Task, TaskStatus
from core.coordination.reservation_manager import ReservationManager
from core.coordination.allocator import TaskAllocator
from core.planning.astar import AStarPlanner
from core.resilience.recovery_manager import RecoveryManager


def test_phase15_robot_failure_recovery_releases_and_requeues_task():
    mgr = RecoveryManager(ReservationManager(), TaskAllocator(seed=42), AStarPlanner())
    robots = {
        "R1": Robot("R1", (0, 0), state=RobotState.MOVING, current_task="T1"),
        "R2": Robot("R2", (5, 5), state=RobotState.IDLE),
    }
    tasks = {"T1": Task("T1", (2, 2), (8, 8), status=TaskStatus.IN_PROGRESS, assigned_robot="R1")}
    mgr.reservation_mgr.request_cell_reservation("R1", (2, 2), 1.0, 5.0)
    incidents = mgr.handle_robot_failure("R1", robots, tasks, 5.0, 4.5)
    assert robots["R1"].state == RobotState.FAILED
    assert tasks["T1"].status == TaskStatus.AVAILABLE
    assert tasks["T1"].assigned_robot is None
    assert mgr.reservation_mgr.get_all_active() == []
    assert incidents


def test_phase15_network_resync_is_deterministic_and_preserves_failed_robot():
    mgr = RecoveryManager(ReservationManager(), TaskAllocator(seed=42), AStarPlanner())
    robots = {
        "R1": Robot("R1", (1, 1), state=RobotState.LOCAL_AUTONOMY, current_task="T1", network_status="PARTITIONED"),
        "R2": Robot("R2", (2, 2), state=RobotState.DEGRADED, network_status="DEGRADED"),
        "R3": Robot("R3", (3, 3), state=RobotState.FAILED, network_status="DISCONNECTED"),
    }
    incidents = mgr.handle_network_resync(robots, 10.0)
    assert robots["R1"].state == RobotState.MOVING
    assert robots["R1"].network_status == "CONNECTED"
    assert robots["R2"].state == RobotState.IDLE
    assert robots["R3"].state == RobotState.FAILED
    assert len(incidents) == 2


def test_phase15_metrics_are_recorded_on_real_recovery_path():
    from core.simulation.engine import SimulationEngine
    sim = SimulationEngine(seed=42, time_step=0.1)
    sim.reset(robot_count=3, task_count=1)
    sim.assign_task("T01", "R1")
    sim.robots["R1"].state = RobotState.FAILED
    sim.robots["R1"].health = 0.0
    sim.robots["R1"].failed_at = 0.0
    sim.clock.current_time = 2.0
    sim.step()
    assert sim.metrics.recovery_detection_times
    # Reassignment/replanning may occur on the same or subsequent tick depending on transport.
    assert "recovery_time" in sim.metrics.get_summary(1, 0, sim.clock.current_time, sim.state_machine.state_durations)
