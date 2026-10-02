"""A* Path Planning implementation for grid-based warehouse environments."""
import heapq
import math
from typing import List, Tuple, Set, Dict, Optional


def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> float:
    """Manhattan distance heuristic for grid movement."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


class AStarPlanner:
    def __init__(self, allow_diagonal: bool = False):
        self.allow_diagonal = allow_diagonal

    def plan(
        self,
        start: Tuple[int, int],
        goal: Tuple[int, int],
        blocked_cells: Set[Tuple[int, int]],
        width: int,
        height: int,
        reserved_cells: Optional[Set[Tuple[int, int]]] = None,
    ) -> Optional[List[Tuple[int, int]]]:
        """Plans a path from start to goal avoiding blocked and reserved cells."""
        if start == goal:
            return [start]

        obstacles = set(blocked_cells)
        if reserved_cells:
            obstacles |= reserved_cells

        if start in obstacles:
            # Start itself is blocked (e.g. initial fault), but robot is already there
            obstacles.discard(start)
        if goal in obstacles:
            # Goal is blocked, cannot reach
            return None

        # Movement directions: (dx, dy, cost)
        directions = [(0, 1, 1.0), (1, 0, 1.0), (0, -1, 1.0), (-1, 0, 1.0)]
        if self.allow_diagonal:
            directions += [(1, 1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (-1, -1, 1.414)]

        open_set: List[Tuple[float, float, Tuple[int, int]]] = []
        heapq.heappush(open_set, (heuristic(start, goal), 0.0, start))

        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        g_score: Dict[Tuple[int, int], float] = {start: 0.0}

        while open_set:
            _, current_g, current = heapq.heappop(open_set)

            if current == goal:
                # Reconstruct path
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path

            if current_g > g_score.get(current, float("inf")):
                continue

            for dx, dy, step_cost in directions:
                neighbor = (current[0] + dx, current[1] + dy)
                nx, ny = neighbor

                # Bounds check
                if nx < 0 or nx >= width or ny < 0 or ny >= height:
                    continue

                if neighbor in obstacles:
                    continue

                tentative_g = current_g + step_cost
                if tentative_g < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score, tentative_g, neighbor))

        return None  # No path found

    def path_cost(self, path: List[Tuple[int, int]]) -> float:
        """Calculate total distance/cost of a path."""
        if not path or len(path) < 2:
            return 0.0
        cost = 0.0
        for i in range(len(path) - 1):
            p1 = path[i]
            p2 = path[i + 1]
            cost += math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        return cost

    def estimated_duration(self, path: List[Tuple[int, int]], velocity: float = 1.0) -> float:
        """Calculate estimated traversal duration in seconds."""
        if velocity <= 0.0:
            return float("inf")
        return self.path_cost(path) / velocity
