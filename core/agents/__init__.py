"""Independent robot-agent architecture for ResilientEdge.

Each simulated AMR owns a RobotAgent instance. The agent is the boundary for
local state, planning, intent, peer knowledge, reservations, conflict and
recovery state, and transport state. The simulation engine may orchestrate
world/clock execution, but must not be treated as the robot's decision owner.
"""

from .robot_agent import RobotAgent, AgentIntent, PeerState

__all__ = ["RobotAgent", "AgentIntent", "PeerState"]
