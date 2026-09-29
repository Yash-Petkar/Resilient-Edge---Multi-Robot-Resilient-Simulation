"""Standalone runner for ResilientEdge core simulation."""
import time
import sys
import os

# Ensure workspace root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.simulation.engine import SimulationEngine
from core.models.fault import FaultType


def main():
    print("=" * 60)
    print("ResilientEdge Multi-Robot Simulation Engine (Standalone)")
    print("=" * 60)

    sim = SimulationEngine(seed=42, time_step=0.2)

    # Spawn 3 robots
    sim.add_robot("R1", (4, 0))
    sim.add_robot("R2", (8, 0))
    sim.add_robot("R3", (12, 0))

    # Add 6 tasks
    for i in range(1, 7):
        p = list(sim.world.pickup_stations.values())[(i - 1) % 4]
        d = list(sim.world.delivery_stations.values())[(i - 1) % 4]
        sim.add_task(f"T{i:02d}", p, d, priority=(i % 3) + 1)

    print(f"Initialized fleet: {list(sim.robots.keys())}")
    print(f"Queued tasks: {list(sim.tasks.keys())}")

    # Step loop for 100 ticks
    for tick in range(1, 101):
        # Inject R2 failure at t=4.0s
        if tick == 20:
            print("\n[CHAOS INJECTION] Injected ROBOT_FAILURE on R2...")
            sim.fault_engine.inject_fault(
                fault_type=FaultType.ROBOT_FAILURE,
                target="R2",
                start_time=sim.clock.current_time,
                duration=30.0,
            )

        telemetry = sim.step()

        if tick % 10 == 0:
            m = telemetry["metrics"]
            res = telemetry["resilience"]["current_state"]
            print(
                f"[t={telemetry['timestamp']:5.1f}s | Tick {tick:3d}] "
                f"Resilience: {res:14s} | "
                f"Completed: {m['completed_tasks']}/{m['total_tasks']} | "
                f"Conflicts: {m['conflict_count']} | "
                f"Msgs: {m['messages_sent']}"
            )

    print("\n" + "=" * 60)
    print("Simulation Complete. Final Metrics:")
    final_m = sim.get_telemetry()["metrics"]
    for k, v in final_m.items():
        print(f"  {k:26s}: {v}")
    print("=" * 60)


if __name__ == "__main__":
    main()
