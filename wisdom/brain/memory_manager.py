"""Short-term + Long-term memory management.

Short-term: Last N messages in-memory per session.
Long-term: ChromaDB vector store for RAG retrieval across sessions.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone

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
    """

    def __init__(self, max_messages: int = 20) -> None:
        self.max_messages = max_messages
        self._sessions: dict[str, list[Message]] = defaultdict(list)
        self._chroma_client = None
        self._collection = None

    def add_message(self, user_id: str, role: str, content: str, language: str = "") -> None:
        """Add a message to the user's conversation history."""
        msg = Message(
            role=role,
            content=content,
            timestamp=datetime.now(timezone.utc).isoformat(),
            language=language,
        )
        self._sessions[user_id].append(msg)

        # Trim to max messages
        if len(self._sessions[user_id]) > self.max_messages:
            self._sessions[user_id] = self._sessions[user_id][-self.max_messages :]

    def get_history(self, user_id: str) -> list[Message]:
        """Get conversation history for a user."""
        return list(self._sessions.get(user_id, []))

    def get_history_as_dicts(self, user_id: str) -> list[dict]:
        """Get history as list of dicts (for LangChain)."""
        return [
            {"role": m.role, "content": m.content}
            for m in self.get_history(user_id)
        ]

    def clear_session(self, user_id: str) -> None:
        """Clear a user's session history."""
        self._sessions.pop(user_id, None)

    def get_context_string(self, user_id: str, max_tokens: int = 2000) -> str:
        """Get conversation history as a formatted string for prompt injection."""
        history = self.get_history(user_id)
        if not history:
            return ""

        lines = []
        char_count = 0
        for msg in reversed(history):
            role = "User" if msg.role == "user" else "WISDOM"
            line = f"{role}: {msg.content}"
            char_count += len(line)
            if char_count > max_tokens * 4:  # rough char-to-token ratio
                break
            lines.insert(0, line)

        return "\n".join(lines)

    # -- Long-term memory (ChromaDB) --

    def init_vector_store(self, persist_path: str = "./data/chroma") -> None:
        """Initialize ChromaDB for long-term memory."""
        try:
            import chromadb

            self._chroma_client = chromadb.PersistentClient(path=persist_path)
            self._collection = self._chroma_client.get_or_create_collection(
                name="wisdom_memory",
                metadata={"description": "WISDOM long-term memory"},
            )
            logger.info("ChromaDB initialized at %s", persist_path)
        except Exception:
            logger.warning("ChromaDB unavailable — long-term memory disabled")

    def store_long_term(self, user_id: str, content: str, metadata: dict | None = None) -> None:
        """Store a fact or summary in long-term vector memory."""
        if not self._collection:
            return

        doc_id = f"{user_id}_{datetime.now(timezone.utc).isoformat()}"
        meta = {"user_id": user_id, **(metadata or {})}

        self._collection.add(
            documents=[content],
            ids=[doc_id],
            metadatas=[meta],
        )

    def recall(self, user_id: str, query: str, n_results: int = 5) -> list[str]:
        """Retrieve relevant memories for a query using vector similarity."""
        if not self._collection:
            return []

        results = self._collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"user_id": user_id},
        )

        return results.get("documents", [[]])[0]
