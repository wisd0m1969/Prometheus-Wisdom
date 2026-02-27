"""Conversation flow controller — wires all WISDOM modules together.

Pipeline:
    1. Language Detection
    2. Context Retrieval (memory)
    3. Profile Loading
    4. Prompt Adaptation (tone, complexity)
    5. LLM Generation
    6. Privacy Post-Processing
    7. Memory Update
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wisdom.brain.memory_manager import MemoryManager
    from wisdom.brain.user_profile import UserProfileManager
    from wisdom.core.llm_provider import LLMProvider
    from wisdom.heart.privacy_manager import PrivacyManager
    from wisdom.voice.language_detect import LanguageDetector
    from wisdom.voice.tone_adapter import ToneAdapter

__all__ = ["Orchestrator"]

logger = logging.getLogger(__name__)


class Orchestrator:
    """Central conversation flow controller.

    Coordinates Voice, Brain, Soul, and Heart modules to process
    each user message through the full WISDOM pipeline.
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        memory: MemoryManager,
        profile_manager: UserProfileManager,
        language_detector: LanguageDetector,
        tone_adapter: ToneAdapter,
        privacy_manager: PrivacyManager,
    ) -> None:
        self.llm_provider = llm_provider
        self.memory = memory
        self.profile_manager = profile_manager
        self.language_detector = language_detector
        self.tone_adapter = tone_adapter
        self.privacy_manager = privacy_manager

    def process_message(self, user_id: str, message: str) -> str:
        """Process a user message through the full WISDOM pipeline.

        Args:
            user_id: Unique user identifier.
            message: User's message in any supported language.

        Returns:
            WISDOM's response in the user's language.
        """
        # 1. Detect language
        language = self.language_detector.detect(message)
        logger.info("Detected language: %s", language)

        # 2. Load or create user profile
        profile = self.profile_manager.get_or_create(user_id)
        if profile.language != language:
            profile.language = language
            self.profile_manager.update(profile)

        # 3. Get conversation history
        history = self.memory.get_history(user_id)

        # 4. Build adapted prompt
        tone_hints = self.tone_adapter.get_adaptation(profile, history)

        # 5. Sanitize for privacy (only if using cloud LLM)
        safe_message = message
        if not self.llm_provider.is_local():
            safe_message = self.privacy_manager.sanitize(message)

        # 6. Generate response via LLM
        from wisdom.voice.chat_engine import ChatEngine

        engine = ChatEngine(self.llm_provider)
        response = engine.generate(
            user_message=safe_message,
            profile=profile,
            history=history,
            tone_hints=tone_hints,
        )

        # 7. Update memory
        self.memory.add_message(user_id, role="user", content=message)
        self.memory.add_message(user_id, role="wisdom", content=response)

        return response
