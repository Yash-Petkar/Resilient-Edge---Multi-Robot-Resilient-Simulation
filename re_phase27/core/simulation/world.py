"""Deterministic, configurable warehouse world model.

The world is intentionally independent from the UI and simulation engine.  A
configuration can be supplied as a dictionary or JSON file; the default map
keeps the historical 24x16 topology for backward compatibility.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Set, Tuple

Position = Tuple[int, int]


class WarehouseWorld:
    """Grid world containing static topology and mutable environmental state."""

    DEFAULT_WIDTH = 24
    DEFAULT_HEIGHT = 16

    def __init__(self, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT,
                 config: Optional[Mapping[str, Any]] = None,
                 config_path: Optional[str | Path] = None):
        if config_path is not None:
            with Path(config_path).open("r", encoding="utf-8") as fh:
                config = json.load(fh)
        if config is None:
            config = self.default_config(width=width, height=height)
        self.load_config(config)

    @staticmethod
    def default_config(width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT) -> Dict[str, Any]:
        """Return the deterministic default warehouse configuration."""
        shelves = []
        for x1, x2 in ((6, 7), (11, 12), (16, 17)):
            for y1, y2 in ((2, 4), (6, 8), (10, 12)):
                shelves.extend([list((x, y)) for x in range(x1, x2 + 1) for y in range(y1, y2 + 1)])
        return {
            "width": width,
            "height": height,
            "shelves": shelves,
            "pickup_stations": {"P1": [2, 2], "P2": [2, 6], "P3": [2, 10], "P4": [2, 14]},
            "delivery_stations": {"D1": [21, 2], "D2": [21, 6], "D3": [21, 10], "D4": [21, 14]},
            "charging_bays": {"C1": [11, 0], "C2": [12, 0], "C3": [13, 0], "C4": [14, 0]},
            "robot_starts": [[4 + i * 2, 0] for i in range(10)],
            "restricted_cells": [],
            "choke_points": [[10, 4], [10, 8], [10, 12], [15, 4], [15, 8], [15, 12]],
            "aisles": {"horizontal": [0, 1, 5, 9, 13, 14, 15], "vertical": [0, 1, 2, 3, 4, 5, 8, 9, 10, 13, 14, 15, 18, 19, 20, 21, 22, 23]},
        }

    @staticmethod
    def _positions(values: Iterable[Iterable[int]]) -> Set[Position]:
        return {tuple(map(int, p)) for p in values}

    @staticmethod
    def _station_map(values: Mapping[str, Iterable[int]]) -> Dict[str, Position]:
        return {str(k): tuple(map(int, v)) for k, v in values.items()}

    def load_config(self, config: Mapping[str, Any]) -> None:
        self.width = int(config.get("width", self.DEFAULT_WIDTH))
        self.height = int(config.get("height", self.DEFAULT_HEIGHT))
        if self.width <= 0 or self.height <= 0:
            raise ValueError("warehouse dimensions must be positive")

        self.shelves: Set[Position] = self._positions(config.get("shelves", []))
        self.restricted_cells: Set[Position] = self._positions(config.get("restricted_cells", []))
        self.pickup_stations: Dict[str, Position] = self._station_map(config.get("pickup_stations", {}))
        self.delivery_stations: Dict[str, Position] = self._station_map(config.get("delivery_stations", {}))
        self.charging_bays: Dict[str, Position] = self._station_map(config.get("charging_bays", {}))
        self.robot_starts: list[Position] = [tuple(map(int, p)) for p in config.get("robot_starts", [])]
        self.choke_points: Set[Position] = self._positions(config.get("choke_points", []))
        aisle_cfg = config.get("aisles", {})
        self.aisles: Dict[str, Set[int]] = {
            "horizontal": {int(v) for v in aisle_cfg.get("horizontal", [])},
            "vertical": {int(v) for v in aisle_cfg.get("vertical", [])},
        }

        # Mutable environmental state is intentionally reset on configuration load.
        self.blocked_aisles: Set[Position] = set()
        self.dynamic_obstacles: Set[Position] = set()
        self.validate()

    def validate(self) -> None:
        """Validate topology and station placement before simulation starts."""
        named = {
            "shelves": self.shelves,
            "restricted_cells": self.restricted_cells,
            "choke_points": self.choke_points,
            "robot_starts": set(self.robot_starts),
            "pickup_stations": set(self.pickup_stations.values()),
            "delivery_stations": set(self.delivery_stations.values()),
            "charging_bays": set(self.charging_bays.values()),
        }
        for label, cells in named.items():
            for pos in cells:
                if not self.in_bounds(pos):
                    raise ValueError(f"{label} contains out-of-bounds cell {pos}")
        if self.shelves & self.restricted_cells:
            raise ValueError("shelves and restricted_cells must not overlap")
        occupied_stations = (
            set(self.pickup_stations.values())
            | set(self.delivery_stations.values())
            | set(self.charging_bays.values())
            | set(self.robot_starts)
        )
        if occupied_stations & (self.shelves | self.restricted_cells):
            raise ValueError("stations/start positions must be walkable in the static map")
        for axis, values in self.aisles.items():
            limit = self.height if axis == "horizontal" else self.width
            if any(v < 0 or v >= limit for v in values):
                raise ValueError(f"{axis} aisle index is outside the map")

    @property
    def static_obstacles(self) -> Set[Position]:
        return self.shelves | self.restricted_cells

    @property
    def all_obstacles(self) -> Set[Position]:
        return self.static_obstacles | self.blocked_aisles | self.dynamic_obstacles

    @property
    def operational_cells(self) -> Set[Position]:
        return {
            *self.pickup_stations.values(),
            *self.delivery_stations.values(),
            *self.charging_bays.values(),
        }

    def in_bounds(self, pos: Position) -> bool:
        x, y = pos
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, pos: Position) -> bool:
        return self.in_bounds(pos) and pos not in self.all_obstacles

    def add_dynamic_obstacle(self, pos: Position) -> None:
        pos = tuple(map(int, pos))
        if not self.in_bounds(pos):
            raise ValueError(f"dynamic obstacle outside map: {pos}")
        self.dynamic_obstacles.add(pos)

    def remove_dynamic_obstacle(self, pos: Position) -> None:
        self.dynamic_obstacles.discard(tuple(map(int, pos)))

    def block_cells(self, cells: Iterable[Position]) -> None:
        normalized = {tuple(map(int, p)) for p in cells}
        if any(not self.in_bounds(p) for p in normalized):
            raise ValueError("blocked cell outside warehouse bounds")
        self.blocked_aisles.update(normalized)

    def unblock_cells(self, cells: Iterable[Position]) -> None:
        self.blocked_aisles.difference_update(tuple(map(int, p)) for p in cells)

    def reset_dynamic_state(self) -> None:
        self.blocked_aisles.clear()
        self.dynamic_obstacles.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize complete world configuration plus mutable environmental state."""
        return {
            "width": self.width,
            "height": self.height,
            "shelves": [list(p) for p in sorted(self.shelves)],
            "restricted_cells": [list(p) for p in sorted(self.restricted_cells)],
            "pickup_stations": {k: list(v) for k, v in sorted(self.pickup_stations.items())},
            "delivery_stations": {k: list(v) for k, v in sorted(self.delivery_stations.items())},
            "charging_bays": {k: list(v) for k, v in sorted(self.charging_bays.items())},
            "robot_starts": [list(p) for p in self.robot_starts],
            "choke_points": [list(p) for p in sorted(self.choke_points)],
            "aisles": {k: sorted(v) for k, v in self.aisles.items()},
            "blocked_aisles": [list(p) for p in sorted(self.blocked_aisles)],
            "dynamic_obstacles": [list(p) for p in sorted(self.dynamic_obstacles)],
        }
