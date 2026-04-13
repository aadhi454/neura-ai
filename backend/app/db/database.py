import sqlite3
from datetime import datetime
from hashlib import sha256
from typing import Any

from ..core.config import settings


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 3000")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                message TEXT NOT NULL,
                message_hash TEXT NOT NULL DEFAULT '',
                timestamp TEXT NOT NULL
            )
            """
        )
        _migrate_conversations_table(conn)
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_conversations_user_session_id
            ON conversations (user_id, session_id, id)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_conversations_user_session_role_hash
            ON conversations (user_id, session_id, role, message_hash)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                summary TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _migrate_conversations_table(conn: sqlite3.Connection) -> None:
    columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(conversations)").fetchall()
    }

    if "user_id" not in columns:
        conn.execute(
            "ALTER TABLE conversations ADD COLUMN user_id TEXT NOT NULL DEFAULT 'default'"
        )

    if "session_id" not in columns:
        conn.execute(
            "ALTER TABLE conversations ADD COLUMN session_id TEXT NOT NULL DEFAULT 'default'"
        )

    if "role" not in columns:
        conn.execute(
            "ALTER TABLE conversations ADD COLUMN role TEXT NOT NULL DEFAULT 'user'"
        )

    if "message_hash" not in columns:
        conn.execute(
            "ALTER TABLE conversations ADD COLUMN message_hash TEXT NOT NULL DEFAULT ''"
        )


def _message_hash(role: str, message: str) -> str:
    normalized = " ".join(message.strip().lower().split())
    payload = f"{role}:{normalized}".encode("utf-8")
    return sha256(payload).hexdigest()


def _fetch_latest_message_hash(
    conn: sqlite3.Connection, user_id: str, session_id: str, role: str
) -> str | None:
    row = conn.execute(
        """
        SELECT message_hash
        FROM conversations
        WHERE user_id = ? AND session_id = ? AND role = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (user_id, session_id, role),
    ).fetchone()
    return row["message_hash"] if row else None


def save_message(user_id: str, session_id: str, role: str, message: str) -> None:
    cleaned_message = " ".join((message or "").strip().split())
    if not cleaned_message:
        return

    if len(cleaned_message) > settings.max_message_chars:
        cleaned_message = cleaned_message[: settings.max_message_chars].rstrip()

    with get_connection() as conn:
        message_hash = _message_hash(role, cleaned_message)
        latest_hash = _fetch_latest_message_hash(conn, user_id, session_id, role)
        if latest_hash == message_hash:
            return

        conn.execute(
            """
            INSERT INTO conversations (
                user_id, session_id, role, message, message_hash, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                session_id,
                role,
                cleaned_message,
                message_hash,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()


def fetch_recent_messages(user_id: str, session_id: str, limit: int) -> list[dict[str, Any]]:
    fetch_limit = max(limit * 2, limit)
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT role, message, timestamp
            FROM conversations
            WHERE user_id = ? AND session_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, session_id, fetch_limit),
        ).fetchall()

    deduped_rows: list[dict[str, Any]] = []
    last_fingerprint: tuple[str | None, str] | None = None

    for row in reversed(rows):
        current = dict(row)
        fingerprint = (
            current.get("role"),
            " ".join((current.get("message") or "").strip().lower().split()),
        )
        if fingerprint == last_fingerprint:
            continue
        last_fingerprint = fingerprint
        deduped_rows.append(current)

    return deduped_rows[-limit:]


def save_summary(user_id: str, session_id: str, summary: str) -> None:
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        existing = conn.execute(
            """
            SELECT id
            FROM memory_summaries
            WHERE user_id = ? AND session_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id, session_id),
        ).fetchone()

        if existing:
            conn.execute(
                """
                UPDATE memory_summaries
                SET summary = ?, updated_at = ?
                WHERE id = ?
                """,
                (summary, now, existing["id"]),
            )
        else:
            conn.execute(
                """
                INSERT INTO memory_summaries (
                    user_id, session_id, summary, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, session_id, summary, now, now),
            )
        conn.commit()


def get_latest_summary(user_id: str, session_id: str) -> str | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT summary
            FROM memory_summaries
            WHERE user_id = ? AND session_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id, session_id),
        ).fetchone()

    return row["summary"] if row else None
