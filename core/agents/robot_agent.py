"""Independent local intelligence boundary for a simulated AMR."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from core.models.robot import Robot, RobotState
from core.planning.astar import AStarPlanner

Position = Tuple[int, int]


@dataclass
class AgentIntent:
    """The locally-owned movement intent shared with peers."""

    robot_id: str
    planned_path: List[Position] = field(default_factory=list)
    priority: int = 1
    intent: str = "IDLE"
    sequence_number: int = 0
    timestamp: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "robot_id": self.robot_id,
            "planned_path": [list(p) for p in self.planned_path],
            "priority": self.priority,
            "intent": self.intent,
            "sequence_number": self.sequence_number,
            "timestamp": self.timestamp,
        }


@dataclass
class PeerState:
    """Last locally-known state of another robot."""

    robot_id: str
    position: Position
    velocity: float
    battery: float
    priority: int
    status: str
    intended_path: List[Position] = field(default_factory=list)
    timestamp: float = 0.0
    sequence_number: int = 0

    def is_stale(self, now: float, max_age: float) -> bool:
        return (now - self.timestamp) > max_age

    def to_dict(self) -> Dict[str, Any]:
        return {
            "robot_id": self.robot_id,
            "position": list(self.position),
            "velocity": self.velocity,
            "battery": self.battery,
            "priority": self.priority,
            "status": self.status,
            "intended_path": [list(p) for p in self.intended_path],
            "timestamp": self.timestamp,
            "sequence_number": self.sequence_number,
        }


class RobotAgent:
    """Owns all state that belongs to one robot's local decision boundary.

    The class deliberately contains no reference to ``SimulationEngine``.
    This makes the agent independently testable and prevents the transport or
    world orchestration layer from becoming a hidden dependency of robot
    intelligence.
    """

    def __init__(
        self,
        robot: Robot,
        planner: Optional[AStarPlanner] = None,
        priority: int = 1,
        peer_stale_after: float = 2.0,
    ) -> None:
        self.robot = robot
        self.planner = planner or AStarPlanner(allow_diagonal=False)
        self.priority = int(priority)
        self.peer_stale_after = float(peer_stale_after)

        # Local decision state. These are intentionally per-agent objects.
        self.intent = AgentIntent(robot_id=robot.robot_id, priority=self.priority)
        self.peer_table: Dict[str, PeerState] = {}
        self.local_reservations: Set[str] = set()
        self.local_conflicts: Dict[str, Dict[str, Any]] = {}
        self.recovery_state: str = "NORMAL"
        self.communication_state: str = robot.network_status
        self.communication_adapter: Any = None
        self.last_decision_timestamp: float = robot.last_heartbeat
        self.decision_sequence: int = 0

    @property
    def robot_id(self) -> str:
        return self.robot.robot_id

    @property
    def state(self) -> RobotState:
        return self.robot.state

    @property
    def position(self) -> Position:
        return self.robot.position


    def attach_communication_adapter(self, adapter: Any) -> None:
        """Attach this agent to its transport and register its robot identity."""
        self.communication_adapter = adapter
        adapter.register(self.robot_id)

    def publish_local_state(self, current_time: float, recipients: Optional[List[str]] = None) -> int:
        """Publish this agent's intent/state directly to peer agents."""
        if self.communication_adapter is None:
            return 0
        payload = {
            "type": "PEER_STATE",
            "robot_id": self.robot_id,
            "position": list(self.robot.position),
            "velocity": self.robot.velocity,
            "battery": self.robot.battery,
            "priority": self.priority,
            "status": self.robot.state.value,
            "intended_path": [list(p) for p in self.intent.planned_path],
            "timestamp": float(current_time),
            "sequence_number": self.intent.sequence_number,
        }
        if recipients is None:
            count = self.communication_adapter.broadcast(self.robot_id, payload, current_time)
        else:
            count = 0
            for recipient in recipients:
                count += int(self.communication_adapter.send(self.robot_id, recipient, payload, current_time))
        # A heartbeat is a local liveness claim at send-attempt time. A network
        # partition must not make a healthy robot look hardware-failed; the
        # resilience layer distinguishes communication loss from robot failure.
        self.robot.last_heartbeat = float(current_time)
        return count

    def receive_messages(self, current_time: float) -> int:
        """Consume only messages addressed to this agent and update local knowledge."""
        if self.communication_adapter is None:
            return 0
        messages = self.communication_adapter.poll(self.robot_id, current_time)
        for message in messages:
            payload = message.payload
            if payload.get("type") != "PEER_STATE":
                continue
            self.update_peer(PeerState(
                robot_id=str(payload["robot_id"]),
                position=tuple(payload["position"]),
                velocity=float(payload.get("velocity", 0.0)),
                battery=float(payload.get("battery", 0.0)),
                priority=int(payload.get("priority", 1)),
                status=str(payload.get("status", "UNKNOWN")),
                intended_path=[tuple(p) for p in payload.get("intended_path", [])],
                timestamp=float(payload.get("timestamp", message.send_time)),
                sequence_number=int(payload.get("sequence_number", 0)),
            ))
        return len(messages)

    def set_intent(
        self,
        planned_path: List[Position],
        *,
        intent: str = "MOVE",
        priority: Optional[int] = None,
        timestamp: float = 0.0,
    ) -> AgentIntent:
        self.decision_sequence += 1
        self.intent = AgentIntent(
            robot_id=self.robot_id,
            planned_path=list(planned_path),
            priority=self.priority if priority is None else int(priority),
            intent=intent,
            sequence_number=self.decision_sequence,
            timestamp=float(timestamp),
        )
        return self.intent

    def update_peer(self, peer: PeerState) -> None:
        """Update local knowledge only; never mutate the peer's Robot object."""
        if peer.robot_id == self.robot_id:
            return
        previous = self.peer_table.get(peer.robot_id)
        if previous and peer.sequence_number < previous.sequence_number:
            return
        self.peer_table[peer.robot_id] = peer

    def remove_peer(self, robot_id: str) -> None:
        self.peer_table.pop(robot_id, None)

    def assess_communication(self, now: float) -> str:
        """Derive local communication health from transport conditions and peer freshness."""
        if self.communication_adapter is None:
            self.set_communication_state("DISCONNECTED")
            return self.communication_state
        health = self.communication_adapter.network_health()
        if health == "PARTITIONED":
            self.set_communication_state("PARTITIONED")
        elif health == "DEGRADED":
            self.set_communication_state("DEGRADED")
        elif self.peer_table and len(self.stale_peers(now)) == len(self.peer_table):
            # No fresh peer knowledge despite nominal transport availability.
            self.set_communication_state("DEGRADED")
        else:
            self.set_communication_state("CONNECTED")
        return self.communication_state

    def stale_peers(self, now: float) -> List[str]:
        return [
            robot_id
            for robot_id, peer in self.peer_table.items()
            if peer.is_stale(float(now), self.peer_stale_after)
        ]

    def set_communication_state(self, state: str) -> None:
        self.communication_state = str(state)
        self.robot.network_status = str(state)

    def record_reservation(self, reservation_id: str) -> None:
        self.local_reservations.add(str(reservation_id))

    def release_reservation(self, reservation_id: str) -> None:
        self.local_reservations.discard(str(reservation_id))

    def clear_reservations(self) -> None:
        self.local_reservations.clear()

    def record_conflict(self, conflict_id: str, data: Dict[str, Any]) -> None:
        self.local_conflicts[str(conflict_id)] = dict(data)

    def clear_conflicts(self) -> None:
        self.local_conflicts.clear()

    def set_recovery_state(self, state: str) -> None:
        self.recovery_state = str(state)

    def plan_local_path(
        self,
        goal: Position,
        blocked_cells: Set[Position],
        width: int,
        height: int,
        reserved_cells: Optional[Set[Position]] = None,
        timestamp: float = 0.0,
    ) -> Optional[List[Position]]:
        """Plan from this agent's current local position and own the intent."""
        path = self.planner.plan(
            self.robot.position,
            goal,
            blocked_cells,
            width,
            height,
            reserved_cells,
        )
        if path is not None:
            self.set_intent(path, intent="MOVE", timestamp=timestamp)
        return path

    def plan_for_goal(
        self,
        goal: Position,
        blocked_cells: Set[Position],
        width: int,
        height: int,
        reserved_cells: Optional[Set[Position]] = None,
        timestamp: float = 0.0,
        priority: Optional[int] = None,
        intent: str = "MOVE",
    ) -> Optional[List[Position]]:
        """Make a local planning decision and publish the resulting intent."""
        path = self.planner.plan(
            start=self.robot.position,
            goal=goal,
            blocked_cells=blocked_cells,
            width=width,
            height=height,
            reserved_cells=reserved_cells,
        )
        if path:
            self.set_intent(
                path,
                intent=intent,
                priority=priority,
                timestamp=timestamp,
            )
        else:
            self.set_intent([], intent="WAIT", priority=priority, timestamp=timestamp)
        return path

    def resolve_conflict(self, other_robot_id: str, other_priority: int) -> str:
        """Choose a local conflict response without consulting SimulationEngine.

        Higher priority wins. Equal priorities use a deterministic robot-id tie
        break so two peers make the same decision independently.
        """
        other_priority = int(other_priority)
        if self.priority > other_priority:
            decision = "PROCEED"
        elif self.priority < other_priority:
            decision = "YIELD"
        else:
            decision = "PROCEED" if self.robot_id < str(other_robot_id) else "YIELD"
        if decision == "YIELD":
            self.robot.state = RobotState.WAITING
            self.intent.intent = "YIELD"
        return decision

    def next_path_position(self) -> Optional[Position]:
        """Return the next locally intended cell, if one exists."""
        path = self.robot.current_path
        idx = self.robot.path_progress
        if not path or idx >= len(path) - 1:
            return None
        return path[idx + 1]

    def enter_planning(self) -> None:
        self.robot.state = RobotState.PLANNING

    def enter_waiting(self) -> None:
        self.robot.state = RobotState.WAITING
        self.intent.intent = "WAIT"

    def execute_local_move(self, next_position: Position) -> None:
        """Apply a movement selected by this agent after the world safety gate passes."""
        current = self.robot.position
        dx = next_position[0] - current[0]
        dy = next_position[1] - current[1]
        import math
        self.robot.orientation = math.atan2(dy, dx)
        self.robot.position = tuple(next_position)
        self.robot.path_progress += 1
        self.last_decision_timestamp = self.robot.last_heartbeat

    def snapshot_local_state(self) -> Dict[str, Any]:
        """Return agent-owned state for testing, telemetry and persistence."""
        return {
            "robot": self.robot.to_dict(),
            "intent": self.intent.to_dict(),
            "peer_table": {k: v.to_dict() for k, v in self.peer_table.items()},
            "local_reservations": sorted(self.local_reservations),
            "local_conflicts": dict(self.local_conflicts),
            "recovery_state": self.recovery_state,
            "communication_state": self.communication_state,
            "last_decision_timestamp": self.last_decision_timestamp,
            "decision_sequence": self.decision_sequence,
        }
