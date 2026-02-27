"""Core personalization logic — adapts WISDOM to each user.

Combines SkillAssessor + GoalTracker + UserProfile + ConversationHistory
to determine the best mode, difficulty, and topic for each interaction.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wisdom.brain.memory_manager import Message
    from wisdom.brain.user_profile import UserProfile

__all__ = ["AdaptationEngine", "AdaptationResult"]


class AdaptationResult:
    """Result of adaptation analysis."""

    def __init__(
        self,
        recommended_mode: str,
        difficulty_level: float,
        prompt_modifiers: list[str],
        suggested_topic: str = "",
    ):
        self.recommended_mode = recommended_mode
        self.difficulty_level = difficulty_level
        self.prompt_modifiers = prompt_modifiers
        self.suggested_topic = suggested_topic

    def to_dict(self) -> dict:
        return {
            "recommended_mode": self.recommended_mode,
            "difficulty_level": self.difficulty_level,
            "prompt_modifiers": self.prompt_modifiers,
            "suggested_topic": self.suggested_topic,
        }


class AdaptationEngine:
    """Central adaptation logic for personalizing WISDOM.

    Analyzes user profile, message, and history to determine:
    - Recommended operating mode
    - Difficulty level
    - Prompt modifiers
    - Suggested next topic
    """

    def adapt(
        self,
        profile: UserProfile,
        message: str,
        history: list[Message],
    ) -> AdaptationResult:
        """Run full adaptation analysis.

        Returns:
            AdaptationResult with mode, difficulty, modifiers, and suggestion.
        """
        mode = self._detect_mode(message, profile, history)
        difficulty = self.adapt_difficulty(profile, history)
        modifiers = self._get_modifiers(profile, message, history)
        topic = self._suggest_topic(profile)

        return AdaptationResult(
            recommended_mode=mode,
            difficulty_level=difficulty,
            prompt_modifiers=modifiers,
            suggested_topic=topic,
        )

    def adapt_difficulty(self, profile: UserProfile, history: list[Message]) -> float:
        """Calculate adjusted difficulty level based on user signals."""
        base_level = profile.skill_level

        if not history:
            return base_level

        recent_user = [m for m in history[-10:] if m.role == "user"]
        increase = 0
        decrease = 0

        for msg in recent_user:
            content = msg.content.lower()

            # Increase signals
            if any(kw in content for kw in ["how does", "why does", "explain more", "tell me about"]):
                increase += 1
            if any(kw in content for kw in ["def ", "class ", "import ", "function", "{", "}"]):
                increase += 2

            # Decrease signals
            if any(kw in content for kw in ["don't understand", "confused", "simpler", "easier"]):
                decrease += 1
            if any(kw in content for kw in ["ไม่เข้าใจ", "ง่ายกว่านี้", "no entiendo", "plus simple"]):
                decrease += 1
            if len(msg.content.strip()) < 5:
                decrease += 0.5

        adjustment = (increase - decrease) * 0.3
        return round(max(0.0, min(10.0, base_level + adjustment)), 1)

    def get_recommendations(self, profile: UserProfile) -> list[str]:
        """Get personalized topic recommendations."""
        level = profile.skill_level
        interests = profile.interests

        if level < 2:
            recs = ["What is AI?", "Your first AI conversation", "AI is not magic"]
        elif level < 4:
            recs = ["How to ask good questions", "AI for daily tasks", "Common AI mistakes"]
        elif level < 6:
            recs = ["How language models work", "AI bias and ethics", "Intro to Python"]
        elif level < 8:
            recs = ["Building web apps with AI", "API integration", "Prompt engineering"]
        else:
            recs = ["Build your own AI tool", "Contributing to open source", "Advanced LLM concepts"]

        # Personalize based on interests
        interest_topics = {
            "farming": "AI for crop management and weather prediction",
            "teaching": "AI for lesson planning and student feedback",
            "business": "AI for business automation and customer service",
            "coding": "Advanced coding techniques with AI",
            "health": "AI in healthcare and wellness",
        }
        for interest in interests:
            for key, topic in interest_topics.items():
                if key in interest.lower():
                    recs.insert(0, topic)

        return recs[:5]

    # ─── Private Helpers ──────────────────────────────────────

    def _detect_mode(self, message: str, profile: UserProfile, history: list[Message]) -> str:
        """Detect the best operating mode from context."""
        lower = message.lower()

        # New user → welcome
        if not profile.name and not history:
            return "free_chat"

        # Code detection
        if re.search(r"(def |class |import |function |var |let |const |<div)", message):
            return "code_helper"

        # Explicit mode requests
        if any(kw in lower for kw in ["teach me", "explain", "lesson", "learn", "สอน", "เรียน"]):
            return "teacher"
        if any(kw in lower for kw in ["quiz", "test me", "question", "ทดสอบ"]):
            return "quiz_master"
        if any(kw in lower for kw in ["search", "find", "research", "what is", "ค้นหา"]):
            return "researcher"
        if any(kw in lower for kw in ["code", "program", "python", "โค้ด", "เขียนโปรแกรม"]):
            return "code_helper"

        # Low skill + active learning → teacher
        if profile.skill_level < 3 and profile.goals:
            return "teacher"

        return "free_chat"

    def _get_modifiers(self, profile: UserProfile, message: str, history: list[Message]) -> list[str]:
        """Get prompt modifiers based on context."""
        modifiers = []

        if profile.skill_level <= 3:
            modifiers.append("Use simple words and real-life analogies.")
        if profile.interests:
            modifiers.append(f"Reference the user's interests: {', '.join(profile.interests[:3])}")
        if profile.name:
            modifiers.append(f"Address the user as {profile.name}.")

        # Detect if user is struggling
        if history:
            recent = [m.content.lower() for m in history[-3:] if m.role == "user"]
            if any("don't understand" in r or "ไม่เข้าใจ" in r for r in recent):
                modifiers.append("The user is struggling. Simplify and use a different approach.")

        return modifiers

    def _suggest_topic(self, profile: UserProfile) -> str:
        """Suggest the next topic based on profile."""
        recs = self.get_recommendations(profile)
        return recs[0] if recs else ""
