"""Windows-friendly CLI for reproducible ResilientEdge Phase 3 experiments."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.runner import run_experiment, compare, execute_all_scenarios


def main() -> int:
    p=argparse.ArgumentParser(description="Run reproducible ResilientEdge experiments")
    p.add_argument("--scenario", help="Scenario ID, e.g. S03")
    p.add_argument("--all", action="store_true", help="Execute all catalog scenarios S01-S12")
    p.add_argument("--config", choices=["baseline","resilient"], default="resilient")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--robots", type=int)
    p.add_argument("--tasks", type=int)
    p.add_argument("--duration", type=float)
    p.add_argument("--output", default="results")
    p.add_argument("--compare", action="store_true", help="Run paired baseline vs resilient comparison")
    args=p.parse_args()
    if args.all:
        result = execute_all_scenarios(seed=args.seed, persist=True)
    elif not args.scenario:
        p.error("--scenario is required unless --all is used")
    elif args.compare:
        result=compare(args.scenario,args.seed,args.runs,robots=args.robots,tasks=args.tasks,duration=args.duration)
    else:
        result=run_experiment(args.scenario,args.config,args.seed,args.runs,args.robots,args.tasks,args.duration,args.output)
    print(json.dumps(result,indent=2,default=str))
    return 0 if result.get("status", "COMPLETED") != "FAILED" else 1

if __name__ == "__main__":
    raise SystemExit(main())
