"""SQLite implementation of the production persistence contract."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from backend.database.sqlite_db import ResilientEdgeDatabase
from backend.database.repository import PersistenceRepository


class SQLiteRepository(PersistenceRepository):
    mode = "sqlite"

    def __init__(self, db: Optional[ResilientEdgeDatabase] = None):
        self.db = db or ResilientEdgeDatabase()

    def create_simulation(self, simulation: Dict[str, Any]) -> None:
        self.db.upsert_simulation(simulation)

    def create_simulation_run(self, run: Dict[str, Any]) -> None:
        self.db.upsert_simulation_run(run)

    def update_simulation(self, simulation_id: str, values: Dict[str, Any]) -> None:
        self.db.update_simulation(simulation_id, values)

    def update_simulation_run(self, run_id: str, values: Dict[str, Any]) -> None:
        self.db.update_simulation_run(run_id, values)

    def get_simulation(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        return self.db.get_simulation(simulation_id)

    def create_robot(self, robot: Dict[str, Any]) -> None:
        self.db.upsert_robot(robot)

    def update_robot(self, robot_id: str, values: Dict[str, Any]) -> None:
        self.db.update_robot(robot_id, values)

    def create_task(self, task: Dict[str, Any]) -> None:
        self.db.upsert_task(task)

    def update_task(self, task_id: str, values: Dict[str, Any]) -> None:
        self.db.update_task(task_id, values)

    def create_fault(self, fault: Dict[str, Any]) -> None:
        self.db.upsert_fault(fault)

    def resolve_fault(self, fault_id: str, values: Optional[Dict[str, Any]] = None) -> None:
        self.db.update_fault(fault_id, {"status": "RESOLVED", **(values or {})})

    def create_incident(self, incident: Dict[str, Any]) -> None:
        self.db.save_incident(incident)

    def create_recovery_event(self, event: Dict[str, Any]) -> None:
        self.db.save_recovery_event(event)

    def create_telemetry_event(self, event: Dict[str, Any]) -> None:
        self.db.save_telemetry_event(event)

    def create_network_event(self, event: Dict[str, Any]) -> None:
        self.db.save_network_event(event)

    def create_experiment_run(self, run: Dict[str, Any]) -> None:
        self.db.save_experiment_run(run)

    def save_experiment(self, experiment: Dict[str, Any]) -> None:
        self.db.save_experiment(experiment)

    def store_metrics(self, metrics: Dict[str, Any]) -> None:
        self.db.save_metrics(metrics)

    def get_run_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.db.get_run_history(limit)

    def get_telemetry(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.db.get_telemetry_events(limit)

    def get_incidents(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.db.get_incidents(limit)

    def get_experiment_results(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.db.get_experiment_runs(limit)

    def sync_telemetry(self, telemetry: Dict[str, Any], run_id: Optional[str] = None) -> None:
        self.db.sync_telemetry(telemetry, run_id=run_id)

    def get_stats(self) -> Dict[str, Any]:
        return self.db.get_stats()

    def get_robots(self) -> List[Dict[str, Any]]:
        return self.db.get_robots()

    def get_tasks(self) -> List[Dict[str, Any]]:
        return self.db.get_tasks()

    def get_decision_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.db.get_decision_events(limit)

    def save_decision_event(self, event: Dict[str, Any]) -> None:
        self.db.save_decision_event(event)

    def health_check(self) -> Dict[str, Any]:
        return {"provider": "local", "connected": True, "database": "sqlite", "status": "online", "storage_mode": "SQLite (Local Transactional)"}

    def get_persistence_status(self) -> Dict[str, Any]:
        return self.health_check()

    def clear_all(self) -> None:
        self.db.clear_all()

    def get_user_by_email(self, email: str): return self.db.get_user_by_email(email)
    def get_user_by_id(self, user_id: str): return self.db.get_user_by_id(user_id)
    def create_user(self, user_id: str, email: str, password_hash: str, full_name: str, role: str = "OBSERVER"): return self.db.create_user(user_id,email,password_hash,full_name,role)
    def list_users(self): return self.db.list_users()
    def update_user_role(self, user_id: str, role: str): return self.db.update_user_role(user_id,role)
    def count_admins(self): return self.db.count_admins()
    def set_user_active(self, user_id, is_active): return self.db.set_user_active(user_id, is_active)
    def save_audit_log(self, log): return self.db.save_audit_log(log)
    def get_audit_logs(self, limit=200): return self.db.get_audit_logs(limit)

