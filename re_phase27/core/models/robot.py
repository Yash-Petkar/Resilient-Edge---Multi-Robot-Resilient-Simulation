"""Domain models for ResilientEdge multi-robot simulation."""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple, Optional, Dict, Any


def robot_home_position(robot_id: str) -> Tuple[int, int]:
    """Return the deterministic initial/home grid position for a robot ID."""
    digits = "".join(character for character in robot_id if character.isdigit())
    index = int(digits) if digits else 1
    return (2 + index * 2, 0)


class RobotState(str, Enum):
    IDLE = "IDLE"
    PLANNING = "PLANNING"
    MOVING = "MOVING"
    WAITING = "WAITING"
    PAUSED = "PAUSED"
    TASK_EXECUTION = "TASK_EXECUTION"
    DEGRADED = "DEGRADED"
    LOCAL_AUTONOMY = "LOCAL_AUTONOMY"
    RECOVERING = "RECOVERING"
    CHARGING = "CHARGING"
    FAILED = "FAILED"


@dataclass
class Robot:
    robot_id: str
    position: Tuple[int, int]
    home_position: Optional[Tuple[int, int]] = None
    orientation: float = 0.0  # radians (0 = east, pi/2 = south, etc.)
    velocity: float = 1.0  # grid units per second
    state: RobotState = RobotState.IDLE
    battery: float = 100.0  # percentage 0.0 - 100.0
    health: float = 1.0  # 0.0 - 1.0
    current_task: Optional[str] = None
    current_path: List[Tuple[int, int]] = field(default_factory=list)
    path_progress: int = 0
    network_status: str = "CONNECTED"  # CONNECTED, DEGRADED, PARTITIONED, DISCONNECTED
    last_heartbeat: float = 0.0
    failed_at: Optional[float] = None  # simulation time when the robot entered FAILED

    def __post_init__(self):
        if self.home_position is None:
            self.home_position = robot_home_position(self.robot_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "robot_id": self.robot_id,
            "position": list(self.position),
            "home_position": list(self.home_position or robot_home_position(self.robot_id)),
            "orientation": round(self.orientation, 2),
            "velocity": self.velocity,
            "state": self.state.value,
            "battery": round(self.battery, 1),
            "health": round(self.health, 2),
            "current_task": self.current_task,
            "current_path": [list(p) for p in self.current_path],
            "path_progress": self.path_progress,
            "network_status": self.network_status,
            "last_heartbeat": round(self.last_heartbeat, 2),
            "failed_at": round(self.failed_at, 4) if self.failed_at is not None else None,
        }
