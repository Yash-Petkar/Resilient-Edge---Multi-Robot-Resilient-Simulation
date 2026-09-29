"""Authoritative SQLite persistence facade."""
from __future__ import annotations
from typing import Any, Dict
from backend.database.sqlite_repository import SQLiteRepository

class ResilientPersistence:
    def __init__(self, sqlite_repo=None, **_ignored):
        self.sqlite = sqlite_repo or SQLiteRepository()
        self.last_error=None
        self.last_success_at=None
        self.cloud_available=False
        self.fallback_enabled=False
        self.explicit_local=True
    @property
    def mode(self): return 'sqlite'
    def _call(self,method,*args,**kwargs): return getattr(self.sqlite,method)(*args,**kwargs)
    def health_check(self): return self.sqlite.health_check()
    def get_persistence_status(self): return self.sqlite.health_check()
    def get_stats(self): return self.sqlite.get_stats()
    def get_robots(self): return self.sqlite.get_robots()
    def get_tasks(self): return self.sqlite.get_tasks()
    def get_incidents(self,limit=50): return self.sqlite.get_incidents(limit)
    def get_decision_events(self,limit=50): return self.sqlite.get_decision_events(limit)
    def get_experiment_results(self,limit=50): return self.sqlite.get_experiment_results(limit)
    def clear_all(self): return self.sqlite.clear_all()
    def __getattr__(self,name):
        return getattr(self.sqlite,name)

persistence=ResilientPersistence()
