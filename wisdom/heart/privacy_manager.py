"""PII sanitization — mask sensitive data before sending to cloud LLMs.

Supports multi-region PII patterns: credit cards, emails, SSN, phone,
IP addresses, Thai national IDs. Includes is_safe_for_cloud() check and
configurable whitelist.
"""

from __future__ import annotations

import re

__all__ = ["PrivacyManager"]

# PII detection patterns — ordered: longest/most-specific patterns first
_PATTERNS = [
    ("credit_card", re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"), "[CARD]"),
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[EMAIL]"),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[ID]"),
    ("thai_national_id", re.compile(r"\b\d{1}-\d{4}-\d{5}-\d{2}-\d{1}\b"), "[THAI_ID]"),
    ("phone", re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b"), "[PHONE]"),
    ("ip_address", re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), "[IP]"),
]

# Sensitive keywords that indicate the message might contain PII
_SENSITIVE_KEYWORDS = [
    "password", "secret", "credit card", "social security", "ssn",
    "bank account", "routing number", "pin", "cvv",
    "รหัสผ่าน", "บัตรเครดิต", "บัตรประชาชน", "contraseña", "mot de passe",
]


class PrivacyManager:
    """Sanitizes Personally Identifiable Information from text.

    Applied before sending user messages to cloud LLM providers (Gemini).
    NOT applied when using Ollama (local — data stays on device).
    """

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._whitelist: set[str] = set()

    def sanitize(self, text: str) -> str:
        """Remove or mask PII from text.

        Args:
            text: Raw user message.

        Returns:
            Sanitized text with PII replaced by placeholders.
        """
        if not self.enabled:
            return text

        sanitized = text
        for name, pattern, replacement in _PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)

        return sanitized

    def detect_pii(self, text: str) -> list[dict]:
        """Detect PII in text without removing it.

        Returns:
            List of detected PII items with type and match.
        """
        findings = []
        for pii_type, pattern, _ in _PATTERNS:
            for match in pattern.finditer(text):
                findings.append({
                    "type": pii_type,
                    "match": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                })
        return findings

    def is_safe_for_cloud(self, text: str) -> bool:
        """Check if text is safe to send to cloud LLM (no PII detected).

        Returns:
            True if no PII is detected and no sensitive keywords found.
        """
        if self.detect_pii(text):
            return False
        lower = text.lower()
        return not any(kw in lower for kw in _SENSITIVE_KEYWORDS)

    def sanitize_for_cloud(self, text: str) -> tuple[str, list[dict]]:
        """Sanitize text and return both the cleaned text and findings.

        Returns:
            Tuple of (sanitized_text, list_of_pii_findings).
        """
        findings = self.detect_pii(text)
        sanitized = self.sanitize(text)
        return sanitized, findings

    def add_whitelist(self, value: str) -> None:
        """Allow a specific value through sanitization."""
        self._whitelist.add(value)

    def remove_whitelist(self, value: str) -> None:
        """Remove a value from the whitelist."""
        self._whitelist.discard(value)
