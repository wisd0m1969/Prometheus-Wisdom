"""Auto-detect user language from Unicode character analysis + trigram frequency.

Two-stage detection:
1. Non-Latin scripts: Unicode range matching (fast, confident)
2. Latin scripts: trigram frequency analysis (en vs es vs pt vs fr vs sw vs id)
"""

from __future__ import annotations

import re
from collections import Counter

__all__ = ["LanguageDetector", "LanguageResult"]

# Unicode ranges for non-Latin script detection
_SCRIPT_RANGES = {
    "th": (re.compile(r"[\u0E00-\u0E7F]"), "Thai"),
    "hi": (re.compile(r"[\u0900-\u097F]"), "Devanagari"),
    "ar": (re.compile(r"[\u0600-\u06FF]"), "Arabic"),
    "zh": (re.compile(r"[\u4E00-\u9FFF]"), "CJK"),
    "ja": (re.compile(r"[\u3040-\u309F\u30A0-\u30FF]"), "Japanese"),
    "ko": (re.compile(r"[\uAC00-\uD7A3]"), "Korean"),
}

# Trigram frequency profiles for Latin-script languages
_TRIGRAM_PROFILES: dict[str, set[str]] = {
    "en": {"the", "ing", "and", "tion", "ent", "ion", "her", "for", "tha", "nth",
           "int", "ere", "tio", "hat", "tha", "ate", "his", "est", "ith", "all"},
    "es": {"que", "ción", "los", "las", "ent", "ado", "por", "con", "est", "ara",
           "ien", "nte", "ión", "mos", "sta", "ero", "aba", "com", "hola", "cómo"},
    "pt": {"que", "ção", "ent", "ado", "com", "par", "est", "ção", "nte", "por",
           "mos", "não", "uma", "dos", "ela", "ava", "olá", "obrigado", "você"},
    "fr": {"les", "ent", "que", "ion", "des", "est", "ait", "par", "ous", "com",
           "eur", "ment", "tre", "bonjour", "merci", "oui", "une", "pas", "dans"},
    "id": {"ang", "kan", "yan", "men", "ber", "ada", "ini", "itu", "dan", "per",
           "saya", "apa", "halo", "terima", "kasih", "bagaimana", "tidak"},
    "sw": {"ana", "kwa", "ili", "amba", "isha", "ndi", "ake", "ata", "habari",
           "asante", "ndio", "hapana", "sawa", "jinsi", "kama", "yako"},
}

# Word-level markers (more reliable than trigrams for short texts)
_WORD_MARKERS = {
    "es": {"hola", "gracias", "por", "favor", "cómo", "qué", "está", "tengo",
           "quiero", "bueno", "también", "pero", "muy", "bien", "usted"},
    "pt": {"olá", "obrigado", "por", "favor", "como", "você", "tenho", "quero",
           "não", "sim", "bom", "também", "muito", "bem"},
    "fr": {"bonjour", "merci", "comment", "suis", "vous", "oui", "non", "très",
           "bien", "avec", "pour", "dans", "une", "pas", "les"},
    "id": {"halo", "terima", "kasih", "bagaimana", "saya", "apa", "ini", "itu",
           "dan", "tidak", "ya", "bisa", "dengan", "untuk", "ada"},
    "sw": {"habari", "asante", "ndio", "hapana", "sawa", "kwa", "jinsi", "nini",
           "sana", "tafadhali", "karibu", "pole", "jambo"},
}


class LanguageResult:
    """Result of language detection."""

    def __init__(self, code: str, name: str, confidence: float, script: str):
        self.code = code
        self.name = name
        self.confidence = confidence
        self.script = script

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "confidence": self.confidence,
            "script": self.script,
        }


# Language name lookup
_LANG_NAMES = {
    "en": "English", "th": "Thai", "hi": "Hindi", "es": "Spanish",
    "zh": "Chinese", "ar": "Arabic", "pt": "Portuguese", "sw": "Swahili",
    "id": "Indonesian", "fr": "French", "ja": "Japanese", "ko": "Korean",
}


class LanguageDetector:
    """Detect the language of a user's message.

    Two-stage approach:
    1. Unicode character range analysis (non-Latin scripts)
    2. Trigram frequency + word marker matching (Latin scripts)
    """

    def detect(self, text: str) -> str:
        """Detect language code from text.

        Args:
            text: User's message.

        Returns:
            ISO 639-1 language code (e.g., "th", "en", "hi").
        """
        result = self.detect_detailed(text)
        return result.code

    def detect_detailed(self, text: str) -> LanguageResult:
        """Detect language with full details (code, name, confidence, script)."""
        if not text.strip():
            return LanguageResult("en", "English", 0.5, "Latin")

        # Stage 1: Non-Latin script detection via Unicode ranges
        for lang_code, (pattern, script_name) in _SCRIPT_RANGES.items():
            matches = pattern.findall(text)
            if matches:
                ratio = len(matches) / max(len(text.replace(" ", "")), 1)
                confidence = min(0.99, 0.7 + ratio * 0.3)
                return LanguageResult(
                    lang_code, _LANG_NAMES.get(lang_code, lang_code),
                    round(confidence, 2), script_name,
                )

        # Stage 2: Latin-script — word markers (better for short text)
        text_lower = text.lower()
        words = set(re.findall(r"[a-záàâãéèêíîóôõúùûçñüö]+", text_lower))

        best_lang = "en"
        best_score = 0.0

        for lang_code, markers in _WORD_MARKERS.items():
            overlap = words & markers
            if overlap:
                score = len(overlap) / max(len(words), 1)
                if score > best_score:
                    best_score = score
                    best_lang = lang_code

        # Stage 3: Trigram analysis (fallback for ambiguous cases)
        if best_score < 0.1 and len(text) > 10:
            text_trigrams = self._get_trigrams(text_lower)
            for lang_code, profile in _TRIGRAM_PROFILES.items():
                overlap = text_trigrams & profile
                score = len(overlap) / max(len(profile), 1)
                if score > best_score:
                    best_score = score
                    best_lang = lang_code

        confidence = min(0.95, 0.5 + best_score)
        if best_lang == "en" and best_score < 0.05:
            confidence = 0.6  # Default English is lower confidence

        return LanguageResult(
            best_lang, _LANG_NAMES.get(best_lang, best_lang),
            round(confidence, 2), "Latin",
        )

    def get_script(self, lang_code: str) -> str:
        """Get the writing script for a language."""
        for code, (_, script_name) in _SCRIPT_RANGES.items():
            if code == lang_code:
                return script_name
        return "Latin"

    @staticmethod
    def _get_trigrams(text: str) -> set[str]:
        """Extract character trigrams from text."""
        clean = re.sub(r"[^a-záàâãéèêíîóôõúùûçñüö]", "", text.lower())
        return {clean[i:i+3] for i in range(len(clean) - 2)}
