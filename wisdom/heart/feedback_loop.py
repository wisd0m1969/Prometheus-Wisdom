"""User feedback collection and improvement pipeline."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

__all__ = ["FeedbackLoop"]


class FeedbackLoop:
    """Collect and process user feedback to improve WISDOM."""

    def __init__(self, db_path: str | Path = "./data/wisdom.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    rating INTEGER,
                    comment TEXT,
                    context TEXT,
                    created_at TEXT NOT NULL
                )
            """)

    def submit(
        self,
        rating: int,
        comment: str = "",
        user_id: str = "",
        context: str = "",
    ) -> int:
        """Submit feedback.

        Args:
            rating: 1-5 star rating.
            comment: Optional text feedback.
            user_id: Optional user ID.
            context: Optional conversation context.

        Returns:
            Feedback entry ID.
        """
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "INSERT INTO feedback (user_id, rating, comment, context, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, rating, comment, context, now),
            )
            return cursor.lastrowid

    def get_average_rating(self) -> float:
        """Get overall average rating."""
        with sqlite3.connect(str(self.db_path)) as conn:
            row = conn.execute("SELECT AVG(rating) FROM feedback WHERE rating IS NOT NULL").fetchone()
        return round(row[0], 2) if row[0] else 0.0

    def get_recent(self, limit: int = 20) -> list[dict]:
        """Get recent feedback entries."""
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(
                "SELECT id, rating, comment, created_at FROM feedback ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {"id": r[0], "rating": r[1], "comment": r[2], "created_at": r[3]}
            for r in rows
        ]
