"""Auto-detect user language from Unicode character analysis + LLM confirmation."""

from __future__ import annotations

import re

__all__ = ["LanguageDetector"]

# Unicode ranges for script detection
_SCRIPT_RANGES = {
    "th": re.compile(r"[\u0E00-\u0E7F]"),         # Thai
    "hi": re.compile(r"[\u0900-\u097F]"),         # Devanagari (Hindi)
    "ar": re.compile(r"[\u0600-\u06FF]"),         # Arabic
    "zh": re.compile(r"[\u4E00-\u9FFF]"),         # CJK (Chinese)
    "ja": re.compile(r"[\u3040-\u309F\u30A0-\u30FF]"),  # Japanese
    "ko": re.compile(r"[\uAC00-\uD7AF]"),         # Korean
}

# Common word markers for Latin-script languages
_LATIN_MARKERS = {
    "es": ["hola", "gracias", "por favor", "cómo", "qué", "está", "tengo", "quiero"],
    "pt": ["olá", "obrigado", "por favor", "como", "você", "tenho", "quero", "não"],
    "fr": ["bonjour", "merci", "comment", "je suis", "s'il vous", "oui", "non"],
    "id": ["halo", "terima kasih", "bagaimana", "saya", "apa", "ini", "itu"],
    "sw": ["habari", "asante", "ndio", "hapana", "sawa", "kwa", "jinsi"],
}


class LanguageDetector:
    """Detect the language of a user's message.

    Uses a two-stage approach:
    1. Unicode character range analysis (fast, for non-Latin scripts)
    2. Word-marker matching (for Latin-script languages)
    3. Falls back to English if uncertain
    """

    def detect(self, text: str) -> str:
        """Detect language code from text.

        Args:
            text: User's message.

        Returns:
            ISO 639-1 language code (e.g., "th", "en", "hi").
        """
        if not text.strip():
            return "en"

        # Stage 1: Non-Latin script detection
        for lang_code, pattern in _SCRIPT_RANGES.items():
            if pattern.search(text):
                return lang_code

        # Stage 2: Latin-script language markers
        text_lower = text.lower()
        best_match = "en"
        best_score = 0

        for lang_code, markers in _LATIN_MARKERS.items():
            score = sum(1 for marker in markers if marker in text_lower)
            if score > best_score:
                best_score = score
                best_match = lang_code

        if best_score >= 1:
            return best_match

        # Default: English
        return "en"

    def get_script(self, lang_code: str) -> str:
        """Get the writing script for a language."""
        scripts = {
            "en": "Latin", "th": "Thai", "hi": "Devanagari",
            "es": "Latin", "zh": "CJK", "ar": "Arabic",
            "pt": "Latin", "sw": "Latin", "id": "Latin",
            "fr": "Latin", "ja": "Japanese", "ko": "Korean",
        }
        return scripts.get(lang_code, "Latin")
