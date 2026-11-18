"""Private SQLite conversation store with schema migrations."""

import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone


SCHEMA_VERSION = 1


def _timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ConversationStore:
    def __init__(self, paths):
        self.paths = paths
        self.paths.prepare()
        self._migrate()

    def _connect(self):
        try:
            descriptor = os.open(str(self.paths.database), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            descriptor = None
        if descriptor is not None:
            os.close(descriptor)
        os.chmod(str(self.paths.database), 0o600)
        connection = sqlite3.connect(str(self.paths.database), timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = DELETE")
        return connection

    @contextmanager
    def _session(self):
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _migrate(self):
        with self._session() as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version > SCHEMA_VERSION:
                raise RuntimeError("O banco do assistente foi criado por uma versão mais nova.")
            if version < 1:
                connection.executescript(
                    """
                    CREATE TABLE conversations (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                    CREATE TABLE messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                        role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                        content TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );
                    CREATE INDEX messages_conversation_id_id ON messages(conversation_id, id);
                    CREATE TABLE memories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT NOT NULL,
                        content TEXT NOT NULL,
                        inferred INTEGER NOT NULL DEFAULT 0 CHECK (inferred IN (0, 1)),
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                    PRAGMA user_version = 1;
                    """
                )

    def create_conversation(self, title="Nova conversa"):
        conversation_id = uuid.uuid4().hex
        timestamp = _timestamp()
        with self._session() as connection:
            connection.execute(
                "INSERT INTO conversations(id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (conversation_id, title[:160], timestamp, timestamp),
            )
        return conversation_id

    def list_conversations(self):
        with self._session() as connection:
            rows = connection.execute(
                "SELECT id, title, updated_at FROM conversations ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def add_message(self, conversation_id, role, content):
        if role not in ("user", "assistant", "system"):
            raise ValueError("Papel de mensagem inválido.")
        if not isinstance(content, str) or not content.strip() or len(content) > 200000:
            raise ValueError("A mensagem está vazia ou excede o limite permitido.")
        timestamp = _timestamp()
        with self._session() as connection:
            cursor = connection.execute(
                "INSERT INTO messages(conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (conversation_id, role, content, timestamp),
            )
            connection.execute(
                "UPDATE conversations SET updated_at=? WHERE id=?", (timestamp, conversation_id)
            )
            if cursor.rowcount != 1:
                raise RuntimeError("Não foi possível salvar a mensagem.")

    def list_messages(self, conversation_id, limit=100):
        if limit < 1 or limit > 500:
            raise ValueError("Limite de mensagens inválido.")
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT role, content, created_at FROM messages WHERE conversation_id=? "
                "ORDER BY id DESC LIMIT ?",
                (conversation_id, limit),
            ).fetchall()
        return [dict(row) for row in reversed(rows)]

    def delete_conversation(self, conversation_id):
        with self._session() as connection:
            cursor = connection.execute("DELETE FROM conversations WHERE id=?", (conversation_id,))
            return cursor.rowcount == 1

    def add_memory(self, category, content, inferred=False):
        if not isinstance(category, str) or not category.strip() or len(category) > 80:
            raise ValueError("Categoria de memória inválida.")
        if not isinstance(content, str) or not content.strip() or len(content) > 4000:
            raise ValueError("A memória está vazia ou excede o limite permitido.")
        if not isinstance(inferred, bool):
            raise ValueError("O estado inferido deve ser booleano.")
        timestamp = _timestamp()
        with self._session() as connection:
            cursor = connection.execute(
                "INSERT INTO memories(category, content, inferred, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (category.strip(), content.strip(), 1 if inferred else 0, timestamp, timestamp),
            )
            return cursor.lastrowid

    def list_memories(self):
        with self._session() as connection:
            rows = connection.execute(
                "SELECT id, category, content, inferred, created_at, updated_at "
                "FROM memories ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]
