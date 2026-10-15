"""Transactional SQLite access. Each service transaction authorizes its project."""
from contextlib import contextmanager
from pathlib import Path
import sqlite3

class Database:
    def __init__(self, path: str | Path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('PRAGMA journal_mode=WAL')
            if db.execute("SELECT json_valid('{}')").fetchone()[0] != 1:
                raise RuntimeError('SQLite JSON functions are required')
            version = db.execute('PRAGMA user_version').fetchone()[0]
            if version == 0:
                if db.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]:
                    raise RuntimeError('Unversioned existing database: back up and migrate separately')
                db.executescript(Path(__file__).with_name('001_initial.sql').read_text())
                db.execute('PRAGMA user_version=2')
            elif version != 2:
                raise RuntimeError('Unsupported database version; back up before migration')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()
