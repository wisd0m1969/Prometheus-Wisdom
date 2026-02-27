"""Shared community knowledge base — anonymous Q&A pairs."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

__all__ = ["CommunityKnowledge"]


class CommunityKnowledge:
    """Community-curated knowledge base.

    Users can share useful Q&A pairs anonymously.
    Community votes on quality. Top answers used as RAG context.
    """

    def __init__(self, db_path: str | Path = "./data/wisdom.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS community_qa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    language TEXT DEFAULT 'en',
                    category TEXT DEFAULT 'general',
                    upvotes INTEGER DEFAULT 0,
                    downvotes INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)

    def submit(self, question: str, answer: str, language: str = "en", category: str = "general") -> int:
        """Submit a Q&A pair anonymously."""
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "INSERT INTO community_qa (question, answer, language, category, created_at) VALUES (?, ?, ?, ?, ?)",
                (question, answer, language, category, now),
            )
            return cursor.lastrowid

    def vote(self, qa_id: int, upvote: bool = True) -> None:
        """Vote on a Q&A pair."""
        col = "upvotes" if upvote else "downvotes"
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(f"UPDATE community_qa SET {col} = {col} + 1 WHERE id = ?", (qa_id,))

    def search(self, query: str, language: str = "en", limit: int = 10) -> list[dict]:
        """Search community knowledge."""
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(
                """SELECT id, question, answer, language, category, upvotes, downvotes
                   FROM community_qa
                   WHERE language = ? AND (question LIKE ? OR answer LIKE ?)
                   ORDER BY (upvotes - downvotes) DESC
                   LIMIT ?""",
                (language, f"%{query}%", f"%{query}%", limit),
            ).fetchall()

        return [
            {
                "id": r[0], "question": r[1], "answer": r[2],
                "language": r[3], "category": r[4],
                "upvotes": r[5], "downvotes": r[6],
            }
            for r in rows
        ]

    def get_top(self, language: str = "en", limit: int = 20) -> list[dict]:
        """Get top-voted community Q&A pairs."""
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(
                """SELECT id, question, answer, category, upvotes
                   FROM community_qa
                   WHERE language = ?
                   ORDER BY (upvotes - downvotes) DESC
                   LIMIT ?""",
                (language, limit),
            ).fetchall()

        return [
            {"id": r[0], "question": r[1], "answer": r[2], "category": r[3], "upvotes": r[4]}
            for r in rows
        ]
