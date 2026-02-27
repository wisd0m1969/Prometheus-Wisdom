"""User feedback collection and improvement pipeline.

Collects ratings, comments, and response context. Provides
improvement suggestions based on aggregated feedback patterns.
"""

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
                    category TEXT DEFAULT 'general',
                    created_at TEXT NOT NULL
                )
            """)
            # Migration: add category column to existing tables
            try:
                conn.execute("ALTER TABLE feedback ADD COLUMN category TEXT DEFAULT 'general'")
            except sqlite3.OperationalError:
                pass  # Column already exists

    def submit(
        self,
        rating: int,
        comment: str = "",
        user_id: str = "",
        context: str = "",
        category: str = "general",
    ) -> int:
        """Submit feedback.

        Args:
            rating: 1-5 star rating.
            comment: Optional text feedback.
            user_id: Optional user ID.
            context: Optional conversation context.
            category: Feedback category (general, response_quality, ui, content).

        Returns:
            Feedback entry ID.
        """
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "INSERT INTO feedback (user_id, rating, comment, context, category, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, rating, comment, context, category, now),
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

    def get_improvement_suggestions(self) -> list[str]:
        """Analyze feedback patterns and return improvement suggestions.

        Returns:
            List of actionable improvement suggestions.
        """
        suggestions = []

        with sqlite3.connect(str(self.db_path)) as conn:
            # Check average rating
            avg_row = conn.execute("SELECT AVG(rating), COUNT(*) FROM feedback WHERE rating IS NOT NULL").fetchone()
            avg_rating = avg_row[0] if avg_row[0] else 5.0
            total_count = avg_row[1] or 0

            if total_count == 0:
                return ["Not enough feedback data yet. Encourage users to rate responses."]

            if avg_rating < 3.0:
                suggestions.append("Overall satisfaction is low. Review response quality and tone adaptation.")

            # Check for low-rated categories
            cat_rows = conn.execute(
                "SELECT category, AVG(rating), COUNT(*) FROM feedback GROUP BY category HAVING COUNT(*) >= 3"
            ).fetchall()
            for cat, cat_avg, cat_count in cat_rows:
                if cat_avg and cat_avg < 3.0:
                    suggestions.append(f"Category '{cat}' has low ratings ({cat_avg:.1f}/5). Needs attention.")

            # Check recent trend
            recent_rows = conn.execute(
                "SELECT AVG(rating) FROM feedback ORDER BY created_at DESC LIMIT 10"
            ).fetchone()
            if recent_rows[0] and avg_rating and recent_rows[0] < avg_rating - 0.5:
                suggestions.append("Recent ratings are declining. Check for regression in response quality.")

            # Check for common negative comments
            negative_rows = conn.execute(
                "SELECT comment FROM feedback WHERE rating <= 2 AND comment != '' LIMIT 20"
            ).fetchall()
            if len(negative_rows) >= 3:
                suggestions.append(f"Found {len(negative_rows)} negative comments. Review for common themes.")

        if not suggestions:
            suggestions.append("Feedback is positive overall. Keep up the good work!")

        return suggestions

    def get_stats(self) -> dict:
        """Get feedback statistics summary."""
        with sqlite3.connect(str(self.db_path)) as conn:
            row = conn.execute(
                "SELECT COUNT(*), AVG(rating), MIN(rating), MAX(rating) FROM feedback"
            ).fetchone()

            distribution = {}
            for rating in range(1, 6):
                count_row = conn.execute(
                    "SELECT COUNT(*) FROM feedback WHERE rating = ?", (rating,)
                ).fetchone()
                distribution[rating] = count_row[0]

        return {
            "total": row[0],
            "average": round(row[1], 2) if row[1] else 0.0,
            "min": row[2] or 0,
            "max": row[3] or 0,
            "distribution": distribution,
        }
