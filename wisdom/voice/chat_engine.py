"""Core conversation engine — LangChain chat with streaming support.

Supports multiple operating modes (teacher, researcher, quiz, code, chat)
with both synchronous and streaming response generation.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Generator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

if TYPE_CHECKING:
    from wisdom.brain.memory_manager import Message
    from wisdom.brain.user_profile import UserProfile
    from wisdom.core.llm_provider import LLMProvider

__all__ = ["ChatEngine"]

logger = logging.getLogger(__name__)


class ChatEngine:
    """LangChain-powered conversation engine.

    Handles message formatting, LLM invocation, streaming responses,
    and operating mode management.
    """

    VALID_MODES = {"teacher", "researcher", "quiz_master", "code_helper", "free_chat"}

    def __init__(self, llm_provider: LLMProvider) -> None:
        self.llm_provider = llm_provider
        self._mode: str = "free_chat"

    def set_mode(self, mode: str) -> None:
        """Set the operating mode.

        Args:
            mode: One of 'teacher', 'researcher', 'quiz_master', 'code_helper', 'free_chat'.
        """
        if mode not in self.VALID_MODES:
            raise ValueError(f"Invalid mode '{mode}'. Must be one of: {self.VALID_MODES}")
        self._mode = mode
        logger.info("Chat mode set to: %s", mode)

    def get_mode(self) -> str:
        """Get the current operating mode."""
        return self._mode

    def generate(
        self,
        user_message: str,
        profile: UserProfile,
        history: list[Message] | None = None,
        tone_hints: dict | None = None,
        mode: str | None = None,
        retrieved_context: str = "",
    ) -> str:
        """Generate a full (non-streaming) response from WISDOM.

        Args:
            user_message: The user's current message.
            profile: User's profile for personalization.
            history: Conversation history.
            tone_hints: Adaptation hints from ToneAdapter.
            mode: Override current mode for this message.
            retrieved_context: RAG-retrieved context from ChromaDB/KG.

        Returns:
            WISDOM's response text.
        """
        messages = self._build_messages(user_message, profile, history, tone_hints, mode, retrieved_context)
        llm = self.llm_provider.get_llm()
        response = llm.invoke(messages)
        return response.content

    def chat_sync(
        self,
        user_message: str,
        profile: UserProfile,
        history: list[Message] | None = None,
        tone_hints: dict | None = None,
    ) -> str:
        """Synchronous chat — alias for generate()."""
        return self.generate(user_message, profile, history, tone_hints)

    def generate_stream(
        self,
        user_message: str,
        profile: UserProfile,
        history: list[Message] | None = None,
        tone_hints: dict | None = None,
        mode: str | None = None,
        retrieved_context: str = "",
    ) -> Generator[str, None, None]:
        """Generate a streaming response from WISDOM.

        Yields response chunks for real-time display.
        """
        messages = self._build_messages(user_message, profile, history, tone_hints, mode, retrieved_context)
        llm = self.llm_provider.get_llm()
        for chunk in llm.stream(messages):
            if chunk.content:
                yield chunk.content

    def chat(
        self,
        user_message: str,
        profile: UserProfile,
        history: list[Message] | None = None,
        tone_hints: dict | None = None,
        stream: bool = True,
    ) -> str | Generator[str, None, None]:
        """Main chat method — returns stream generator or full string."""
        if stream:
            return self.generate_stream(user_message, profile, history, tone_hints)
        return self.generate(user_message, profile, history, tone_hints)

    # ─── Private Helpers ──────────────────────────────────────

    def _build_messages(
        self,
        user_message: str,
        profile: UserProfile,
        history: list[Message] | None,
        tone_hints: dict | None,
        mode: str | None = None,
        retrieved_context: str = "",
    ) -> list:
        """Build the full message list for LLM invocation."""
        from wisdom.voice.prompt_templates import PromptTemplates

        active_mode = mode or self._mode

        # Build system prompt with retrieved context
        system_prompt = PromptTemplates.build_system_prompt(
            user_name=profile.name,
            user_language=profile.language,
            skill_level=profile.skill_level,
            current_goal=profile.goals[0] if profile.goals else "Explore AI",
            mode=active_mode,
            retrieved_context=retrieved_context or "No prior context.",
        )

        # Add tone adaptation instructions
        if tone_hints and tone_hints.get("instructions"):
            system_prompt += f"\n\nAdaptation: {tone_hints['instructions']}"

        # Build message list
        messages = [SystemMessage(content=system_prompt)]

        # Add conversation history
        if history:
            for msg in history[-10:]:
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                else:
                    messages.append(AIMessage(content=msg.content))

        # Add current message
        messages.append(HumanMessage(content=user_message))

        return messages
