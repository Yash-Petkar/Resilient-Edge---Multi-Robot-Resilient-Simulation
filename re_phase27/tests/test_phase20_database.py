"""Phase 20 SQLite persistence acceptance tests."""
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from backend.database.sqlite_db import SQLiteDatabase


REQUIRED_TABLES = {
    "robots", "tasks", "experiments", "experiment_runs", "faults",
    "incidents", "reservations", "decision_events", "metrics",
}


class TestPhase20Database(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "resilientedge.db")

    def tearDown(self):
        self.tmp.cleanup()

    def test_required_schema_and_foreign_keys(self):
        db = SQLiteDatabase(self.path)
        with db.connection() as conn:
            tables = {
                r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            self.assertTrue(REQUIRED_TABLES.issubset(tables))
            self.assertEqual(conn.execute("PRAGMA foreign_keys").fetchone()[0], 1)
            self.assertIn(
                20,
                {r[0] for r in conn.execute(
                    "SELECT version FROM schema_migrations"
                )},
            )

    def test_initialization_is_idempotent_and_preserves_data(self):
        db = SQLiteDatabase(self.path)
        with db.connection() as conn:
            conn.execute(
                "INSERT INTO reservations(reservation_id, robot_id, resource_id, start_time, end_time, priority, status) "
                "VALUES(?,?,?,?,?,?,?)",
                ("res1", "R1", "cell_1", 1.0, 2.0, 1, "GRANTED"),
            )
            conn.commit()

        SQLiteDatabase(self.path)
        with db.connection() as conn:
            row = conn.execute(
                "SELECT robot_id, resource_id, status FROM reservations WHERE reservation_id='res1'"
            ).fetchone()
            self.assertEqual(tuple(row), ("R1", "cell_1", "GRANTED"))
            self.assertEqual(
                conn.execute("SELECT COUNT(*) FROM schema_migrations WHERE version=20").fetchone()[0],
                1,
            )

    def test_required_indexes_exist(self):
        db = SQLiteDatabase(self.path)
        with db.connection() as conn:
            indexes = {
                r[1] for r in conn.execute(
                    "PRAGMA index_list(reservations)"
                )
            }
            self.assertIn("idx_reservations_resource_time", indexes)
            self.assertIn("idx_reservations_robot_status", indexes)

    def test_transaction_rolls_back_failed_write(self):
        db = SQLiteDatabase(self.path)
        with self.assertRaises(sqlite3.IntegrityError):
            with db.connection() as conn:
                conn.execute(
                    "INSERT INTO reservations(reservation_id, robot_id, resource_id, start_time, end_time, priority, status) "
                    "VALUES(?,?,?,?,?,?,?)",
                    ("dup", "R1", "c", 0, 1, 1, "GRANTED"),
                )
                conn.execute(
                    "INSERT INTO reservations(reservation_id, robot_id, resource_id, start_time, end_time, priority, status) "
                    "VALUES(?,?,?,?,?,?,?)",
                    ("dup", "R2", "c", 1, 2, 1, "GRANTED"),
                )
        with db.connection() as conn:
            self.assertEqual(
                conn.execute("SELECT COUNT(*) FROM reservations WHERE reservation_id='dup'").fetchone()[0],
                0,
            )
