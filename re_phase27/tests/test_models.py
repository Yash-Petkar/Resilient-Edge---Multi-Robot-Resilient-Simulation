"""Unit tests for ResilientEdge domain models."""
import unittest
from core.models.robot import Robot, RobotState
from core.models.task import Task, TaskStatus
from core.models.reservation import Reservation, ReservationStatus
from core.models.fault import Fault, FaultType
from core.models.incident import Incident, IncidentSeverity


class TestDomainModels(unittest.TestCase):
    def test_robot_initialization(self):
        r = Robot(robot_id="R1", position=(2, 2))
        self.assertEqual(r.robot_id, "R1")
        self.assertEqual(r.state, RobotState.IDLE)
        self.assertEqual(r.battery, 100.0)
        self.assertEqual(r.health, 1.0)
        d = r.to_dict()
        self.assertEqual(d["robot_id"], "R1")
        self.assertEqual(d["state"], "IDLE")

    def test_task_phases(self):
        t = Task(task_id="T01", pickup=(2, 2), delivery=(20, 10), priority=4)
        self.assertEqual(t.status, TaskStatus.CREATED)
        self.assertEqual(t.priority, 4)
        t.status = TaskStatus.IN_PROGRESS
        self.assertEqual(t.status, TaskStatus.IN_PROGRESS)

    def test_reservation_serialization(self):
        res = Reservation(
            reservation_id="res_01",
            robot_id="R1",
            resource_id="cell:5,5",
            start_time=1.0,
            end_time=2.0,
            priority=2,
            status=ReservationStatus.GRANTED,
        )
        d = res.to_dict()
        self.assertEqual(d["status"], "GRANTED")
        self.assertEqual(d["resource_id"], "cell:5,5")

    def test_fault_model(self):
        f = Fault(
            fault_id="flt_01",
            fault_type=FaultType.ROBOT_FAILURE,
            target="R2",
            start_time=10.0,
            duration=30.0,
        )
        self.assertEqual(f.fault_type, FaultType.ROBOT_FAILURE)
        self.assertEqual(f.target, "R2")


if __name__ == "__main__":
    unittest.main()
