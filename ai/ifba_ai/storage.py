"""Private SQLite conversation store with schema migrations."""

import os
import json
import re
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path


SCHEMA_VERSION = 2
MEMORY_CATEGORIES = {
    "learning_preference", "language", "application", "learned_topic",
    "difficulty", "goal", "project", "other",
}
_SENSITIVE_MEMORY = re.compile(
    r"\b(senha|password|api[ _-]?key|token|cpf|rg|matr[ií]cula|telefone|e-mail|email)\b",
    re.IGNORECASE,
)


def _timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ConversationStore:
    def __init__(self, paths, in_memory=False):
        self.paths = paths
        self.in_memory = bool(in_memory)
        self._memory_connection = None
        if self.in_memory:
            self._memory_connection = sqlite3.connect(":memory:", check_same_thread=False)
            self._memory_connection.row_factory = sqlite3.Row
            self._memory_connection.execute("PRAGMA foreign_keys = ON")
        else:
            self.paths.prepare()
        self._migrate()

    def _connect(self):
        if self.in_memory:
            return self._memory_connection
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
            if not self.in_memory:
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
                version = 1
            if version < 2:
                connection.execute("ALTER TABLE conversations ADD COLUMN summary TEXT NOT NULL DEFAULT ''")
                connection.execute("CREATE INDEX messages_created_at ON messages(created_at)")
                connection.execute("CREATE INDEX memories_updated_at ON memories(updated_at)")
                connection.execute("PRAGMA user_version = 2")

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

    def conversation_summary(self, conversation_id):
        with self._connect() as connection:
            row = connection.execute("SELECT summary FROM conversations WHERE id=?", (conversation_id,)).fetchone()
        if row is None:
            raise KeyError("Conversa não encontrada.")
        return row["summary"]

    def update_conversation_summary(self, conversation_id, summary):
        if not isinstance(summary, str) or len(summary) > 4000:
            raise ValueError("O resumo excede o limite permitido.")
        with self._session() as connection:
            cursor = connection.execute("UPDATE conversations SET summary=? WHERE id=?",
                                        (summary.strip(), conversation_id))
            return cursor.rowcount == 1

    def build_bounded_context(self, conversation_id, max_messages=24, max_chars=24000):
        if not 1 <= max_messages <= 100 or not 100 <= max_chars <= 100000:
            raise ValueError("Limites de contexto inválidos.")
        with self._connect() as connection:
            row = connection.execute("SELECT summary FROM conversations WHERE id=?", (conversation_id,)).fetchone()
            if row is None:
                raise KeyError("Conversa não encontrada.")
            messages = connection.execute(
                "SELECT role, content FROM messages WHERE conversation_id=? AND role IN ('user','assistant') "
                "ORDER BY id DESC LIMIT ?", (conversation_id, max_messages)
            ).fetchall()
        selected = []
        used = 0
        for message in reversed(messages):
            content = message["content"]
            remaining = max_chars - used
            if remaining <= 0:
                break
            content = content[-remaining:]
            selected.append({"role": message["role"], "content": content})
            used += len(content)
        return selected

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
            count = connection.execute("SELECT COUNT(*) FROM messages WHERE conversation_id=?",
                                       (conversation_id,)).fetchone()[0]
            if count > 32:
                self._refresh_summary(connection, conversation_id)

    @staticmethod
    def _refresh_summary(connection, conversation_id):
        rows = connection.execute(
            "SELECT role, content FROM messages WHERE conversation_id=? ORDER BY id DESC LIMIT -1 OFFSET 24",
            (conversation_id,),
        ).fetchall()
        snippets = []
        total = 0
        for row in reversed(rows):
            content = " ".join(row["content"].split())
            if not content or _SENSITIVE_MEMORY.search(content):
                continue
            excerpt = content[:280]
            label = "Estudante" if row["role"] == "user" else "Assistente"
            fragment = "{}: {}".format(label, excerpt)
            if total + len(fragment) > 3500:
                break
            snippets.append(fragment)
            total += len(fragment)
        summary = "\n".join(snippets[-12:])
        connection.execute("UPDATE conversations SET summary=? WHERE id=?",
                           (summary, conversation_id))

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
        if category not in MEMORY_CATEGORIES:
            raise ValueError("Categoria de memória inválida.")
        if not isinstance(content, str) or not content.strip() or len(content) > 4000:
            raise ValueError("A memória está vazia ou excede o limite permitido.")
        if _SENSITIVE_MEMORY.search(content):
            raise ValueError("Essa memória parece conter dado sensível. Remova identificadores ou credenciais antes de salvar.")
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

    def update_memory(self, memory_id, category, content, inferred=None):
        if category not in MEMORY_CATEGORIES:
            raise ValueError("Categoria de memória inválida.")
        if not isinstance(content, str) or not content.strip() or len(content) > 4000:
            raise ValueError("A memória está vazia ou excede o limite permitido.")
        if _SENSITIVE_MEMORY.search(content):
            raise ValueError("Essa memória parece conter dado sensível. Remova identificadores ou credenciais antes de salvar.")
        with self._session() as connection:
            if inferred is None:
                cursor = connection.execute("UPDATE memories SET category=?, content=?, updated_at=? WHERE id=?",
                                            (category, content.strip(), _timestamp(), int(memory_id)))
            else:
                if not isinstance(inferred, bool):
                    raise ValueError("O estado inferido deve ser booleano.")
                cursor = connection.execute("UPDATE memories SET category=?, content=?, inferred=?, updated_at=? WHERE id=?",
                                            (category, content.strip(), int(inferred), _timestamp(), int(memory_id)))
            return cursor.rowcount == 1

    def delete_memory(self, memory_id):
        with self._session() as connection:
            return connection.execute("DELETE FROM memories WHERE id=?", (int(memory_id),)).rowcount == 1

    def clear_memories(self):
        with self._session() as connection:
            return connection.execute("DELETE FROM memories").rowcount

    def clear_history(self):
        with self._session() as connection:
            return connection.execute("DELETE FROM conversations").rowcount

    def search_memories(self, query, limit=8):
        if not isinstance(query, str) or not 1 <= limit <= 50:
            raise ValueError("Busca de memória inválida.")
        terms = {term.casefold() for term in re.findall(r"[\wÀ-ÿ]{2,}", query)}
        if not terms:
            return []
        memories = self.list_memories()
        def score(item):
            content_terms = set(re.findall(r"[\wÀ-ÿ]{2,}", (item["category"] + " " + item["content"]).casefold()))
            return len(terms & content_terms)
        ranked = [(score(item), item) for item in memories]
        return [item for value, item in sorted(ranked, key=lambda pair: (pair[0], pair[1]["updated_at"]), reverse=True)
                if value][:limit]

    def prune(self, history_days=365, memory_days=365):
        for value in (history_days, memory_days):
            if not isinstance(value, int) or not 0 <= value <= 3650:
                raise ValueError("Prazo de retenção inválido.")
        now = datetime.now(timezone.utc)
        history_cutoff = (now - timedelta(days=history_days)).isoformat(timespec="seconds")
        memory_cutoff = (now - timedelta(days=memory_days)).isoformat(timespec="seconds")
        with self._session() as connection:
            old_memories = connection.execute(
                "DELETE FROM memories WHERE updated_at < ?" if memory_days else "DELETE FROM memories",
                (memory_cutoff,) if memory_days else (),
            ).rowcount
            old_conversations = connection.execute(
                "DELETE FROM conversations WHERE updated_at < ?" if history_days else "DELETE FROM conversations",
                (history_cutoff,) if history_days else (),
            ).rowcount
        return {"memories": old_memories, "conversations": old_conversations}

    def export_json(self):
        with self._connect() as connection:
            conversations = connection.execute(
                "SELECT id,title,summary,created_at,updated_at FROM conversations ORDER BY created_at"
            ).fetchall()
            messages = connection.execute(
                "SELECT conversation_id,role,content,created_at FROM messages ORDER BY id"
            ).fetchall()
        payload = {
            "format": "ifba-ai-export-v1",
            "conversations": [dict(row) for row in conversations],
            "messages": [dict(row) for row in messages],
            "memories": self.list_memories(),
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)
