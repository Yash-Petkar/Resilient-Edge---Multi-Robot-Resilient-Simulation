"""Future ROS 2 adapter boundary. No ROS 2 dependency is imported locally."""
from __future__ import annotations
from typing import Dict, Any, Tuple
from core.interfaces.robot_interface import RobotCommand


class ROS2RobotAdapter:
    """Placeholder boundary only; implementation belongs on the ROS 2 machine."""
    def __init__(self, robot_id: str, *args, **kwargs):
        self.robot_id = robot_id
        self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def _not_implemented(self):
        raise NotImplementedError("ROS2RobotAdapter is a Phase 7 integration boundary; ROS 2 is not installed locally.")

    def get_state(self): self._not_implemented()
    def send_command(self, command: RobotCommand): self._not_implemented()
    def publish_intent(self, intent: Dict[str, Any]): self._not_implemented()
    def get_position(self) -> Tuple[int, int]: self._not_implemented()
    def get_battery(self): self._not_implemented()
    def stop(self): self._not_implemented()
    def resume(self): self._not_implemented()
