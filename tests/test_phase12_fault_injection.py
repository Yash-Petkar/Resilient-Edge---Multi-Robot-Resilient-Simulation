"""Phase 12 — authoritative fault injection and real simulation effects."""
import unittest

from core.faults.fault_engine import FaultEngine
from core.models.fault import FaultType
from core.models.robot import RobotState
from core.simulation.engine import SimulationEngine


class TestPhase12FaultInjection(unittest.TestCase):
    def test_deterministic_fault_ids_and_lifecycle(self):
        engine = FaultEngine()
        first = engine.inject_fault(FaultType.ROBOT_FAILURE, "R2", 0.0, duration=1.0)
        second = engine.inject_fault(FaultType.LATENCY, "network", 0.0, duration=1.0)
        self.assertEqual(first.fault_id, "flt_000001")
        self.assertEqual(second.fault_id, "flt_000002")
        self.assertTrue(engine.is_robot_failed("R2"))

        resolved = engine.update(1.0)
        self.assertEqual([f.fault_id for f in resolved], ["flt_000001", "flt_000002"])
        self.assertFalse(engine.is_robot_failed("R2"))

    def test_scheduled_fault_is_pending_then_active(self):
        engine = FaultEngine()
        fault = engine.schedule_fault(
            FaultType.PACKET_LOSS, "network", start_time=5.0, duration=2.0,
            parameters={"rate": 1.0},
        )
        self.assertEqual(fault.status, "PENDING")
        engine.update(4.99)
        self.assertEqual(fault.status, "PENDING")
        engine.update(5.0)
        self.assertEqual(fault.status, "ACTIVE")
        self.assertEqual(engine.get_packet_loss_rate(), 1.0)
        engine.update(7.0)
        self.assertEqual(fault.status, "RESOLVED")
        self.assertEqual(engine.get_packet_loss_rate(), 0.001)

    def test_environment_faults_change_authoritative_world(self):
        engine = SimulationEngine(seed=21, time_step=0.1)
        engine.reset(robot_count=2, task_count=0)
        engine.fault_engine.inject_fault(
            FaultType.BLOCKED_AISLE, "aisle", 0.0, duration=2.0,
            parameters={"cells": [(8, 4), (8, 5)]},
        )
        engine.fault_engine.inject_fault(
            FaultType.DYNAMIC_OBSTACLE, "cell:10,8", 0.0, duration=2.0,
        )
        telemetry = engine.force_step()
        self.assertIn((8, 4), engine.world.blocked_aisles)
        self.assertIn((8, 5), engine.world.blocked_aisles)
        self.assertIn((10, 8), engine.world.dynamic_obstacles)
        self.assertEqual(
            telemetry["fault_effects"]["dynamic_obstacles"], [[10, 8]]
        )

    def test_robot_failure_stops_participation_and_releases_reservations(self):
        engine = SimulationEngine(seed=22, time_step=0.1)
        engine.reset(robot_count=2, task_count=0)
        robot = engine.robots["R2"]
        robot.position = (5, 5)
        reservation = engine.reservation_mgr.request_cell_reservation(
            "R2", (5, 5), 0.0, 10.0, priority=1
        )
        self.assertIsNotNone(reservation)
        engine.fault_engine.inject_fault(
            FaultType.ROBOT_FAILURE, "R2", engine.clock.current_time, duration=5.0
        )
        engine.force_step()
        self.assertEqual(robot.state, RobotState.FAILED)
        self.assertEqual(engine.reservation_mgr.get_all_active(), [])

    def test_low_battery_fault_is_real_simulation_input(self):
        engine = SimulationEngine(seed=23, time_step=0.1)
        engine.reset(robot_count=2, task_count=0)
        robot = engine.robots["R2"]
        robot.battery = 100.0
        engine.fault_engine.inject_fault(
            FaultType.LOW_BATTERY, "R2", engine.clock.current_time, duration=2.0
        )
        engine.force_step()
        self.assertLessEqual(robot.battery, 8.0)
        self.assertTrue(
            any(i.fault == "LOW_BATTERY" for i in engine.incidents)
            or robot.state in (RobotState.DEGRADED, RobotState.CHARGING)
        )

    def test_all_network_faults_reach_network_simulator(self):
        engine = SimulationEngine(seed=24, time_step=0.1)
        engine.reset(robot_count=3, task_count=0)
        now = engine.clock.current_time
        engine.fault_engine.inject_fault(
            FaultType.PACKET_LOSS, "network", now, duration=5.0,
            parameters={"rate": 1.0},
        )
        engine.fault_engine.inject_fault(
            FaultType.LATENCY, "network", now, duration=5.0,
            parameters={"latency_seconds": 0.8},
        )
        engine.fault_engine.inject_fault(
            FaultType.JITTER, "network", now, duration=5.0,
            parameters={"jitter_seconds": 0.2},
        )
        engine.fault_engine.inject_fault(
            FaultType.MESSAGE_DUPLICATION, "network", now, duration=5.0,
            parameters={"rate": 1.0},
        )
        engine.fault_engine.inject_fault(
            FaultType.MESSAGE_REORDERING, "network", now, duration=5.0,
            parameters={"rate": 1.0},
        )
        engine.force_step()
        metrics = engine.network_sim.get_network_metrics()
        self.assertEqual(metrics["packet_loss_rate"], 1.0)
        self.assertEqual(metrics["latency_ms"], 800.0)
        self.assertEqual(metrics["jitter_ms"], 200.0)
        self.assertEqual(metrics["is_partitioned"], False)

    def test_network_partition_affects_delivery(self):
        engine = SimulationEngine(seed=25, time_step=0.1)
        engine.reset(robot_count=3, task_count=0)
        now = engine.clock.current_time
        engine.fault_engine.inject_fault(
            FaultType.NETWORK_PARTITION, "network", now, duration=5.0,
            parameters={"group_a": ["R1"], "group_b": ["R2", "R3"]},
        )
        engine.force_step()
        self.assertTrue(engine.network_sim.is_partitioned)
        self.assertEqual(engine.state_machine.current_state.value, "LOCAL_AUTONOMY")


if __name__ == "__main__":
    unittest.main()
