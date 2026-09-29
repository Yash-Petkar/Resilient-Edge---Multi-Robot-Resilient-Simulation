"""Deterministic fault injection engine for the ResilientEdge simulation.

Phase 12 makes injected faults authoritative simulation inputs.  Faults are
represented as data, can be scheduled or injected immediately, expire
deterministically, and expose effective conditions consumed by the simulation
engine/network simulator.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Any, Set, Tuple

from core.models.fault import Fault, FaultType


class FaultEngine:
    """Own the lifecycle of scheduled, active and historical simulation faults."""

    _DEFAULTS = {
        "packet_loss": 0.001,
        "latency": 0.012,
        "jitter": 0.002,
        "duplication": 0.0,
        "reordering": 0.0,
    }

    def __init__(self):
        self.active_faults: Dict[str, Fault] = {}
        self.pending_faults: Dict[str, Fault] = {}
        self.fault_history: List[Fault] = []
        self._next_id = 1
        self.last_activated: List[Fault] = []
        self.last_resolved: List[Fault] = []

    def _new_fault_id(self) -> str:
        fault_id = f"flt_{self._next_id:06d}"
        self._next_id += 1
        return fault_id

    @staticmethod
    def _validate_duration(duration: float) -> None:
        if duration < 0:
            raise ValueError("fault duration must be >= 0")

    @staticmethod
    def _validate_probability(value: float, name: str) -> float:
        value = float(value)
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be between 0 and 1")
        return value

    def _build_fault(
        self,
        fault_type: FaultType,
        target: str,
        start_time: float,
        duration: float,
        parameters: Optional[Dict[str, Any]],
        status: str,
    ) -> Fault:
        self._validate_duration(duration)
        if not isinstance(fault_type, FaultType):
            fault_type = FaultType(fault_type)
        params = dict(parameters or {})
        # Validate probability-bearing parameters at injection time rather than
        # allowing invalid network conditions to reach the simulator.
        for key in ("rate", "loss_rate", "duplication_rate", "reorder_rate"):
            if key in params:
                params[key] = self._validate_probability(params[key], key)
        for key in ("latency_seconds", "latency", "jitter_seconds", "jitter"):
            if key in params and float(params[key]) < 0:
                raise ValueError(f"{key} must be >= 0")

        fault = Fault(
            fault_id=self._new_fault_id(),
            fault_type=fault_type,
            target=str(target),
            start_time=float(start_time),
            duration=float(duration),
            parameters=params,
            status=status,
        )
        self.fault_history.append(fault)
        return fault

    def inject_fault(
        self,
        fault_type: FaultType,
        target: str,
        start_time: float,
        duration: float = 30.0,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Fault:
        """Inject and activate a fault immediately.

        This preserves the Phase 7-11 API used by the REST endpoint and tests.
        Use :meth:`schedule_fault` when the fault must begin in the future.
        """
        fault = self._build_fault(
            fault_type, target, start_time, duration, parameters, "ACTIVE"
        )
        self.active_faults[fault.fault_id] = fault
        return fault

    def schedule_fault(
        self,
        fault_type: FaultType,
        target: str,
        start_time: float,
        duration: float = 30.0,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Fault:
        """Create a future fault that becomes active when simulation time reaches start_time."""
        fault = self._build_fault(
            fault_type, target, start_time, duration, parameters, "PENDING"
        )
        self.pending_faults[fault.fault_id] = fault
        return fault

    def clear_fault(self, fault_id: str) -> Optional[Fault]:
        """Manually clear an active or pending fault."""
        fault = self.active_faults.pop(fault_id, None)
        if fault is None:
            fault = self.pending_faults.pop(fault_id, None)
        if fault is None:
            return None
        fault.status = "CLEARED"
        return fault

    def clear_all(self) -> List[Fault]:
        """Clear all currently active and pending faults."""
        cleared: List[Fault] = []
        for fid in list(self.active_faults) + list(self.pending_faults):
            fault = self.clear_fault(fid)
            if fault is not None:
                cleared.append(fault)
        return cleared

    def update(self, current_time: float) -> List[Fault]:
        """Advance fault lifecycle and return faults that resolved this tick."""
        now = float(current_time)
        self.last_activated = []
        self.last_resolved = []

        # Activate scheduled faults deterministically by start time then ID.
        for fid, fault in sorted(
            list(self.pending_faults.items()),
            key=lambda item: (item[1].start_time, item[0]),
        ):
            if now >= fault.start_time:
                fault.status = "ACTIVE"
                self.active_faults[fid] = self.pending_faults.pop(fid)
                self.last_activated.append(fault)

        for fid, fault in sorted(list(self.active_faults.items())):
            if fault.duration > 0 and now >= fault.start_time + fault.duration:
                fault.status = "RESOLVED"
                self.last_resolved.append(self.active_faults.pop(fid))

        return list(self.last_resolved)

    def _active(self, fault_type: FaultType, target: Optional[str] = None) -> List[Fault]:
        return [
            f for f in self.active_faults.values()
            if f.status == "ACTIVE"
            and f.fault_type == fault_type
            and (target is None or f.target in (target, "*", "network"))
        ]

    def is_robot_failed(self, robot_id: str) -> bool:
        return bool(self._active(FaultType.ROBOT_FAILURE, robot_id))

    def is_low_battery(self, robot_id: str) -> bool:
        return bool(self._active(FaultType.LOW_BATTERY, robot_id))

    def get_blocked_cells(self) -> Set[Tuple[int, int]]:
        cells: Set[Tuple[int, int]] = set()
        for fault in self._active(FaultType.BLOCKED_AISLE):
            raw = fault.parameters.get("cells")
            if raw is None:
                raw = [fault.target] if fault.target.startswith("cell:") else []
            for cell in raw:
                if isinstance(cell, str) and cell.startswith("cell:"):
                    cell = cell[5:]
                if isinstance(cell, str):
                    x, y = cell.split(",")
                    cells.add((int(x), int(y)))
                else:
                    cells.add(tuple(map(int, cell)))
        return cells

    def get_dynamic_obstacles(self) -> Set[Tuple[int, int]]:
        obstacles: Set[Tuple[int, int]] = set()
        for fault in self._active(FaultType.DYNAMIC_OBSTACLE):
            raw = fault.parameters.get("position")
            if raw is None and fault.target.startswith("cell:"):
                raw = fault.target[5:]
            if raw is not None:
                if isinstance(raw, str):
                    x, y = raw.split(",")
                    obstacles.add((int(x), int(y)))
                else:
                    obstacles.add(tuple(map(int, raw)))
        return obstacles

    @staticmethod
    def _max_condition(
        faults: List[Fault],
        default: float,
        *keys: str,
    ) -> float:
        values = []
        for fault in faults:
            for key in keys:
                if key in fault.parameters:
                    values.append(float(fault.parameters[key]))
                    break
        return max(values) if values else default

    def get_packet_loss_rate(self) -> float:
        faults = self._active(FaultType.PACKET_LOSS)
        return min(1.0, self._max_condition(faults, self._DEFAULTS["packet_loss"], "rate", "loss_rate"))

    def get_network_latency(self) -> float:
        faults = self._active(FaultType.LATENCY)
        return max(0.001, self._max_condition(faults, self._DEFAULTS["latency"], "latency_seconds", "latency"))

    def get_network_jitter(self) -> float:
        faults = self._active(FaultType.JITTER)
        return max(0.0, self._max_condition(faults, self._DEFAULTS["jitter"], "jitter_seconds", "jitter"))

    def get_message_duplication_rate(self) -> float:
        faults = self._active(FaultType.MESSAGE_DUPLICATION)
        return min(1.0, self._max_condition(faults, 0.0, "rate", "duplication_rate"))

    def get_message_reordering_rate(self) -> float:
        faults = self._active(FaultType.MESSAGE_REORDERING)
        return min(1.0, self._max_condition(faults, 0.0, "rate", "reorder_rate"))

    def is_network_partitioned(self) -> bool:
        return bool(self._active(FaultType.NETWORK_PARTITION))

    def get_partition_groups(self) -> Tuple[Set[str], Set[str]]:
        faults = self._active(FaultType.NETWORK_PARTITION)
        if not faults:
            return (set(), set())
        fault = sorted(faults, key=lambda f: f.fault_id)[0]
        group_a = set(map(str, fault.parameters.get("group_a", ["R1"])))
        group_b = set(map(str, fault.parameters.get("group_b", ["R2", "R3"])))
        return (group_a, group_b)

    def get_active_effects(self) -> Dict[str, Any]:
        """Expose effective fault conditions for authoritative telemetry."""
        return {
            "robot_failures": sorted(
                f.target for f in self._active(FaultType.ROBOT_FAILURE)
            ),
            "low_battery": sorted(
                f.target for f in self._active(FaultType.LOW_BATTERY)
            ),
            "blocked_cells": [list(c) for c in sorted(self.get_blocked_cells())],
            "dynamic_obstacles": [list(c) for c in sorted(self.get_dynamic_obstacles())],
            "network": {
                "packet_loss": self.get_packet_loss_rate(),
                "latency": self.get_network_latency(),
                "jitter": self.get_network_jitter(),
                "duplication": self.get_message_duplication_rate(),
                "reordering": self.get_message_reordering_rate(),
                "partitioned": self.is_network_partitioned(),
            },
        }

    def restore(self, data: Dict[str, Any]) -> None:
        """Restore active/pending faults without changing their IDs."""
        self.active_faults.clear()
        self.pending_faults.clear()
        self.fault_history.clear()
        self.last_activated = []
        self.last_resolved = []

        def restore_one(item: Dict[str, Any]) -> Fault:
            fault = Fault(
                fault_id=str(item["fault_id"]),
                fault_type=FaultType(item["fault_type"]),
                target=str(item["target"]),
                start_time=float(item.get("start_time", 0.0)),
                duration=float(item.get("duration", 30.0)),
                parameters=dict(item.get("parameters", {})),
                status=str(item.get("status", "ACTIVE")),
            )
            self.fault_history.append(fault)
            return fault

        for item in data.get("active", []):
            fault = restore_one(item)
            self.active_faults[fault.fault_id] = fault
        for item in data.get("pending", []):
            fault = restore_one(item)
            self.pending_faults[fault.fault_id] = fault
        # Backward compatibility with pre-Phase-12 snapshots.
        if not data.get("active") and not data.get("pending") and data.get("faults"):
            for item in data["faults"]:
                fault = restore_one(item)
                self.active_faults[fault.fault_id] = fault

        max_seen = 0
        for fault in self.fault_history:
            try:
                max_seen = max(max_seen, int(fault.fault_id.split("_")[-1]))
            except (ValueError, IndexError):
                pass
        self._next_id = max(int(data.get("next_id", 1)), max_seen + 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "active": [f.to_dict() for f in self.active_faults.values()],
            "pending": [f.to_dict() for f in self.pending_faults.values()],
            "history": [f.to_dict() for f in self.fault_history[-200:]],
            "next_id": self._next_id,
        }
