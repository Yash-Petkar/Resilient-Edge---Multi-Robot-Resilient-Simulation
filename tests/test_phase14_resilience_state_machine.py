"""Phase 14 — auditable resilience state machine tests."""
import unittest

from core.resilience.state_machine import ResilienceState, ResilienceStateMachine
from core.simulation.engine import SimulationEngine
from core.models.fault import FaultType


class TestPhase14ResilienceStateMachine(unittest.TestCase):
    def test_required_transition_chain_and_event_schema(self):
        sm = ResilienceStateMachine()
        sm.transition(ResilienceState.DEGRADED, 1.0, "packet loss", entity="NETWORK")
        sm.transition(ResilienceState.LOCAL_AUTONOMY, 2.0, "communication unavailable", entity="NETWORK")
        sm.transition(ResilienceState.RESYNC, 3.0, "network restored", entity="NETWORK")
        sm.transition(ResilienceState.NORMAL, 4.0, "resync complete", entity="SYSTEM")

        self.assertEqual(sm.current_state, ResilienceState.NORMAL)
        self.assertEqual(len(sm.transitions), 4)
        self.assertEqual(
            set(sm.transitions[-1]),
            {"timestamp", "entity", "old_state", "new_state", "reason"},
        )
        self.assertEqual(sm.transitions[1]["old_state"], "DEGRADED")
        self.assertEqual(sm.transitions[1]["new_state"], "LOCAL_AUTONOMY")

    def test_invalid_transition_is_rejected(self):
        sm = ResilienceStateMachine()
        with self.assertRaises(ValueError):
            sm.transition(ResilienceState.RESYNC, 1.0, "invalid")

    def test_failed_state_is_supported_and_recoverable(self):
        sm = ResilienceStateMachine()
        sm.transition(ResilienceState.RECOVERY, 1.0, "robot failure", entity="R2")
        sm.transition(ResilienceState.FAILED, 2.0, "all critical services unavailable", entity="SYSTEM")
        self.assertEqual(sm.current_state, ResilienceState.FAILED)
        sm.transition(ResilienceState.RECOVERY, 3.0, "recovery started", entity="SYSTEM")
        self.assertEqual(sm.current_state, ResilienceState.RECOVERY)

    def test_snapshot_restore_preserves_state_history(self):
        sm = ResilienceStateMachine()
        sm.transition(ResilienceState.DEGRADED, 2.0, "latency", entity="NETWORK")
        sm.transition(ResilienceState.LOCAL_AUTONOMY, 4.0, "partition", entity="NETWORK")
        snap = sm.to_dict()
        restored = ResilienceStateMachine()
        restored.restore_snapshot(snap, 9.0)
        self.assertEqual(restored.current_state, sm.current_state)
        self.assertEqual(restored.transitions, sm.transitions)
        self.assertEqual(restored.last_transition_time, sm.last_transition_time)

    def test_engine_records_network_resilience_transitions(self):
        engine = SimulationEngine(seed=141, time_step=0.1)
        engine.reset(robot_count=3, task_count=0)
        engine.fault_engine.inject_fault(
            FaultType.NETWORK_PARTITION,
            target="network",
            start_time=0.0,
            duration=1.0,
            parameters={"groups": [["R1"], ["R2", "R3"]]},
        )
        engine.force_step()
        self.assertEqual(engine.state_machine.current_state, ResilienceState.LOCAL_AUTONOMY)
        event = engine.state_machine.transitions[-1]
        self.assertEqual(event["new_state"], "LOCAL_AUTONOMY")
        self.assertIn("entity", event)


if __name__ == "__main__":
    unittest.main()
