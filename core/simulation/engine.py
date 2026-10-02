"""Core simulation engine for ResilientEdge multi-robot platform."""
import math
import random
import time
import ast
from typing import Dict, List, Optional, Tuple, Set, Any

from core.models.robot import Robot, RobotState, robot_home_position
from core.agents.robot_agent import RobotAgent, PeerState
from core.models.task import Task, TaskStatus
from core.models.fault import Fault, FaultType
from core.models.incident import Incident, IncidentSeverity
from core.simulation.world import WarehouseWorld
from core.simulation.clock import SimulationClock
from core.planning.astar import AStarPlanner
from core.coordination.allocator import TaskAllocator
from core.coordination.reservation_manager import ReservationManager
from core.coordination.conflict import ConflictDetector
from core.coordination.deadlock import DeadlockDetector
from core.faults.fault_engine import FaultEngine
from core.networking.network_sim import NetworkSimulator
from core.networking.adapter import LocalP2PCommunicationAdapter
from core.resilience.state_machine import ResilienceStateMachine, ResilienceState
from core.resilience.failure_detector import FailureDetector
from core.resilience.recovery_manager import RecoveryManager
from core.metrics.collector import MetricsCollector


class SimulationEngine:
    def __init__(self, seed: int = 42, time_step: float = 0.1, resilience_enabled: bool = True, dynamic_reassignment: bool = True, deadlock_recovery: bool = True, network_resync: bool = True, coordination_mode: str = "resilient"):
        self.seed = seed
        self.resilience_enabled = bool(resilience_enabled)
        self.dynamic_reassignment = bool(dynamic_reassignment)
        self.deadlock_recovery = bool(deadlock_recovery)
        self.network_resync = bool(network_resync)
        self.coordination_mode = coordination_mode
        if self.coordination_mode not in {"resilient", "stop_and_wait", "centralized"}:
            raise ValueError(f"unsupported coordination_mode: {coordination_mode}")
        self.random = random.Random(seed)
        self.clock = SimulationClock(time_step=time_step)
        self.world = WarehouseWorld()
        self.planner = AStarPlanner(allow_diagonal=False)
        self.allocator = TaskAllocator(seed=seed)
        self.reservation_mgr = ReservationManager()
        self.deadlock_detector = DeadlockDetector()
        self.fault_engine = FaultEngine()
        self.network_sim = NetworkSimulator(seed=seed)
        self.p2p = LocalP2PCommunicationAdapter(self.network_sim)
        self.state_machine = ResilienceStateMachine()
        self.failure_detector = FailureDetector(heartbeat_timeout=2.0)
        self.recovery_mgr = RecoveryManager(
            self.reservation_mgr, self.allocator, self.planner
        )
        self.metrics = MetricsCollector()

        # State storage. Robot objects are owned by independent RobotAgent instances.
        self.agents: Dict[str, RobotAgent] = {}
        # Backward-compatible read/write view retained while remaining simulation
        # subsystems migrate to the agent boundary in subsequent phases.
        self.robots: Dict[str, Robot] = {}
        self.tasks: Dict[str, Task] = {}
        self.incidents: List[Incident] = []
        self.action_timers: Dict[str, float] = {}  # robot_id -> time remaining for loading/unloading
        self.robot_route_traversed: Dict[str, float] = {}  # distance traversed for current task
        self.pending_reassignment_times: Dict[str, float] = {}
        # Phase 15 recovery context keyed by recovered task.
        self.recovery_contexts: Dict[str, Dict[str, float]] = {}
        self.charging_robots: Set[str] = set()
        # Phase 11: deterministic deadlock recovery backoff windows.
        self.deadlock_backoff_until: Dict[str, float] = {}

    def reset(self, robot_count: int = 3, task_count: int = 6):
        """Reset the simulation fleet, tasks, faults, clock, and metrics."""
        self.clock.reset()
        self.robots.clear()
        self.agents.clear()
        self.p2p.peers.clear()
        self.tasks.clear()
        self.incidents.clear()
        self.action_timers.clear()
        self.robot_route_traversed.clear()
        self.pending_reassignment_times.clear()
        self.recovery_contexts.clear()
        self.charging_robots.clear()
        self.deadlock_backoff_until.clear()
        self.fault_engine.clear_all()
        self.network_sim.reset()
        self.p2p.conditions = type(self.p2p.conditions)()
        self.world.reset_dynamic_state()
        self.state_machine = ResilienceStateMachine()
        self.reservation_mgr = ReservationManager()
        self.deadlock_detector = DeadlockDetector()
        self.failure_detector = FailureDetector(heartbeat_timeout=2.0)
        self.recovery_mgr = RecoveryManager(
            self.reservation_mgr, self.allocator, self.planner
        )
        self.metrics = MetricsCollector()

        # Re-add robots at deterministic walkable perimeter positions. The first
        # ten preserve the historical R1..R10 positions; additional robots use
        # the opposite perimeter row so arbitrary fleet sizes remain valid.
        starts = []
        for i in range(robot_count):
            if i < 10:
                starts.append((4 + i * 2, 0))
            else:
                x = 2 + ((i - 10) % 11) * 2
                y = self.world.height - 1
                starts.append((x, y))
        for i, start in enumerate(starts, start=1):
            self.add_robot(f"R{i}", start)

        # Re-add tasks
        p_stations = list(self.world.pickup_stations.values())
        d_stations = list(self.world.delivery_stations.values())
        for j in range(1, task_count + 1):
            p = p_stations[(j - 1) % len(p_stations)]
            d = d_stations[(j - 1) % len(d_stations)]
            self.add_task(f"T{j:02d}", p, d, priority=(j % 3) + 1)

        self._log_incident("SIM_RESET", "SYSTEM", IncidentSeverity.INFO, f"Simulation reset with {robot_count} robots and {task_count} tasks.")

    def save_snapshot(self) -> Dict[str, Any]:
        """Produce an authoritative and complete snapshot of all simulation state."""
        return {
            "version": "1.0",
            "seed": self.seed,
            "clock": self.clock.to_dict(),
            "world": self.world.to_dict(),
            "home_positions": {
                robot_id: list(robot_home_position(robot_id))
                for robot_id in self.robots
            },
            "robots": [r.to_dict() for r in self.robots.values()],
            "tasks": [t.to_dict() for t in self.tasks.values()],
            "faults": [f.to_dict() for f in self.fault_engine.active_faults.values()],
            "fault_engine": self.fault_engine.to_dict(),
            "resilience": self.state_machine.to_dict(),
            "metrics": self.metrics.snapshot_dict(),
            "random_state": repr(self.random.getstate()),
            "coordination_mode": self.coordination_mode,
            "network": self.network_sim.to_dict(),
            "reservations": [r.to_dict() for r in self.reservation_mgr.get_all_active()],
            "action_timers": dict(self.action_timers),
            "robot_route_traversed": dict(self.robot_route_traversed),
            "pending_reassignment_times": dict(self.pending_reassignment_times),
            "recovery_contexts": {k: dict(v) for k, v in self.recovery_contexts.items()},
            "charging_robots": sorted(self.charging_robots),
            "deadlock_backoff_until": dict(self.deadlock_backoff_until),
            "deadlock_graph": self.deadlock_detector.graph_snapshot(),
            "deadlock_cycles": [list(c) for c in self.deadlock_detector.last_cycles],
            "incidents": [inc.to_dict() for inc in self.incidents[-50:]],
            "failure_detector": self.failure_detector.snapshot(),
        }


    def restore_snapshot(self, snapshot: Dict[str, Any]):
        """Restore an authoritative snapshot; invalid state fails loudly."""
        if not isinstance(snapshot, dict):
            raise ValueError("snapshot must be a dictionary")
        try:
            c_data = snapshot["clock"]
            self.clock.current_time = float(c_data["current_time"])
            self.clock.tick_count = int(c_data["tick_count"])
            self.clock.is_paused = bool(c_data.get("is_paused", False))
            self.clock.time_step = float(c_data.get("time_step", self.clock.time_step))
            self.clock.time_scale = float(c_data.get("time_scale", self.clock.time_scale))

            self.robots.clear()
            self.agents.clear()
            for r_data in snapshot["robots"]:
                robot_id = str(r_data["robot_id"])
                home = tuple(r_data.get("home_position", snapshot.get("home_positions", {}).get(robot_id, robot_home_position(robot_id))))
                restored_robot = Robot(
                    robot_id=robot_id, position=tuple(r_data["position"]), home_position=home,
                    orientation=float(r_data.get("orientation", 0.0)), velocity=float(r_data.get("velocity", 1.0)),
                    state=RobotState(r_data.get("state", "IDLE")), battery=float(r_data.get("battery", 100.0)),
                    health=float(r_data.get("health", 1.0)), current_task=r_data.get("current_task"),
                    current_path=[tuple(p) for p in r_data.get("current_path", [])],
                    path_progress=int(r_data.get("path_progress", 0)), network_status=r_data.get("network_status", "CONNECTED"),
                    last_heartbeat=float(r_data.get("last_heartbeat", self.clock.current_time)),
                    failed_at=(float(r_data["failed_at"]) if r_data.get("failed_at") is not None else None),
                )
                self.agents[robot_id] = RobotAgent(robot=restored_robot, planner=AStarPlanner(allow_diagonal=False), priority=1)
                self.agents[robot_id].attach_communication_adapter(self.p2p)
                self.robots[robot_id] = self.agents[robot_id].robot

            self.tasks.clear()
            for t_data in snapshot["tasks"]:
                self.tasks[t_data["task_id"]] = Task(
                    task_id=t_data["task_id"], pickup=tuple(t_data["pickup"]), delivery=tuple(t_data["delivery"]),
                    priority=int(t_data.get("priority", 1)), deadline=float(t_data.get("deadline", 300.0)),
                    status=TaskStatus(t_data.get("status", "AVAILABLE")), assigned_robot=t_data.get("assigned_robot"),
                    creation_time=float(t_data.get("creation_time", 0.0)),
                    start_time=float(t_data["start_time"]) if t_data.get("start_time") is not None else None,
                    completion_time=float(t_data["completion_time"]) if t_data.get("completion_time") is not None else None,
                    phase=t_data.get("phase", "PICKUP"),
                )

            w_data = snapshot["world"]
            if "width" in w_data: self.world.width = int(w_data["width"])
            if "height" in w_data: self.world.height = int(w_data["height"])
            if "shelves" in w_data: self.world.shelves = {tuple(c) for c in w_data["shelves"]}
            self.world.blocked_aisles = {tuple(c) for c in w_data.get("blocked_aisles", [])}
            self.world.dynamic_obstacles = {tuple(c) for c in w_data.get("dynamic_obstacles", [])}
            if "pickup_stations" in w_data: self.world.pickup_stations = {k: tuple(v) for k,v in w_data["pickup_stations"].items()}
            if "delivery_stations" in w_data: self.world.delivery_stations = {k: tuple(v) for k,v in w_data["delivery_stations"].items()}
            if "charging_bays" in w_data: self.world.charging_bays = {k: tuple(v) for k,v in w_data["charging_bays"].items()}

            fault_snapshot = snapshot.get("fault_engine", snapshot.get("faults", {}))
            # Backward-compatible restore for Phase 1-11 snapshots that stored
            # a flat list of active faults.
            if isinstance(fault_snapshot, list):
                fault_snapshot = {"faults": fault_snapshot}
            self.fault_engine.restore(fault_snapshot)

            self.state_machine.restore_snapshot(snapshot.get("resilience", {}), self.clock.current_time)
            self.action_timers = {k: float(v) for k,v in snapshot.get("action_timers", {}).items()}
            self.robot_route_traversed = {k: float(v) for k,v in snapshot.get("robot_route_traversed", {}).items()}
            self.pending_reassignment_times = {k: float(v) for k,v in snapshot.get("pending_reassignment_times", {}).items()}
            self.recovery_contexts = {str(k): {str(kk): float(vv) for kk, vv in val.items()} for k, val in snapshot.get("recovery_contexts", {}).items()}
            self.charging_robots = set(snapshot.get("charging_robots", []))
            self.deadlock_backoff_until = {
                str(k): float(v) for k, v in snapshot.get("deadlock_backoff_until", {}).items()
            }

            self.reservation_mgr.restore(snapshot.get("reservations", []))
            # Reconstruct the detector graph from serialized state when present.
            graph = snapshot.get("deadlock_graph", {})
            if isinstance(graph, dict):
                self.deadlock_detector.build_graph(graph)
            self.deadlock_detector.last_cycles = [list(c) for c in snapshot.get("deadlock_cycles", [])]
            self.network_sim.from_dict(snapshot.get("network", {}))
            self.metrics.restore_snapshot(snapshot.get("metrics", {}))
            if snapshot.get("random_state"):
                self.random.setstate(ast.literal_eval(snapshot["random_state"]))
            self.coordination_mode = snapshot.get("coordination_mode", self.coordination_mode)
            if self.coordination_mode not in {"resilient", "stop_and_wait", "centralized"}:
                raise ValueError(f"invalid coordination_mode in snapshot: {self.coordination_mode}")
            # Reconstruct incidents from their serialized representation.
            self.incidents = []
            for inc_data in snapshot.get("incidents", []):
                inc = Incident(
                    incident_id=inc_data["incident_id"], timestamp=float(inc_data["timestamp"]), entity=inc_data["entity"],
                    fault=inc_data["fault"], severity=IncidentSeverity(inc_data["severity"]), state=inc_data.get("state", "NORMAL"), message=inc_data["message"]
                )
                for attr in ("fault_time", "detection_time", "detection_latency", "resolved_time"):
                    if attr in inc_data:
                        setattr(inc, attr, float(inc_data[attr]))
                if "lifecycle" in inc_data:
                    inc.lifecycle = str(inc_data["lifecycle"])
                self.incidents.append(inc)
            self.failure_detector.restore(snapshot.get("failure_detector", {}))
            # Rebind active network incident IDs to the restored authoritative objects.
            restored_by_id = {inc.incident_id: inc for inc in self.incidents}
            self.failure_detector._incident_objects = {
                iid: restored_by_id[iid]
                for iid in self.failure_detector._active_network_incidents.values()
                if iid in restored_by_id
            }
        except (KeyError, TypeError, ValueError, SyntaxError) as exc:
            raise ValueError(f"snapshot restoration failed: {exc}") from exc

        self._log_incident("SNAPSHOT_RESTORE", "SYSTEM", IncidentSeverity.INFO, "Simulation state restored from snapshot.")


    def pause_robot(self, robot_id: str) -> Robot:
        """Pause a specific robot. Stops its movement without failing it or creating faults."""
        if robot_id not in self.robots:
            raise ValueError(f"Robot {robot_id} not found")
        robot = self.robots[robot_id]
        if robot.state == RobotState.FAILED:
            raise ValueError(f"Cannot pause robot {robot_id} because it is FAILED")
        robot.state = RobotState.PAUSED
        self._log_incident("ROBOT_PAUSED", robot_id, IncidentSeverity.INFO, f"Robot {robot_id} paused by operator.")
        return robot

    def resume_robot(self, robot_id: str) -> Robot:
        """Resume a specific robot without clearing unrelated faults."""
        if robot_id not in self.robots:
            raise ValueError(f"Robot {robot_id} not found")
        robot = self.robots[robot_id]
        if robot.state == RobotState.PAUSED:
            if robot.current_task and robot.current_task in self.tasks:
                robot.state = RobotState.PLANNING
            else:
                robot.state = RobotState.IDLE
            self._log_incident("ROBOT_RESUMED", robot_id, IncidentSeverity.INFO, f"Robot {robot_id} resumed operation.")
        elif robot.state == RobotState.FAILED:
            f_to_clear = [fid for fid, f in self.fault_engine.active_faults.items() if f.target == robot_id]
            for fid in f_to_clear:
                self.fault_engine.clear_fault(fid)
            robot.position = robot_home_position(robot_id)
            robot.health = 1.0
            robot.state = RobotState.IDLE
            self._log_incident("ROBOT_RECOVERED", robot_id, IncidentSeverity.INFO, f"Robot {robot_id} recovered from failure.")
        elif robot.state == RobotState.WAITING:
            robot.state = RobotState.PLANNING
        return robot

    def reset_robot(self, robot_id: str) -> Robot:
        """Reset only the specified robot without clearing unrelated faults or tasks."""
        if robot_id not in self.robots:
            raise ValueError(f"Robot {robot_id} not found")
        robot = self.robots[robot_id]

        # Release reservations owned by this robot
        self.reservation_mgr.release_all_for_robot(robot_id)

        # If robot had an active task, release task back to AVAILABLE
        if robot.current_task and robot.current_task in self.tasks:
            task = self.tasks[robot.current_task]
            if task.assigned_robot == robot_id:
                task.assigned_robot = None
                task.status = TaskStatus.AVAILABLE
                task.phase = "PICKUP"
                task.start_time = None

        # Clear only faults targeting this specific robot
        f_to_clear = [fid for fid, f in self.fault_engine.active_faults.items() if f.target == robot_id]
        for fid in f_to_clear:
            self.fault_engine.clear_fault(fid)

        home_pos = robot_home_position(robot_id)

        robot.position = home_pos
        robot.home_position = home_pos
        robot.orientation = 0.0
        robot.velocity = 1.0
        robot.state = RobotState.IDLE
        robot.battery = 100.0
        robot.health = 1.0
        robot.current_task = None
        robot.current_path = []
        robot.path_progress = 0
        robot.network_status = "CONNECTED"
        robot.last_heartbeat = self.clock.current_time
        self.robot_route_traversed[robot_id] = 0.0
        if robot_id in self.action_timers:
            del self.action_timers[robot_id]

        self._log_incident("ROBOT_RESET", robot_id, IncidentSeverity.INFO, f"Robot {robot_id} reset to home position {home_pos}.")
        return robot

    def reassign_task(self, task_id: str) -> Dict[str, Any]:
        """Atomically reassign a task to another eligible robot.

        The previous implementation detached the source robot before checking whether
        a replacement existed. A failed reassignment could therefore silently leave
        the task unassigned. This method evaluates candidates first and only mutates
        the authoritative state after a replacement is selected.

        It also supports recovery of tasks that have already been released to
        AVAILABLE by the failure-recovery path, which is important after a robot
        fault has cleared its ``current_task`` reference.
        """
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")

        task = self.tasks[task_id]
        previous_robot_id = task.assigned_robot
        source_robot = self.robots.get(previous_robot_id) if previous_robot_id else None

        if task.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.FAILED):
            raise ValueError(f"Cannot reassign task {task_id} with terminal status {task.status.value}")

        # A task can be explicitly requeued by failure recovery. In that case there
        # is no source robot to detach; the allocator-style handoff is still valid.
        target_station = task.pickup if task.phase in ("PICKUP", "NAVIGATE_PICKUP") else task.delivery

        candidate_evaluations = []
        for cand in self.robots.values():
            dist = abs(cand.position[0] - target_station[0]) + abs(cand.position[1] - target_station[1])
            is_self = cand.robot_id == previous_robot_id
            is_busy = bool(cand.current_task and cand.robot_id != previous_robot_id)
            is_failed = cand.state == RobotState.FAILED or cand.health <= 0.0
            is_low_battery = cand.battery < 20.0
            is_degraded = cand.health < 0.8
            is_unavailable_state = cand.state not in (RobotState.IDLE, RobotState.DEGRADED)
            is_disconnected = cand.network_status in ("DISCONNECTED", "PARTITIONED")

            if is_self:
                decision = "REJECTED"
                reason = "Originating robot undergoing reassignment"
                p_len = 0
                p_feas = False
            elif is_failed:
                decision = "REJECTED"
                reason = "Hardware failure state"
                p_len = 0
                p_feas = False
            elif is_busy:
                decision = "REJECTED"
                reason = f"Busy with task {cand.current_task}"
                p_len = 0
                p_feas = False
            elif is_unavailable_state:
                decision = "REJECTED"
                reason = f"Robot state {cand.state.value} is not available for reassignment"
                p_len = 0
                p_feas = False
            elif is_low_battery:
                decision = "REJECTED"
                reason = f"Insufficient battery ({cand.battery:.1f}% < 20%)"
                p_len = 0
                p_feas = False
            elif is_degraded:
                decision = "REJECTED"
                reason = f"Degraded health ({cand.health*100:.0f}%)"
                p_len = 0
                p_feas = False
            elif is_disconnected:
                decision = "REJECTED"
                reason = f"Network status {cand.network_status}"
                p_len = 0
                p_feas = False
            else:
                test_path = self.agents[cand.robot_id].plan_for_goal(
                    target_station, self.world.all_obstacles, self.world.width, self.world.height,
                    timestamp=self.clock.current_time, intent="REASSIGNMENT_EVALUATION"
                )
                if test_path:
                    decision = "ELIGIBLE"
                    reason = "Available with feasible path"
                    p_len = len(test_path)
                    p_feas = True
                else:
                    decision = "REJECTED"
                    reason = "Path blocked / infeasible"
                    p_len = 0
                    p_feas = False

            candidate_evaluations.append({
                "robot_id": cand.robot_id,
                "battery": round(cand.battery, 1),
                "health": round(cand.health, 2),
                "distance": dist,
                "path_length": p_len,
                "path_feasible": p_feas,
                "connectivity": cand.network_status,
                "decision": decision,
                "reason": reason,
            })

        eligible = [c for c in candidate_evaluations if c["decision"] == "ELIGIBLE"]
        if not eligible:
            # IMPORTANT: leave the existing assignment untouched. The previous
            # implementation corrupted state on a failed manual reassignment.
            return {
                "status": "NO_ELIGIBLE_ROBOT",
                "error": "No eligible replacement robot available with a feasible path",
                "task_id": task.task_id,
                "previous_robot": previous_robot_id,
                "decision_explanation": candidate_evaluations,
            }

        eligible.sort(key=lambda c: (c["path_length"], c["distance"], -c["battery"], c["robot_id"]))
        best_id = eligible[0]["robot_id"]
        selected_replacement = self.robots[best_id]
        candidate_path = self.agents[best_id].plan_for_goal(
            target_station, self.world.all_obstacles, self.world.width, self.world.height,
            timestamp=self.clock.current_time, intent="REASSIGNMENT"
        )
        if not candidate_path:
            # Defensive guard against a world change between evaluation and commit.
            return {
                "status": "NO_ELIGIBLE_ROBOT",
                "error": "Replacement path became infeasible before reassignment",
                "task_id": task.task_id,
                "previous_robot": previous_robot_id,
                "decision_explanation": candidate_evaluations,
            }

        for c in candidate_evaluations:
            if c["robot_id"] == best_id:
                c["decision"] = "SELECTED"
                c["reason"] = "Optimal candidate: shortest feasible path and highest reserve energy"

        # Commit the handoff atomically after a valid replacement has been found.
        if source_robot and source_robot.current_task == task.task_id:
            source_robot.current_task = None
            if source_robot.state in (RobotState.PLANNING, RobotState.MOVING, RobotState.WAITING, RobotState.TASK_EXECUTION, RobotState.RECOVERING):
                source_robot.state = RobotState.IDLE
            source_robot.current_path = []
            source_robot.path_progress = 0
            self.robot_route_traversed[source_robot.robot_id] = 0.0
            self.reservation_mgr.release_all_for_robot(source_robot.robot_id)

        task.assigned_robot = selected_replacement.robot_id
        task.status = TaskStatus.REASSIGNED
        task.start_time = self.clock.current_time
        selected_replacement.current_task = task.task_id
        selected_replacement.state = RobotState.PLANNING
        selected_replacement.current_path = candidate_path
        selected_replacement.path_progress = 0
        self.robot_route_traversed[selected_replacement.robot_id] = 0.0

        self.metrics.task_reassignments += 1
        if task.task_id in self.recovery_contexts:
            ctx = self.recovery_contexts[task.task_id]
            ctx["replan_time"] = float(self.clock.current_time)
            if "replan_recorded" not in ctx:
                ctx["replan_recorded"] = 1.0
                self.metrics.record_recovery_replanning(max(0.0, self.clock.current_time - ctx["reassignment_time"]))
        self.pending_reassignment_times.pop(task.task_id, None)
        self._log_incident(
            "TASK_REASSIGNED",
            selected_replacement.robot_id,
            IncidentSeverity.WARNING,
            f"Task {task.task_id} successfully reassigned from {previous_robot_id or 'QUEUE'} to {selected_replacement.robot_id}.",
        )

        return {
            "status": "REASSIGNED",
            "task_id": task.task_id,
            "previous_robot": previous_robot_id,
            "new_robot": selected_replacement.robot_id,
            "decision_explanation": candidate_evaluations,
        }

    def reassign_robot(self, robot_id: str) -> Dict[str, Any]:
        """Reassign the active task owned by ``robot_id``.

        Kept as the robot-level compatibility API used by the existing UI and
        recovery code. The task-level implementation above is authoritative.
        """
        if robot_id not in self.robots:
            raise ValueError(f"Robot {robot_id} not found")
        robot = self.robots[robot_id]
        if not robot.current_task or robot.current_task not in self.tasks:
            raise ValueError(f"Robot {robot_id} has no active task to reassign")
        return self.reassign_task(robot.current_task)

    def assign_task(self, task_id: str, robot_id: Optional[str] = None) -> Task:
        """Explicitly assign task to a specific or best available robot."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        task = self.tasks[task_id]

        if task.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
            raise ValueError(f"Cannot assign task {task_id} with terminal status {task.status.value}")

        target_robot = None
        if robot_id:
            if robot_id not in self.robots:
                raise ValueError(f"Robot {robot_id} not found")
            cand = self.robots[robot_id]
            if cand.state not in (RobotState.IDLE, RobotState.WAITING):
                raise ValueError(f"Robot {robot_id} is not available (state: {cand.state.value})")
            target_robot = cand
        else:
            allocation = self.allocator.allocate_next_task([task], self.robots, self.clock.current_time)
            if allocation:
                target_robot = allocation[1]

        if not target_robot:
            raise ValueError("No available robot eligible for assignment")

        # If previously assigned to another robot, unassign it cleanly
        if task.assigned_robot and task.assigned_robot in self.robots and task.assigned_robot != target_robot.robot_id:
            prev_robot = self.robots[task.assigned_robot]
            if prev_robot.current_task == task_id:
                prev_robot.current_task = None
                if prev_robot.state != RobotState.FAILED:
                    prev_robot.state = RobotState.IDLE
                prev_robot.current_path = []
                self.reservation_mgr.release_all_for_robot(prev_robot.robot_id)

        task.status = TaskStatus.ASSIGNED
        task.assigned_robot = target_robot.robot_id
        task.start_time = self.clock.current_time
        task.phase = "PICKUP"
        target_robot.current_task = task.task_id
        target_robot.state = RobotState.PLANNING
        self.robot_route_traversed[target_robot.robot_id] = 0.0

        self._log_incident("TASK_ASSIGNED", target_robot.robot_id, IncidentSeverity.INFO, f"Task {task.task_id} assigned to {target_robot.robot_id}.")
        return task

    def start_task(self, task_id: str) -> Task:
        """Start task execution."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        task = self.tasks[task_id]
        if task.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.FAILED):
            raise ValueError(f"Cannot start task {task_id} with status {task.status.value}")
        if not task.assigned_robot:
            self.assign_task(task_id)
        task.status = TaskStatus.IN_PROGRESS
        if not task.start_time:
            task.start_time = self.clock.current_time
        if task.assigned_robot and task.assigned_robot in self.robots:
            robot = self.robots[task.assigned_robot]
            if robot.state in (RobotState.IDLE, RobotState.WAITING):
                robot.state = RobotState.PLANNING
        self._log_incident("TASK_STARTED", task.assigned_robot or "SYSTEM", IncidentSeverity.INFO, f"Task {task_id} started.")
        return task

    def pause_task(self, task_id: str) -> Task:
        """Pause a task (set to BLOCKED) and set assigned robot to WAITING."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        task = self.tasks[task_id]
        if task.status not in (TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS):
            raise ValueError(f"Cannot pause task {task_id} with status {task.status.value}")
        task.status = TaskStatus.BLOCKED
        if task.assigned_robot and task.assigned_robot in self.robots:
            robot = self.robots[task.assigned_robot]
            if robot.state not in (RobotState.FAILED, RobotState.PAUSED):
                robot.state = RobotState.WAITING
        self._log_incident("TASK_PAUSED", task.assigned_robot or "SYSTEM", IncidentSeverity.INFO, f"Task {task_id} paused (BLOCKED).")
        return task

    def resume_task(self, task_id: str) -> Task:
        """Resume a blocked task."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        task = self.tasks[task_id]
        if task.status != TaskStatus.BLOCKED:
            raise ValueError(f"Cannot resume task {task_id} because it is not BLOCKED (status: {task.status.value})")
        task.status = TaskStatus.IN_PROGRESS
        if task.assigned_robot and task.assigned_robot in self.robots:
            robot = self.robots[task.assigned_robot]
            if robot.state not in (RobotState.FAILED, RobotState.PAUSED):
                robot.state = RobotState.PLANNING
        self._log_incident("TASK_RESUMED", task.assigned_robot or "SYSTEM", IncidentSeverity.INFO, f"Task {task_id} resumed.")
        return task

    def complete_task(self, task_id: str) -> Task:
        """Mark task as COMPLETED and release assigned robot."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        task = self.tasks[task_id]
        if task.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
            raise ValueError(f"Task {task_id} is already in terminal state {task.status.value}")
        task.status = TaskStatus.COMPLETED
        task.completion_time = self.clock.current_time
        task.phase = "COMPLETED"
        if task.assigned_robot and task.assigned_robot in self.robots:
            robot = self.robots[task.assigned_robot]
            if robot.current_task == task_id:
                robot.current_task = None
                if robot.state != RobotState.FAILED:
                    robot.state = RobotState.IDLE
                robot.current_path = []
                self.reservation_mgr.release_all_for_robot(robot.robot_id)
        self._log_incident("TASK_COMPLETED", task.assigned_robot or "SYSTEM", IncidentSeverity.INFO, f"Task {task_id} marked COMPLETED.")
        return task

    def fail_task(self, task_id: str, reason: str = "Task failed") -> Task:
        """Mark task as FAILED and release assigned robot."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        task = self.tasks[task_id]
        task.status = TaskStatus.FAILED
        task.completion_time = self.clock.current_time
        if task.assigned_robot and task.assigned_robot in self.robots:
            robot = self.robots[task.assigned_robot]
            if robot.current_task == task_id:
                robot.current_task = None
                if robot.state != RobotState.FAILED:
                    robot.state = RobotState.IDLE
                robot.current_path = []
                self.reservation_mgr.release_all_for_robot(robot.robot_id)
        self._log_incident("TASK_FAILED", task.assigned_robot or "SYSTEM", IncidentSeverity.WARNING, f"Task {task_id} FAILED: {reason}")
        return task

    def cancel_task(self, task_id: str) -> Task:
        """Cancel a task and release assigned robot and reservations."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        task = self.tasks[task_id]
        if task.assigned_robot and task.assigned_robot in self.robots:
            robot = self.robots[task.assigned_robot]
            if robot.current_task == task_id:
                robot.current_task = None
                if robot.state != RobotState.FAILED:
                    robot.state = RobotState.IDLE
                robot.current_path = []
                robot.path_progress = 0
                self.reservation_mgr.release_all_for_robot(robot.robot_id)

        task.status = TaskStatus.CANCELLED
        task.completion_time = self.clock.current_time
        self._log_incident("TASK_CANCELLED", task_id, IncidentSeverity.WARNING, f"Task {task_id} cancelled.")
        return task


    def update_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and apply simulation settings."""
        time_step = settings.get("time_step")
        if time_step is not None:
            time_step = float(time_step)
            if time_step <= 0 or time_step > 5.0:
                raise ValueError("time_step must be between 0.01 and 5.0")
            self.clock.time_step = time_step

        time_scale = settings.get("time_scale")
        if time_scale is not None:
            time_scale = float(time_scale)
            if time_scale <= 0 or time_scale > 20.0:
                raise ValueError("time_scale must be between 0.1 and 20.0")
            self.clock.time_scale = time_scale

        telemetry_interval = settings.get("telemetry_interval")
        if telemetry_interval is not None:
            telemetry_interval = float(telemetry_interval)
            if telemetry_interval <= 0 or telemetry_interval > 10.0:
                raise ValueError("telemetry_interval must be between 0.05 and 10.0")

        robot_count = settings.get("default_robot_count")
        if robot_count is not None:
            robot_count = int(robot_count)
            if robot_count < 1 or robot_count > 10:
                raise ValueError("default_robot_count must be between 1 and 10")

        seed = settings.get("seed")
        if seed is not None:
            self.seed = int(seed)
            self.random = random.Random(self.seed)

        return {
            "time_step": self.clock.time_step,
            "time_scale": self.clock.time_scale,
            "seed": self.seed,
            "telemetry_interval": telemetry_interval or 0.1,
            "default_robot_count": robot_count or len(self.robots),
            "log_level": settings.get("log_level", "INFO"),
        }

    def add_robot(self, robot_id: str, start_pos: Optional[Tuple[int, int]] = None) -> Robot:
        """Add a robot to the simulation fleet."""
        robot = Robot(
            robot_id=robot_id,
            position=start_pos if start_pos is not None else robot_home_position(robot_id),
            orientation=0.0,
            velocity=1.0,
            state=RobotState.IDLE,
            battery=100.0,
            health=1.0,
            last_heartbeat=self.clock.current_time,
        )
        agent = RobotAgent(robot=robot, planner=AStarPlanner(allow_diagonal=False), priority=1)
        agent.attach_communication_adapter(self.p2p)
        self.agents[robot_id] = agent
        self.robots[robot_id] = agent.robot
        self.robot_route_traversed[robot_id] = 0.0
        return agent.robot

    def add_task(
        self,
        task_id: str,
        pickup: Tuple[int, int],
        delivery: Tuple[int, int],
        priority: int = 1,
        deadline: float = 300.0,
    ) -> Task:
        """Add a task to the queue."""
        task = Task(
            task_id=task_id,
            pickup=pickup,
            delivery=delivery,
            priority=priority,
            deadline=deadline,
            status=TaskStatus.AVAILABLE,
            creation_time=self.clock.current_time,
        )
        self.tasks[task_id] = task
        return task

    def force_step(self) -> Dict[str, Any]:
        """Advance exactly one simulation timestep even while paused."""
        return self.step(force=True)

    def _reserve_path(self, robot_id: str, path: List[Tuple[int, int]], path_progress: int, current_time: float, priority: int) -> bool:
        """Reserve future cells and directed edges using the simulation timestep."""
        self.reservation_mgr.release_all_for_robot(robot_id)
        previous = path[path_progress] if path and path_progress < len(path) else None
        if previous is None:
            return False
        dt = self.clock.time_step
        for offset, cell in enumerate(path[path_progress + 1:path_progress + 9], start=1):
            start_t = current_time + (offset - 1) * dt
            end_t = start_t + dt * 1.05
            if self.reservation_mgr.request_cell_reservation(robot_id, cell, start_t, end_t, priority) is None:
                self.reservation_mgr.release_all_for_robot(robot_id)
                return False
            if self.reservation_mgr.request_edge_reservation(robot_id, previous, cell, start_t, end_t, priority) is None:
                self.reservation_mgr.release_all_for_robot(robot_id)
                return False
            previous = cell
        return True

    def _movement_is_safe(self, robot_id: str, current: Tuple[int, int], next_pos: Tuple[int, int], current_time: float) -> bool:
        """Enforce reservations and direct occupancy/edge-swap safety at execution time."""
        if not self.world.is_walkable(next_pos):
            return False
        charging_priority = self.robots[robot_id].current_task is None and self.robots[robot_id].battery <= 20.0

        # Phase 19 Baseline B: a deliberately simple centralized coordination
        # policy. One global movement lock is granted to the lowest-ID robot
        # currently executing a route. This is an actual behavioral baseline,
        # not a post-hoc metric adjustment. ResilientEdge and Stop/Wait retain
        # their existing movement policies.
        if self.coordination_mode == "centralized" and not charging_priority:
            active = sorted(
                r.robot_id for r in self.robots.values()
                if r.robot_id != robot_id
                and r.state in (RobotState.MOVING, RobotState.LOCAL_AUTONOMY)
                and r.current_path
            )
            if active and active[0] < robot_id:
                return False

        if self.coordination_mode != "stop_and_wait" and not charging_priority:
            arrival = current_time + self.clock.time_step
            if self.reservation_mgr.is_cell_reserved(next_pos, arrival, exclude_robot=robot_id):
                return False
            if self.reservation_mgr.is_edge_reserved(current, next_pos, arrival, exclude_robot=robot_id):
                return False
        for other in self.robots.values():
            if other.robot_id == robot_id or other.state == RobotState.FAILED:
                continue
            if other.position == next_pos:
                return False
            if other.current_path and other.path_progress < len(other.current_path) - 1:
                other_next = other.current_path[other.path_progress + 1]
                if other_next == next_pos:
                    return False
                if other.position == next_pos and other_next == current:
                    return False
                if other_next == current and other.position == next_pos:
                    return False
        return True

    def step(self, force: bool = False) -> Dict[str, Any]:
        """
        Executes one full simulation tick:
        1. update_clock()
        2. update_faults()
        3. update_network()
        4. process_messages()
        5. update_tasks()
        6. update_robot_states()
        7. plan_and_replan()
        8. process_reservations()
        9. detect_conflicts()
        10. detect_failures()
        11. execute_recovery()
        12. move_robots()
        13. collect_metrics()
        14. publish_telemetry()
        """
        if self.clock.is_paused and not force:
            return self.get_telemetry()

        current_time = self.clock.force_step() if force else self.clock.tick()
        dt = self.clock.time_step

        # 1. Update Faults.  Faults are simulation inputs, not UI-only events.
        expired_faults = self.fault_engine.update(current_time)
        for activated in self.fault_engine.last_activated:
            self._log_incident(
                "FAULT_ACTIVATED",
                activated.target,
                IncidentSeverity.WARNING,
                f"Fault {activated.fault_type.value} on {activated.target} became active.",
            )
        for ef in expired_faults:
            self._log_incident(
                "FAULT_RESOLVED",
                ef.target,
                IncidentSeverity.INFO,
                f"Fault {ef.fault_type.value} on {ef.target} expired and resolved.",
            )

        # Apply environmental faults every tick from authoritative fault state.
        # Rebuilding the dynamic layer makes activation/expiry deterministic.
        self.world.reset_dynamic_state()
        for cell in self.fault_engine.get_blocked_cells():
            self.world.blocked_aisles.add(cell)
        for pos in self.fault_engine.get_dynamic_obstacles():
            self.world.dynamic_obstacles.add(pos)

        # Robot faults are applied to the actual robot state and coordination
        # state. A failed robot cannot publish, plan, reserve or move.
        for rid, robot in self.robots.items():
            if self.fault_engine.is_robot_failed(rid):
                if robot.state != RobotState.FAILED:
                    self.reservation_mgr.release_all_for_robot(rid)
                    robot.state = RobotState.FAILED
                    robot.failed_at = current_time
                    robot.health = 0.0
                    self._log_incident(
                        "ROBOT_FAILURE",
                        rid,
                        IncidentSeverity.CRITICAL,
                        f"Robot {rid} failed due to an active injected fault.",
                    )

            if self.fault_engine.is_low_battery(rid):
                if robot.state != RobotState.CHARGING:
                    robot.battery = min(robot.battery, 8.0)

        # 2. Update Network & Resilience Machine
        loss_rate = self.fault_engine.get_packet_loss_rate()
        latency = self.fault_engine.get_network_latency()
        jitter = self.fault_engine.get_network_jitter()
        dup_rate = self.fault_engine.get_message_duplication_rate()
        reorder_rate = self.fault_engine.get_message_reordering_rate()
        is_partitioned = self.fault_engine.is_network_partitioned()
        groups = self.fault_engine.get_partition_groups()

        if is_partitioned:
            self.state_machine.transition(
                ResilienceState.LOCAL_AUTONOMY, current_time, "Network partition active"
            )
            for r in self.robots.values():
                if r.state != RobotState.FAILED:
                    r.network_status = "PARTITIONED"
                    if r.state == RobotState.MOVING:
                        r.state = RobotState.LOCAL_AUTONOMY
        elif loss_rate > 0.15 or latency > 0.5:
            self.state_machine.transition(
                ResilienceState.DEGRADED, current_time, f"High loss ({loss_rate*100:.0f}%) or latency ({latency}s)"
            )
            for r in self.robots.values():
                if r.state != RobotState.FAILED:
                    r.network_status = "DEGRADED"
        else:
            if self.state_machine.current_state in (ResilienceState.LOCAL_AUTONOMY, ResilienceState.DEGRADED):
                self.state_machine.transition(
                    ResilienceState.RESYNC, current_time, "Network restored, reconciling state"
                )
                if self.network_resync:
                    sync_incidents = self.recovery_mgr.handle_network_resync(self.robots, current_time)
                    self.incidents.extend(sync_incidents)
                self.state_machine.transition(ResilienceState.NORMAL, current_time, "Resync complete")
            for r in self.robots.values():
                if r.state != RobotState.FAILED:
                    r.network_status = "CONNECTED"

        self.state_machine.update_durations(current_time)

        # 3. Detect robot failures before the heartbeat can be refreshed by
        # this tick's P2P publication. This keeps heartbeat timeout detection
        # observable rather than allowing the detector to see its own recovery.
        heartbeat_incidents = self.failure_detector.check_robot_heartbeats(
            self.robots, current_time
        )
        for inc in heartbeat_incidents:
            self.incidents.append(inc)
            if hasattr(inc, "detection_latency"):
                self.metrics.record_failure_detection(float(inc.detection_latency))
            if inc.fault in ("HEARTBEAT_TIMEOUT", "ROBOT_FAILURE_DETECTED"):
                if self.resilience_enabled:
                    self.state_machine.transition(
                        ResilienceState.RECOVERY, current_time,
                        f"Heartbeat lost on {inc.entity}"
                    )
                    failed_task_id = self.robots[inc.entity].current_task if inc.entity in self.robots else None
                    self.metrics.record_recovery_detection(float(getattr(inc, "detection_latency", 0.0)))
                    rec_incidents = self.recovery_mgr.handle_robot_failure(
                        failed_robot_id=inc.entity,
                        robots=self.robots,
                        tasks=self.tasks,
                        current_time=current_time,
                        failure_detected_time=current_time,
                    )
                    self.incidents.extend(rec_incidents)
                    if failed_task_id and failed_task_id in self.tasks and self.tasks[failed_task_id].status == TaskStatus.AVAILABLE:
                        self.pending_reassignment_times[failed_task_id] = current_time
                        self.recovery_contexts[failed_task_id] = {
                            "detection_time": float(current_time),
                            "reassignment_time": float(current_time),
                            "replan_time": float(current_time),
                        }
                        if self.dynamic_reassignment:
                            reassignment = self.reassign_task(failed_task_id)
                            if reassignment.get("status") == "REASSIGNED":
                                elapsed = max(0.0, current_time - self.recovery_contexts[failed_task_id]["detection_time"])
                                self.recovery_contexts[failed_task_id]["reassignment_time"] = float(current_time)
                                self.metrics.record_recovery_reassignment(elapsed)
                                # The selected replacement already received a feasible path during
                                # candidate evaluation. The authoritative planning pass below remains
                                # responsible for reservation-safe execution.

        # 4. Robot-to-robot P2P exchange. Each agent publishes its own state
        # to peers; the engine only configures transport conditions and pumps
        # the transport. No coordinator recipient is used.
        self.p2p.configure(
            loss_rate=loss_rate, latency=latency, jitter=jitter,
            duplication_rate=dup_rate, reorder_rate=reorder_rate,
            is_partitioned=is_partitioned, partition_groups=groups,
        )
        for rid, robot in self.robots.items():
            if robot.state != RobotState.FAILED:
                self.agents[rid].publish_local_state(current_time)
        delivered = self.p2p.pump_all(current_time)
        for rid, messages in delivered.items():
            if rid in self.agents:
                for message in messages:
                    payload = message.payload
                    if payload.get("type") == "PEER_STATE":
                        self.agents[rid].update_peer(PeerState(
                            robot_id=str(payload["robot_id"]),
                            position=tuple(payload["position"]),
                            velocity=float(payload.get("velocity", 0.0)),
                            battery=float(payload.get("battery", 0.0)),
                            priority=int(payload.get("priority", 1)),
                            status=str(payload.get("status", "UNKNOWN")),
                            intended_path=[tuple(p) for p in payload.get("intended_path", [])],
                            timestamp=float(payload.get("timestamp", current_time)),
                            sequence_number=int(payload.get("sequence_number", 0)),
                        ))

        self.metrics.messages_sent = self.network_sim.total_sent
        self.metrics.messages_dropped = self.network_sim.total_dropped
        if self.network_sim.latency_samples_ms:
            self.metrics.network_latency_samples_ms = list(self.network_sim.latency_samples_ms)

        # 5. Detect communication failures from observed transport behavior.
        network_incidents = self.failure_detector.check_network(
            self.network_sim.get_network_metrics(), current_time
        )
        for inc in network_incidents:
            self.incidents.append(inc)
            if hasattr(inc, "detection_latency"):
                self.metrics.record_failure_detection(float(inc.detection_latency))

        # 6. Task Allocation
        allocation = self.allocator.allocate_next_task(
            list(self.tasks.values()), self.robots, current_time
        )
        if allocation:
            task, robot = allocation
            was_reassignment = task.task_id in self.pending_reassignment_times
            task.status = TaskStatus.ASSIGNED
            task.assigned_robot = robot.robot_id
            task.start_time = current_time
            if was_reassignment:
                self.metrics.record_task_reassignment(max(0.0, current_time - self.pending_reassignment_times.pop(task.task_id)))
            task.phase = "PICKUP"
            robot.current_task = task.task_id
            robot.state = RobotState.PLANNING
            self.robot_route_traversed[robot.robot_id] = 0.0

            self._log_incident(
                "TASK_ASSIGNED",
                robot.robot_id,
                IncidentSeverity.INFO,
                f"Task {task.task_id} (Pri {task.priority}) assigned to {robot.robot_id}.",
            )

        # 6. Planning & Replanning
        # Phase 11 deterministic backoff prevents the selected deadlock victim
        # from immediately recreating the same reservation cycle.
        for rid in list(self.deadlock_backoff_until):
            if current_time >= self.deadlock_backoff_until[rid]:
                del self.deadlock_backoff_until[rid]

        for rid, robot in self.robots.items():
            if robot.state in (RobotState.PLANNING, RobotState.MOVING, RobotState.WAITING, RobotState.LOCAL_AUTONOMY, RobotState.DEGRADED):
                if rid in self.deadlock_backoff_until and current_time < self.deadlock_backoff_until[rid]:
                    robot.state = RobotState.WAITING
                    continue
                if not robot.current_task and rid not in self.charging_robots:
                    robot.state = RobotState.IDLE
                    robot.current_path = []
                    continue
                if rid in self.charging_robots and not robot.current_task:
                    target_pos = min(self.world.charging_bays.values(), key=lambda b: abs(b[0]-robot.position[0]) + abs(b[1]-robot.position[1]))
                    if not robot.current_path or robot.path_progress >= len(robot.current_path):
                        agent = self.agents[rid]
                        robot.current_path = agent.plan_for_goal(
                            target_pos, self.world.all_obstacles, self.world.width, self.world.height,
                            timestamp=current_time, intent="CHARGE"
                        ) or []
                        robot.path_progress = 0
                    robot.state = RobotState.MOVING if robot.current_path else RobotState.DEGRADED
                    if not robot.current_path:
                        continue
                    # Continue directly to movement for charging navigation.
                elif not robot.current_task:
                    continue

                task = self.tasks.get(robot.current_task) if robot.current_task else None
                if rid in self.charging_robots and not robot.current_task:
                    target_pos = min(self.world.charging_bays.values(), key=lambda b: abs(b[0]-robot.position[0]) + abs(b[1]-robot.position[1]))
                else:
                    if not task:
                        robot.current_task = None
                        robot.state = RobotState.IDLE
                        continue
                    target_pos = task.pickup if task.phase in ("PICKUP", "NAVIGATE_PICKUP") else task.delivery

                # If path is empty or next cell is now blocked, replan!
                needs_plan = False
                if not robot.current_path or robot.path_progress >= len(robot.current_path):
                    needs_plan = True
                else:
                    # Check if next steps are blocked by newly added obstacles
                    for step_idx in range(robot.path_progress, min(len(robot.current_path), robot.path_progress + 3)):
                        if robot.current_path[step_idx] in self.world.all_obstacles:
                            needs_plan = True
                            break

                if needs_plan:
                    if robot.current_path and robot.path_progress < len(robot.current_path) - 1:
                        self.metrics.record_reroute()
                    reserved = self.reservation_mgr.get_reserved_cells_at(current_time, exclude_robot=rid)
                    plan_started = time.perf_counter()
                    agent = self.agents[rid]
                    path = agent.plan_for_goal(
                        target_pos, self.world.all_obstacles, self.world.width, self.world.height,
                        reserved_cells=reserved, timestamp=current_time,
                        priority=task.priority if task else agent.priority, intent="MOVE"
                    )
                    self.metrics.record_planning_latency((time.perf_counter() - plan_started) * 1000.0)
                    if path:
                        robot.current_path = path
                        robot.path_progress = 0
                        robot.state = RobotState.MOVING
                        if task and task.task_id in self.recovery_contexts:
                            ctx = self.recovery_contexts[task.task_id]
                            if "replan_recorded" not in ctx:
                                ctx["replan_recorded"] = 1.0
                                ctx["replan_time"] = float(current_time)
                                self.metrics.record_recovery_replanning(max(0.0, current_time - ctx["reassignment_time"]))
                        if self.coordination_mode != "stop_and_wait":
                            if not self._reserve_path(rid, path, robot.path_progress, current_time, task.priority):
                                robot.current_path = []
                                self.agents[rid].enter_waiting()
                                self.metrics.record_conflict()
                    else:
                        robot.state = RobotState.WAITING

        # 7. Coordination & Conflict Detection
        trajectories: Dict[str, List[Tuple[int, int]]] = {}
        for rid, robot in self.robots.items():
            if robot.current_path and robot.state in (RobotState.MOVING, RobotState.LOCAL_AUTONOMY):
                trajectories[rid] = robot.current_path[robot.path_progress:]
        conflicts = ConflictDetector.detect_trajectory_conflicts(trajectories, current_time, dt=1.0)
        for c in conflicts:
            self.metrics.record_conflict()
            agent_a = self.agents.get(c.robot_a)
            agent_b = self.agents.get(c.robot_b)
            if not agent_a or not agent_b:
                continue
            # Each agent independently evaluates the peer priority. Both peers
            # receive the same deterministic tie-break rule; no global conflict
            # winner is selected by SimulationEngine.
            agent_a.update_peer(PeerState(
                robot_id=agent_b.robot_id, position=agent_b.position, velocity=agent_b.robot.velocity,
                battery=agent_b.robot.battery, priority=agent_b.priority, status=agent_b.state.value,
                intended_path=list(agent_b.intent.planned_path), timestamp=current_time,
                sequence_number=agent_b.intent.sequence_number,
            ))
            agent_b.update_peer(PeerState(
                robot_id=agent_a.robot_id, position=agent_a.position, velocity=agent_a.robot.velocity,
                battery=agent_a.robot.battery, priority=agent_a.priority, status=agent_a.state.value,
                intended_path=list(agent_a.intent.planned_path), timestamp=current_time,
                sequence_number=agent_a.intent.sequence_number,
            ))
            decision_a = agent_a.resolve_conflict(agent_b.robot_id, agent_b.priority)
            decision_b = agent_b.resolve_conflict(agent_a.robot_id, agent_a.priority)
            if decision_a == "PROCEED" and decision_b == "PROCEED":
                # Equal-priority deterministic tie-break guarantees this should
                # not happen; retain a safety stop rather than allowing overlap.
                agent_b.enter_waiting()

        # 8. Deadlock Detection and Recovery
        # Build the WFG from both physical occupancy and spatial-temporal
        # reservation dependencies. A reservation blocker is a real dependency:
        # the waiting robot cannot safely enter that cell/edge until the blocker
        # releases or moves.
        waiting_on: Dict[str, Set[str]] = {}
        arrival = current_time + dt

        for rid, robot in self.robots.items():
            if robot.state != RobotState.WAITING:
                continue
            if not robot.current_path or robot.path_progress >= len(robot.current_path) - 1:
                continue

            current_pos = robot.current_path[robot.path_progress]
            next_cell = robot.current_path[robot.path_progress + 1]
            blockers: Set[str] = set()

            # Physical occupancy dependency.
            for other in self.robots.values():
                if other.robot_id == rid or other.state == RobotState.FAILED:
                    continue
                if other.position == next_cell:
                    blockers.add(other.robot_id)
                if other.current_path and other.path_progress < len(other.current_path) - 1:
                    other_next = other.current_path[other.path_progress + 1]
                    if other.position == next_cell and other_next == current_pos:
                        blockers.add(other.robot_id)
                    elif other.position == current_pos and other_next == next_cell:
                        blockers.add(other.robot_id)

            # Reservation dependencies for the next cell and directed edge.
            blockers.update(
                self.reservation_mgr.get_cell_blockers(
                    next_cell, current_time, arrival, exclude_robot=rid
                )
            )
            blockers.update(
                self.reservation_mgr.get_edge_blockers(
                    current_pos, next_cell, current_time, arrival, exclude_robot=rid
                )
            )

            if blockers:
                waiting_on[rid] = blockers

        self.deadlock_detector.build_graph(waiting_on)
        cycles = self.deadlock_detector.find_cycles()

        if cycles and self.deadlock_recovery:
            for cycle in cycles:
                priorities = {
                    r: (
                        self.tasks[self.robots[r].current_task].priority
                        if r in self.robots
                        and self.robots[r].current_task
                        and self.robots[r].current_task in self.tasks
                        else 1
                    )
                    for r in cycle
                }
                victim, action = self.deadlock_detector.resolve_deadlock(cycle, priorities)
                if victim not in self.robots:
                    continue

                # Release the victim's reservations first. This breaks the
                # resource dependency instead of merely clearing its path.
                released = self.reservation_mgr.release_all_for_robot(victim)

                # Deterministic backoff, then force a fresh plan.
                backoff = max(2.0 * dt, 0.5)
                self.deadlock_backoff_until[victim] = current_time + backoff
                self.robots[victim].current_path = []
                self.robots[victim].path_progress = 0
                self.robots[victim].state = RobotState.WAITING

                self.metrics.record_deadlock(recovery_time=backoff)
                self.metrics.record_reroute()
                self._log_incident(
                    "DEADLOCK_RESOLVED",
                    victim,
                    IncidentSeverity.WARNING,
                    f"Deadlock cycle {cycle} resolved by {action}; released {released} reservations and backed off {backoff:.2f}s.",
                )

        # 9. Move Robots physically through the grid
        for rid, robot in self.robots.items():
            if robot.state in (RobotState.FAILED, RobotState.PAUSED):
                continue

            # Autonomous Charging Lifecycle (Phase 7)
            if robot.state == RobotState.CHARGING:
                robot.battery = min(100.0, robot.battery + 15.0 * dt)
                self.metrics.total_energy_consumed += 0.02 * dt
                if robot.battery >= 99.9:
                    robot.battery = 100.0
                    robot.state = RobotState.IDLE
                    robot.current_path = []
                    self._log_incident("BATTERY_RECOVERED", rid, IncidentSeverity.INFO, f"Robot {rid} battery fully charged (100%). Ready for operations.")
                continue

            # Check if robot should enter low battery degraded state
            has_low_bat_fault = any(
                f.fault_type == FaultType.LOW_BATTERY and f.target == rid and f.status == "ACTIVE"
                for f in self.fault_engine.active_faults.values()
            )
            if (robot.battery <= 20.0 or has_low_bat_fault) and robot.state not in (RobotState.CHARGING, RobotState.DEGRADED):
                robot.state = RobotState.DEGRADED
                self._log_incident("LOW_BATTERY", rid, IncidentSeverity.WARNING, f"Robot {rid} low battery ({robot.battery:.1f}%). Triggering task handoff and docking.")
                if robot.current_task:
                    handoff = self.reassign_robot(rid) if self.dynamic_reassignment else {"status": "DISABLED"}
                    if handoff.get("status") == "REASSIGNED":
                        self._log_incident("TASK_HANDOFF", rid, IncidentSeverity.INFO, f"Task {handoff['task_id']} handed off to {handoff['new_robot']} due to low battery.")
                
                # Navigate to closest charging bay
                bays = list(self.world.charging_bays.values())
                bays.sort(key=lambda b: abs(b[0] - robot.position[0]) + abs(b[1] - robot.position[1]))
                target_bay = bays[0]
                chg_path = self.agents[rid].plan_for_goal(
                    target_bay, self.world.all_obstacles, self.world.width, self.world.height,
                    timestamp=current_time, intent="CHARGE"
                )
                if chg_path:
                    self.charging_robots.add(rid)
                    robot.current_path = chg_path
                    robot.path_progress = 0
                    robot.state = RobotState.MOVING

            # Battery drain based on state
            if robot.state in (RobotState.MOVING, RobotState.LOCAL_AUTONOMY):
                robot.battery = max(0.0, robot.battery - 0.05 * dt)
                self.metrics.total_energy_consumed += 0.05 * dt
            else:
                robot.battery = max(0.0, robot.battery - 0.005 * dt)
                self.metrics.total_energy_consumed += 0.005 * dt

            # Handle action timers (loading / unloading at stations)
            if rid in self.action_timers:
                self.action_timers[rid] -= dt
                if self.action_timers[rid] <= 0:
                    del self.action_timers[rid]
                    # Advance task phase
                    if robot.current_task and robot.current_task in self.tasks:
                        task = self.tasks[robot.current_task]
                        if task.phase == "ACTION_PICKUP":
                            task.phase = "NAVIGATE_DELIVERY"
                            robot.state = RobotState.PLANNING
                            robot.current_path = []
                        elif task.phase == "ACTION_DELIVERY":
                            task.phase = "COMPLETED"
                            task.status = TaskStatus.COMPLETED
                            task.completion_time = current_time
                            robot.current_task = None
                            robot.state = RobotState.IDLE
                            robot.current_path = []
                            self.reservation_mgr.release_all_for_robot(rid)
                            # Record metrics
                            wait_t = task.start_time - task.creation_time if task.start_time else 0.0
                            exec_t = task.completion_time - (task.start_time or task.creation_time)
                            dist = self.robot_route_traversed.get(rid, 0.0)
                            self.metrics.record_task_completion(wait_t, exec_t, dist, task.completion_time - task.creation_time)
                            if task.task_id in self.recovery_contexts:
                                ctx = self.recovery_contexts.pop(task.task_id)
                                total = max(0.0, current_time - ctx["detection_time"])
                                self.metrics.record_recovery_total(total)
                                self._log_incident(
                                    "RECOVERY_COMPLETED", rid, IncidentSeverity.INFO,
                                    f"Recovery for task {task.task_id} completed in {total:.3f}s."
                                )
                            self._log_incident(
                                "TASK_COMPLETED",
                                rid,
                                IncidentSeverity.INFO,
                                f"Task {task.task_id} completed successfully in {exec_t:.1f}s.",
                            )
                continue

            # Step along path
            if robot.state in (RobotState.MOVING, RobotState.LOCAL_AUTONOMY) and robot.current_path:
                if robot.path_progress < len(robot.current_path) - 1:
                    next_pos = robot.current_path[robot.path_progress + 1]

                    # Execution-layer safety gate: reservations and direct occupancy are authoritative.
                    if not self._movement_is_safe(rid, robot.position, next_pos, current_time):
                        robot.state = RobotState.DEGRADED if rid in self.charging_robots else RobotState.WAITING
                        self.metrics.record_conflict()
                        # A blocked command is not a physical collision. The collision counter is reserved
                        # for an invariant violation that reaches the physical state transition.
                        continue

                        # Movement is applied through the owning agent after the
                    # world-level safety gate has approved the transition.
                    self.agents[rid].execute_local_move(next_pos)
                    self.robot_route_traversed[rid] = self.robot_route_traversed.get(rid, 0.0) + 1.0

                    # Check if reached destination of current phase
                    if robot.current_task and robot.current_task in self.tasks:
                        task = self.tasks[robot.current_task]
                        if task.phase in ("PICKUP", "NAVIGATE_PICKUP") and robot.position == task.pickup:
                            task.phase = "ACTION_PICKUP"
                            robot.state = RobotState.TASK_EXECUTION
                            self.action_timers[rid] = 1.0  # 1.0s loading action
                        elif task.phase == "NAVIGATE_DELIVERY" and robot.position == task.delivery:
                            task.phase = "ACTION_DELIVERY"
                            robot.state = RobotState.TASK_EXECUTION
                            self.action_timers[rid] = 1.0  # 1.0s unloading action
                else:
                    # Reached end of current path
                    if robot.current_task and robot.current_task in self.tasks:
                        task = self.tasks[robot.current_task]
                        if task.phase in ("PICKUP", "NAVIGATE_PICKUP") and robot.position == task.pickup:
                            task.phase = "ACTION_PICKUP"
                            robot.state = RobotState.TASK_EXECUTION
                            self.action_timers[rid] = 1.0
                        elif task.phase == "NAVIGATE_DELIVERY" and robot.position == task.delivery:
                            task.phase = "ACTION_DELIVERY"
                            robot.state = RobotState.TASK_EXECUTION
                            self.action_timers[rid] = 1.0
                    else:
                        # Reached end of path without a task
                        if robot.position in self.world.charging_bays.values():
                            self.charging_robots.discard(rid)
                            robot.state = RobotState.CHARGING
                            self._log_incident("CHARGING_STARTED", rid, IncidentSeverity.INFO, f"Robot {rid} docked at charging bay. Charging initiated.")
                        else:
                            robot.state = RobotState.IDLE
                            self.reservation_mgr.release_all_for_robot(rid)

        self.metrics.record_robot_time(dt, [r.state.value for r in self.robots.values()])

        # Purge expired reservations
        self.reservation_mgr.clean_expired(current_time)

        return self.get_telemetry()

    def _log_incident(self, fault: str, entity: str, severity: IncidentSeverity, msg: str):
        inc = Incident(
            incident_id=f"inc_{entity}_{int(self.clock.current_time*10)}_{self.random.randint(100,999)}",
            timestamp=self.clock.current_time,
            entity=entity,
            fault=fault,
            severity=severity,
            state=self.state_machine.current_state.value,
            message=msg,
        )
        self.incidents.append(inc)

    def get_telemetry(self) -> Dict[str, Any]:
        """Compile complete real-time telemetry snapshot.

        Phase 17 keeps metrics derived from authoritative simulation state and
        transport counters. Resilience durations are finalized through the
        current simulation timestamp before the summary is emitted.
        """
        self.state_machine.update_durations(self.clock.current_time)
        self.metrics.sync_network_metrics(self.network_sim.get_network_metrics())
        completed_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        failed_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
        metrics_summary = self.metrics.get_summary(
            total_tasks=len(self.tasks),
            completed_tasks=completed_tasks,
            current_time=self.clock.current_time,
            resilience_state_durations=self.state_machine.state_durations,
            failed_tasks=failed_tasks,
        )

        return {
            "timestamp": round(self.clock.current_time, 2),
            "clock": self.clock.to_dict(),
            "world": self.world.to_dict(),
            "robots": [r.to_dict() for r in self.robots.values()],
            "tasks": [t.to_dict() for t in self.tasks.values()],
            "faults": [f.to_dict() for f in self.fault_engine.active_faults.values()],
            "fault_engine": self.fault_engine.to_dict(),
            "fault_effects": self.fault_engine.get_active_effects(),
            "incidents": [inc.to_dict() for inc in self.incidents[-25:]],
            "reservations": [r.to_dict() for r in self.reservation_mgr.get_all_active()],
            "deadlock": {
                "wait_for_graph": self.deadlock_detector.graph_snapshot(),
                "cycles": [list(c) for c in self.deadlock_detector.last_cycles],
                "backoff_until": dict(self.deadlock_backoff_until),
            },
            "resilience": self.state_machine.to_dict(),
            "metrics": metrics_summary,
            "network": self.network_sim.get_network_metrics(),
        }
