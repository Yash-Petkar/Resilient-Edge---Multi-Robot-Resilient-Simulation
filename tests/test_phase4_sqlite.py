import os, tempfile
from backend.database.sqlite_db import ResilientEdgeDatabase
from backend.database.sqlite_repository import SQLiteRepository
from backend.database.factory import ResilientPersistence

def test_sqlite_health_is_real_connection_check():
    with tempfile.TemporaryDirectory() as td:
        repo=SQLiteRepository(ResilientEdgeDatabase(os.path.join(td,'db.sqlite')))
        result=repo.db.health_check(); assert result['provider']=='local'; assert result['connected']

def test_sqlite_repository_preserves_existing_simulation_schema():
    with tempfile.TemporaryDirectory() as td:
        repo=SQLiteRepository(ResilientEdgeDatabase(os.path.join(td,'db.sqlite')))
        repo.create_simulation_run({'run_id':'r1','simulation_id':'s1','status':'RUNNING'})
        repo.create_network_event({'run_id':'r1','timestamp':1,'event_type':'network_degradation'})
        assert repo.get_run_history(1)[0]['run_id']=='r1'

def test_persistence_is_always_sqlite():
    with tempfile.TemporaryDirectory() as td:
        repo=SQLiteRepository(ResilientEdgeDatabase(os.path.join(td,'db.sqlite'))); facade=ResilientPersistence(sqlite_repo=repo)
        facade.create_telemetry_event({'event_type':'test','timestamp':1}); assert facade.mode=='sqlite'; assert len(repo.get_telemetry())==1
