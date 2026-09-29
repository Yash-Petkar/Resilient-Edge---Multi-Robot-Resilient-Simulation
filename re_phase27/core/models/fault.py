"""Fault domain model for chaos and resilience testing."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any


class FaultType(str, Enum):
    ROBOT_FAILURE = "ROBOT_FAILURE"
    LOW_BATTERY = "LOW_BATTERY"
    BLOCKED_AISLE = "BLOCKED_AISLE"
    DYNAMIC_OBSTACLE = "DYNAMIC_OBSTACLE"
    PACKET_LOSS = "PACKET_LOSS"
    LATENCY = "LATENCY"
    JITTER = "JITTER"
    MESSAGE_DUPLICATION = "MESSAGE_DUPLICATION"
    MESSAGE_REORDERING = "MESSAGE_REORDERING"
    NETWORK_PARTITION = "NETWORK_PARTITION"


@dataclass
class Fault:
    fault_id: str
    fault_type: FaultType
    target: str  # e.g., "R2", "network", "cell:8,5", "partition:group_a"
    start_time: float
    duration: float = 30.0  # seconds; <= 0 means permanent until manually cleared
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: str = "PENDING"  # PENDING, ACTIVE, RESOLVED, CLEARED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fault_id": self.fault_id,
            "fault_type": self.fault_type.value,
            "target": self.target,
            "start_time": round(self.start_time, 2),
            "duration": round(self.duration, 2),
            "parameters": self.parameters,
            "status": self.status,
        }
