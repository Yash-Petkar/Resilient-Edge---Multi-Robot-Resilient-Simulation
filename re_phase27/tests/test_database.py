"""Unit and integration tests for SQLite persistent database and clear operations."""
import unittest
import os
import sqlite3
import tempfile
from pathlib import Path
from backend.database.sqlite_db import SQLiteDatabase, default_database_path


class TestSQLiteDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_resilientedge.db")
        self.db = SQLiteDatabase(db_path=self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass
        if os.path.exists(self.temp_dir):
            try:
                os.rmdir(self.temp_dir)
            except Exception:
                pass

    def test_database_initialization(self):
        """Test tables are created upon initialization."""
        stats = self.db.get_stats()
        self.assertIn("robots", stats)
        self.assertIn("tasks", stats)
        self.assertIn("incidents", stats)
        self.assertIn("decision_events", stats)
        self.assertEqual(stats["storage_mode"], "SQLite (Local Transactional)")

    def test_default_database_path_is_repository_relative(self):
        expected_path = Path(__file__).resolve().parents[1] / "data" / "resilientedge.db"
        self.assertEqual(default_database_path(), expected_path)

    def test_connection_context_closes_connection(self):
        with self.db.connection() as conn:
            self.assertEqual(conn.execute("SELECT 1").fetchone()[0], 1)
        with self.assertRaises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")

    def test_save_and_retrieve_telemetry(self):
        """Test persisting and reading telemetry data."""
        telemetry = {
            "timestamp": 12.5,
            "robots": [
                {
                    "robot_id": "R1",
                    "position": [4, 2],
                    "state": "IDLE",
                    "battery": 95.0,
                    "health": 1.0,
                    "current_task": "T01",
                },
                {
                    "robot_id": "R2",
                    "position": [8, 6],
                    "state": "MOVING",
                    "battery": 88.0,
                    "health": 1.0,
                    "current_task": "T02",
                },
            ],
            "tasks": [
                {
                    "task_id": "T01",
                    "pickup": [2, 2],
                    "delivery": [21, 2],
                    "priority": 3,
                    "deadline": 300.0,
                    "status": "IN_PROGRESS",
                    "assigned_robot": "R1",
                    "creation_time": 0.0,
                }
            ],
            "incidents": [
                {
                    "incident_id": "inc_test_1",
                    "timestamp": 10.0,
                    "entity": "R1",
                    "fault": "TASK_ASSIGNED",
                    "severity": "INFO",
                    "state": "NORMAL",
                    "message": "Task T01 assigned to R1",
                }
            ],
        }

        self.db.save_telemetry_snapshot(telemetry)
        stats = self.db.get_stats()
        self.assertEqual(stats["robots"], 2)
        self.assertEqual(stats["tasks"], 1)
        self.assertEqual(stats["incidents"], 1)

        robots = self.db.get_robots()
        self.assertEqual(len(robots), 2)
        self.assertEqual(robots[0]["robot_id"], "R1")

        incidents = self.db.get_incidents()
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0]["entity"], "R1")

    def test_save_and_get_decision_event(self):
        """Test logging explainable decision events."""
        event = {
            "event_type": "ROBOT_REASSIGNMENT",
            "robot_id": "R1",
            "task_id": "T01",
            "timestamp": 15.2,
            "details": {"replacement_robot": "R2", "distance": 4.5, "battery": 92.0},
        }
        self.db.save_decision_event(event)
        events = self.db.get_decision_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["robot_id"], "R1")
        self.assertEqual(events[0]["task_id"], "T01")

    def test_clear_all(self):
        """Test clearing all records across tables."""
        telemetry = {
            "timestamp": 1.0,
            "robots": [{"robot_id": "R1", "position": [0, 0], "state": "IDLE", "battery": 100, "health": 1}],
            "tasks": [{"task_id": "T01", "pickup": [1, 1], "delivery": [2, 2], "priority": 1, "status": "AVAILABLE"}],
            "incidents": [{"incident_id": "inc_1", "timestamp": 1.0, "entity": "SYS", "severity": "INFO", "message": "Init"}],
        }
        self.db.save_telemetry_snapshot(telemetry)
        stats_before = self.db.get_stats()
        self.assertGreater(stats_before["robots"], 0)

        self.db.clear_all()
        stats_after = self.db.get_stats()
        self.assertEqual(stats_after["robots"], 0)
        self.assertEqual(stats_after["tasks"], 0)
        self.assertEqual(stats_after["incidents"], 0)


if __name__ == "__main__":
    unittest.main()
