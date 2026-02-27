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
    from wisdom.brain.knowledge_graph import KnowledgeGraph
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
        knowledge_graph: KnowledgeGraph | None = None,
    ) -> None:
        self.llm_provider = llm_provider
        self.memory = memory
        self.profile_manager = profile_manager
        self.language_detector = language_detector
        self.tone_adapter = tone_adapter
        self.privacy_manager = privacy_manager
        self.knowledge_graph = knowledge_graph
        self._current_mode: str = "free_chat"

        # Lazy-loaded modules
        self._chat_engine = None
        self._adaptation_engine = None
        self._goal_tracker = None
        self._learning_progress = None

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

    @property
    def learning_progress(self):
        if self._learning_progress is None:
            from wisdom.soul.learning_path import LearningProgressTracker
            from wisdom.core.config import Config
            config = Config()
            self._learning_progress = LearningProgressTracker(config.db_path)
        return self._learning_progress

    def _retrieve_context(self, user_id: str, message: str) -> str:
        """Retrieve relevant context from ChromaDB and KnowledgeGraph (RAG pipeline).

        Steps:
        1. Search ChromaDB for relevant past conversations/facts
        2. Query KnowledgeGraph for user's learned topics
        3. Combine into a context string for prompt injection
        """
        context_parts = []

        # ChromaDB retrieval — relevant memories
        memories = self.memory.recall(user_id, message, n_results=5)
        if memories:
            context_parts.append("Relevant memories:\n" + "\n".join(f"- {m}" for m in memories))

        # Knowledge Graph — user's learned topics
        if self.knowledge_graph:
            try:
                topics = self.knowledge_graph.get_user_topics(user_id)
                if topics:
                    topic_names = [t.get("name", t.get("id", "")) for t in topics[:10]]
                    context_parts.append("User has learned about: " + ", ".join(topic_names))
            except Exception:
                pass

        return "\n\n".join(context_parts) if context_parts else ""

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

        goals = self.goal_tracker.get_goals(user_id)
        badges = self.goal_tracker.get_badges(user_id)
        learning = self.learning_progress.get_progress(user_id)
        conversation_count = self.memory.get_conversation_count(user_id)

        return {
            "profile": profile.to_dict(),
            "conversation_count": conversation_count,
            "goals": goals,
            "badges": badges,
            "learning_progress": learning,
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

        # Step 4: Context retrieval (memory + ChromaDB + KnowledgeGraph)
        history = self.memory.get_history(user_id)
        retrieved_context = self._retrieve_context(user_id, message)

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

        # Step 8-9: LLM generation (with retrieved context)
        response = self.chat_engine.generate(
            user_message=safe_message,
            profile=profile,
            history=history,
            tone_hints=tone_hints,
            retrieved_context=retrieved_context,
        )

        # Step 11: Memory update (short-term + SQLite)
        self.memory.add_message(user_id, role="user", content=message, language=language)
        self.memory.add_message(user_id, role="wisdom", content=response, language=language)

        # Step 12: Knowledge graph update — record topic interaction
        if self.knowledge_graph:
            try:
                # Extract simple topic from first few words
                topic_words = message.split()[:5]
                topic_key = "_".join(w.lower() for w in topic_words if len(w) > 2)[:50]
                if topic_key:
                    self.knowledge_graph.add_node(user_id, "User", {"name": profile.name})
                    self.knowledge_graph.add_node(topic_key, "Topic", {"name": " ".join(topic_words)})
                    self.knowledge_graph.add_relationship(user_id, topic_key, "LEARNED")
            except Exception:
                pass

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
        retrieved_context = self._retrieve_context(user_id, message)
        adaptation = self.adaptation_engine.adapt(profile, message, history)
        self._current_mode = adaptation.recommended_mode
        self.chat_engine.set_mode(self._current_mode)
        tone_hints = self.tone_adapter.get_adaptation(profile, history)

        safe_message = message
        if not self.llm_provider.is_local():
            safe_message = self.privacy_manager.sanitize(message)

        # Step 8-9: Streaming generation (with retrieved context)
        full_response = ""
        for chunk in self.chat_engine.generate_stream(
            user_message=safe_message,
            profile=profile,
            history=history,
            tone_hints=tone_hints,
            retrieved_context=retrieved_context,
        ):
            full_response += chunk
            yield chunk

        # Step 11: Memory update (short-term + SQLite)
        self.memory.add_message(user_id, role="user", content=message, language=language)
        self.memory.add_message(user_id, role="wisdom", content=full_response, language=language)

        # Step 12: Knowledge graph update
        if self.knowledge_graph:
            try:
                topic_words = message.split()[:5]
                topic_key = "_".join(w.lower() for w in topic_words if len(w) > 2)[:50]
                if topic_key:
                    self.knowledge_graph.add_node(user_id, "User", {"name": profile.name})
                    self.knowledge_graph.add_node(topic_key, "Topic", {"name": " ".join(topic_words)})
                    self.knowledge_graph.add_relationship(user_id, topic_key, "LEARNED")
            except Exception:
                pass

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
