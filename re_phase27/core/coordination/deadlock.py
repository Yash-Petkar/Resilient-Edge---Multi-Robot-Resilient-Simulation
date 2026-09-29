"""Deadlock detection and deterministic recovery via Wait-For Graphs (WFG)."""
from __future__ import annotations

from typing import Dict, Iterable, List, Set, Tuple, Optional, Union


WaitTargets = Union[Optional[str], Iterable[str]]


class DeadlockDetector:
    """Build and analyze a robot wait-for graph.

    An edge A -> B means robot A cannot make progress until robot B releases
    a resource or changes its trajectory.  The detector is deliberately
    independent of the simulation engine so it can later be reused by ROS 2
    adapters.
    """

    def __init__(self):
        self.wait_for_graph: Dict[str, Set[str]] = {}
        self.last_cycles: List[List[str]] = []

    def build_graph(self, robot_waiting_on: Dict[str, WaitTargets]):
        """Construct a deterministic WFG from one or more blocking robots."""
        self.wait_for_graph = {}
        for waiter, targets in robot_waiting_on.items():
            if targets is None:
                continue
            if isinstance(targets, str):
                normalized = [targets]
            else:
                normalized = list(targets)
            for blocker in sorted({str(t) for t in normalized if t and str(t) != str(waiter)}):
                self.wait_for_graph.setdefault(str(waiter), set()).add(blocker)
                self.wait_for_graph.setdefault(blocker, set())

        # Keep all known nodes, including robots that are only blockers.
        for node in list(self.wait_for_graph):
            self.wait_for_graph.setdefault(node, set())

    def find_cycles(self) -> List[List[str]]:
        """Find deterministic directed cycles using DFS.

        Each simple cycle is normalized by its lexicographically smallest
        robot ID so the same cycle is not reported multiple times because of
        traversal order.
        """
        visited: Set[str] = set()
        stack: List[str] = []
        active: Set[str] = set()
        found: Set[Tuple[str, ...]] = set()

        def dfs(node: str):
            visited.add(node)
            active.add(node)
            stack.append(node)

            for neighbor in sorted(self.wait_for_graph.get(node, set())):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in active:
                    start = stack.index(neighbor)
                    cycle = stack[start:].copy()
                    if cycle:
                        pivot = min(range(len(cycle)), key=lambda i: cycle[i])
                        normalized = tuple(cycle[pivot:] + cycle[:pivot])
                        found.add(normalized)

            stack.pop()
            active.remove(node)

        for node in sorted(self.wait_for_graph):
            if node not in visited:
                dfs(node)

        self.last_cycles = [list(c) for c in sorted(found)]
        return [list(c) for c in self.last_cycles]

    def resolve_deadlock(
        self,
        cycle: List[str],
        robot_priorities: Dict[str, int],
    ) -> Tuple[str, str]:
        """Choose one deterministic victim and return its recovery action.

        Lower task priority yields first; robot ID is the deterministic tie
        breaker. The caller performs the actual reservation release and
        replanning.
        """
        if not cycle:
            return ("", "NO_ACTION")
        victim = min(cycle, key=lambda r: (robot_priorities.get(r, 1), r))
        return (victim, "BACKOFF_AND_REPLAN")

    def graph_snapshot(self) -> Dict[str, List[str]]:
        """Return a stable, JSON-serializable WFG snapshot."""
        return {node: sorted(targets) for node, targets in sorted(self.wait_for_graph.items())}
