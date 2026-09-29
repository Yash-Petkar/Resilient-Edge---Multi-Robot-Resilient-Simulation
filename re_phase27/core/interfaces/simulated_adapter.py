"""Current local adapter implementing the future RobotInterface contract."""
from __future__ import annotations
from typing import Dict, Any
from core.interfaces.robot_interface import RobotCommand, RobotTelemetry


class SimulatedRobotAdapter:
    def __init__(self, robot):
        self.robot = robot

    def get_state(self) -> RobotTelemetry:
        return RobotTelemetry(self.robot.robot_id, self.robot.position, self.robot.orientation, self.robot.velocity, self.robot.battery, self.robot.state.value, self.robot.network_status)

    def send_command(self, command: RobotCommand) -> bool:
        if command.robot_id != self.robot.robot_id:
            return False
        if command.command == "STOP":
            return self.stop()
        if command.command == "RESUME":
            return self.resume()
        return True

    def publish_intent(self, intent: Dict[str, Any]) -> bool:
        return bool(intent)

    def get_position(self): return self.robot.position
    def get_battery(self): return self.robot.battery

    def stop(self) -> bool:
        if self.robot.state.value == "FAILED":
            return False
        self.robot.state = type(self.robot.state).PAUSED
        return True

    def resume(self) -> bool:
        if self.robot.state.value == "FAILED":
            return False
        if self.robot.state.value == "PAUSED":
            self.robot.state = type(self.robot.state).PLANNING if self.robot.current_task else type(self.robot.state).IDLE
        return True
