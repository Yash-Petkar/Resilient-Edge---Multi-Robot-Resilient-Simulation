"""Task domain model for ResilientEdge."""
from dataclasses import dataclass
from enum import Enum
from typing import Tuple, Optional, Dict, Any


class TaskStatus(str, Enum):
    CREATED = "CREATED"
    AVAILABLE = "AVAILABLE"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    REASSIGNED = "REASSIGNED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class Task:
    task_id: str
    pickup: Tuple[int, int]
    delivery: Tuple[int, int]
    priority: int = 1  # 1 (lowest) to 5 (highest)
    deadline: float = 300.0  # seconds
    status: TaskStatus = TaskStatus.CREATED
    assigned_robot: Optional[str] = None
    creation_time: float = 0.0
    start_time: Optional[float] = None
    completion_time: Optional[float] = None
    phase: str = "PICKUP"  # "PICKUP" -> "NAVIGATE_PICKUP" -> "ARRIVE_PICKUP" -> "ACTION_PICKUP" -> "NAVIGATE_DELIVERY" -> "ACTION_DELIVERY" -> "COMPLETED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "pickup": list(self.pickup),
            "delivery": list(self.delivery),
            "priority": self.priority,
            "deadline": self.deadline,
            "status": self.status.value,
            "assigned_robot": self.assigned_robot,
            "creation_time": round(self.creation_time, 2),
            "start_time": round(self.start_time, 2) if self.start_time is not None else None,
            "completion_time": round(self.completion_time, 2) if self.completion_time is not None else None,
            "phase": self.phase,
        }
