"""Explicit user preference learning from conversation patterns.

Tracks and learns:
- Preferred topics (from message frequency)
- Learning style (visual, step-by-step, examples)
- Response length preference (short vs detailed)
- Complexity preference (simple vs technical)
- Active time patterns (morning, afternoon, evening)

Stores learned preferences in UserProfile.preferences dict.
"""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wisdom.brain.memory_manager import Message
    from wisdom.brain.user_profile import UserProfile

__all__ = ["PreferenceLearner"]

logger = logging.getLogger(__name__)

# Keywords that indicate learning style preferences
_STYLE_SIGNALS = {
    "step_by_step": ["step by step", "step-by-step", "one at a time", "ทีละขั้น", "paso a paso"],
    "examples": ["example", "show me", "for instance", "ตัวอย่าง", "ejemplo"],
    "visual": ["diagram", "chart", "picture", "visualize", "รูปภาพ", "แผนภาพ"],
    "concise": ["short", "brief", "quick", "tldr", "สั้นๆ", "breve"],
    "detailed": ["detail", "explain more", "in depth", "elaborate", "อธิบายเพิ่ม", "detallado"],
}

# Topic categories for preference tracking
_TOPIC_KEYWORDS = {
    "ai_basics": ["what is ai", "ai คือ", "artificial intelligence", "machine learning"],
    "coding": ["code", "python", "programming", "function", "โค้ด", "โปรแกรม"],
    "ethics": ["bias", "ethics", "fair", "responsible", "จริยธรรม"],
    "practical": ["daily", "work", "business", "practical", "ใช้งาน", "ประยุกต์"],
    "creative": ["creative", "write", "story", "art", "สร้างสรรค์"],
    "technical": ["api", "model", "architecture", "neural", "เทคนิค"],
}


class PreferenceLearner:
    """Learns user preferences from conversation history.

    Analyzes patterns across messages to build an explicit preference
    profile that the adaptation engine uses for personalization.
    """

    def analyze(self, profile: UserProfile, history: list[Message]) -> dict:
        """Analyze conversation history and return learned preferences.

        Returns:
            Dict with keys: preferred_topics, learning_style, response_length,
            complexity, active_hours, topic_counts.
        """
        if not history:
            return self._default_preferences()

        user_messages = [m for m in history if m.role == "user"]
        if not user_messages:
            return self._default_preferences()

        return {
            "preferred_topics": self._learn_topics(user_messages),
            "learning_style": self._learn_style(user_messages),
            "response_length": self._learn_length_preference(user_messages),
            "complexity": self._learn_complexity(user_messages, profile),
            "active_hours": self._learn_active_hours(user_messages),
            "topic_counts": self._count_topics(user_messages),
        }

    def update_profile(self, profile: UserProfile, history: list[Message]) -> bool:
        """Analyze history and update the user profile's preferences.

        Returns True if preferences were updated.
        """
        learned = self.analyze(profile, history)
        if learned == self._default_preferences():
            return False

        profile.preferences = {**profile.preferences, **learned}
        return True

    def get_prompt_hints(self, profile: UserProfile) -> list[str]:
        """Generate prompt modifier hints from learned preferences."""
        prefs = profile.preferences
        hints = []

        style = prefs.get("learning_style", "")
        if style == "step_by_step":
            hints.append("User prefers step-by-step explanations.")
        elif style == "examples":
            hints.append("User learns best through concrete examples.")
        elif style == "visual":
            hints.append("User prefers visual explanations (diagrams, charts).")

        length = prefs.get("response_length", "")
        if length == "concise":
            hints.append("Keep responses short and to the point.")
        elif length == "detailed":
            hints.append("User prefers detailed, thorough explanations.")

        topics = prefs.get("preferred_topics", [])
        if topics:
            hints.append(f"User is interested in: {', '.join(topics[:3])}")

        return hints

    # ─── Private Analysis Methods ────────────────────────────

    def _learn_topics(self, messages: list[Message]) -> list[str]:
        """Identify preferred topics from message frequency."""
        counts = self._count_topics(messages)
        if not counts:
            return []
        sorted_topics = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return [t for t, c in sorted_topics[:3] if c >= 2]

    def _count_topics(self, messages: list[Message]) -> dict[str, int]:
        """Count topic mentions across messages."""
        counts: dict[str, int] = Counter()
        for msg in messages:
            lower = msg.content.lower()
            for topic, keywords in _TOPIC_KEYWORDS.items():
                if any(kw in lower for kw in keywords):
                    counts[topic] += 1
        return dict(counts)

    def _learn_style(self, messages: list[Message]) -> str:
        """Detect preferred learning style from message patterns."""
        style_counts: dict[str, int] = Counter()
        for msg in messages:
            lower = msg.content.lower()
            for style, signals in _STYLE_SIGNALS.items():
                if any(s in lower for s in signals):
                    style_counts[style] += 1

        if not style_counts:
            return "balanced"
        return style_counts.most_common(1)[0][0]

    def _learn_length_preference(self, messages: list[Message]) -> str:
        """Infer response length preference from user message lengths."""
        if not messages:
            return "balanced"

        avg_len = sum(len(m.content) for m in messages) / len(messages)
        # Short messages suggest preference for concise responses
        if avg_len < 30:
            return "concise"
        elif avg_len > 150:
            return "detailed"
        return "balanced"

    def _learn_complexity(self, messages: list[Message], profile: UserProfile) -> str:
        """Determine complexity preference from vocabulary and profile."""
        technical_count = 0
        total = len(messages)
        if total == 0:
            return "basic"

        technical_words = {"algorithm", "architecture", "neural", "parameter", "model",
                          "gradient", "epoch", "embedding", "vector", "token", "api"}
        for msg in messages:
            words = set(msg.content.lower().split())
            if words & technical_words:
                technical_count += 1

        ratio = technical_count / total
        if ratio > 0.3 or profile.skill_level >= 7:
            return "technical"
        elif ratio > 0.1 or profile.skill_level >= 4:
            return "intermediate"
        return "basic"

    def _learn_active_hours(self, messages: list[Message]) -> str:
        """Detect when the user is most active."""
        hours: list[int] = []
        for msg in messages:
            try:
                dt = datetime.fromisoformat(msg.timestamp.replace("Z", "+00:00"))
                hours.append(dt.hour)
            except (ValueError, AttributeError):
                continue

        if not hours:
            return "unknown"

        avg_hour = sum(hours) / len(hours)
        if avg_hour < 12:
            return "morning"
        elif avg_hour < 18:
            return "afternoon"
        return "evening"

    def _default_preferences(self) -> dict:
        """Return default preferences for new users."""
        return {
            "preferred_topics": [],
            "learning_style": "balanced",
            "response_length": "balanced",
            "complexity": "basic",
            "active_hours": "unknown",
            "topic_counts": {},
        }
