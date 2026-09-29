"""Unit tests for deadlock cycle detection and resolution."""
import unittest
from core.coordination.deadlock import DeadlockDetector


class TestDeadlock(unittest.TestCase):
    def test_cycle_detection(self):
        detector = DeadlockDetector()
        # R1 waits on R2, R2 waits on R3, R3 waits on R1 (classic 3-way cycle)
        waiting = {
            "R1": "R2",
            "R2": "R3",
            "R3": "R1",
        }
        detector.build_graph(waiting)
        cycles = detector.find_cycles()
        self.assertGreater(len(cycles), 0)
        # Cycle should contain R1, R2, R3
        flattened = [item for sublist in cycles for item in sublist]
        self.assertIn("R1", flattened)
        self.assertIn("R2", flattened)
        self.assertIn("R3", flattened)

    def test_deadlock_resolution_victim(self):
        detector = DeadlockDetector()
        cycle = ["R1", "R2", "R3"]
        priorities = {"R1": 3, "R2": 1, "R3": 2}
        victim, action = detector.resolve_deadlock(cycle, priorities)
        # Lowest priority is R2 (priority 1)
        self.assertEqual(victim, "R2")
        self.assertEqual(action, "BACKOFF_AND_REPLAN")


if __name__ == "__main__":
    unittest.main()
