"""User profile management with SQLite persistence."""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

__all__ = ["UserProfile", "UserProfileManager"]


@dataclass
class UserProfile:
    """Represents a WISDOM user."""

    id: str
    name: str = ""
    language: str = "en"
    skill_level: float = 0.0
    interests: list[str] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)
    created_at: str = ""
    last_seen: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "language": self.language,
            "skill_level": self.skill_level,
            "interests": self.interests,
            "goals": self.goals,
            "preferences": self.preferences,
            "created_at": self.created_at,
            "last_seen": self.last_seen,
        }


class UserProfileManager:
    """CRUD operations for user profiles stored in SQLite."""

    def __init__(self, db_path: str | Path = "./data/wisdom.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    name TEXT DEFAULT '',
                    language TEXT DEFAULT 'en',
                    skill_level REAL DEFAULT 0.0,
                    interests TEXT DEFAULT '[]',
                    goals TEXT DEFAULT '[]',
                    preferences TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    last_seen TEXT NOT NULL
                )
            """)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    def get_or_create(self, user_id: str | None = None) -> UserProfile:
        """Get existing profile or create a new one."""
        if user_id:
            profile = self.get(user_id)
            if profile:
                profile.last_seen = datetime.now(timezone.utc).isoformat()
                self.update(profile)
                return profile
        return self.create(user_id)

    def create(self, user_id: str | None = None, name: str = "", language: str = "en") -> UserProfile:
        """Create a new user profile."""
        now = datetime.now(timezone.utc).isoformat()
        profile = UserProfile(
            id=user_id or str(uuid.uuid4()),
            name=name,
            language=language,
            created_at=now,
            last_seen=now,
        )
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO users (id, name, language, skill_level,
                   interests, goals, preferences, created_at, last_seen)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    profile.id,
                    profile.name,
                    profile.language,
                    profile.skill_level,
                    json.dumps(profile.interests),
                    json.dumps(profile.goals),
                    json.dumps(profile.preferences),
                    profile.created_at,
                    profile.last_seen,
                ),
            )
        return profile

    def get(self, user_id: str) -> UserProfile | None:
        """Get a user profile by ID. Auto-updates last_seen."""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return None
        return UserProfile(
            id=row[0],
            name=row[1],
            language=row[2],
            skill_level=row[3],
            interests=json.loads(row[4]),
            goals=json.loads(row[5]),
            preferences=json.loads(row[6]),
            created_at=row[7],
            last_seen=row[8],
        )

    def update(self, profile: UserProfile) -> None:
        """Update an existing profile."""
        with self._connect() as conn:
            conn.execute(
                """UPDATE users SET name=?, language=?, skill_level=?,
                   interests=?, goals=?, preferences=?, last_seen=?
                   WHERE id=?""",
                (
                    profile.name,
                    profile.language,
                    profile.skill_level,
                    json.dumps(profile.interests),
                    json.dumps(profile.goals),
                    json.dumps(profile.preferences),
                    profile.last_seen,
                    profile.id,
                ),
            )

    def delete(self, user_id: str) -> None:
        """Delete a user profile (right to be forgotten)."""
        with self._connect() as conn:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))

    def list_users(self) -> list[dict]:
        """List all user profiles (summary only)."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, name, language, skill_level, last_seen FROM users ORDER BY last_seen DESC"
            ).fetchall()
        return [
            {"id": r[0], "name": r[1], "language": r[2], "skill_level": r[3], "last_seen": r[4]}
            for r in rows
        ]

    def export_json(self, user_id: str) -> str | None:
        """Export user data as JSON string."""
        profile = self.get(user_id)
        if not profile:
            return None
        return json.dumps(profile.to_dict(), indent=2, ensure_ascii=False)

    def import_json(self, json_string: str) -> str:
        """Import user profile from JSON string. Returns user_id."""
        data = json.loads(json_string)
        user_id = data.get("id", str(uuid.uuid4()))

        existing = self.get(user_id)
        if existing:
            self.delete(user_id)

        now = datetime.now(timezone.utc).isoformat()
        profile = UserProfile(
            id=user_id,
            name=data.get("name", ""),
            language=data.get("language", "en"),
            skill_level=data.get("skill_level", 0.0),
            interests=data.get("interests", []),
            goals=data.get("goals", []),
            preferences=data.get("preferences", {}),
            created_at=data.get("created_at", now),
            last_seen=now,
        )
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO users (id, name, language, skill_level,
                   interests, goals, preferences, created_at, last_seen)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    profile.id, profile.name, profile.language,
                    profile.skill_level,
                    json.dumps(profile.interests),
                    json.dumps(profile.goals),
                    json.dumps(profile.preferences),
                    profile.created_at, profile.last_seen,
                ),
            )
        return user_id
