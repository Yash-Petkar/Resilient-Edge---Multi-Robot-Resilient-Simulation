"""Unit tests for A* planner."""
import unittest
from core.planning.astar import AStarPlanner


class TestAStar(unittest.TestCase):
    def setUp(self):
        self.planner = AStarPlanner(allow_diagonal=False)

    def test_straight_line_path(self):
        start = (0, 0)
        goal = (4, 0)
        path = self.planner.plan(start, goal, blocked_cells=set(), width=10, height=10)
        self.assertIsNotNone(path)
        self.assertEqual(path[0], start)
        self.assertEqual(path[-1], goal)
        self.assertEqual(len(path), 5)

    def test_obstacle_avoidance(self):
        start = (0, 0)
        goal = (2, 0)
        # Block the direct route at (1, 0)
        blocked = {(1, 0)}
        path = self.planner.plan(start, goal, blocked_cells=blocked, width=5, height=5)
        self.assertIsNotNone(path)
        self.assertNotIn((1, 0), path)
        self.assertEqual(path[0], start)
        self.assertEqual(path[-1], goal)

    def test_unreachable_goal(self):
        start = (0, 0)
        goal = (2, 2)
        # Completely surround goal
        blocked = {(2, 1), (1, 2), (2, 3), (3, 2)}
        path = self.planner.plan(start, goal, blocked_cells=blocked, width=5, height=5)
        self.assertIsNone(path)


if __name__ == "__main__":
    unittest.main()
