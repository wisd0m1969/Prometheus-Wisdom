"""Conversation flow controller — wires all WISDOM modules together.

Full 13-step pipeline:
    1.  Receive message
    2.  Language detection
    3.  Profile load/create
    4.  Context retrieval (memory + ChromaDB)
    5.  Adaptation analysis (mode, difficulty, modifiers)
    6.  Tone analysis (emotion, formality, complexity)
    7.  Privacy sanitization (cloud only)
    8.  Prompt building with system prompt + history
    9.  LLM generation (streaming or sync)
    10. Response post-processing
    11. Memory update (short-term + long-term)
    12. Knowledge graph update
    13. Badge/achievement check
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Generator

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
        self._current_mode: str = "free_chat"

        # Lazy-loaded modules
        self._chat_engine = None
        self._adaptation_engine = None
        self._goal_tracker = None

    @property
    def chat_engine(self):
        if self._chat_engine is None:
            from wisdom.voice.chat_engine import ChatEngine
            self._chat_engine = ChatEngine(self.llm_provider)
        return self._chat_engine

    @property
    def adaptation_engine(self):
        if self._adaptation_engine is None:
            from wisdom.soul.adaptation_engine import AdaptationEngine
            self._adaptation_engine = AdaptationEngine()
        return self._adaptation_engine

    @property
    def goal_tracker(self):
        if self._goal_tracker is None:
            from wisdom.soul.goal_tracker import GoalTracker
            from wisdom.core.config import Config
            config = Config()
            self._goal_tracker = GoalTracker(config.db_path)
        return self._goal_tracker

    def process_message(self, user_id: str, message: str) -> str:
        """Process a user message through the full WISDOM pipeline.

        Args:
            user_id: Unique user identifier.
            message: User's message in any supported language.

        Returns:
            WISDOM's response in the user's language.
        """
        try:
            return self._run_pipeline(user_id, message)
        except Exception as e:
            logger.exception("Pipeline error for user %s: %s", user_id, e)
            return self._graceful_error(e)

    def process_message_stream(self, user_id: str, message: str) -> Generator[str, None, None]:
        """Process a user message and yield streaming response chunks.

        Args:
            user_id: Unique user identifier.
            message: User's message.

        Yields:
            Response text chunks.
        """
        try:
            yield from self._run_pipeline_stream(user_id, message)
        except Exception as e:
            logger.exception("Stream pipeline error for user %s: %s", user_id, e)
            yield self._graceful_error(e)

    def start_assessment(self, user_id: str) -> dict:
        """Start a skill assessment for a user."""
        from wisdom.soul.skill_assessor import SkillAssessor

        assessor = SkillAssessor()
        question = assessor.start_assessment()
        return {"question": question, "assessor_state": "started"}

    def set_goal(self, user_id: str, description: str, milestones: list[str] | None = None) -> int:
        """Set a learning goal for a user."""
        return self.goal_tracker.create_goal(user_id, description, milestones)

    def get_user_goals(self, user_id: str) -> list[dict]:
        """Get all goals for a user."""
        return self.goal_tracker.get_goals(user_id)

    def export_user_data(self, user_id: str) -> dict:
        """Export all user data (GDPR compliance)."""
        profile = self.profile_manager.get(user_id)
        if not profile:
            return {"error": "User not found"}

        history = self.memory.get_history(user_id)
        goals = self.goal_tracker.get_goals(user_id)
        badges = self.goal_tracker.get_badges(user_id)

        return {
            "profile": profile.to_dict(),
            "conversation_count": len(history),
            "goals": goals,
            "badges": badges,
        }

    def delete_user_data(self, user_id: str) -> bool:
        """Delete all user data (right to be forgotten)."""
        try:
            self.profile_manager.delete(user_id)
            self.memory.clear_session(user_id)
            logger.info("Deleted all data for user %s", user_id)
            return True
        except Exception as e:
            logger.error("Failed to delete data for user %s: %s", user_id, e)
            return False

    # ─── Private Pipeline Methods ──────────────────────────────

    def _run_pipeline(self, user_id: str, message: str) -> str:
        """Full synchronous pipeline."""
        # Step 1-2: Language detection
        language = self.language_detector.detect(message)
        logger.info("Step 2: Detected language: %s", language)

        # Step 3: Profile load/create
        profile = self.profile_manager.get_or_create(user_id)
        if profile.language != language:
            profile.language = language
            self.profile_manager.update(profile)

        # Step 4: Context retrieval
        history = self.memory.get_history(user_id)

        # Step 5: Adaptation analysis
        adaptation = self.adaptation_engine.adapt(profile, message, history)
        self._current_mode = adaptation.recommended_mode
        self.chat_engine.set_mode(self._current_mode)
        logger.info("Step 5: Mode=%s, Difficulty=%.1f", self._current_mode, adaptation.difficulty_level)

        # Step 6: Tone analysis
        tone_hints = self.tone_adapter.get_adaptation(profile, history)

        # Step 7: Privacy sanitization (cloud only)
        safe_message = message
        if not self.llm_provider.is_local():
            safe_message = self.privacy_manager.sanitize(message)
            logger.info("Step 7: PII sanitized for cloud LLM")

        # Step 8-9: LLM generation
        response = self.chat_engine.generate(
            user_message=safe_message,
            profile=profile,
            history=history,
            tone_hints=tone_hints,
        )

        # Step 11: Memory update
        self.memory.add_message(user_id, role="user", content=message)
        self.memory.add_message(user_id, role="wisdom", content=response)

        # Step 13: Badge check (first_contact)
        if len(history) == 0:
            self.goal_tracker.award_badge(user_id, "first_contact")

        return response

    def _run_pipeline_stream(self, user_id: str, message: str) -> Generator[str, None, None]:
        """Full streaming pipeline."""
        # Steps 1-7: Same as sync
        language = self.language_detector.detect(message)
        profile = self.profile_manager.get_or_create(user_id)
        if profile.language != language:
            profile.language = language
            self.profile_manager.update(profile)

        history = self.memory.get_history(user_id)
        adaptation = self.adaptation_engine.adapt(profile, message, history)
        self._current_mode = adaptation.recommended_mode
        self.chat_engine.set_mode(self._current_mode)
        tone_hints = self.tone_adapter.get_adaptation(profile, history)

        safe_message = message
        if not self.llm_provider.is_local():
            safe_message = self.privacy_manager.sanitize(message)

        # Step 8-9: Streaming generation
        full_response = ""
        for chunk in self.chat_engine.generate_stream(
            user_message=safe_message,
            profile=profile,
            history=history,
            tone_hints=tone_hints,
        ):
            full_response += chunk
            yield chunk

        # Step 11: Memory update
        self.memory.add_message(user_id, role="user", content=message)
        self.memory.add_message(user_id, role="wisdom", content=full_response)

        # Step 13: Badge check
        if len(history) == 0:
            self.goal_tracker.award_badge(user_id, "first_contact")

    def _graceful_error(self, error: Exception) -> str:
        """Return a user-friendly error message."""
        error_str = str(error).lower()
        if "connection" in error_str or "refused" in error_str:
            return (
                "I'm having trouble connecting to my AI brain right now. "
                "Please check that Ollama is running (`ollama serve`) or "
                "that your GOOGLE_API_KEY is set in the .env file."
            )
        if "model" in error_str:
            return (
                "I can't find the AI model I need. "
                "Try running `ollama pull llama3:latest` to download it."
            )
        return (
            "Something went wrong on my end. "
            "Please try again, and if the problem persists, check the logs."
        )
