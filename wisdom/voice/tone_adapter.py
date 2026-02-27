"""Auto-adjust response complexity and formality based on user signals."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wisdom.brain.memory_manager import Message
    from wisdom.brain.user_profile import UserProfile

__all__ = ["ToneAdapter"]

# Signal patterns that indicate user state
_CONFUSION_SIGNALS = ["?", "don't understand", "ไม่เข้าใจ", "confused", "what", "huh"]
_EXCITEMENT_SIGNALS = ["wow", "cool", "amazing", "great", "!", "เจ๋ง", "ดีมาก"]
_FRUSTRATION_SIGNALS = ["stupid", "doesn't work", "hate", "ugh", "ไม่ได้"]
_ADVANCED_SIGNALS = ["def ", "class ", "import ", "function", "algorithm", "API"]


class ToneAdapter:
    """Dynamically adapts WISDOM's communication style.

    Detects user emotional state and skill signals from messages,
    then provides tone hints for prompt generation.
    """

    def get_adaptation(
        self,
        profile: UserProfile,
        history: list[Message],
    ) -> dict:
        """Analyze conversation and return tone adaptation hints.

        Returns:
            Dict with keys: complexity_level, tone, suggestions
        """
        complexity = self._assess_complexity(profile, history)
        tone = self._detect_tone(history)

        return {
            "complexity_level": complexity,
            "tone": tone,
            "instructions": self._build_instructions(complexity, tone),
        }

    def _assess_complexity(self, profile: UserProfile, history: list[Message]) -> str:
        """Determine target complexity level."""
        level = profile.skill_level

        # Adjust based on recent signals
        if history:
            recent = [m.content.lower() for m in history[-5:] if m.role == "user"]
            recent_text = " ".join(recent)

            if any(s in recent_text for s in _CONFUSION_SIGNALS):
                level = max(0, level - 1)
            if any(s in recent_text for s in _ADVANCED_SIGNALS):
                level = min(10, level + 1)

        if level <= 3:
            return "basic"
        elif level <= 6:
            return "intermediate"
        else:
            return "advanced"

    def _detect_tone(self, history: list[Message]) -> str:
        """Detect user's emotional state from recent messages."""
        if not history:
            return "neutral"

        recent = [m.content.lower() for m in history[-3:] if m.role == "user"]
        recent_text = " ".join(recent)

        if any(s in recent_text for s in _FRUSTRATION_SIGNALS):
            return "frustrated"
        if any(s in recent_text for s in _CONFUSION_SIGNALS):
            return "confused"
        if any(s in recent_text for s in _EXCITEMENT_SIGNALS):
            return "excited"

        # Short responses may indicate boredom
        if recent and all(len(m) < 10 for m in recent):
            return "bored"

        return "engaged"

    def _build_instructions(self, complexity: str, tone: str) -> str:
        """Build natural-language instructions for the LLM."""
        parts = []

        complexity_map = {
            "basic": "Use simple everyday words. Explain with real-life analogies. Keep sentences short.",
            "intermediate": "Use some technical terms but always explain them. Mix analogies with facts.",
            "advanced": "Use full technical vocabulary. Include code examples when relevant.",
        }
        parts.append(complexity_map.get(complexity, complexity_map["basic"]))

        tone_map = {
            "confused": "The user seems confused. Simplify your explanation. Use a different analogy.",
            "frustrated": "The user seems frustrated. Be extra patient. Acknowledge the difficulty.",
            "excited": "The user is excited! Match their enthusiasm. Suggest the next challenge.",
            "bored": "The user seems disengaged. Try a different approach. Ask about their interests.",
            "engaged": "The user is engaged. Continue at this level.",
            "neutral": "Be warm and welcoming.",
        }
        parts.append(tone_map.get(tone, tone_map["neutral"]))

        return " ".join(parts)
