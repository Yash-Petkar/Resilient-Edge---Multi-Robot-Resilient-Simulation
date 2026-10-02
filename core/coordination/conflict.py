"""Conflict detection for multi-robot path reservation and execution."""
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Dict, Optional


class ConflictType(str, Enum):
    VERTEX = "VERTEX"        # Two robots in the same cell at the same time
    EDGE = "EDGE"            # Two robots crossing the same edge in opposite directions
    CROSSING = "CROSSING"    # Path intersection without adequate separation
    RESOURCE = "RESOURCE"    # Incompatible resource request


@dataclass
class Conflict:
    conflict_type: ConflictType
    robot_a: str
    robot_b: str
    location: Tuple[int, int]
    time_step: float
    description: str


class ConflictDetector:
    @staticmethod
    def detect_trajectory_conflicts(
        trajectories: Dict[str, List[Tuple[int, int]]],
        current_time: float,
        dt: float = 1.0,
    ) -> List[Conflict]:
        """
        Detects vertex and edge conflicts between planned trajectories of robots.
        trajectories: map of robot_id -> list of positions at time current_time + i*dt
        """
        conflicts: List[Conflict] = []
        robot_ids = sorted(trajectories.keys())

        for i in range(len(robot_ids)):
            r_a = robot_ids[i]
            traj_a = trajectories[r_a]

            for j in range(i + 1, len(robot_ids)):
                r_b = robot_ids[j]
                traj_b = trajectories[r_b]

                min_len = min(len(traj_a), len(traj_b))
                for step in range(min_len):
                    t = current_time + step * dt
                    pos_a = traj_a[step]
                    pos_b = traj_b[step]

                    # 1. Vertex Conflict (same cell at same step)
                    if pos_a == pos_b:
                        conflicts.append(
                            Conflict(
                                conflict_type=ConflictType.VERTEX,
                                robot_a=r_a,
                                robot_b=r_b,
                                location=pos_a,
                                time_step=t,
                                description=f"Vertex conflict at {pos_a} between {r_a} and {r_b} at t={t:.1f}s",
                            )
                        )

                    # 2. Edge Conflict (swap cells in opposite directions between step-1 and step)
                    if step > 0:
                        prev_a = traj_a[step - 1]
                        prev_b = traj_b[step - 1]
                        if prev_a == pos_b and prev_b == pos_a:
                            conflicts.append(
                                Conflict(
                                    conflict_type=ConflictType.EDGE,
                                    robot_a=r_a,
                                    robot_b=r_b,
                                    location=pos_a,
                                    time_step=t,
                                    description=f"Edge head-on swap conflict between {prev_a} and {pos_a} between {r_a} and {r_b} at t={t:.1f}s",
                                )
                            )

        return conflicts
