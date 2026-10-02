"""Unit tests for network simulation and resilience states."""
import unittest
from core.networking.network_sim import NetworkSimulator
from core.resilience.state_machine import ResilienceStateMachine, ResilienceState


class TestNetworkAndResilience(unittest.TestCase):
    def test_packet_loss(self):
        net = NetworkSimulator(seed=42)
        # With 100% loss rate, message must be dropped
        sent = net.send_message("R1", "COORDINATOR", {"test": 1}, current_time=1.0, loss_rate=1.0)
        self.assertFalse(sent)
        self.assertEqual(net.total_dropped, 1)

    def test_network_partition(self):
        net = NetworkSimulator(seed=42)
        groups = ({"R1"}, {"R2", "R3"})
        # R1 to R2 cross-partition communication must be blocked
        sent = net.send_message("R1", "R2", {"data": 123}, current_time=1.0, is_partitioned=True, partition_groups=groups)
        self.assertFalse(sent)

    def test_resilience_state_machine_transitions(self):
        sm = ResilienceStateMachine()
        self.assertEqual(sm.current_state, ResilienceState.NORMAL)

        sm.transition(ResilienceState.DEGRADED, current_time=5.0, reason="High packet loss")
        self.assertEqual(sm.current_state, ResilienceState.DEGRADED)

        sm.transition(ResilienceState.RECOVERY, current_time=10.0, reason="Robot failure recovery")
        self.assertEqual(sm.current_state, ResilienceState.RECOVERY)

        sm.transition(ResilienceState.NORMAL, current_time=15.0, reason="System normalized")
        self.assertEqual(sm.current_state, ResilienceState.NORMAL)
        self.assertEqual(len(sm.transitions), 3)


if __name__ == "__main__":
    unittest.main()
