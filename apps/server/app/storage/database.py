"""Transactional SQLite access. Each service transaction authorizes its project."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path


class Database:
    def __init__(self, path: str | Path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path, timeout=10)
        try:
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("PRAGMA journal_mode=WAL")
            if db.execute("SELECT json_valid('{}')").fetchone()[0] != 1:
                raise RuntimeError("SQLite JSON functions are required")
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if (
                version == 0
                and db.execute(
                    "SELECT count(*) FROM sqlite_master WHERE type='table'"
                ).fetchone()[0]
            ):
                raise RuntimeError(
                    "Unversioned existing database: back up and migrate separately"
                )
            if version not in (0, 2, 3, 4, 5, 6):
                raise RuntimeError(
                    "Unsupported database version; back up before migration"
                )
            for source, target, filename in [
                (0, 2, "001_initial.sql"),
                (2, 3, "002_runtime.sql"),
                (3, 4, "003_profiles.sql"),
                (4, 5, "004_codex.sql"),
                (5, 6, "005_browser_sessions.sql"),
            ]:
                if version == source:
                    script = Path(__file__).with_name(filename).read_text()
                    db.executescript(
                        "BEGIN IMMEDIATE;\n"
                        + script
                        + f"\nPRAGMA user_version={target};\nCOMMIT;"
                    )
                    version = target
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()
