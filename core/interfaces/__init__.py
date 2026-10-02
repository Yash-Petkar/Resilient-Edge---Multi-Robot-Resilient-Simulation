"""Robot execution interfaces; ROS 2 remains an optional future adapter."""
from .robot_interface import RobotInterface, RobotCommand, RobotTelemetry
from .simulated_adapter import SimulatedRobotAdapter
from .ros2_adapter import ROS2RobotAdapter

__all__ = ["RobotInterface", "RobotCommand", "RobotTelemetry", "SimulatedRobotAdapter", "ROS2RobotAdapter"]
