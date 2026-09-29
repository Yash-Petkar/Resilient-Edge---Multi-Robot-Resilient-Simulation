"""Unit tests for fault injection and failure detection."""
import unittest
from core.faults.fault_engine import FaultEngine
from core.models.fault import FaultType
from core.resilience.failure_detector import FailureDetector
from core.models.robot import Robot, RobotState


class TestFaults(unittest.TestCase):
    def test_fault_injection_lifecycle(self):
        engine = FaultEngine()
        fault = engine.inject_fault(
            fault_type=FaultType.ROBOT_FAILURE,
            target="R2",
            start_time=5.0,
            duration=10.0,
        )
        self.assertEqual(fault.status, "ACTIVE")
        self.assertTrue(engine.is_robot_failed("R2"))

        # Advance past duration
        resolved = engine.update(current_time=16.0)
        self.assertEqual(len(resolved), 1)
        self.assertFalse(engine.is_robot_failed("R2"))

    def test_heartbeat_timeout_detection(self):
        detector = FailureDetector(heartbeat_timeout=2.0)
        robots = {
            "R1": Robot(robot_id="R1", position=(0, 0), last_heartbeat=9.5),
            "R2": Robot(robot_id="R2", position=(2, 2), last_heartbeat=6.0),  # 4s elapsed > 2.0s
        }
        incidents = detector.check_robot_heartbeats(robots, current_time=10.0)
        self.assertTrue(any(inc.entity == "R2" and inc.fault == "HEARTBEAT_TIMEOUT" for inc in incidents))


if __name__ == "__main__":
    unittest.main()
