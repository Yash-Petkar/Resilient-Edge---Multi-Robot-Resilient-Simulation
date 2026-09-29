from core.models.robot import RobotState
from core.models.task import TaskStatus
from core.simulation.engine import SimulationEngine


def make_sim():
    sim = SimulationEngine(seed=42, time_step=0.1)
    sim.reset(robot_count=3, task_count=6)
    return sim


def test_task_reassignment_uses_task_id_and_preserves_state_on_success():
    sim = make_sim()
    sim.assign_task("T02", "R1")

    result = sim.reassign_task("T02")

    assert result["status"] == "REASSIGNED"
    assert result["task_id"] == "T02"
    assert result["previous_robot"] == "R1"
    assert result["new_robot"] in {"R2", "R3"}
    assert sim.tasks["T02"].assigned_robot == result["new_robot"]
    assert sim.tasks["T02"].status == TaskStatus.REASSIGNED
    assert sim.robots["R1"].current_task is None
    assert sim.robots[result["new_robot"]].current_task == "T02"
    assert sim.robots[result["new_robot"]].state == RobotState.PLANNING


def test_failed_reassignment_is_atomic():
    sim = make_sim()
    sim.assign_task("T02", "R1")
    sim.assign_task("T01", "R2")
    sim.assign_task("T03", "R3")

    result = sim.reassign_task("T02")

    assert result["status"] == "NO_ELIGIBLE_ROBOT"
    assert sim.tasks["T02"].assigned_robot == "R1"
    assert sim.tasks["T02"].status == TaskStatus.ASSIGNED
    assert sim.robots["R1"].current_task == "T02"


def test_reassign_released_task_after_failure_recovery():
    sim = make_sim()
    sim.assign_task("T02", "R1")
    sim.robots["R1"].state = RobotState.FAILED
    sim.robots["R1"].health = 0.0
    sim.robots["R1"].current_task = None
    sim.tasks["T02"].assigned_robot = None
    sim.tasks["T02"].status = TaskStatus.AVAILABLE

    result = sim.reassign_task("T02")

    assert result["status"] == "REASSIGNED"
    assert result["previous_robot"] is None
    assert sim.tasks["T02"].assigned_robot == result["new_robot"]
