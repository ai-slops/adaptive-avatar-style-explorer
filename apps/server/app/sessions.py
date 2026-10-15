"""Revocable remembered-browser sessions, independent of provider credentials."""

import hashlib
import time

REMEMBER_SECONDS = 30 * 24 * 3600
SESSION_SECONDS = 12 * 3600
PERSISTED_FIELDS = frozenset(
    {
        "principal",
        "registration",
        "csrf",
        "expires",
        "created",
        "remembered",
        "usagePaused",
    }
)


class BrowserSession(dict):
    def __init__(self, value, save):
        super().__init__(value)
        self.save = save
        self.active = True

    def __setitem__(self, key, value):
        changed = self.get(key) != value
        super().__setitem__(key, value)
        if changed and key in PERSISTED_FIELDS:
            self.save(self)

    def update(self, *args, **kwargs):
        changes = dict(*args, **kwargs)
        persist = any(
            key in PERSISTED_FIELDS and self.get(key) != value
            for key, value in changes.items()
        )
        super().update(changes)
        if persist:
            self.save(self)


class Sessions:
    def __init__(self, database, execution_mode):
        self.database, self.execution_mode = database, execution_mode
        self.cache = {}
        with database.connect() as db:
            db.execute(
                "DELETE FROM browser_sessions WHERE expires_at<=?", (time.time(),)
            )

    @staticmethod
    def token_digest(token):
        if not isinstance(token, str) or not 1 <= len(token) <= 200:
            return None
        return hashlib.sha256(token.encode()).hexdigest()

    def save(self, key, value):
        if not value.active:
            return
        with self.database.connect() as db:
            if not value.get("remembered"):
                db.execute("DELETE FROM browser_sessions WHERE token_digest=?", (key,))
                return
            db.execute(
                """INSERT INTO browser_sessions VALUES (?,?,?,?,?,?,?,?)
                ON CONFLICT(token_digest) DO UPDATE SET
                principal_id=excluded.principal_id, registration_id=excluded.registration_id,
                csrf_token=excluded.csrf_token, expires_at=excluded.expires_at,
                usage_paused=excluded.usage_paused""",
                (
                    key,
                    self.execution_mode,
                    value["principal"],
                    value.get("registration"),
                    value["csrf"],
                    value["created"],
                    value["expires"],
                    int(value.get("usagePaused", False)),
                ),
            )

    def wrap(self, key, value):
        return BrowserSession(value, lambda current: self.save(key, current))

    def __setitem__(self, token, value):
        key = self.token_digest(token)
        if key is None:
            raise ValueError("Invalid browser session token")
        session = self.wrap(key, value)
        self.save(key, session)
        self.cache[key] = session

    def get(self, token, default=None):
        key = self.token_digest(token)
        if key is None:
            return default
        session = self.cache.get(key)
        if session is None:
            with self.database.connect() as db:
                row = db.execute(
                    "SELECT * FROM browser_sessions WHERE token_digest=? AND execution_mode=?",
                    (key, self.execution_mode),
                ).fetchone()
            if row is None:
                return default
            session = self.wrap(
                key,
                {
                    "principal": row["principal_id"],
                    "registration": row["registration_id"],
                    "csrf": row["csrf_token"],
                    "created": row["created_at"],
                    "expires": row["expires_at"],
                    "remembered": True,
                    "usagePaused": bool(row["usage_paused"]),
                    "remainingRequests": 0,
                },
            )
            self.cache[key] = session
        if session["expires"] <= time.time():
            self.pop(token, None)
            return default
        return session

    def __getitem__(self, token):
        result = self.get(token)
        if result is None:
            raise KeyError(token)
        return result

    def __contains__(self, token):
        return self.get(token) is not None

    def pop(self, token, default=None):
        result = (
            self.get(token, default)
            if self.token_digest(token) not in self.cache
            else self.cache[self.token_digest(token)]
        )
        key = self.token_digest(token)
        if key is not None:
            removed = self.cache.pop(key, None)
            if removed is not None:
                removed.active = False
            with self.database.connect() as db:
                db.execute(
                    "DELETE FROM browser_sessions WHERE token_digest=? AND execution_mode=?",
                    (key, self.execution_mode),
                )
        return result
