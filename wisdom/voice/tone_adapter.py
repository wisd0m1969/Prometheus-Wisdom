"""Auto-adjust response complexity and formality based on user signals.

Detects emotional state and skill level from message patterns,
then provides tone hints for prompt generation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wisdom.brain.memory_manager import Message
    from wisdom.brain.user_profile import UserProfile

__all__ = ["ToneAdapter", "ToneAnalysis"]

# Signal patterns (multilingual)
_CONFUSION_SIGNALS = [
    "?", "don't understand", "what", "huh", "confused",
    "ไม่เข้าใจ", "อะไร", "no entiendo", "不明白", "لا أفهم",
    "je ne comprends pas", "não entendo", "saya tidak mengerti",
]
_EXCITEMENT_SIGNALS = [
    "wow", "cool", "amazing", "great", "awesome", "!",
    "เจ๋ง", "ดีมาก", "สุดยอด", "increíble", "太好了", "رائع", "génial",
]
_FRUSTRATION_SIGNALS = [
    "stupid", "doesn't work", "hate", "ugh", "broken",
    "ไม่ได้", "โง่", "no funciona", "不行", "لا يعمل",
]
_BOREDOM_SIGNALS = [
    "ok", "sure", "fine", "whatever", "k",
]
_ADVANCED_SIGNALS = [
    "def ", "class ", "import ", "function", "algorithm", "API",
    "lambda", "async", "database", "transformer", "embedding",
    "{", "}", "=>", "->",
]


class ToneAnalysis:
    """Result of tone analysis."""

    def __init__(
        self,
        estimated_level: float,
        emotional_state: str,
        formality: str,
        complexity_level: str,
    ):
        self.estimated_level = estimated_level
        self.emotional_state = emotional_state
        self.formality = formality
        self.complexity_level = complexity_level

    def to_dict(self) -> dict:
        return {
            "estimated_level": self.estimated_level,
            "emotional_state": self.emotional_state,
            "formality": self.formality,
            "complexity_level": self.complexity_level,
        }


class ToneAdapter:
    """Dynamically adapts WISDOM's communication style.

    Detects user emotional state and skill signals from messages,
    then provides tone hints for prompt generation.
    """

    def analyze_user_message(
        self, message: str, history: list[Message] | None = None,
    ) -> ToneAnalysis:
        """Analyze a single message plus recent history for tone signals."""
        messages = [m.content for m in (history or []) if m.role == "user"]
        messages.append(message)
        recent_text = " ".join(m.lower() for m in messages[-5:])

        emotional_state = self._detect_emotion(recent_text, messages[-3:] if len(messages) >= 3 else messages)
        estimated_level = self._estimate_level(recent_text)
        formality = self._detect_formality(message)

        if estimated_level <= 3:
            complexity = "basic"
        elif estimated_level <= 6:
            complexity = "intermediate"
        else:
            complexity = "advanced"

        return ToneAnalysis(
            estimated_level=estimated_level,
            emotional_state=emotional_state,
            formality=formality,
            complexity_level=complexity,
        )

    def get_adaptation(
        self,
        profile: UserProfile,
        history: list[Message],
    ) -> dict:
        """Analyze conversation and return tone adaptation hints."""
        complexity = self._assess_complexity(profile, history)
        tone = self._detect_tone(history)

        return {
            "complexity_level": complexity,
            "tone": tone,
            "instructions": self._build_instructions(complexity, tone),
        }

    def get_adapted_prompt(
        self,
        base_prompt: str,
        profile: UserProfile,
        analysis: ToneAnalysis,
    ) -> str:
        """Modify a base prompt based on tone analysis."""
        additions = []

        # Complexity adaptation
        if analysis.complexity_level == "basic":
            additions.append(
                "Use simple everyday words. Explain with real-life analogies. "
                "Keep sentences short (under 15 words)."
            )
        elif analysis.complexity_level == "advanced":
            additions.append(
                "Use full technical vocabulary. Include code examples when relevant."
            )

        # Emotional adaptation
        emotion_responses = {
            "confused": "The user seems confused. Simplify. Use a different analogy. Ask what part is unclear.",
            "frustrated": "The user seems frustrated. Be extra patient. Acknowledge the difficulty. Offer a different approach.",
            "excited": "The user is excited! Match their enthusiasm. Suggest the next challenge.",
            "bored": "The user seems disengaged. Try something interactive. Ask about their interests.",
        }
        if analysis.emotional_state in emotion_responses:
            additions.append(emotion_responses[analysis.emotional_state])

        # Formality
        if analysis.formality == "casual":
            additions.append("Use a casual, friendly tone. Short sentences.")
        elif analysis.formality == "formal":
            additions.append("Use a polite, respectful tone.")

        if additions:
            return f"{base_prompt}\n\nAdaptation: {' '.join(additions)}"
        return base_prompt

    # ─── Private Helpers ──────────────────────────────────────

    def _assess_complexity(self, profile: UserProfile, history: list[Message]) -> str:
        level = profile.skill_level
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
        return "advanced"

    def _detect_tone(self, history: list[Message]) -> str:
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
        if recent and all(len(m) < 10 for m in recent):
            return "bored"
        return "engaged"

    def _detect_emotion(self, recent_text: str, recent_messages: list[str]) -> str:
        if any(s in recent_text for s in _FRUSTRATION_SIGNALS):
            return "frustrated"
        if any(s in recent_text for s in _CONFUSION_SIGNALS):
            return "confused"
        if any(s in recent_text for s in _EXCITEMENT_SIGNALS):
            return "excited"
        if recent_messages and all(len(m) < 10 for m in recent_messages):
            return "bored"
        return "engaged"

    def _estimate_level(self, text: str) -> float:
        level = 3.0
        if any(s in text for s in _ADVANCED_SIGNALS):
            level += 3.0
        if any(s in text for s in _CONFUSION_SIGNALS):
            level -= 1.5
        word_count = len(text.split())
        if word_count > 50:
            level += 1.0
        return max(0.0, min(10.0, level))

    def _detect_formality(self, message: str) -> str:
        lower = message.lower()
        casual_markers = {"lol", "haha", "gonna", "wanna", "sup", "yo", "btw", "555"}
        formal_markers = {"please", "could you", "would you", "kindly", "sir", "ครับ", "ค่ะ"}
        words = set(lower.split())
        if words & casual_markers:
            return "casual"
        if words & formal_markers:
            return "formal"
        return "neutral"

    def _build_instructions(self, complexity: str, tone: str) -> str:
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
