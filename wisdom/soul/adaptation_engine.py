"""Core personalization logic — adapts WISDOM to each user."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wisdom.brain.memory_manager import Message
    from wisdom.brain.user_profile import UserProfile

__all__ = ["AdaptationEngine"]


class AdaptationEngine:
    """Central adaptation logic for personalizing WISDOM.

    Analyzes user behavior signals to dynamically adjust:
    - Content difficulty level
    - Teaching pace
    - Topic recommendations
    - Response style
    """

    def adapt_difficulty(self, profile: UserProfile, history: list[Message]) -> float:
        """Calculate adjusted difficulty level based on user signals.

        Signals that increase difficulty:
        - Correct quiz answers
        - Technical follow-up questions
        - Using terminology correctly
        - Completing modules quickly

        Signals that decrease difficulty:
        - "I don't understand" messages
        - Long pauses
        - Requesting simpler explanations
        - Abandoning modules

        Returns:
            Adjusted skill level (0.0-10.0)
        """
        base_level = profile.skill_level

        if not history:
            return base_level

        recent_user = [m for m in history[-10:] if m.role == "user"]

        increase_signals = 0
        decrease_signals = 0

        for msg in recent_user:
            content = msg.content.lower()

            # Increase signals
            if any(kw in content for kw in ["how does", "why does", "explain more", "tell me about"]):
                increase_signals += 1
            if any(kw in content for kw in ["def ", "class ", "import ", "function", "{", "}"]):
                increase_signals += 2

            # Decrease signals
            if any(kw in content for kw in ["don't understand", "confused", "simpler", "easier"]):
                decrease_signals += 1
            if any(kw in content for kw in ["ไม่เข้าใจ", "ง่ายกว่านี้", "no entiendo", "plus simple"]):
                decrease_signals += 1
            if len(msg.content.strip()) < 5:
                decrease_signals += 0.5

        adjustment = (increase_signals - decrease_signals) * 0.3
        new_level = max(0.0, min(10.0, base_level + adjustment))

        return round(new_level, 1)

    def get_recommendations(self, profile: UserProfile) -> list[str]:
        """Get personalized topic recommendations based on profile."""
        level = profile.skill_level
        interests = profile.interests

        recs = []

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
        if "farming" in interests:
            recs.insert(0, "AI for crop management and weather prediction")
        if "teaching" in interests:
            recs.insert(0, "AI for lesson planning and student feedback")
        if "business" in interests:
            recs.insert(0, "AI for business automation")

        return recs[:5]
