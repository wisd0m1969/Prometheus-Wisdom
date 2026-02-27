"""Goal tracking, milestones, achievements, and badges."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from wisdom.core.constants import BADGES

__all__ = ["GoalTracker"]


class GoalTracker:
    """Track user goals, milestones, and achievements.

    Features:
    - Set and break down goals into milestones
    - Track progress as percentage
    - Award achievement badges
    - Celebration messages on milestones
    """

    def __init__(self, db_path: str | Path = "./data/wisdom.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    description TEXT NOT NULL,
                    milestones TEXT DEFAULT '[]',
                    progress REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'active',
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS achievements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    badge_id TEXT NOT NULL,
                    earned_at TEXT NOT NULL,
                    UNIQUE(user_id, badge_id)
                )
            """)

    def create_goal(self, user_id: str, description: str, milestones: list[str] | None = None) -> int:
        """Create a new goal with optional milestones."""
        now = datetime.now(timezone.utc).isoformat()
        milestone_data = [{"text": m, "done": False} for m in (milestones or [])]

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "INSERT INTO goals (user_id, description, milestones, created_at) VALUES (?, ?, ?, ?)",
                (user_id, description, json.dumps(milestone_data), now),
            )
            return cursor.lastrowid

    def update_progress(self, goal_id: int, progress: float) -> None:
        """Update goal progress (0.0 to 1.0)."""
        status = "completed" if progress >= 1.0 else "active"
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "UPDATE goals SET progress = ?, status = ? WHERE id = ?",
                (min(1.0, progress), status, goal_id),
            )

    def complete_milestone(self, goal_id: int, milestone_index: int) -> None:
        """Mark a milestone as completed."""
        with sqlite3.connect(str(self.db_path)) as conn:
            row = conn.execute("SELECT milestones FROM goals WHERE id = ?", (goal_id,)).fetchone()
            if not row:
                return
            milestones = json.loads(row[0])
            if milestone_index < len(milestones):
                milestones[milestone_index]["done"] = True
                done_count = sum(1 for m in milestones if m["done"])
                progress = done_count / len(milestones) if milestones else 0
                conn.execute(
                    "UPDATE goals SET milestones = ?, progress = ?, status = ? WHERE id = ?",
                    (json.dumps(milestones), progress, "completed" if progress >= 1.0 else "active", goal_id),
                )

    def get_goals(self, user_id: str) -> list[dict]:
        """Get all goals for a user."""
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(
                "SELECT id, description, milestones, progress, status, created_at FROM goals WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        return [
            {
                "id": r[0], "description": r[1],
                "milestones": json.loads(r[2]), "progress": r[3],
                "status": r[4], "created_at": r[5],
            }
            for r in rows
        ]

    def award_badge(self, user_id: str, badge_id: str) -> bool:
        """Award a badge to a user. Returns True if newly awarded."""
        if badge_id not in BADGES:
            return False
        now = datetime.now(timezone.utc).isoformat()
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    "INSERT INTO achievements (user_id, badge_id, earned_at) VALUES (?, ?, ?)",
                    (user_id, badge_id, now),
                )
            return True
        except sqlite3.IntegrityError:
            return False  # Already earned

    def get_badges(self, user_id: str) -> list[dict]:
        """Get all badges earned by a user."""
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(
                "SELECT badge_id, earned_at FROM achievements WHERE user_id = ? ORDER BY earned_at",
                (user_id,),
            ).fetchall()
        return [
            {"badge_id": r[0], "name": BADGES[r[0]]["name"], "earned_at": r[1]}
            for r in rows
            if r[0] in BADGES
        ]

    # ─── Celebration Messages ──────────────────────────────────

    _BADGE_CELEBRATIONS = {
        "first_contact": "You just had your first AI conversation! Welcome to the future!",
        "polyglot": "You're speaking to AI in multiple languages — amazing!",
        "curious_mind": "50 questions asked! Your curiosity is your superpower!",
        "level_up": "Level complete! You're learning so fast!",
        "perfect_score": "100% on a quiz — you're a natural!",
        "streak_master": "7 days in a row! Your dedication is inspiring!",
        "code_rookie": "You wrote your first code with AI — the sky is the limit!",
        "builder": "You built an app! You're no longer just a user — you're a creator!",
        "creator": "You've built your own AI tool! Incredible achievement!",
        "helper": "You helped the community — thank you for sharing your knowledge!",
        "pioneer": "You're one of the first 1000 WISDOM users — a true pioneer!",
    }

    _MILESTONE_CELEBRATIONS = [
        "Great progress! You're doing amazing!",
        "One step closer to your goal — keep going!",
        "Milestone achieved! You should be proud of yourself!",
        "You're making real progress — don't stop now!",
    ]

    def get_celebration_message(self, badge_id: str) -> str:
        """Get a celebration message for a newly earned badge."""
        return self._BADGE_CELEBRATIONS.get(
            badge_id,
            "Congratulations! You earned a new achievement!",
        )

    def get_milestone_celebration(self, goal_id: int, milestone_index: int) -> str:
        """Get a celebration message for a completed milestone."""
        return self._MILESTONE_CELEBRATIONS[milestone_index % len(self._MILESTONE_CELEBRATIONS)]

    def award_badge_with_message(self, user_id: str, badge_id: str) -> tuple[bool, str]:
        """Award a badge and return (newly_awarded, celebration_message)."""
        awarded = self.award_badge(user_id, badge_id)
        if awarded:
            return True, self.get_celebration_message(badge_id)
        return False, ""
