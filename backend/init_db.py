from backend.database.sqlite_db import ResilientEdgeDatabase
if __name__ == '__main__':
    db=ResilientEdgeDatabase()
    print(f'Initialized SQLite database: {db.db_path}')
