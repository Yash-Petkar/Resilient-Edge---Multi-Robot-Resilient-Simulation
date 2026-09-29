"""Phase 14 cleanup/hardening regression tests."""
import unittest

from core.models.robot import Robot, RobotState
from core.models.incident import Incident, IncidentSeverity
from core.resilience.failure_detector import FailureDetector
from core.simulation.engine import SimulationEngine


class TestPhase14Cleanup(unittest.TestCase):
    def test_messages_sent_metric_matches_network_counter(self):
        engine = SimulationEngine(seed=71, time_step=0.1)
        engine.reset(robot_count=3, task_count=0)
        engine.force_step()
        self.assertEqual(engine.metrics.messages_sent, engine.network_sim.total_sent)

    def test_failed_at_survives_robot_serialization(self):
        robot = Robot(robot_id="R1", position=(2, 2), state=RobotState.FAILED, failed_at=4.5)
        self.assertEqual(robot.to_dict()["failed_at"], 4.5)

    def test_snapshot_restore_preserves_active_network_incident_without_duplication(self):
        engine = SimulationEngine(seed=72, time_step=0.1)
        engine.reset(robot_count=2, task_count=0)
        detector = engine.failure_detector
        detector.check_network({"messages_sent": 0, "messages_dropped": 0, "latency_ms": 0, "is_partitioned": False}, 0.0)
        incidents = detector.check_network({"messages_sent": 10, "messages_dropped": 8, "latency_ms": 0, "is_partitioned": False}, 1.0)
        engine.incidents.extend(incidents)
        snapshot = engine.save_snapshot()
        restored = SimulationEngine(seed=72, time_step=0.1)
        restored.restore_snapshot(snapshot)
        before = len(restored.incidents)
        restored.failure_detector.check_network({"messages_sent": 20, "messages_dropped": 16, "latency_ms": 0, "is_partitioned": False}, 2.0)
        self.assertEqual(len(restored.incidents), before)


if __name__ == "__main__":
    unittest.main()
