import unittest
from core.agents.robot_agent import RobotAgent
from core.models.robot import Robot
from core.networking.adapter import LocalP2PCommunicationAdapter
from core.networking.network_sim import NetworkSimulator


class TestPhase8P2P(unittest.TestCase):
    def make_agents(self):
        net = NetworkSimulator(seed=7)
        adapter = LocalP2PCommunicationAdapter(net)
        a = RobotAgent(Robot(robot_id="AMR-01", position=(1, 1)))
        b = RobotAgent(Robot(robot_id="AMR-02", position=(2, 1)))
        c = RobotAgent(Robot(robot_id="AMR-03", position=(3, 1)))
        for agent in (a, b, c):
            agent.attach_communication_adapter(adapter)
        return a, b, c, adapter

    def test_robot_to_robot_broadcast_not_coordinator(self):
        a, b, c, adapter = self.make_agents()
        a.set_intent([(1, 1), (2, 1)], timestamp=1.0)
        sent = a.publish_local_state(1.0)
        self.assertEqual(sent, 2)
        grouped = adapter.pump_all(1.02)
        self.assertEqual(len(grouped["AMR-02"]), 1)
        self.assertEqual(len(grouped["AMR-03"]), 1)
        self.assertNotIn("COORDINATOR", adapter.peers)

    def test_peer_table_is_populated_from_p2p_message(self):
        a, b, c, adapter = self.make_agents()
        a.set_intent([(1, 1), (2, 1)], timestamp=2.0)
        a.publish_local_state(2.0, recipients=["AMR-02"])
        messages = adapter.pump_all(2.02)["AMR-02"]
        for m in messages:
            payload = m.payload
            b.update_peer(type("P", (), {
                "robot_id": payload["robot_id"], "position": tuple(payload["position"]),
                "velocity": payload["velocity"], "battery": payload["battery"],
                "priority": payload["priority"], "status": payload["status"],
                "intended_path": [tuple(p) for p in payload["intended_path"]],
                "timestamp": payload["timestamp"], "sequence_number": payload["sequence_number"]
            })())
        self.assertIn("AMR-01", b.peer_table)
        self.assertEqual(b.peer_table["AMR-01"].position, (1, 1))

    def test_partition_blocks_cross_group_p2p(self):
        a, b, c, adapter = self.make_agents()
        adapter.configure(is_partitioned=True, partition_groups=({"AMR-01"}, {"AMR-02", "AMR-03"}))
        self.assertEqual(a.publish_local_state(1.0), 0)
        self.assertEqual(len(adapter.network.in_flight_messages), 0)

    def test_loss_is_applied_to_robot_peer_messages(self):
        a, b, c, adapter = self.make_agents()
        adapter.configure(loss_rate=1.0)
        self.assertEqual(a.publish_local_state(1.0), 0)
        self.assertEqual(adapter.network.total_dropped, 2)

    def test_each_agent_has_same_transport_boundary_but_private_peer_state(self):
        a, b, c, adapter = self.make_agents()
        self.assertIs(a.communication_adapter, b.communication_adapter)
        self.assertIsNot(a.peer_table, b.peer_table)
        a.set_intent([(1, 1)], timestamp=1.0)
        self.assertNotEqual(a.intent, b.intent)


if __name__ == "__main__":
    unittest.main()
