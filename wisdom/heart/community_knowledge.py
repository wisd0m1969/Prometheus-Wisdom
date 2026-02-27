"""Shared community knowledge base — anonymous Q&A pairs.

Includes content reporting, privacy sanitization before storage,
and quality filtering by vote score.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

__all__ = ["CommunityKnowledge"]


class CommunityKnowledge:
    """Community-curated knowledge base.

    Users can share useful Q&A pairs anonymously.
    Community votes on quality. Top answers used as RAG context.
    All content is sanitized for PII before storage.
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
                    reported INTEGER DEFAULT 0,
                    report_reason TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                )
            """)
            # Migration: add new columns to existing tables
            for col, default in [("reported", "0"), ("report_reason", "''")]:
                try:
                    conn.execute(f"ALTER TABLE community_qa ADD COLUMN {col} TEXT DEFAULT {default}")
                except sqlite3.OperationalError:
                    pass  # Column already exists

    def submit(self, question: str, answer: str, language: str = "en", category: str = "general") -> int:
        """Submit a Q&A pair anonymously. PII is sanitized before storage."""
        from wisdom.heart.privacy_manager import PrivacyManager

        pm = PrivacyManager()
        clean_q = pm.sanitize(question)
        clean_a = pm.sanitize(answer)

        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "INSERT INTO community_qa (question, answer, language, category, created_at) VALUES (?, ?, ?, ?, ?)",
                (clean_q, clean_a, language, category, now),
            )
            return cursor.lastrowid

    def vote(self, qa_id: int, upvote: bool = True) -> None:
        """Vote on a Q&A pair."""
        col = "upvotes" if upvote else "downvotes"
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(f"UPDATE community_qa SET {col} = {col} + 1 WHERE id = ?", (qa_id,))

    def report(self, qa_id: int, reason: str = "") -> None:
        """Report a Q&A pair for inappropriate content.

        Items with 3+ reports are hidden from search results.
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "UPDATE community_qa SET reported = reported + 1, report_reason = ? WHERE id = ?",
                (reason, qa_id),
            )

    def search(self, query: str, language: str = "en", limit: int = 10) -> list[dict]:
        """Search community knowledge (excludes reported items)."""
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(
                """SELECT id, question, answer, language, category, upvotes, downvotes
                   FROM community_qa
                   WHERE language = ? AND reported < 3
                     AND (question LIKE ? OR answer LIKE ?)
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
                   WHERE language = ? AND reported < 3
                   ORDER BY (upvotes - downvotes) DESC
                   LIMIT ?""",
                (language, limit),
            ).fetchall()

        return [
            {"id": r[0], "question": r[1], "answer": r[2], "category": r[3], "upvotes": r[4]}
            for r in rows
        ]

    def get_by_category(self, category: str, language: str = "en", limit: int = 10) -> list[dict]:
        """Get Q&A pairs filtered by category."""
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(
                """SELECT id, question, answer, upvotes
                   FROM community_qa
                   WHERE category = ? AND language = ? AND reported < 3
                   ORDER BY (upvotes - downvotes) DESC
                   LIMIT ?""",
                (category, language, limit),
            ).fetchall()

        return [
            {"id": r[0], "question": r[1], "answer": r[2], "upvotes": r[3]}
            for r in rows
        ]
