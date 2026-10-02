import unittest
from core.agents.robot_agent import RobotAgent
from core.models.robot import Robot, RobotState
from core.networking.adapter import LocalP2PCommunicationAdapter
from core.networking.network_sim import NetworkSimulator


class TestPhase9NetworkDegradation(unittest.TestCase):
    def make_agents(self):
        adapter = LocalP2PCommunicationAdapter(NetworkSimulator(seed=11))
        agents = [RobotAgent(Robot(robot_id=f"AMR-0{i}", position=(i, 1))) for i in range(1, 4)]
        for a in agents:
            a.attach_communication_adapter(adapter)
        return agents, adapter

    def test_latency_is_applied_and_observable(self):
        agents, adapter = self.make_agents()
        adapter.configure(latency=0.5, jitter=0.0)
        agents[0].publish_local_state(10.0, recipients=["AMR-02"])
        self.assertEqual(adapter.network.total_delivered, 0)
        self.assertEqual(len(adapter.pump_all(10.49)["AMR-02"]), 0)
        self.assertEqual(len(adapter.pump_all(10.50)["AMR-02"]), 1)

    def test_packet_loss_prevents_delivery(self):
        agents, adapter = self.make_agents()
        adapter.configure(loss_rate=1.0)
        agents[0].publish_local_state(1.0, recipients=["AMR-02"])
        self.assertEqual(adapter.network.total_dropped, 1)
        self.assertEqual(adapter.network.in_flight_messages, [])

    def test_duplication_creates_duplicate_delivery(self):
        agents, adapter = self.make_agents()
        adapter.configure(duplication_rate=1.0)
        agents[0].publish_local_state(2.0, recipients=["AMR-02"])
        messages = adapter.pump_all(2.2)["AMR-02"]
        self.assertEqual(len(messages), 2)
        self.assertEqual(adapter.network.total_duplicated, 1)

    def test_reordering_is_recorded(self):
        agents, adapter = self.make_agents()
        adapter.configure(reorder_rate=1.0)
        agents[0].publish_local_state(3.0, recipients=["AMR-02"])
        self.assertEqual(adapter.network.total_reordered, 1)
        self.assertGreater(adapter.network.latency_samples_ms[-1], 100.0)

    def test_partition_changes_local_communication_state(self):
        agents, adapter = self.make_agents()
        adapter.configure(is_partitioned=True, partition_groups=({"AMR-01"}, {"AMR-02", "AMR-03"}))
        self.assertEqual(agents[0].assess_communication(1.0), "PARTITIONED")
        self.assertEqual(agents[1].assess_communication(1.0), "PARTITIONED")
        self.assertEqual(agents[0].publish_local_state(1.0), 0)

    def test_degradation_is_not_robot_failure(self):
        agents, adapter = self.make_agents()
        adapter.configure(loss_rate=1.0)
        for a in agents:
            a.assess_communication(2.0)
        self.assertTrue(all(a.communication_state == "DEGRADED" for a in agents))
        self.assertTrue(all(a.robot.state != RobotState.FAILED for a in agents))

    def test_conditions_are_validated(self):
        _, adapter = self.make_agents()
        with self.assertRaises(ValueError):
            adapter.configure(loss_rate=1.2)
        with self.assertRaises(ValueError):
            adapter.configure(latency=-1)
        with self.assertRaises(ValueError):
            adapter.configure(unknown_condition=1)

    def test_conditions_and_metrics_are_authoritative(self):
        _, adapter = self.make_agents()
        adapter.configure(loss_rate=0.4, latency=0.2, jitter=0.03, duplication_rate=0.2, reorder_rate=0.1)
        c = adapter.get_conditions()
        self.assertEqual(c["loss_rate"], 0.4)
        self.assertEqual(c["latency"], 0.2)
        self.assertEqual(c["jitter"], 0.03)
        self.assertEqual(adapter.network_health(), "DEGRADED")


if __name__ == "__main__":
    unittest.main()
