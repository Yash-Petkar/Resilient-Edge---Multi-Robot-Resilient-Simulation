"""Deterministic reproducibility tests using seed=42."""
import unittest
from experiments.scenarios import run_scenario


class TestDeterministic(unittest.TestCase):
    def test_reproducibility_seed_42(self):
        # Run identical scenario S01 twice with seed=42
        run1 = run_scenario("S01", seed=42, max_steps=100)
        run2 = run_scenario("S01", seed=42, max_steps=100)

        self.assertEqual(run1["steps_run"], run2["steps_run"])
        self.assertEqual(run1["metrics"]["completed_tasks"], run2["metrics"]["completed_tasks"])
        self.assertEqual(run1["metrics"]["conflict_count"], run2["metrics"]["conflict_count"])
        self.assertEqual(run1["metrics"]["messages_sent"], run2["metrics"]["messages_sent"])


if __name__ == "__main__":
    unittest.main()
