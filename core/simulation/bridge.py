"""IPC Bridge for ResilientEdge Python Simulation Engine.
Allows Node.js host (server.ts) to execute the authoritative Python SimulationEngine
directly via stdio IPC when FastAPI is not running as a separate service.
"""
import sys
import os
import json
import time
import threading
from typing import Dict, Any
import uuid

# Ensure workspace root is in python path before importing project packages.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.auth import auth_service, AuthenticationError
from backend.database.factory import persistence
from backend.database.worker import PersistenceWorker

from core.simulation.engine import SimulationEngine
from core.models.fault import FaultType
from backend.database.sqlite_db import ResilientEdgeDatabase
from experiments.scenarios import SCENARIOS, run_scenario
from experiments.baseline import run_baseline_comparison

sim = SimulationEngine(seed=42, time_step=0.1)
db = ResilientEdgeDatabase()
persistence_worker = PersistenceWorker(persistence)
run_id = str(uuid.uuid4())
simulation_id = "resilientedge-local"

# Initialize default fleet and tasks
sim.reset(robot_count=3, task_count=6)
persistence_worker.submit("create_simulation", {"simulation_id": simulation_id, "name": "ResilientEdge", "status": "RUNNING", "config": {"seed": sim.seed, "time_step": sim.clock.time_step}})
persistence_worker.submit("create_simulation_run", {"run_id": run_id, "simulation_id": simulation_id, "name": "Simulation Run", "status": "RUNNING", "config": {"seed": sim.seed, "time_step": sim.clock.time_step}})

def persist_state_changes(previous: Dict[str, Any] | None, current: Dict[str, Any]) -> None:
    if previous is None:
        return
    now = current.get("timestamp", 0)
    prev_robots = {r.get("robot_id"): r for r in previous.get("robots", [])}
    for robot in current.get("robots", []):
        rid = robot.get("robot_id")
        old = prev_robots.get(rid, {})
        if old.get("state") != robot.get("state"):
            persistence_worker.submit("create_telemetry_event", {"run_id": run_id, "timestamp": now, "simulation_time": now, "event_type": "robot_state_changed", "robot_id": rid, "payload": {"from": old.get("state"), "to": robot.get("state")}})
    prev_tasks = {t.get("task_id"): t for t in previous.get("tasks", [])}
    for task in current.get("tasks", []):
        tid = task.get("task_id")
        old = prev_tasks.get(tid, {})
        if old.get("status") != task.get("status"):
            event = {"run_id": run_id, "timestamp": now, "simulation_time": now, "event_type": f"task_{str(task.get('status','changed')).lower()}", "task_id": tid, "payload": {"from": old.get("status"), "to": task.get("status"), "assigned_robot": task.get("assigned_robot")}}
            persistence_worker.submit("create_telemetry_event", event)
    prev_incidents = {i.get("incident_id") for i in previous.get("incidents", [])}
    for incident in current.get("incidents", []):
        if incident.get("incident_id") not in prev_incidents:
            persistence_worker.submit("create_incident", {**incident, "run_id": run_id})
            persistence_worker.submit("create_telemetry_event", {"run_id": run_id, "timestamp": now, "simulation_time": now, "event_type": "incident_created", "payload": incident})
            recovery_faults = {"TASK_REASSIGNED", "TASK_HANDOFF", "ROBOT_RECOVERED", "BATTERY_RECOVERED", "DEADLOCK_RECOVERED", "NETWORK_RESYNC"}
            if incident.get("fault") in recovery_faults or incident.get("state") in {"RECOVERY", "RESYNC"}:
                persistence_worker.submit("create_recovery_event", {
                    "event_id": f"rec_{incident.get('incident_id')}",
                    "run_id": run_id,
                    "timestamp": incident.get("timestamp", now),
                    "robot_id": incident.get("entity", "SYSTEM"),
                    "recovery_strategy": incident.get("fault", "RECOVERY"),
                    "status": "SUCCESS",
                    "details": {"message": incident.get("message", ""), "state": incident.get("state")},
                })
    if previous.get("clock", {}).get("is_paused") != current.get("clock", {}).get("is_paused"):
        event_type = "simulation_paused" if current.get("clock", {}).get("is_paused") else "simulation_resumed"
        persistence_worker.submit("create_telemetry_event", {"run_id": run_id, "timestamp": now, "simulation_time": now, "event_type": event_type, "payload": {"clock": current.get("clock", {})}})
    prev_net = previous.get("network", {})
    cur_net = current.get("network", {})
    if prev_net.get("is_partitioned") != cur_net.get("is_partitioned") or prev_net.get("packet_loss_rate") != cur_net.get("packet_loss_rate"):
        event_type = "network_degradation" if cur_net.get("is_partitioned") or cur_net.get("packet_loss_rate", 0) > 0.01 else "network_recovery"
        persistence_worker.submit("create_telemetry_event", {"run_id": run_id, "timestamp": now, "simulation_time": now, "event_type": event_type, "payload": cur_net})
        persistence_worker.submit("create_network_event", {"run_id": run_id, "timestamp": now, "event_type": event_type, "latency": cur_net.get("latency_ms", 0), "packet_loss": cur_net.get("packet_loss_rate", 0), "jitter": cur_net.get("jitter_ms", 0), "details": cur_net})

def send_msg(payload: Dict[str, Any]):
    try:
        sys.stdout.write(json.dumps(payload) + "\n")
        sys.stdout.flush()
    except Exception:
        pass

def handle_command(cmd: Dict[str, Any]):
    req_id = cmd.get("req_id")
    cmd_type = cmd.get("type", "")

    try:
        if cmd_type == "DATABASE_STATUS":
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": persistence.get_persistence_status()})
            return
        user = auth_service.authenticate_token(cmd.get("access_token"))
        cmd["_auth_user"] = {"id": user.id, "role": user.role, "email": user.email}
        permission_map = {
            "CLOCK": "simulation_control", "TASK": "task_dispatch", "TASK_ASSIGN": "task_dispatch", "TASK_START": "task_dispatch",
            "TASK_PAUSE": "task_dispatch", "TASK_RESUME": "task_dispatch", "TASK_COMPLETE": "task_dispatch", "TASK_FAIL": "task_dispatch", "TASK_CANCEL": "task_dispatch",
            "FAULT": "fault_injection", "CLEAR_FAULT": "fault_injection", "CLEAR_ALL_FAULTS": "fault_injection",
            "ROBOT_PAUSE": "recovery", "ROBOT_RESUME": "recovery", "ROBOT_RESET": "recovery", "ROBOT_REASSIGN": "recovery",
            "RUN_SCENARIO": "experiments", "RUN_EXPERIMENT": "experiments", "COMPARE_EXPERIMENT": "experiments", "RUN_MONTE_CARLO": "experiments", "RUN_PARAMETER_SWEEP": "experiments",
            "UPDATE_SETTINGS": "settings", "DATABASE_CLEAR": "database_admin", "RESTORE": "destructive",
        }
        required = permission_map.get(cmd_type)
        if required:
            from backend.api.permissions import role_allows
            if not role_allows(user.role, required):
                send_msg({"type": "RESPONSE", "req_id": req_id, "error": "Forbidden: insufficient role"})
                return
        if cmd_type == "AUTH_VALIDATE":
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": {"authenticated": True, "user_id": user.id, "role": user.role}})
            return
        if cmd_type == "AUTH_ME":
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": {"id": user.id, "email": user.email, "role": user.role, "full_name": user.full_name, "local": user.local}})
            return

        if cmd_type == "CLOCK":
            action = cmd.get("action", "").lower()
            scale = cmd.get("scale")
            if action == "pause":
                sim.clock.pause()
                persistence_worker.submit("create_telemetry_event", {"run_id": run_id, "timestamp": sim.clock.current_time, "simulation_time": sim.clock.current_time, "event_type": "simulation_paused", "payload": {}})
            elif action == "resume":
                sim.clock.resume()
                persistence_worker.submit("create_telemetry_event", {"run_id": run_id, "timestamp": sim.clock.current_time, "simulation_time": sim.clock.current_time, "event_type": "simulation_resumed", "payload": {}})
            elif action == "step":
                sim.clock.pause()
                sim.force_step()
                persistence_worker.submit("create_telemetry_event", {"run_id": run_id, "timestamp": sim.clock.current_time, "simulation_time": sim.clock.current_time, "event_type": "simulation_step", "payload": {}})
                send_msg({"type": "TELEMETRY", "data": sim.get_telemetry()})
            elif action == "reset":
                sim.reset(cmd.get("robot_count", 3), cmd.get("task_count", 6))
                persistence_worker.submit("create_telemetry_event", {"run_id": run_id, "timestamp": sim.clock.current_time, "simulation_time": sim.clock.current_time, "event_type": "simulation_reset", "payload": {}})
                send_msg({"type": "TELEMETRY", "data": sim.get_telemetry()})
            if scale is not None and scale > 0:
                sim.clock.time_scale = float(scale)
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": {
                "is_paused": sim.clock.is_paused,
                "time_scale": sim.clock.time_scale,
                "sim_time": round(sim.clock.current_time, 2)
            }})

        elif cmd_type == "TASK":
            tid = f"T{len(sim.tasks) + 1:02d}"
            task = sim.add_task(
                task_id=tid,
                pickup=tuple(cmd["pickup"]),
                delivery=tuple(cmd["delivery"]),
                priority=int(cmd.get("priority", 1)),
                deadline=float(cmd.get("deadline", 300.0)),
            )
            task_data = task.to_dict()
            persistence_worker.submit("create_task", {**task_data, "run_id": run_id})
            persistence_worker.submit("create_telemetry_event", {"run_id": run_id, "timestamp": sim.clock.current_time, "simulation_time": sim.clock.current_time, "event_type": "task_created", "task_id": task.task_id, "payload": task_data})
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": task_data})

        elif cmd_type == "FAULT":
            ftype = FaultType(cmd["fault_type"])
            fault = sim.fault_engine.inject_fault(
                fault_type=ftype,
                target=cmd["target"],
                start_time=sim.clock.current_time,
                duration=float(cmd.get("duration", 30.0)),
                parameters=cmd.get("parameters", {}),
            )
            fault_data = fault.to_dict()
            persistence_worker.submit("create_fault", {**fault_data, "run_id": run_id})
            persistence_worker.submit("create_telemetry_event", {"run_id": run_id, "timestamp": sim.clock.current_time, "simulation_time": sim.clock.current_time, "event_type": "fault_injected", "payload": fault_data})
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": fault_data})

        elif cmd_type == "CLEAR_FAULT":
            f = sim.fault_engine.clear_fault(cmd["fault_id"])
            if f:
                persistence_worker.submit("resolve_fault", cmd["fault_id"])
                persistence_worker.submit("create_telemetry_event", {"run_id": run_id, "timestamp": sim.clock.current_time, "simulation_time": sim.clock.current_time, "event_type": "fault_resolved", "payload": f.to_dict()})
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": {"status": "CLEARED" if f else "NOT_FOUND"}})

        elif cmd_type == "CLEAR_ALL_FAULTS":
            cleared = sim.fault_engine.clear_all()
            for r in sim.robots.values():
                if r.state == "FAILED":
                    r.state = "IDLE"
                    r.health = 1.0
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": {"cleared_count": len(cleared)}})

        elif cmd_type == "RUN_SCENARIO":
            sc_id = cmd.get("scenario_id")
            seed = int(cmd.get("seed", 42))
            if sc_id not in SCENARIOS:
                send_msg({"type": "RESPONSE", "req_id": req_id, "error": f"Scenario {sc_id} not found"})
                return
            sim.reset(robot_count=SCENARIOS[sc_id].robot_count, task_count=SCENARIOS[sc_id].task_count)
            SCENARIOS[sc_id].setup_fn(sim)
            res = run_scenario(sc_id, seed=seed)
            db.save_experiment({
                "experiment_id": f"exp_{sc_id}_{int(sim.clock.current_time)}",
                "scenario": sc_id,
                "seed": seed,
                "robot_count": len(res["robots"]),
                "task_count": res["metrics"]["total_tasks"],
                "start_time": 0.0,
                "end_time": res["duration"],
                "status": "COMPLETED",
                "metrics": res["metrics"],
            })
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": res})

        elif cmd_type == "GET_SCENARIOS":
            sc_list = [
                {
                    "id": s.scenario_id,
                    "name": s.name,
                    "description": s.description,
                    "robot_count": s.robot_count,
                    "task_count": s.task_count,
                    "duration": s.duration,
                }
                for s in SCENARIOS.values()
            ]
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": sc_list})

        elif cmd_type == "GET_EXPERIMENTS":
            exps = persistence.get_experiment_results(100)
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": exps})

        elif cmd_type == "GET_BASELINE":
            res = run_baseline_comparison(cmd.get("scenario_id", "S06"), seed=cmd.get("seed", sim.seed))
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": res})

        elif cmd_type == "RUN_EXPERIMENT":
            from experiments.runner import run_experiment
            res = run_experiment(
                scenario=cmd.get("scenario_id", "S01"),
                config=cmd.get("config", "resilient"),
                seed=int(cmd.get("seed", 42)),
                runs=int(cmd.get("runs", 1)),
                robots=cmd.get("robots"),
                tasks=cmd.get("tasks"),
                duration=cmd.get("duration"),
                output=cmd.get("output"),
                persist=True,
            )
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": res})

        elif cmd_type == "COMPARE_EXPERIMENT":
            from experiments.runner import compare
            res = compare(
                scenario=cmd.get("scenario_id", "S03"),
                seed=int(cmd.get("seed", 42)),
                runs=int(cmd.get("runs", 5)),
                robots=cmd.get("robots"),
                tasks=cmd.get("tasks"),
                duration=cmd.get("duration"),
            )
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": res})

        elif cmd_type == "RUN_MONTE_CARLO":
            from experiments.monte_carlo import run_monte_carlo
            res = run_monte_carlo(
                scenario_id=cmd.get("scenario_id", "S06"),
                num_runs=int(cmd.get("num_runs", 10)),
                start_seed=int(cmd.get("start_seed", 100)),
            )
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": res})

        elif cmd_type == "RUN_PARAMETER_SWEEP":
            from experiments.parameter_sweep import run_parameter_sweep
            res = run_parameter_sweep(
                param_type=cmd.get("param_type", "robot_count"),
                values=cmd.get("values"),
                seed=int(cmd.get("seed", 42)),
            )
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": res})

        elif cmd_type == "DATABASE_STATS":
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": persistence.get_stats()})

        elif cmd_type == "DATABASE_ROBOTS":
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": persistence.get_robots()})

        elif cmd_type == "DATABASE_TASKS":
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": persistence.get_tasks()})

        elif cmd_type == "DATABASE_INCIDENTS":
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": persistence.get_incidents(cmd.get("limit", 50))})

        elif cmd_type == "DATABASE_EVENTS":
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": persistence.get_decision_events(cmd.get("limit", 50))})

        elif cmd_type == "DATABASE_CLEAR":
            persistence.clear_all()
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": {"status": "CLEARED"}})


        elif cmd_type == "ROBOT_PAUSE":
            robot = sim.pause_robot(cmd["robot_id"])
            send_msg({"type": "TELEMETRY", "data": sim.get_telemetry()})
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": robot.to_dict()})

        elif cmd_type == "ROBOT_RESUME":
            robot = sim.resume_robot(cmd["robot_id"])
            send_msg({"type": "TELEMETRY", "data": sim.get_telemetry()})
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": robot.to_dict()})

        elif cmd_type == "ROBOT_RESET":
            robot = sim.reset_robot(cmd["robot_id"])
            send_msg({"type": "TELEMETRY", "data": sim.get_telemetry()})
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": robot.to_dict()})

        elif cmd_type == "ROBOT_REASSIGN":
            res = sim.reassign_robot(cmd["robot_id"])
            send_msg({"type": "TELEMETRY", "data": sim.get_telemetry()})
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": res})

        elif cmd_type == "TASK_REASSIGN":
            res = sim.reassign_task(cmd["task_id"])
            send_msg({"type": "TELEMETRY", "data": sim.get_telemetry()})
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": res})

        elif cmd_type == "TASK_ASSIGN":
            task = sim.assign_task(cmd["task_id"], cmd.get("robot_id"))
            send_msg({"type": "TELEMETRY", "data": sim.get_telemetry()})
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": task.to_dict()})

        elif cmd_type == "TASK_START":
            task = sim.start_task(cmd["task_id"])
            send_msg({"type": "TELEMETRY", "data": sim.get_telemetry()})
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": task.to_dict()})

        elif cmd_type == "TASK_PAUSE":
            task = sim.pause_task(cmd["task_id"])
            send_msg({"type": "TELEMETRY", "data": sim.get_telemetry()})
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": task.to_dict()})

        elif cmd_type == "TASK_RESUME":
            task = sim.resume_task(cmd["task_id"])
            send_msg({"type": "TELEMETRY", "data": sim.get_telemetry()})
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": task.to_dict()})

        elif cmd_type == "TASK_COMPLETE":
            task = sim.complete_task(cmd["task_id"])
            send_msg({"type": "TELEMETRY", "data": sim.get_telemetry()})
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": task.to_dict()})

        elif cmd_type == "TASK_FAIL":
            task = sim.fail_task(cmd["task_id"], cmd.get("reason", "Task failed"))
            send_msg({"type": "TELEMETRY", "data": sim.get_telemetry()})
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": task.to_dict()})

        elif cmd_type == "TASK_CANCEL":
            task = sim.cancel_task(cmd["task_id"])
            send_msg({"type": "TELEMETRY", "data": sim.get_telemetry()})
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": task.to_dict()})


        elif cmd_type == "UPDATE_SETTINGS":
            updated = sim.update_settings(cmd["settings"])
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": updated})

        elif cmd_type == "SNAPSHOT_SAVE":
            snap = sim.save_snapshot()
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": snap})

        elif cmd_type == "RESTORE":
            sim.restore_snapshot(cmd["snapshot"])
            send_msg({"type": "TELEMETRY", "data": sim.get_telemetry()})
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": {"status": "RESTORED", "sim_time": round(sim.clock.current_time, 2)}})

        elif cmd_type == "GET_TELEMETRY":
            send_msg({"type": "RESPONSE", "req_id": req_id, "data": sim.get_telemetry()})

        else:
            send_msg({"type": "RESPONSE", "req_id": req_id, "error": f"Unknown command: {cmd_type}"})

    except Exception as e:
        send_msg({"type": "RESPONSE", "req_id": req_id, "error": str(e)})

def stdin_listener():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            cmd = json.loads(line)
            handle_command(cmd)
        except Exception as e:
            pass

def main():
    # Start stdin listener thread
    t = threading.Thread(target=stdin_listener, daemon=True)
    t.start()

    # Initial telemetry emit
    initial = sim.get_telemetry()
    initial["persistence"] = persistence.get_persistence_status()
    persistence_worker.submit("sync_telemetry", initial, run_id=run_id)
    persistence_worker.submit("create_telemetry_event", {"run_id": run_id, "timestamp": initial.get("timestamp", 0), "simulation_time": initial.get("clock", {}).get("current_time", 0), "event_type": "simulation_started", "payload": initial})
    send_msg({"type": "TELEMETRY", "data": initial})

    last_step_time = time.time()
    previous_telemetry = initial
    while True:
        try:
            now = time.time()
            dt = now - last_step_time
            last_step_time = now

            telemetry = sim.step()
            persist_state_changes(previous_telemetry, telemetry)
            previous_telemetry = telemetry
            send_msg({"type": "TELEMETRY", "data": telemetry})

            # Sync to local transactional DB periodically
            if sim.clock.tick_count % 10 == 0:
                persistence_worker.submit("sync_telemetry", telemetry, run_id=run_id)

            # Sleep scaled by time_scale
            interval = sim.clock.time_step / max(0.1, sim.clock.time_scale)
            time.sleep(interval)
        except KeyboardInterrupt:
            persistence_worker.submit("update_simulation_run", run_id, {"status": "COMPLETED", "end_time": time.time(), "final_metrics": sim.get_telemetry().get("metrics", {})})
            break
        except Exception as e:
            time.sleep(0.1)

if __name__ == "__main__":
    main()
