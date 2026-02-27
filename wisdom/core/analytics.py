"""Analytics and metrics tracking for WISDOM.

Tracks: session events, daily active users, lesson completions,
feature usage, retention, and session duration.
Stores in SQLite analytics table for dashboard and API access.
"""

from __future__ import annotations

import logging
import sqlite3
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

__all__ = ["Analytics"]

logger = logging.getLogger(__name__)


class Analytics:
    """Lightweight analytics tracker using SQLite.

    Records events like session_start, session_end, lesson_complete,
    chat_message, feature_use, etc. Provides aggregate queries for
    dashboards and the /api/v1/analytics endpoint.
    """

    def __init__(self, db_path: str | Path = "./data/wisdom.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    event TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    timestamp TEXT NOT NULL
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_analytics_event "
                "ON analytics(event, timestamp)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_analytics_user "
                "ON analytics(user_id, timestamp)"
            )

    def track(self, user_id: str, event: str, metadata: dict | None = None) -> None:
        """Record an analytics event."""
        now = datetime.now(timezone.utc).isoformat()
        import json
        meta_str = json.dumps(metadata or {})
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    "INSERT INTO analytics (user_id, event, metadata, timestamp) VALUES (?, ?, ?, ?)",
                    (user_id, event, meta_str, now),
                )
        except Exception:
            logger.warning("Failed to track event %s for user %s", event, user_id)

    # ─── Aggregate Queries ───────────────────────────────────

    def get_daily_active_users(self, days: int = 30) -> list[dict]:
        """Get daily active user counts for the last N days."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(
                """SELECT DATE(timestamp) as day, COUNT(DISTINCT user_id) as users
                   FROM analytics
                   WHERE timestamp >= ?
                   GROUP BY DATE(timestamp)
                   ORDER BY day""",
                (cutoff,),
            ).fetchall()
        return [{"date": r[0], "active_users": r[1]} for r in rows]

    def get_total_users(self) -> int:
        """Get total unique users."""
        with sqlite3.connect(str(self.db_path)) as conn:
            row = conn.execute(
                "SELECT COUNT(DISTINCT user_id) FROM analytics"
            ).fetchone()
        return row[0] if row else 0

    def get_event_counts(self, days: int = 30) -> dict[str, int]:
        """Get event type counts for the last N days."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(
                """SELECT event, COUNT(*) as count
                   FROM analytics
                   WHERE timestamp >= ?
                   GROUP BY event
                   ORDER BY count DESC""",
                (cutoff,),
            ).fetchall()
        return {r[0]: r[1] for r in rows}

    def get_retention_rate(self, days: int = 7) -> float:
        """Calculate N-day retention rate.

        Returns the percentage of users who were active both
        in the first half and second half of the period.
        """
        now = datetime.now(timezone.utc)
        mid = (now - timedelta(days=days)).isoformat()
        start = (now - timedelta(days=days * 2)).isoformat()

        with sqlite3.connect(str(self.db_path)) as conn:
            # Users in first period
            first = conn.execute(
                "SELECT DISTINCT user_id FROM analytics WHERE timestamp >= ? AND timestamp < ?",
                (start, mid),
            ).fetchall()
            first_users = {r[0] for r in first}

            # Users in second period
            second = conn.execute(
                "SELECT DISTINCT user_id FROM analytics WHERE timestamp >= ?",
                (mid,),
            ).fetchall()
            second_users = {r[0] for r in second}

        if not first_users:
            return 0.0
        retained = first_users & second_users
        return round(len(retained) / len(first_users) * 100, 1)

    def get_lesson_completion_rate(self) -> float:
        """Calculate lesson completion rate from events."""
        with sqlite3.connect(str(self.db_path)) as conn:
            started = conn.execute(
                "SELECT COUNT(*) FROM analytics WHERE event = 'lesson_start'"
            ).fetchone()[0]
            completed = conn.execute(
                "SELECT COUNT(*) FROM analytics WHERE event = 'lesson_complete'"
            ).fetchone()[0]
        if started == 0:
            return 0.0
        return round(completed / started * 100, 1)

    def get_avg_session_duration(self, days: int = 30) -> float:
        """Calculate average session duration in minutes."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        with sqlite3.connect(str(self.db_path)) as conn:
            # Get session start/end pairs per user
            rows = conn.execute(
                """SELECT user_id, MIN(timestamp) as first, MAX(timestamp) as last
                   FROM analytics
                   WHERE timestamp >= ?
                   GROUP BY user_id, DATE(timestamp)
                   HAVING COUNT(*) > 1""",
                (cutoff,),
            ).fetchall()

        if not rows:
            return 0.0

        durations = []
        for _, first, last in rows:
            try:
                t1 = datetime.fromisoformat(first.replace("Z", "+00:00"))
                t2 = datetime.fromisoformat(last.replace("Z", "+00:00"))
                duration = (t2 - t1).total_seconds() / 60
                if 0 < duration < 480:  # Filter outliers (>8 hours)
                    durations.append(duration)
            except (ValueError, AttributeError):
                continue

        return round(sum(durations) / len(durations), 1) if durations else 0.0

    def get_summary(self, days: int = 30) -> dict:
        """Get a full analytics summary."""
        return {
            "total_users": self.get_total_users(),
            "daily_active_users": self.get_daily_active_users(days),
            "event_counts": self.get_event_counts(days),
            "retention_rate_7d": self.get_retention_rate(7),
            "lesson_completion_rate": self.get_lesson_completion_rate(),
            "avg_session_minutes": self.get_avg_session_duration(days),
            "period_days": days,
        }
