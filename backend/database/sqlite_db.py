"""SQLite database persistence for ResilientEdge."""
import json
import sqlite3
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Any, Optional


def default_database_path() -> Path:
    configured = os.getenv("DATABASE_PATH", "").strip()
    if configured:
        path = Path(configured)
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[2] / path
        return path
    return Path(__file__).resolve().parents[2] / "data" / "resilientedge.db"


class ResilientEdgeDatabase:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(Path(db_path) if db_path is not None else default_database_path())
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def connection(self):
        conn = self.get_connection()
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def init_db(self):
        """Creates tables if they do not exist."""
        with self.connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                full_name TEXT,
                role TEXT NOT NULL DEFAULT 'OBSERVER' CHECK(role IN ('ADMIN','OPERATOR','OBSERVER','VIEWER')),
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                FOREIGN KEY(id) REFERENCES users(id) ON DELETE CASCADE
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                log_id TEXT PRIMARY KEY,
                user_id TEXT,
                user_role TEXT,
                action TEXT NOT NULL,
                entity_type TEXT,
                entity_id TEXT,
                metadata TEXT,
                created_at REAL NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
            );
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_profiles_role ON profiles(role)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_logs(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_logs(user_id)")
            cursor.execute("""CREATE TABLE IF NOT EXISTS auth_sessions (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL, refresh_token_hash TEXT NOT NULL UNIQUE,
                created_at REAL NOT NULL, expires_at REAL NOT NULL, revoked_at REAL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )""")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id ON auth_sessions(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_auth_sessions_expires_at ON auth_sessions(expires_at)")

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS robots (
                robot_id TEXT PRIMARY KEY,
                position TEXT,
                state TEXT,
                battery REAL,
                health REAL,
                current_task TEXT,
                network_status TEXT,
                updated_at REAL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                pickup TEXT,
                delivery TEXT,
                priority INTEGER,
                deadline REAL,
                status TEXT,
                assigned_robot TEXT,
                creation_time REAL,
                start_time REAL,
                completion_time REAL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
                experiment_id TEXT PRIMARY KEY,
                scenario TEXT,
                seed INTEGER,
                robot_count INTEGER,
                task_count INTEGER,
                start_time REAL,
                end_time REAL,
                status TEXT,
                metrics TEXT
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiment_runs (
                run_id TEXT PRIMARY KEY,
                experiment_id TEXT,
                scenario TEXT,
                status TEXT,
                duration REAL,
                metrics TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS faults (
                fault_id TEXT PRIMARY KEY,
                fault_type TEXT,
                target TEXT,
                start_time REAL,
                duration REAL,
                parameters TEXT,
                status TEXT
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                incident_id TEXT PRIMARY KEY,
                timestamp REAL,
                entity TEXT,
                fault TEXT,
                severity TEXT,
                state TEXT,
                message TEXT
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS reservations (
                reservation_id TEXT PRIMARY KEY,
                robot_id TEXT,
                resource_id TEXT,
                start_time REAL,
                end_time REAL,
                priority INTEGER,
                status TEXT
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS decision_events (
                event_id TEXT PRIMARY KEY,
                timestamp REAL,
                component TEXT,
                action TEXT,
                details TEXT
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                timestamp REAL,
                completion_rate REAL,
                makespan REAL,
                conflicts INTEGER,
                deadlocks INTEGER,
                metrics_json TEXT
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS simulations (
                simulation_id TEXT PRIMARY KEY,
                name TEXT,
                status TEXT,
                config TEXT,
                created_at REAL,
                updated_at REAL
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS simulation_runs (
                run_id TEXT PRIMARY KEY,
                simulation_id TEXT,
                name TEXT,
                status TEXT,
                config TEXT,
                start_time REAL,
                end_time REAL,
                final_metrics TEXT,
                created_at REAL
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS telemetry_events (
                event_id TEXT PRIMARY KEY,
                run_id TEXT,
                timestamp REAL,
                simulation_time REAL,
                event_type TEXT,
                robot_id TEXT,
                task_id TEXT,
                payload TEXT,
                created_at REAL
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS network_events (
                event_id TEXT PRIMARY KEY,
                run_id TEXT,
                timestamp REAL,
                event_type TEXT,
                sender TEXT,
                recipient TEXT,
                latency REAL,
                packet_loss REAL,
                jitter REAL,
                details TEXT,
                created_at REAL
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS recovery_actions (
                action_id TEXT PRIMARY KEY,
                run_id TEXT,
                timestamp REAL,
                robot_id TEXT,
                fault_id TEXT,
                recovery_strategy TEXT,
                duration REAL,
                status TEXT,
                details TEXT
            );
            """)
            # Phase 20 schema versioning and query indexes.  The migration ledger is
            # idempotent so initialization can safely run against an existing database.
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at REAL NOT NULL
            );
            """)
            import time as _schema_time
            cursor.execute(
                "INSERT OR IGNORE INTO schema_migrations(version, name, applied_at) VALUES(?,?,?)",
                (20, "phase20_persistence_schema", _schema_time.time()),
            )
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_experiment_runs_experiment ON experiment_runs(experiment_id)",
                "CREATE INDEX IF NOT EXISTS idx_experiment_runs_scenario ON experiment_runs(scenario)",
                "CREATE INDEX IF NOT EXISTS idx_faults_target_status ON faults(target, status)",
                "CREATE INDEX IF NOT EXISTS idx_incidents_timestamp ON incidents(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_reservations_robot_status ON reservations(robot_id, status)",
                "CREATE INDEX IF NOT EXISTS idx_reservations_resource_time ON reservations(resource_id, start_time, end_time)",
                "CREATE INDEX IF NOT EXISTS idx_decision_events_timestamp ON decision_events(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_metrics_run_timestamp ON metrics(run_id, timestamp)",
            ]
            for statement in indexes:
                cursor.execute(statement)

            # Lightweight forward migrations for databases created by older builds.
            existing_columns = {row[1] for row in cursor.execute("PRAGMA table_info(metrics)").fetchall()}
            if "run_id" not in existing_columns:
                cursor.execute("ALTER TABLE metrics ADD COLUMN run_id TEXT")
            migration = Path(__file__).resolve().parent / "migrations" / "001_auth_rbac.sql"
            if migration.exists():
                conn.executescript(migration.read_text(encoding="utf-8"))
            conn.commit()

    def save_incident(self, inc: Dict[str, Any]):
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO incidents (incident_id, timestamp, entity, fault, severity, state, message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    inc.get("incident_id"),
                    inc.get("timestamp"),
                    inc.get("entity"),
                    inc.get("fault"),
                    inc.get("severity"),
                    inc.get("state"),
                    inc.get("message"),
                ),
            )
            conn.commit()

    def save_recovery_event(self, event: Dict[str, Any]):
        import time as _time
        with self.connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO recovery_actions (action_id, run_id, timestamp, robot_id, fault_id, recovery_strategy, duration, status, details) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (event.get("event_id") or event.get("action_id") or f"rec_{_time.time_ns()}", event.get("run_id"), event.get("timestamp", 0), event.get("robot_id") or event.get("entity") or "SYSTEM", event.get("fault_id"), event.get("recovery_strategy", "RECOVERY"), event.get("duration", 0), event.get("status", "SUCCESS"), json.dumps(event.get("details", {}))),
            )
            conn.commit()

    def get_incidents(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM incidents ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def save_experiment(self, exp: Dict[str, Any]):
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO experiments (experiment_id, scenario, seed, robot_count, task_count, start_time, end_time, status, metrics)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    exp.get("experiment_id"),
                    exp.get("scenario"),
                    exp.get("seed", 42),
                    exp.get("robot_count", 3),
                    exp.get("task_count", 6),
                    exp.get("start_time", 0.0),
                    exp.get("end_time"),
                    exp.get("status", "COMPLETED"),
                    json.dumps(exp.get("metrics", {})),
                ),
            )
            conn.commit()

    def get_experiments(self) -> List[Dict[str, Any]]:
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM experiments ORDER BY start_time DESC")
            rows = cursor.fetchall()
            result = []
            for r in rows:
                item = dict(r)
                if item.get("metrics"):
                    try:
                        item["metrics"] = json.loads(item["metrics"])
                    except Exception:
                        pass
                result.append(item)
            return result

    def sync_telemetry(self, telemetry: Dict[str, Any], run_id: Optional[str] = None):
        """Persists latest robots, tasks, faults, and incidents from telemetry snapshot."""
        with self.connection() as conn:
            cursor = conn.cursor()
            now = telemetry.get("timestamp", 0.0)

            # Robots
            for r in telemetry.get("robots", []):
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO robots (robot_id, position, state, battery, health, current_task, network_status, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        r["robot_id"],
                        json.dumps(r.get("position", [0, 0])),
                        r.get("state", "IDLE"),
                        r.get("battery", 100.0),
                        r.get("health", 1.0),
                        r.get("current_task"),
                        r.get("network_status", "CONNECTED"),
                        now,
                    ),
                )

            # Tasks
            for t in telemetry.get("tasks", []):
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO tasks (task_id, pickup, delivery, priority, deadline, status, assigned_robot, creation_time, start_time, completion_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        t["task_id"],
                        json.dumps(t.get("pickup", [0, 0])),
                        json.dumps(t.get("delivery", [0, 0])),
                        t.get("priority", 1),
                        t.get("deadline", 300.0),
                        t.get("status", "AVAILABLE"),
                        t.get("assigned_robot"),
                        t.get("creation_time", 0.0),
                        t.get("start_time"),
                        t.get("completion_time"),
                    ),
                )

            # Incidents
            for inc in telemetry.get("incidents", []):
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO incidents (incident_id, timestamp, entity, fault, severity, state, message)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        inc.get("incident_id"), inc.get("timestamp"), inc.get("entity"), inc.get("fault"),
                        inc.get("severity"), inc.get("state"), inc.get("message"),
                    ),
                )

            # Important simulation state is also retained as append-only telemetry.
            import time as _time
            event_id = f"telemetry_{run_id or 'local'}_{int(now * 1000)}"
            cursor.execute(
                "INSERT OR REPLACE INTO telemetry_events (event_id, run_id, timestamp, simulation_time, event_type, payload, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (event_id, run_id, now, now, "telemetry_snapshot", json.dumps(telemetry), _time.time()),
            )
            metrics = telemetry.get("metrics", {})
            cursor.execute(
                "INSERT INTO metrics (run_id, timestamp, completion_rate, makespan, conflicts, deadlocks, metrics_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (run_id, now, metrics.get("task_completion_rate", 0), metrics.get("makespan", 0),
                 metrics.get("conflict_count", 0), metrics.get("deadlock_count", 0), json.dumps(metrics)),
            )
            conn.commit()

    def health_check(self) -> Dict[str, Any]:
        import time as _time
        started=_time.perf_counter()
        try:
            with self.connection() as conn: conn.execute("SELECT 1").fetchone()
            return {"provider":"local","connected":True,"database":"sqlite","status":"online","storage_mode":"SQLite (Local Persistent)","latency_ms":round((_time.perf_counter()-started)*1000,2)}
        except Exception as exc:
            return {"provider":"error","connected":False,"database":"sqlite","status":"error","storage_mode":"SQLite (Unavailable)","last_error":str(exc)}

    def get_stats(self) -> Dict[str, Any]:
        """Returns actual row counts and storage metrics across all database tables."""
        with self.connection() as conn:
            cursor = conn.cursor()
            stats = {}
            for table in ["robots", "tasks", "faults", "incidents", "experiments", "experiment_runs", "reservations", "decision_events", "metrics", "simulations", "simulation_runs", "telemetry_events", "network_events", "recovery_actions", "schema_migrations"]:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[table] = cursor.fetchone()[0]
                except Exception:
                    stats[table] = 0
            stats["storage_mode"] = "SQLite (Local Transactional)"
            return stats

    def get_robots(self) -> List[Dict[str, Any]]:
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM robots ORDER BY robot_id")
            return [dict(r) for r in cursor.fetchall()]

    def get_tasks(self) -> List[Dict[str, Any]]:
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks ORDER BY task_id")
            return [dict(r) for r in cursor.fetchall()]

    def get_decision_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM decision_events ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            result = []
            for r in rows:
                item = dict(r)
                if item.get("details"):
                    try:
                        item["details"] = json.loads(item["details"])
                    except Exception:
                        pass
                # Map component/action and task_id back for flexible schemas
                item["robot_id"] = item.get("component")
                item["event_type"] = item.get("action")
                if isinstance(item.get("details"), dict):
                    item["task_id"] = item["details"].get("task_id")
                else:
                    item["task_id"] = None
                result.append(item)
            return result

    def save_decision_event(self, event: Dict[str, Any]):
        with self.connection() as conn:
            cursor = conn.cursor()
            event_id = event.get("event_id") or f"dec_{int(event.get('timestamp', 0)*100)}_{event.get('robot_id', 'SYS')}"
            details = event.get("details", {})
            if isinstance(details, dict):
                if "task_id" not in details and "task_id" in event:
                    details["task_id"] = event["task_id"]
                details_str = json.dumps(details)
            else:
                details_str = str(details)

            cursor.execute(
                """
                INSERT OR REPLACE INTO decision_events (event_id, timestamp, component, action, details)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    event.get("timestamp", 0.0),
                    event.get("component") or event.get("robot_id", "COORDINATOR"),
                    event.get("action") or event.get("event_type", "DECISION"),
                    details_str,
                ),
            )
            conn.commit()


    def upsert_simulation(self, simulation: Dict[str, Any]):
        import time as _time
        now = _time.time()
        with self.connection() as conn:
            conn.execute("INSERT OR REPLACE INTO simulations (simulation_id, name, status, config, created_at, updated_at) VALUES (?, ?, ?, ?, COALESCE((SELECT created_at FROM simulations WHERE simulation_id = ?), ?), ?)",
                         (simulation["simulation_id"], simulation.get("name", "ResilientEdge"), simulation.get("status", "RUNNING"), json.dumps(simulation.get("config", {})), simulation["simulation_id"], now, now))
            conn.commit()

    def upsert_simulation_run(self, run: Dict[str, Any]):
        import time as _time
        now = _time.time()
        with self.connection() as conn:
            conn.execute("INSERT OR REPLACE INTO simulation_runs (run_id, simulation_id, name, status, config, start_time, end_time, final_metrics, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                         (run["run_id"], run.get("simulation_id"), run.get("name", "Simulation Run"), run.get("status", "RUNNING"), json.dumps(run.get("config", {})), run.get("start_time", now), run.get("end_time"), json.dumps(run.get("final_metrics", {})) if run.get("final_metrics") is not None else None, now))
            conn.commit()

    def update_simulation(self, simulation_id: str, values: Dict[str, Any]):
        import time as _time
        allowed = {k: v for k, v in values.items() if k in {"name", "status", "config"}}
        if not allowed:
            return
        sets = ", ".join(f"{k} = ?" for k in allowed)
        params = [json.dumps(v) if k == "config" else v for k, v in allowed.items()]
        params.extend([_time.time(), simulation_id])
        with self.connection() as conn:
            conn.execute(f"UPDATE simulations SET {sets}, updated_at = ? WHERE simulation_id = ?", params)
            conn.commit()

    def update_simulation_run(self, run_id: str, values: Dict[str, Any]):
        import time as _time
        allowed = {k: v for k, v in values.items() if k in {"name", "status", "config", "end_time", "final_metrics"}}
        if not allowed:
            return
        sets = ", ".join(f"{k} = ?" for k in allowed)
        params = [json.dumps(v) if k in {"config", "final_metrics"} else v for k, v in allowed.items()]
        params.append(run_id)
        with self.connection() as conn:
            conn.execute(f"UPDATE simulation_runs SET {sets} WHERE run_id = ?", params)
            conn.commit()

    def get_simulation(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM simulations WHERE simulation_id = ?", (simulation_id,)).fetchone()
            if not row:
                return None
            item = dict(row)
            if item.get("config"):
                try: item["config"] = json.loads(item["config"])
                except Exception: pass
            return item

    def upsert_robot(self, robot: Dict[str, Any]):
        with self.connection() as conn:
            conn.execute("INSERT OR REPLACE INTO robots (robot_id, position, state, battery, health, current_task, network_status, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                         (robot["robot_id"], json.dumps(robot.get("position", [0,0])), robot.get("state", "IDLE"), robot.get("battery",100), robot.get("health",1), robot.get("current_task"), robot.get("network_status","CONNECTED"), robot.get("updated_at", 0)))
            conn.commit()

    def update_robot(self, robot_id: str, values: Dict[str, Any]):
        current = self.get_robots()
        item = next((r for r in current if r["robot_id"] == robot_id), {"robot_id": robot_id})
        item.update(values)
        self.upsert_robot(item)

    def upsert_task(self, task: Dict[str, Any]):
        with self.connection() as conn:
            conn.execute("INSERT OR REPLACE INTO tasks (task_id, pickup, delivery, priority, deadline, status, assigned_robot, creation_time, start_time, completion_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                         (task["task_id"], json.dumps(task.get("pickup",[0,0])), json.dumps(task.get("delivery",[0,0])), task.get("priority",1), task.get("deadline",300), task.get("status","AVAILABLE"), task.get("assigned_robot"), task.get("creation_time",0), task.get("start_time"), task.get("completion_time")))
            conn.commit()

    def update_task(self, task_id: str, values: Dict[str, Any]):
        item = next((t for t in self.get_tasks() if t["task_id"] == task_id), {"task_id": task_id})
        item.update(values)
        self.upsert_task(item)

    def upsert_fault(self, fault: Dict[str, Any]):
        with self.connection() as conn:
            conn.execute("INSERT OR REPLACE INTO faults (fault_id, fault_type, target, start_time, duration, parameters, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                         (fault["fault_id"], fault.get("fault_type"), fault.get("target"), fault.get("start_time",0), fault.get("duration",0), json.dumps(fault.get("parameters",{})), fault.get("status","ACTIVE")))
            conn.commit()

    def update_fault(self, fault_id: str, values: Dict[str, Any]):
        with self.connection() as conn:
            sets = ", ".join(f"{k} = ?" for k in values if k in {"status", "duration", "parameters"})
            vals = [json.dumps(v) if k == "parameters" else v for k,v in values.items() if k in {"status","duration","parameters"}]
            if sets:
                vals.append(fault_id)
                conn.execute(f"UPDATE faults SET {sets} WHERE fault_id = ?", vals)
                conn.commit()

    def save_network_event(self, event: Dict[str, Any]):
        import time as _time
        with self.connection() as conn:
            conn.execute("INSERT OR REPLACE INTO network_events (event_id, run_id, timestamp, event_type, sender, recipient, latency, packet_loss, jitter, details, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                         (event.get("event_id") or f"net_{_time.time_ns()}", event.get("run_id"), event.get("timestamp", 0), event.get("event_type", "network_event"), event.get("sender", "SYSTEM"), event.get("recipient", "BROADCAST"), event.get("latency", 0), event.get("packet_loss", 0), event.get("jitter", 0), json.dumps(event.get("details", {})), _time.time()))
            conn.commit()

    def save_telemetry_event(self, event: Dict[str, Any]):
        import time as _time
        with self.connection() as conn:
            conn.execute("INSERT OR REPLACE INTO telemetry_events (event_id, run_id, timestamp, simulation_time, event_type, robot_id, task_id, payload, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                         (event.get("event_id") or f"evt_{_time.time_ns()}", event.get("run_id"), event.get("timestamp",0), event.get("simulation_time",event.get("timestamp",0)), event.get("event_type","event"), event.get("robot_id"), event.get("task_id"), json.dumps(event.get("payload",event.get("details",{}))), _time.time()))
            conn.commit()

    def save_experiment_run(self, run: Dict[str, Any]):
        with self.connection() as conn:
            conn.execute("INSERT OR REPLACE INTO experiment_runs (run_id, experiment_id, scenario, status, duration, metrics) VALUES (?, ?, ?, ?, ?, ?)",
                         (run["run_id"], run.get("experiment_id"), run.get("scenario") or run.get("scenario_id"), run.get("status","COMPLETED"), run.get("duration",0), json.dumps(run.get("metrics",{}))))
            conn.commit()

    def save_metrics(self, metrics: Dict[str, Any]):
        with self.connection() as conn:
            conn.execute("INSERT INTO metrics (run_id, timestamp, completion_rate, makespan, conflicts, deadlocks, metrics_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                         (metrics.get("run_id"), metrics.get("timestamp",0), metrics.get("task_completion_rate", metrics.get("completion_rate",0)), metrics.get("makespan",0), metrics.get("conflict_count",metrics.get("conflicts",0)), metrics.get("deadlock_count",metrics.get("deadlocks",0)), json.dumps(metrics)))
            conn.commit()

    def get_run_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.connection() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM simulation_runs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()]

    def get_telemetry_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self.connection() as conn:
            rows = [dict(r) for r in conn.execute("SELECT * FROM telemetry_events ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()]
        for row in rows:
            try: row["payload"] = json.loads(row["payload"])
            except Exception: pass
        return rows

    def get_experiment_runs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.connection() as conn:
            rows = [dict(r) for r in conn.execute("SELECT * FROM experiment_runs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()]
        for row in rows:
            try: row["metrics"] = json.loads(row["metrics"])
            except Exception: pass
        return rows

    def save_telemetry_snapshot(self, telemetry: Dict[str, Any]):
        """Persists snapshot via sync_telemetry."""
        return self.sync_telemetry(telemetry)


    def get_user_by_email(self, email: str):
        with self.connection() as conn:
            row = conn.execute("SELECT u.*, p.full_name, p.role FROM users u LEFT JOIN profiles p ON p.id=u.id WHERE lower(u.email)=lower(?) LIMIT 1", (email.strip(),)).fetchone()
            return dict(row) if row else None

    def get_user_by_id(self, user_id: str):
        with self.connection() as conn:
            row = conn.execute("SELECT u.*, p.full_name, p.role FROM users u LEFT JOIN profiles p ON p.id=u.id WHERE u.id=? LIMIT 1", (user_id,)).fetchone()
            return dict(row) if row else None

    def create_user(self, user_id: str, email: str, password_hash: str, full_name: str, role: str = "OBSERVER"):
        import time as _time
        now = _time.time()
        with self.connection() as conn:
            conn.execute("INSERT INTO users(id,email,password_hash,is_active,created_at,updated_at) VALUES(?,?,?,?,?,?)", (user_id,email.lower().strip(),password_hash,1,now,now))
            conn.execute("INSERT INTO profiles(id,email,full_name,role,created_at,updated_at) VALUES(?,?,?,?,?,?)", (user_id,email.lower().strip(),full_name,role,now,now))
            conn.execute("INSERT INTO audit_logs(log_id,user_id,user_role,action,entity_type,entity_id,metadata,created_at) VALUES(?,?,?,?,?,?,?,?)", (str(__import__('uuid').uuid4()),user_id,role,"USER_CREATED","user",user_id,json.dumps({"role":role}),now))
            conn.commit()

    def list_users(self):
        with self.connection() as conn:
            rows=conn.execute("SELECT u.id,u.email,u.is_active,u.created_at,u.updated_at,p.full_name,p.role FROM users u LEFT JOIN profiles p ON p.id=u.id ORDER BY u.created_at ASC").fetchall()
            return [dict(r) for r in rows]

    def update_user_password(self, user_id: str, password_hash: str):
        import time as _time
        with self.connection() as conn:
            conn.execute(
                "UPDATE users SET password_hash=?, is_active=1, updated_at=? WHERE id=?",
                (password_hash, _time.time(), user_id),
            )
            conn.commit()

    def update_user_role(self, user_id: str, role: str):
        import time as _time
        with self.connection() as conn:
            conn.execute("UPDATE profiles SET role=?,updated_at=? WHERE id=?", (role,_time.time(),user_id))
            conn.commit()

    def set_user_active(self, user_id: str, is_active: bool):
        import time as _time
        with self.connection() as conn:
            conn.execute("UPDATE users SET is_active=?,updated_at=? WHERE id=?", (1 if is_active else 0,_time.time(),user_id)); conn.commit()

    def count_admins(self) -> int:
        with self.connection() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM profiles WHERE role='ADMIN'").fetchone()[0])

    def create_auth_session(self, session_id: str, user_id: str, refresh_token_hash: str, created_at: float, expires_at: float):
        with self.connection() as conn:
            conn.execute("INSERT INTO auth_sessions(id,user_id,refresh_token_hash,created_at,expires_at,revoked_at) VALUES(?,?,?,?,?,NULL)", (session_id,user_id,refresh_token_hash,created_at,expires_at))
            conn.commit()

    def get_auth_session(self, refresh_token_hash: str):
        with self.connection() as conn:
            row=conn.execute("SELECT * FROM auth_sessions WHERE refresh_token_hash=? LIMIT 1", (refresh_token_hash,)).fetchone()
            return dict(row) if row else None

    def get_auth_session_by_id(self, session_id: str):
        with self.connection() as conn:
            row=conn.execute("SELECT * FROM auth_sessions WHERE id=? LIMIT 1", (session_id,)).fetchone()
            return dict(row) if row else None

    def revoke_auth_session(self, session_id: str):
        import time as _time
        with self.connection() as conn:
            conn.execute("UPDATE auth_sessions SET revoked_at=? WHERE id=? AND revoked_at IS NULL", (_time.time(),session_id)); conn.commit()

    def revoke_user_sessions(self, user_id: str):
        import time as _time
        with self.connection() as conn:
            conn.execute("UPDATE auth_sessions SET revoked_at=? WHERE user_id=? AND revoked_at IS NULL", (_time.time(),user_id)); conn.commit()

    def save_audit_log(self, log: Dict[str, Any]):
        import time as _time
        with self.connection() as conn:
            conn.execute("INSERT INTO audit_logs(log_id,user_id,user_role,action,entity_type,entity_id,metadata,created_at) VALUES(?,?,?,?,?,?,?,?)", (log["log_id"],log.get("user_id"),log.get("user_role"),log["action"],log.get("entity_type"),log.get("entity_id"),json.dumps(log.get("metadata",{})),log.get("created_at",_time.time())))
            conn.commit()

    def get_audit_logs(self, limit: int = 200):
        with self.connection() as conn:
            rows=[dict(r) for r in conn.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()]
        for row in rows:
            try: row["metadata"]=json.loads(row.get("metadata") or "{}")
            except Exception: row["metadata"]={}
        return rows

    def clear_all(self):
        """Clears all records in persistent tables on administrative request."""
        with self.connection() as conn:
            cursor = conn.cursor()
            for table in ["robots", "tasks", "faults", "incidents", "experiments", "experiment_runs", "reservations", "decision_events", "metrics", "simulations", "simulation_runs", "telemetry_events", "network_events", "recovery_actions", "schema_migrations"]:
                try:
                    cursor.execute(f"DELETE FROM {table}")
                except Exception:
                    pass
            conn.commit()


# Alias for compatibility with external references and test suites
SQLiteDatabase = ResilientEdgeDatabase
