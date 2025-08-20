import json
import threading
from typing import Any, Dict, List, Optional
import sqlite3
from datetime import datetime
from google.adk.sessions import BaseSessionService, Session


class SQLiteSessionService(BaseSessionService):
    def __init__(self, db_path: str = "sessions.db"):
        self.db_path = db_path
        self._init_lock = threading.Lock()
        self._initialized = False

    def _init(self):
        if self._initialized:
            return
        with self._init_lock:
            if self._initialized:
                return
            with sqlite3.connect(self.db_path) as db:
                db.execute(
                    """
                    CREATE TABLE IF NOT EXISTS sessions (
                        app_name   TEXT NOT NULL,
                        user_id    TEXT NOT NULL,
                        session_id TEXT NOT NULL,
                        state_json TEXT NOT NULL DEFAULT '{}',
                        created_at TEXT NOT NULL,
                        PRIMARY KEY (app_name, user_id, session_id)
                    )
                    """
                )
                db.execute(
                    """
                    CREATE TABLE IF NOT EXISTS events (
                        id         INTEGER PRIMARY KEY AUTOINCREMENT,
                        app_name   TEXT NOT NULL,
                        user_id    TEXT NOT NULL,
                        session_id TEXT NOT NULL,
                        idx        INTEGER NOT NULL,
                        event_json TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        UNIQUE(app_name, user_id, session_id, idx)
                    )
                    """
                )
                db.commit()
            self._initialized = True

    def create_session(
        self, app_name: str, user_id: str, session_id: str, state: Optional[Dict[str, Any]] = None
    ) -> Session:
        self._init()
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as db:
            db.execute(
                """INSERT OR IGNORE INTO sessions (app_name, user_id, session_id, state_json, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (app_name, user_id, session_id, json.dumps(state or {}), now),
            )
            db.commit()
        return Session(id=session_id, app_name=app_name, user_id=user_id, state=state or {})

    def get_session(self, app_name: str, user_id: str, session_id: str) -> Optional[Session]:
        """Fetch a session by id."""
        self._init()
        with sqlite3.connect(self.db_path) as db:
            cur = db.execute(
                """SELECT state_json FROM sessions
                   WHERE app_name=? AND user_id=? AND session_id=?""",
                (app_name, user_id, session_id),
            )
            row = cur.fetchone()
            if not row:
                return None
            state = json.loads(row[0]) if row[0] else {}
            return Session(id=session_id, app_name=app_name, user_id=user_id, state=state)

    def update_state(self, app_name: str, user_id: str, session_id: str, state_update: Dict[str, Any]) -> None:
        self._init()
        with sqlite3.connect(self.db_path) as db:
            cur = db.execute(
                """SELECT state_json FROM sessions
                   WHERE app_name=? AND user_id=? AND session_id=?""",
                (app_name, user_id, session_id),
            )
            row = cur.fetchone()
            current = json.loads(row[0]) if row and row[0] else {}
            current.update(state_update or {})
            db.execute(
                """UPDATE sessions SET state_json=? WHERE app_name=? AND user_id=? AND session_id=?""",
                (json.dumps(current), app_name, user_id, session_id),
            )
            db.commit()

    def get_state(self, app_name: str, user_id: str, session_id: str) -> Dict[str, Any]:
        sess = self.get_session(app_name, user_id, session_id)
        return sess.state if sess else {}

    def list_events(self, app_name: str, user_id: str, session_id: str) -> List[Dict[str, Any]]:
        self._init()
        with sqlite3.connect(self.db_path) as db:
            cur = db.execute(
                """SELECT idx, event_json, created_at FROM events
                   WHERE app_name=? AND user_id=? AND session_id=?
                   ORDER BY idx ASC""",
                (app_name, user_id, session_id),
            )
            rows = cur.fetchall()
            return [{"idx": r[0], "event": json.loads(r[1]), "created_at": r[2]} for r in rows]

    def add_event(self, app_name: str, user_id: str, session_id: str, event: Dict[str, Any]) -> int:
        self._init()
        with sqlite3.connect(self.db_path) as db:
            cur = db.execute(
                """SELECT COALESCE(MAX(idx), -1) + 1 FROM events
                   WHERE app_name=? AND user_id=? AND session_id=?""",
                (app_name, user_id, session_id),
            )
            row = cur.fetchone()
            next_idx = int(row[0]) if row and row[0] is not None else 0
            now = datetime.utcnow().isoformat()
            db.execute(
                """INSERT INTO events (app_name, user_id, session_id, idx, event_json, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (app_name, user_id, session_id, next_idx, json.dumps(event), now),
            )
            db.commit()
            return next_idx

    def delete_session(self, app_name: str, user_id: str, session_id: str) -> None:
        self._init()
        with sqlite3.connect(self.db_path) as db:
            db.execute(
                "DELETE FROM events WHERE app_name=? AND user_id=? AND session_id=?",
                (app_name, user_id, session_id),
            )
            db.execute(
                "DELETE FROM sessions WHERE app_name=? AND user_id=? AND session_id=?",
                (app_name, user_id, session_id),
            )
            db.commit()

    def list_sessions(self, app_name: str, user_id: str) -> List[Session]:
        """Return all sessions for a given app_name and user_id."""
        self._init()
        with sqlite3.connect(self.db_path) as db:
            cur = db.execute(
                """SELECT session_id, state_json
                   FROM sessions
                   WHERE app_name=? AND user_id=?""",
                (app_name, user_id),
            )
            rows = cur.fetchall()
            sessions = []
            for r in rows:
                state = json.loads(r[1]) if r[1] else {}
                sessions.append(
                    Session(
                        id=r[0],
                        app_name=app_name,
                        user_id=user_id,
                        state=state
                    )
                )
            return sessions
