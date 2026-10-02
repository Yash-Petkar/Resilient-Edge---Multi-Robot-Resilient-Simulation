"""Unit and integration tests for production features: real baselines, Monte Carlo, battery lifecycle, network, explainability."""
import unittest
from core.simulation.engine import SimulationEngine
from core.models.robot import RobotState
from core.models.fault import FaultType
from core.models.task import TaskStatus
from core.networking.network_sim import NetworkSimulator
from experiments.baseline import run_baseline_comparison, run_baseline_a_stop_and_wait, run_baseline_b_centralized_lock
from experiments.monte_carlo import run_monte_carlo
from experiments.parameter_sweep import run_parameter_sweep


class TestProductionAndBaselines(unittest.TestCase):
    def setUp(self):
        self.sim = SimulationEngine(seed=42, time_step=0.1)
        self.sim.reset(robot_count=3, task_count=6)

    def test_real_baseline_simulations(self):
        """Test real execution of Baseline A and B without fabricated multipliers."""
        comp = run_baseline_comparison("S06", seed=42)
        self.assertEqual(comp["scenario"], "S06")
        self.assertEqual(len(comp["comparisons"]), 3)

        base_a = comp["comparisons"][0]
        base_b = comp["comparisons"][1]
        re_sys = comp["comparisons"][2]

        self.assertEqual(base_a["system"], "Baseline A (Stop/Wait)")
        self.assertEqual(base_b["system"], "Baseline B (Centralized Lock)")
        self.assertEqual(re_sys["system"], "ResilientEdge (Proposed)")

        # In S06 (robot failure), Baseline A cannot reassign, so completion rate must be lower than ResilientEdge
        self.assertLessEqual(base_a["task_completion_rate"], re_sys["task_completion_rate"])
        self.assertTrue(re_sys["resilience_recovery"])
        self.assertFalse(base_a["resilience_recovery"])

    def test_monte_carlo_execution(self):
        """Test Monte Carlo runs across multiple seeds and generates valid statistics."""
        mc_results = run_monte_carlo("S01", num_runs=3, start_seed=10)
        self.assertEqual(mc_results["num_runs"], 3)
        self.assertEqual(len(mc_results["runs"]), 3)
        stats = mc_results["statistics"]
        self.assertIn("completion_rate", stats)
        self.assertIn("mean", stats["completion_rate"])
        self.assertIn("ci_95", stats["completion_rate"])

    def test_parameter_sweep_execution(self):
        """Test parameter sweep across parameter values."""
        sweep = run_parameter_sweep("robot_count", values=[2, 3], seed=42)
        self.assertEqual(sweep["parameter_type"], "robot_count")
        self.assertEqual(len(sweep["sweep_results"]), 2)
        self.assertEqual(sweep["sweep_results"][0]["parameter_value"], 2)
        self.assertEqual(sweep["sweep_results"][1]["parameter_value"], 3)

    def test_low_battery_lifecycle(self):
        """Test autonomous low battery lifecycle: handoff, docking, charging, and recovery."""
        r1 = self.sim.robots["R1"]
        # Assign task to R1
        task = list(self.sim.tasks.values())[0]
        self.sim.assign_task(task.task_id, "R1")
        self.assertEqual(r1.current_task, task.task_id)

        # Inject low battery fault
        self.sim.fault_engine.inject_fault(FaultType.LOW_BATTERY, "R1", 0.0, 30.0)
        r1.battery = 15.0

        # Step simulation to trigger autonomous handoff
        self.sim.step(force=True)

        # R1 should have handed off task or transitioned to degraded/charging
        self.assertIn(r1.state, [RobotState.DEGRADED, RobotState.MOVING, RobotState.CHARGING])

        # Test charging directly at bay
        r1.position = (11, 0)
        r1.state = RobotState.CHARGING
        r1.battery = 50.0
        # Step simulation ticks
        for _ in range(50):
            self.sim.step(force=True)
            if r1.state == RobotState.IDLE:
                break
        self.assertGreater(r1.battery, 50.0)

    def test_network_jitter_and_reordering(self):
        """Test NetworkSimulator jitter perturbation, duplication, and reordering."""
        net = NetworkSimulator(seed=123)
        # Send 10 messages with jitter and duplication
        for i in range(10):
            net.send_message(
                sender="R1",
                recipient="COORDINATOR",
                payload={"index": i},
                current_time=0.0,
                latency=0.05,
                jitter=0.02,
                duplication_rate=0.5,
                reorder_rate=0.5,
            )
        self.assertEqual(net.total_sent, 10)
        metrics = net.get_network_metrics()
        self.assertGreaterEqual(metrics["messages_sent"], 10)
        self.assertIn("jitter_ms", metrics)
        self.assertIn("messages_duplicated", metrics)

    def test_decision_explainability(self):
        """Test that reassign_robot records candidate evaluations and explainable rationale."""
        self.sim.step(force=True)
        r1 = self.sim.robots["R1"]
        if not r1.current_task:
            task = list(self.sim.tasks.values())[0]
            self.sim.assign_task(task.task_id, "R1")

        res = self.sim.reassign_robot("R1")
        self.assertIn("decision_explanation", res)
        explanation = res["decision_explanation"]
        self.assertIsInstance(explanation, list)
        self.assertGreater(len(explanation), 0)

        # Ensure explanation contains required explainability metrics
        candidate_item = explanation[0]
        self.assertIn("robot_id", candidate_item)
        self.assertIn("battery", candidate_item)
        self.assertIn("decision", candidate_item)
        self.assertIn("reason", candidate_item)
        self.assertIn(candidate_item["decision"], ["SELECTED", "REJECTED", "ELIGIBLE"])

    def test_snapshot_determinism(self):
        """Test that restoring a snapshot and stepping produces identical state."""
        # 1. Step 10 times
        for _ in range(10):
            self.sim.step(force=True)

        # 2. Save snapshot
        snapshot = self.sim.save_snapshot()

        # 3. Step another 10 times and record positions
        pos_run_1 = {}
        for _ in range(10):
            self.sim.step(force=True)
        for rid, r in self.sim.robots.items():
            pos_run_1[rid] = r.position

        # 4. Restore snapshot
        self.sim.restore_snapshot(snapshot)

        # 5. Step 10 times again
        pos_run_2 = {}
        for _ in range(10):
            self.sim.step(force=True)
        for rid, r in self.sim.robots.items():
            pos_run_2[rid] = r.position

        # Positions must be deterministic
        self.assertEqual(pos_run_1, pos_run_2)
