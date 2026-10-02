"""Robot-to-robot communication adapters for the ResilientEdge simulation.

The adapter is deliberately transport-oriented: agents decide what to send and
how to react; the adapter only delivers messages subject to simulated network
conditions. The same interface can later be backed by ROS 2 topics/services.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, Set, Tuple

from .network_sim import NetworkSimulator, NetworkMessage


class CommunicationAdapter(ABC):
    """Transport boundary owned by each RobotAgent."""

    @abstractmethod
    def send(self, sender: str, recipient: str, payload: Dict[str, Any], current_time: float) -> bool:
        raise NotImplementedError

    @abstractmethod
    def broadcast(self, sender: str, payload: Dict[str, Any], current_time: float) -> int:
        raise NotImplementedError

    @abstractmethod
    def register(self, robot_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def poll(self, robot_id: str, current_time: float) -> list[NetworkMessage]:
        raise NotImplementedError


@dataclass
class NetworkConditions:
    loss_rate: float = 0.0
    latency: float = 0.01
    jitter: float = 0.0
    duplication_rate: float = 0.0
    reorder_rate: float = 0.0
    is_partitioned: bool = False
    partition_groups: Optional[Tuple[Set[str], Set[str]]] = None


class LocalP2PCommunicationAdapter(CommunicationAdapter):
    """In-process P2P transport with no coordinator recipient.

    All recipients are robot IDs. Delivery is mediated by NetworkSimulator so
    latency/loss/jitter/duplication/reordering/partition behavior remains real
    and deterministic under a fixed seed.
    """

    def __init__(self, network: Optional[NetworkSimulator] = None):
        self.network = network or NetworkSimulator()
        self.peers: Set[str] = set()
        self.conditions = NetworkConditions()

    def register(self, robot_id: str) -> None:
        self.peers.add(str(robot_id))

    def unregister(self, robot_id: str) -> None:
        self.peers.discard(str(robot_id))

    def configure(self, **kwargs: Any) -> None:
        """Apply validated degradation conditions to the live transport."""
        unknown = [key for key in kwargs if not hasattr(self.conditions, key)]
        if unknown:
            raise ValueError(f"Unknown network condition(s): {', '.join(sorted(unknown))}")
        candidate = NetworkConditions(**{**self.conditions.__dict__, **kwargs})
        if not 0.0 <= float(candidate.loss_rate) <= 1.0:
            raise ValueError("loss_rate must be between 0 and 1")
        if not 0.0 <= float(candidate.duplication_rate) <= 1.0:
            raise ValueError("duplication_rate must be between 0 and 1")
        if not 0.0 <= float(candidate.reorder_rate) <= 1.0:
            raise ValueError("reorder_rate must be between 0 and 1")
        if float(candidate.latency) < 0.0 or float(candidate.jitter) < 0.0:
            raise ValueError("latency and jitter must be non-negative")
        self.conditions = candidate

    def get_conditions(self) -> Dict[str, Any]:
        """Return the authoritative live degradation configuration."""
        return {
            "loss_rate": float(self.conditions.loss_rate),
            "latency": float(self.conditions.latency),
            "jitter": float(self.conditions.jitter),
            "duplication_rate": float(self.conditions.duplication_rate),
            "reorder_rate": float(self.conditions.reorder_rate),
            "is_partitioned": bool(self.conditions.is_partitioned),
            "partition_groups": [sorted(g) for g in self.conditions.partition_groups]
                if self.conditions.partition_groups else [],
        }

    def network_health(self) -> str:
        """Classify transport conditions for agent-level resilience decisions."""
        c = self.conditions
        if c.is_partitioned:
            return "PARTITIONED"
        if c.loss_rate > 0.15 or c.latency > 0.5 or c.jitter > 0.25:
            return "DEGRADED"
        return "CONNECTED"

    def send(self, sender: str, recipient: str, payload: Dict[str, Any], current_time: float) -> bool:
        sender, recipient = str(sender), str(recipient)
        if sender not in self.peers or recipient not in self.peers:
            return False
        c = self.conditions
        return self.network.send_message(
            sender=sender,
            recipient=recipient,
            payload=payload,
            current_time=current_time,
            loss_rate=c.loss_rate,
            latency=c.latency,
            jitter=c.jitter,
            duplication_rate=c.duplication_rate,
            reorder_rate=c.reorder_rate,
            is_partitioned=c.is_partitioned,
            partition_groups=c.partition_groups,
        )

    def broadcast(self, sender: str, payload: Dict[str, Any], current_time: float) -> int:
        delivered_to_transport = 0
        for recipient in sorted(self.peers - {str(sender)}):
            if self.send(sender, recipient, payload, current_time):
                delivered_to_transport += 1
        return delivered_to_transport

    def poll(self, robot_id: str, current_time: float) -> list[NetworkMessage]:
        # The shared transport queue is drained once and messages for other
        # robots are retained, preserving true point-to-point routing.
        due = self.network.poll_delivered(current_time)
        mine: list[NetworkMessage] = []
        for message in due:
            if message.recipient == str(robot_id):
                mine.append(message)
            else:
                # Reinsert messages for other recipients without changing
                # their delivery timestamp or network counters.
                self.network.in_flight_messages.append(message)
        return mine

    def pump_all(self, current_time: float) -> Dict[str, list[NetworkMessage]]:
        """Deliver all due messages grouped by robot recipient."""
        due = self.network.poll_delivered(current_time)
        grouped: Dict[str, list[NetworkMessage]] = {rid: [] for rid in self.peers}
        for message in due:
            if message.recipient in grouped:
                grouped[message.recipient].append(message)
        return grouped
