"""Authoritative spatial-temporal reservation table for multi-robot motion."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Set

from core.models.reservation import (
    Reservation,
    ReservationDecision,
    ReservationDecisionStatus,
    ReservationStatus,
)


_ACTIVE_STATUSES = (ReservationStatus.GRANTED, ReservationStatus.ACTIVE)
_TERMINAL_STATUSES = (
    ReservationStatus.REJECTED,
    ReservationStatus.RELEASED,
    ReservationStatus.EXPIRED,
    ReservationStatus.CANCELLED,
)


@dataclass(frozen=True)
class ReservationConflict:
    reservation_id: str
    robot_id: str
    resource_id: str
    start_time: float
    end_time: float
    priority: int


class ReservationManager:
    """Own the REQUEST -> EVALUATE -> GRANT/REJECT -> ACTIVE -> RELEASE lifecycle.

    The manager remains in-memory because the simulation engine is the authoritative
    runtime state owner. SQLite persistence can serialize the returned Reservation
    objects without changing this API.
    """

    def __init__(self):
        self._reservations: Dict[str, List[Reservation]] = {}
        self._next_id = 1
        self._decision_log: List[ReservationDecision] = []

    @staticmethod
    def cell_resource(cell: Tuple[int, int]) -> str:
        return f"cell:{cell[0]},{cell[1]}"

    @staticmethod
    def edge_resource(start: Tuple[int, int], end: Tuple[int, int]) -> str:
        return f"edge:({start[0]},{start[1]})->({end[0]},{end[1]})"

    def _new_reservation_id(self) -> str:
        reservation_id = f"res_{self._next_id:06d}"
        self._next_id += 1
        return reservation_id

    @staticmethod
    def _validate_interval(start_time: float, end_time: float) -> None:
        if end_time <= start_time:
            raise ValueError("reservation end_time must be greater than start_time")

    @staticmethod
    def _overlaps(start_a: float, end_a: float, start_b: float, end_b: float) -> bool:
        return not (end_a <= start_b or start_a >= end_b)

    def _conflicts_for_resource(
        self,
        resource_id: str,
        start_time: float,
        end_time: float,
        robot_id: Optional[str] = None,
    ) -> List[ReservationConflict]:
        conflicts: List[ReservationConflict] = []
        for r in self._reservations.get(resource_id, []):
            if r.status not in _ACTIVE_STATUSES:
                continue
            if robot_id is not None and r.robot_id == robot_id:
                continue
            if self._overlaps(start_time, end_time, r.start_time, r.end_time):
                conflicts.append(
                    ReservationConflict(
                        reservation_id=r.reservation_id,
                        robot_id=r.robot_id,
                        resource_id=r.resource_id,
                        start_time=r.start_time,
                        end_time=r.end_time,
                        priority=r.priority,
                    )
                )
        return conflicts

    def evaluate_request(
        self,
        robot_id: str,
        resource_id: str,
        start_time: float,
        end_time: float,
        priority: int = 1,
        *,
        reservation_id: Optional[str] = None,
    ) -> ReservationDecision:
        """Evaluate without mutating state and return a deterministic decision."""
        self._validate_interval(start_time, end_time)
        priority = int(priority)
        conflicts = self._conflicts_for_resource(resource_id, start_time, end_time, robot_id)
        if conflicts:
            ids = tuple(sorted(c.reservation_id for c in conflicts))
            decision = ReservationDecision(
                status=ReservationDecisionStatus.REJECTED,
                robot_id=str(robot_id),
                resource_id=str(resource_id),
                start_time=float(start_time),
                end_time=float(end_time),
                priority=priority,
                reservation_id=reservation_id,
                conflicting_reservation_ids=ids,
                reason=f"resource conflict with {', '.join(ids)}",
            )
        else:
            decision = ReservationDecision(
                status=ReservationDecisionStatus.GRANTED,
                robot_id=str(robot_id),
                resource_id=str(resource_id),
                start_time=float(start_time),
                end_time=float(end_time),
                priority=priority,
                reservation_id=reservation_id,
                reason="resource and time window available",
            )
        self._decision_log.append(decision)
        return decision

    def _request(
        self,
        robot_id: str,
        resource_id: str,
        start_time: float,
        end_time: float,
        priority: int = 1,
        reservation_id: Optional[str] = None,
        status: ReservationStatus = ReservationStatus.GRANTED,
    ) -> Optional[Reservation]:
        decision = self.evaluate_request(
            robot_id,
            resource_id,
            start_time,
            end_time,
            priority,
            reservation_id=reservation_id,
        )
        if not decision.granted:
            return None

        reservation = Reservation(
            reservation_id=reservation_id or self._new_reservation_id(),
            robot_id=str(robot_id),
            resource_id=str(resource_id),
            start_time=float(start_time),
            end_time=float(end_time),
            priority=int(priority),
            status=status,
        )
        self._reservations.setdefault(resource_id, []).append(reservation)
        return reservation

    def request_cell_reservation(
        self, robot_id: str, cell: Tuple[int, int], start_time: float,
        end_time: float, priority: int = 1
    ) -> Optional[Reservation]:
        return self._request(robot_id, self.cell_resource(cell), start_time, end_time, priority)

    def request_edge_reservation(
        self, robot_id: str, start: Tuple[int, int], end: Tuple[int, int],
        start_time: float, end_time: float, priority: int = 1
    ) -> Optional[Reservation]:
        """Reserve a directed edge while rejecting an overlapping reverse-edge swap."""
        self._validate_interval(start_time, end_time)
        reverse_id = self.edge_resource(end, start)
        reverse_conflicts = self._conflicts_for_resource(reverse_id, start_time, end_time, robot_id)
        if reverse_conflicts:
            # Record the reverse-edge rejection as an authoritative decision.
            self._decision_log.append(
                ReservationDecision(
                    status=ReservationDecisionStatus.REJECTED,
                    robot_id=str(robot_id),
                    resource_id=self.edge_resource(start, end),
                    start_time=float(start_time),
                    end_time=float(end_time),
                    priority=int(priority),
                    conflicting_reservation_ids=tuple(sorted(c.reservation_id for c in reverse_conflicts)),
                    reason="reverse-edge conflict",
                )
            )
            return None
        return self._request(robot_id, self.edge_resource(start, end), start_time, end_time, priority)

    def activate(self, reservation_id: str, current_time: Optional[float] = None) -> Reservation:
        reservation = self._find(reservation_id)
        if reservation.status != ReservationStatus.GRANTED:
            raise ValueError(f"reservation {reservation_id} cannot become ACTIVE from {reservation.status.value}")
        if current_time is not None and not (reservation.start_time <= current_time < reservation.end_time):
            raise ValueError(f"reservation {reservation_id} is outside its active time window")
        reservation.status = ReservationStatus.ACTIVE
        return reservation

    def release(self, reservation_id: str) -> Reservation:
        reservation = self._find(reservation_id)
        if reservation.status not in _ACTIVE_STATUSES:
            raise ValueError(f"reservation {reservation_id} is not releasable from {reservation.status.value}")
        reservation.status = ReservationStatus.RELEASED
        return reservation

    def cancel(self, reservation_id: str) -> Reservation:
        reservation = self._find(reservation_id)
        if reservation.status in _TERMINAL_STATUSES:
            raise ValueError(f"reservation {reservation_id} is already terminal: {reservation.status.value}")
        reservation.status = ReservationStatus.CANCELLED
        return reservation

    def _find(self, reservation_id: str) -> Reservation:
        for res_list in self._reservations.values():
            for reservation in res_list:
                if reservation.reservation_id == reservation_id:
                    return reservation
        raise KeyError(f"unknown reservation: {reservation_id}")

    def _active_at(self, resource_id: str, time_point: float, exclude_robot: Optional[str] = None) -> List[Reservation]:
        return [
            r for r in self._reservations.get(resource_id, [])
            if r.status in _ACTIVE_STATUSES
            and (exclude_robot is None or r.robot_id != exclude_robot)
            and r.start_time <= time_point < r.end_time
        ]

    def get_blocking_robot_ids(
        self,
        resource_id: str,
        start_time: float,
        end_time: float,
        exclude_robot: Optional[str] = None,
    ) -> List[str]:
        """Return deterministic robot IDs holding incompatible reservations."""
        conflicts = self._conflicts_for_resource(
            resource_id, start_time, end_time, exclude_robot
        )
        return sorted({c.robot_id for c in conflicts})

    def get_cell_blockers(
        self,
        cell: Tuple[int, int],
        start_time: float,
        end_time: float,
        exclude_robot: Optional[str] = None,
    ) -> List[str]:
        return self.get_blocking_robot_ids(
            self.cell_resource(cell), start_time, end_time, exclude_robot
        )

    def get_edge_blockers(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        start_time: float,
        end_time: float,
        exclude_robot: Optional[str] = None,
    ) -> List[str]:
        """Return blockers on either direction of an edge."""
        blockers = set(
            self.get_blocking_robot_ids(
                self.edge_resource(start, end), start_time, end_time, exclude_robot
            )
        )
        blockers.update(
            self.get_blocking_robot_ids(
                self.edge_resource(end, start), start_time, end_time, exclude_robot
            )
        )
        return sorted(blockers)

    def is_cell_reserved(self, cell: Tuple[int, int], time_point: float, exclude_robot: Optional[str] = None) -> bool:
        return bool(self._active_at(self.cell_resource(cell), time_point, exclude_robot))

    def is_edge_reserved(self, start: Tuple[int, int], end: Tuple[int, int], time_point: float, exclude_robot: Optional[str] = None) -> bool:
        resource = self.edge_resource(start, end)
        reverse = self.edge_resource(end, start)
        return bool(self._active_at(resource, time_point, exclude_robot) or self._active_at(reverse, time_point, exclude_robot))

    def get_reserved_cells_at(self, time_point: float, exclude_robot: Optional[str] = None) -> Set[Tuple[int, int]]:
        blocked: Set[Tuple[int, int]] = set()
        for resource_id in self._reservations:
            if not resource_id.startswith("cell:"):
                continue
            if self._active_at(resource_id, time_point, exclude_robot):
                x, y = resource_id[5:].split(",")
                blocked.add((int(x), int(y)))
        return blocked

    def release_all_for_robot(self, robot_id: str) -> int:
        released = 0
        for res_list in self._reservations.values():
            for r in res_list:
                if r.robot_id == robot_id and r.status in _ACTIVE_STATUSES:
                    r.status = ReservationStatus.RELEASED
                    released += 1
        return released

    def clean_expired(self, current_time: float) -> int:
        expired = 0
        for res_id, res_list in list(self._reservations.items()):
            kept: List[Reservation] = []
            for r in res_list:
                if r.status in _ACTIVE_STATUSES and r.end_time <= current_time:
                    r.status = ReservationStatus.EXPIRED
                    expired += 1
                if r.status not in _TERMINAL_STATUSES:
                    kept.append(r)
            self._reservations[res_id] = kept
            if not kept:
                del self._reservations[res_id]
        return expired

    def get_all_active(self) -> List[Reservation]:
        return [
            r for res_list in self._reservations.values()
            for r in res_list
            if r.status in _ACTIVE_STATUSES
        ]

    def get_all(self) -> List[Reservation]:
        return [r for res_list in self._reservations.values() for r in res_list]

    def get_decision_log(self) -> List[ReservationDecision]:
        return list(self._decision_log)

    def clear_decision_log(self) -> None:
        self._decision_log.clear()

    def restore(self, reservations: List[Dict]) -> None:
        """Restore serialized reservations without changing their resource identity."""
        self._reservations.clear()
        self._decision_log.clear()
        self._next_id = 1
        for data in reservations:
            resource_id = str(data["resource_id"])
            status = ReservationStatus(str(data.get("status", ReservationStatus.GRANTED.value)))
            if status in _TERMINAL_STATUSES:
                continue
            r = Reservation(
                reservation_id=str(data["reservation_id"]),
                robot_id=str(data["robot_id"]),
                resource_id=resource_id,
                start_time=float(data["start_time"]),
                end_time=float(data["end_time"]),
                priority=int(data.get("priority", 1)),
                status=status,
            )
            self._validate_interval(r.start_time, r.end_time)
            self._reservations.setdefault(resource_id, []).append(r)
            if r.reservation_id.startswith("res_"):
                try:
                    self._next_id = max(self._next_id, int(r.reservation_id.split("_", 1)[1]) + 1)
                except ValueError:
                    pass
