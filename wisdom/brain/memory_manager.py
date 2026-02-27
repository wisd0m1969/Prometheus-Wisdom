"""Short-term + Long-term memory management.

Short-term: Last N messages in-memory per session.
Long-term: ChromaDB vector store for RAG retrieval across sessions.
Persistence: SQLite conversations table for durable message storage.
Session lifecycle: start → chat → end (summarize + persist).
"""

from __future__ import annotations

import logging
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

__all__ = ["MemoryManager", "Message"]

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """A single conversation message."""

    role: str  # "user" or "wisdom"
    content: str
    timestamp: str
    language: str = ""


class MemoryManager:
    """Manages short-term conversation memory and long-term vector storage.

    Short-term: In-memory list of recent messages per user.
    Long-term: ChromaDB for RAG retrieval (initialized lazily).
    Persistence: SQLite conversations table for durable storage.
    """

    def __init__(self, max_messages: int = 20, db_path: str | Path = "./data/wisdom.db") -> None:
        self.max_messages = max_messages
        self.db_path = Path(db_path)
        self._sessions: dict[str, list[Message]] = defaultdict(list)
        self._chroma_client = None
        self._collections: dict[str, object] = {}
        self._session_summaries: dict[str, str] = {}
        self._init_db()

    def _init_db(self) -> None:
        """Create conversations table if it doesn't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    language TEXT DEFAULT '',
                    sentiment REAL DEFAULT 0.0,
                    timestamp TEXT NOT NULL
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_conversations_user "
                "ON conversations(user_id, timestamp)"
            )

    # ─── Short-term Memory ────────────────────────────────────

    def add_message(self, user_id: str, role: str, content: str, language: str = "") -> None:
        """Add a message to the user's conversation history.

        Stores both in-memory (short-term) and in SQLite (persistent).
        """
        now = datetime.now(timezone.utc).isoformat()
        msg = Message(role=role, content=content, timestamp=now, language=language)
        self._sessions[user_id].append(msg)

        # Persist to SQLite
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    "INSERT INTO conversations (user_id, role, content, language, timestamp) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (user_id, role, content, language, now),
                )
        except Exception:
            logger.warning("Failed to persist message to SQLite for user %s", user_id)

        # Trim: summarize oldest when exceeding limit
        if len(self._sessions[user_id]) > self.max_messages:
            self._trim_history(user_id)

    def get_history(self, user_id: str) -> list[Message]:
        """Get conversation history for a user."""
        return list(self._sessions.get(user_id, []))

    def get_history_as_dicts(self, user_id: str) -> list[dict]:
        """Get history as list of dicts (for LangChain)."""
        return [
            {"role": m.role, "content": m.content}
            for m in self.get_history(user_id)
        ]

    def get_history_text(self, user_id: str) -> str:
        """Get history as formatted text for prompt injection."""
        history = self.get_history(user_id)
        if not history:
            return ""
        lines = []
        for msg in history:
            role = "User" if msg.role == "user" else "WISDOM"
            lines.append(f"{role}: {msg.content}")
        return "\n".join(lines)

    def clear_session(self, user_id: str) -> None:
        """Clear a user's session history (in-memory and SQLite)."""
        self._sessions.pop(user_id, None)
        self._session_summaries.pop(user_id, None)
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
        except Exception:
            logger.warning("Failed to clear SQLite conversations for user %s", user_id)

    def get_conversation_count(self, user_id: str) -> int:
        """Get total number of persisted messages for a user."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                row = conn.execute(
                    "SELECT COUNT(*) FROM conversations WHERE user_id = ?",
                    (user_id,),
                ).fetchone()
                return row[0] if row else 0
        except Exception:
            return len(self._sessions.get(user_id, []))

    def get_context_string(self, user_id: str, max_tokens: int = 2000) -> str:
        """Get conversation history as a formatted string for prompt injection."""
        # Include previous session summary if available
        parts = []
        summary = self._session_summaries.get(user_id)
        if summary:
            parts.append(f"[Previous session summary: {summary}]")

        history = self.get_history(user_id)
        if not history:
            return "\n".join(parts) if parts else ""

        char_count = sum(len(p) for p in parts)
        for msg in reversed(history):
            role = "User" if msg.role == "user" else "WISDOM"
            line = f"{role}: {msg.content}"
            char_count += len(line)
            if char_count > max_tokens * 4:
                break
            parts.append(line)

        return "\n".join(parts)

    def _trim_history(self, user_id: str) -> None:
        """Trim history by summarizing oldest 5 messages and keeping newest."""
        msgs = self._sessions[user_id]
        oldest_5 = msgs[:5]
        summary_text = " | ".join(
            f"{m.role}: {m.content[:80]}" for m in oldest_5
        )
        self._session_summaries[user_id] = summary_text
        self._sessions[user_id] = msgs[5:]
        logger.debug("Trimmed %d oldest messages for user %s", 5, user_id)

    # ─── Session Lifecycle ────────────────────────────────────

    def on_session_start(self, user_id: str) -> None:
        """Called when a user session begins.

        Loads recent messages from SQLite and last summary from ChromaDB.
        """
        # Load recent messages from SQLite into memory
        if not self._sessions[user_id]:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    rows = conn.execute(
                        "SELECT role, content, language, timestamp FROM conversations "
                        "WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
                        (user_id, self.max_messages),
                    ).fetchall()
                if rows:
                    for r in reversed(rows):
                        self._sessions[user_id].append(
                            Message(role=r[0], content=r[1], timestamp=r[3], language=r[2])
                        )
                    logger.info("Loaded %d messages from SQLite for user %s", len(rows), user_id)
            except Exception:
                logger.warning("Failed to load messages from SQLite for user %s", user_id)

        # Load last summary from ChromaDB long-term memory
        memories = self.recall(user_id, "last session summary", n_results=1)
        if memories:
            self._session_summaries[user_id] = memories[0]
            logger.info("Loaded previous session context for user %s", user_id)

    def on_session_end(self, user_id: str) -> None:
        """Called when a user session ends. Summarize and persist to long-term memory."""
        history = self.get_history(user_id)
        if not history:
            return

        # Build a summary from messages
        topics = set()
        for msg in history:
            words = msg.content.lower().split()
            for w in words:
                if len(w) > 5:
                    topics.add(w)

        summary = (
            f"Session with {len(history)} messages. "
            f"Topics discussed: {', '.join(list(topics)[:10])}"
        )

        self.store_long_term(
            user_id, summary,
            metadata={"type": "session_summary", "message_count": len(history)},
        )
        logger.info("Saved session summary for user %s", user_id)

    # ─── Long-term Memory (ChromaDB) ─────────────────────────

    def init_vector_store(self, persist_path: str = "./data/chroma") -> None:
        """Initialize ChromaDB for long-term memory."""
        try:
            import chromadb

            self._chroma_client = chromadb.PersistentClient(path=persist_path)
            logger.info("ChromaDB initialized at %s", persist_path)
        except Exception:
            logger.warning("ChromaDB unavailable — long-term memory disabled")

    def get_or_create_collection(self, name: str = "wisdom_memory") -> object | None:
        """Get or create a ChromaDB collection."""
        if not self._chroma_client:
            return None
        if name not in self._collections:
            self._collections[name] = self._chroma_client.get_or_create_collection(
                name=name,
                metadata={"description": f"WISDOM {name}"},
            )
        return self._collections[name]

    def store_long_term(
        self, user_id: str, content: str, metadata: dict | None = None,
        collection_name: str = "wisdom_memory",
    ) -> None:
        """Store a fact or summary in long-term vector memory."""
        collection = self.get_or_create_collection(collection_name)
        if not collection:
            return

        doc_id = f"{user_id}_{datetime.now(timezone.utc).isoformat()}"
        meta = {"user_id": user_id, **(metadata or {})}

        collection.add(documents=[content], ids=[doc_id], metadatas=[meta])
        logger.debug("Stored long-term memory: %s", doc_id)

    def save_fact(self, user_id: str, fact_text: str, metadata: dict | None = None) -> None:
        """Store an important fact about the user."""
        self.store_long_term(
            user_id, fact_text,
            metadata={"type": "user_fact", **(metadata or {})},
            collection_name="user_facts",
        )

    def save_conversation_summary(self, user_id: str, summary: str) -> None:
        """Store a conversation summary for future retrieval."""
        self.store_long_term(
            user_id, summary,
            metadata={"type": "conversation_summary"},
            collection_name="conversation_summaries",
        )

    def recall(
        self, user_id: str, query: str, n_results: int = 5,
        collection_name: str = "wisdom_memory",
    ) -> list[str]:
        """Retrieve relevant memories for a query using vector similarity."""
        collection = self.get_or_create_collection(collection_name)
        if not collection:
            return []

        try:
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"user_id": user_id},
            )
            return results.get("documents", [[]])[0]
        except Exception:
            return []
