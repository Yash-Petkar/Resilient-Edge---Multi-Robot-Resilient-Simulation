"""Spatial-temporal reservation domain models."""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional, Tuple


class ReservationStatus(str, Enum):
    REQUESTED = "REQUESTED"
    GRANTED = "GRANTED"
    REJECTED = "REJECTED"
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class ReservationDecisionStatus(str, Enum):
    GRANTED = "GRANTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class ReservationDecision:
    """Authoritative outcome of evaluating a reservation request."""

    status: ReservationDecisionStatus
    robot_id: str
    resource_id: str
    start_time: float
    end_time: float
    priority: int
    reservation_id: Optional[str] = None
    conflicting_reservation_ids: Tuple[str, ...] = ()
    reason: str = ""

    @property
    def granted(self) -> bool:
        return self.status is ReservationDecisionStatus.GRANTED


@dataclass
class Reservation:
    reservation_id: str
    robot_id: str
    resource_id: str  # e.g., "cell:12,8" or "edge:(12,8)->(12,9)"
    start_time: float
    end_time: float
    priority: int = 1
    status: ReservationStatus = ReservationStatus.REQUESTED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reservation_id": self.reservation_id,
            "robot_id": self.robot_id,
            "resource_id": self.resource_id,
            "start_time": round(self.start_time, 2),
            "end_time": round(self.end_time, 2),
            "priority": self.priority,
            "status": self.status.value,
        }
