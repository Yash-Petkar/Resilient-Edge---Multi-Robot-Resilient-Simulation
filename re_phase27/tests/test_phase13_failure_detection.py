"""Phase 13 — observable failure detection and detection latency."""
import unittest

from core.models.robot import Robot, RobotState
from core.resilience.failure_detector import FailureDetector
from core.simulation.engine import SimulationEngine


class TestPhase13FailureDetection(unittest.TestCase):
    def test_heartbeat_timeout_records_detection_latency(self):
        detector = FailureDetector(heartbeat_timeout=2.0)
        robots = {"R2": Robot(robot_id="R2", position=(2, 2), last_heartbeat=6.0)}
        incidents = detector.check_robot_heartbeats(robots, current_time=10.0)
        inc = next(i for i in incidents if i.fault == "HEARTBEAT_TIMEOUT")
        self.assertEqual(inc.fault_time, 8.0)
        self.assertEqual(inc.detection_time, 10.0)
        self.assertEqual(inc.detection_latency, 2.0)

    def test_network_packet_loss_is_detected_from_observed_drops(self):
        detector = FailureDetector(network_loss_threshold=0.5)
        detector.check_network(
            {"messages_sent": 0, "messages_dropped": 0, "latency_ms": 12.0, "is_partitioned": False},
            0.0,
        )
        incidents = detector.check_network(
            {"messages_sent": 10, "messages_dropped": 8, "latency_ms": 12.0, "is_partitioned": False},
            1.0,
        )
        inc = next(i for i in incidents if i.fault == "PACKET_LOSS_DETECTED")
        self.assertEqual(inc.detection_latency, 0.0)

    def test_packet_loss_incident_is_edge_triggered_and_resolves(self):
        detector = FailureDetector(network_loss_threshold=0.5)
        detector.check_network({"messages_sent": 0, "messages_dropped": 0, "latency_ms": 0, "is_partitioned": False}, 0.0)
        first = detector.check_network({"messages_sent": 10, "messages_dropped": 8, "latency_ms": 0, "is_partitioned": False}, 1.0)
        self.assertEqual(len([i for i in first if i.fault == "PACKET_LOSS_DETECTED"]), 1)
        second = detector.check_network({"messages_sent": 20, "messages_dropped": 16, "latency_ms": 0, "is_partitioned": False}, 2.0)
        self.assertEqual(len([i for i in second if i.fault == "PACKET_LOSS_DETECTED"]), 0)
        resolved = detector.active_incidents()["PACKET_LOSS_DETECTED"]
        self.assertEqual(resolved.lifecycle, "ACTIVE")
        detector.check_network({"messages_sent": 30, "messages_dropped": 16, "latency_ms": 0, "is_partitioned": False}, 3.0)
        self.assertEqual(resolved.lifecycle, "RESOLVED")
        self.assertEqual(resolved.resolved_time, 3.0)

    def test_high_latency_incident_is_edge_triggered_and_resolves(self):
        detector = FailureDetector(network_latency_threshold=0.5)
        first = detector.check_network({"messages_sent": 10, "messages_dropped": 0, "latency_ms": 800, "is_partitioned": False}, 1.0)
        self.assertEqual(len([i for i in first if i.fault == "HIGH_NETWORK_LATENCY"]), 1)
        second = detector.check_network({"messages_sent": 20, "messages_dropped": 0, "latency_ms": 900, "is_partitioned": False}, 2.0)
        self.assertEqual(len([i for i in second if i.fault == "HIGH_NETWORK_LATENCY"]), 0)
        inc = detector.active_incidents()["HIGH_NETWORK_LATENCY"]
        detector.check_network({"messages_sent": 30, "messages_dropped": 0, "latency_ms": 100, "is_partitioned": False}, 3.0)
        self.assertEqual(inc.lifecycle, "RESOLVED")

    def test_explicit_failed_state_uses_transition_timestamp(self):
        detector = FailureDetector(heartbeat_timeout=2.0)
        robot = Robot(robot_id="R2", position=(2, 2), last_heartbeat=0.0, state=RobotState.FAILED, failed_at=5.0)
        incidents = detector.check_robot_heartbeats({"R2": robot}, 8.0)
        inc = next(i for i in incidents if i.fault == "ROBOT_FAILURE_DETECTED")
        self.assertEqual(inc.fault_time, 5.0)
        self.assertEqual(inc.detection_time, 8.0)
        self.assertEqual(inc.detection_latency, 3.0)

    def test_detection_latencies_are_never_negative(self):
        detector = FailureDetector(heartbeat_timeout=2.0)
        robot = Robot(robot_id="R2", position=(2, 2), last_heartbeat=0.0, state=RobotState.FAILED, failed_at=10.0)
        incidents = detector.check_robot_heartbeats({"R2": robot}, 8.0)
        inc = next(i for i in incidents if i.fault == "ROBOT_FAILURE_DETECTED")
        self.assertGreaterEqual(inc.detection_latency, 0.0)

    def test_partition_detected_from_transport_observation(self):
        detector = FailureDetector()
        incidents = detector.check_network(
            {"messages_sent": 10, "messages_dropped": 10, "latency_ms": 12.0, "is_partitioned": True},
            3.0,
        )
        self.assertTrue(any(i.fault == "NETWORK_PARTITION_DETECTED" for i in incidents))

    def test_engine_emits_detection_incidents(self):
        engine = SimulationEngine(seed=31, time_step=0.1)
        engine.reset(robot_count=2, task_count=0)
        engine.fault_engine.inject_fault(
            fault_type=__import__("core.models.fault", fromlist=["FaultType"]).FaultType.PACKET_LOSS,
            target="network", start_time=0.0, duration=2.0,
            parameters={"rate": 1.0},
        )
        engine.force_step()
        faults = [i.fault for i in engine.incidents]
        self.assertIn("PACKET_LOSS_DETECTED", faults)

    def test_detection_state_survives_snapshot_restore(self):
        engine = SimulationEngine(seed=32, time_step=0.1)
        engine.reset(robot_count=2, task_count=0)
        r2 = engine.robots["R2"]
        r2.last_heartbeat = -3.0
        engine.force_step()
        self.assertTrue(engine.failure_detector.detection_records)
        snap = engine.save_snapshot()

        restored = SimulationEngine(seed=32, time_step=0.1)
        restored.restore_snapshot(snap)
        self.assertEqual(
            restored.failure_detector.detection_records,
            engine.failure_detector.detection_records,
        )
        active = restored.failure_detector.active_incidents()
        if active:
            self.assertEqual(set(active), set(engine.failure_detector.active_incidents()))


if __name__ == "__main__":
    unittest.main()
