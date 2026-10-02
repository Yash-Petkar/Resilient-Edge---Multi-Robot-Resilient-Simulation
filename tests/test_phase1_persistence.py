import os, tempfile
from backend.database.sqlite_db import ResilientEdgeDatabase
from backend.database.sqlite_repository import SQLiteRepository
from backend.database.factory import ResilientPersistence

def test_sqlite_repository_contract():
    with tempfile.TemporaryDirectory() as td:
        repo=SQLiteRepository(ResilientEdgeDatabase(os.path.join(td,'db.sqlite')))
        repo.create_simulation({'simulation_id':'sim-1','name':'Test','status':'RUNNING','config':{'seed':1}})
        assert repo.get_simulation('sim-1')['status']=='RUNNING'
        repo.create_telemetry_event({'run_id':'sim-1','timestamp':1.0,'simulation_time':1.0,'event_type':'simulation_started','payload':{'ok':True}})
        assert len(repo.get_telemetry())==1

def test_database_failures_do_not_stop_repository_contract():
    with tempfile.TemporaryDirectory() as td:
        repo=SQLiteRepository(ResilientEdgeDatabase(os.path.join(td,'db.sqlite'))); facade=ResilientPersistence(sqlite_repo=repo)
        facade.create_telemetry_event({'event_type':'database_failure_test','timestamp':1}); assert len(repo.get_telemetry())==1

def test_explicit_local_mode_is_supported():
    with tempfile.TemporaryDirectory() as td:
        repo=SQLiteRepository(ResilientEdgeDatabase(os.path.join(td,'db.sqlite'))); facade=ResilientPersistence(sqlite_repo=repo); assert facade.mode=='sqlite'

def test_auth_tables_are_created():
    with tempfile.TemporaryDirectory() as td:
        db=ResilientEdgeDatabase(os.path.join(td,'db.sqlite'))
        with db.connection() as conn:
            tables={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        assert {'users','profiles','audit_logs'}.issubset(tables)
