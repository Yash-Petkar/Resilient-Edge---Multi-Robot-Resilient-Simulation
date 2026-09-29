"""Stable execution boundary between coordination and robot transports."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Tuple, Optional, Dict, Any


@dataclass(frozen=True)
class RobotCommand:
    robot_id: str
    command: str
    target: Optional[Tuple[int, int]] = None
    payload: Dict[str, Any] | None = None


@dataclass(frozen=True)
class RobotTelemetry:
    robot_id: str
    position: Tuple[int, int]
    orientation: float
    velocity: float
    battery: float
    state: str
    communication_status: str


class RobotInterface(Protocol):
    def get_state(self) -> RobotTelemetry: ...
    def send_command(self, command: RobotCommand) -> bool: ...
    def publish_intent(self, intent: Dict[str, Any]) -> bool: ...
    def get_position(self) -> Tuple[int, int]: ...
    def get_battery(self) -> float: ...
    def stop(self) -> bool: ...
    def resume(self) -> bool: ...
