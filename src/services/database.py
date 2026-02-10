import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from src.config import settings


class DatabaseManager:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        if not self.db_path.parent.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        self._setup()

    def _setup(self) -> None:
        users_table = """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            authorized_at TEXT NOT NULL
        )
        """

        banned_table = """
        CREATE TABLE IF NOT EXISTS banned_users (
            user_id INTEGER PRIMARY KEY,
            banned_at TEXT NOT NULL,
            reason TEXT
        )
        """

        attempts_table = """
        CREATE TABLE IF NOT EXISTS auth_attempts (
            user_id INTEGER PRIMARY KEY,
            attempts INTEGER NOT NULL DEFAULT 0
        )
        """

        settings_table = """
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """

        history_table = """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            base_url TEXT NOT NULL,
            utm_url TEXT NOT NULL,
            short_url TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """

        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(users_table)
            cursor.execute(banned_table)
            cursor.execute(attempts_table)
            cursor.execute(settings_table)
            cursor.execute(history_table)
            self._connection.commit()

        self._ensure_column("users", "username", "TEXT")
        self._ensure_column("banned_users", "username", "TEXT")
        self._ensure_default_password()

    def _ensure_column(self, table: str, column: str, definition: str) -> None:
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(f"PRAGMA table_info({table})")
            columns = {row["name"] for row in cursor.fetchall()}
            if column not in columns:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                self._connection.commit()

    def _ensure_default_password(self) -> None:
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(
                "SELECT value FROM app_settings WHERE key = ?", ("bot_password",)
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    "INSERT INTO app_settings (key, value) VALUES (?, ?)",
                    ("bot_password", settings.bot_access_password),
                )
                self._connection.commit()

    def is_user_authorized(self, user_id: int) -> bool:
        query = "SELECT 1 FROM users WHERE user_id = ?"
        return self._exists(query, (user_id,))

    def authorize_user(self, user_id: int, username: Optional[str]) -> None:
        now = datetime.utcnow().isoformat()
        query = """
        INSERT INTO users (user_id, username, authorized_at)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET username = excluded.username
        """
        self._execute(query, (user_id, username, now))
        self.reset_auth_attempts(user_id)

    def is_user_banned(self, user_id: int) -> bool:
        query = "SELECT 1 FROM banned_users WHERE user_id = ?"
        return self._exists(query, (user_id,))

    def ban_user(self, user_id: int, username: Optional[str], reason: str | None = None) -> None:
        now = datetime.utcnow().isoformat()
        query = """
        INSERT OR IGNORE INTO banned_users (user_id, username, banned_at, reason)
        VALUES (?, ?, ?, ?)
        """
        self._execute(query, (user_id, username, now, reason))
        self.reset_auth_attempts(user_id)

    def add_history(self, user_id: int, base_url: str, utm_url: str, short_url: str) -> None:
        now = datetime.utcnow().isoformat()
        query = """
        INSERT INTO history (user_id, base_url, utm_url, short_url, created_at)
        VALUES (?, ?, ?, ?, ?)
        """
        self._execute(query, (user_id, base_url, utm_url, short_url, now))

    def get_history(self, user_id: int, limit: int = 50) -> List[Tuple[str, str, str]]:
        query = """
        SELECT base_url, utm_url, short_url
        FROM history
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """
        rows = self._fetchall(query, (user_id, limit))
        return [(row["base_url"], row["utm_url"], row["short_url"]) for row in rows]

    def list_authorized_users(self) -> List[sqlite3.Row]:
        query = """
        SELECT user_id, username, authorized_at
        FROM users
        ORDER BY authorized_at DESC
        """
        return self._fetchall(query, ())

    def list_banned_users(self) -> List[sqlite3.Row]:
        query = """
        SELECT user_id, username, banned_at, reason
        FROM banned_users
        ORDER BY banned_at DESC
        """
        return self._fetchall(query, ())

    def delete_user(self, user_id: int) -> bool:
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute("DELETE FROM history WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM auth_attempts WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            deleted_from_users = cursor.rowcount
            cursor.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
            deleted_from_banned = cursor.rowcount
            self._connection.commit()
        return (deleted_from_users + deleted_from_banned) > 0

    def get_bot_password(self) -> str:
        query = "SELECT value FROM app_settings WHERE key = ?"
        rows = self._fetchall(query, ("bot_password",))
        if not rows:
            return settings.bot_access_password
        return str(rows[0]["value"])

    def update_bot_password(self, new_password: str) -> None:
        query = """
        INSERT INTO app_settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """
        self._execute(query, ("bot_password", new_password))

    def get_auth_attempts(self, user_id: int) -> int:
        query = "SELECT attempts FROM auth_attempts WHERE user_id = ?"
        rows = self._fetchall(query, (user_id,))
        if not rows:
            return 0
        return int(rows[0]["attempts"])

    def increment_auth_attempts(self, user_id: int) -> int:
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(
                """
                INSERT INTO auth_attempts (user_id, attempts)
                VALUES (?, 1)
                ON CONFLICT(user_id) DO UPDATE SET attempts = attempts + 1
                """,
                (user_id,),
            )
            self._connection.commit()
            cursor.execute("SELECT attempts FROM auth_attempts WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
        return int(row["attempts"]) if row else 0

    def reset_auth_attempts(self, user_id: int) -> None:
        query = "DELETE FROM auth_attempts WHERE user_id = ?"
        self._execute(query, (user_id,))

    def _execute(self, query: str, params: Iterable) -> None:
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(query, tuple(params))
            self._connection.commit()

    def _fetchall(self, query: str, params: Iterable) -> List[sqlite3.Row]:
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(query, tuple(params))
            return cursor.fetchall()

    def _exists(self, query: str, params: Iterable) -> bool:
        with self._lock:
            cursor = self._connection.cursor()
            cursor.execute(query, tuple(params))
            return cursor.fetchone() is not None


database = DatabaseManager(settings.database_path)
