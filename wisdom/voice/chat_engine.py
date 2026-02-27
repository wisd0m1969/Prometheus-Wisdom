"""Core conversation engine — LangChain chat with streaming support."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

if TYPE_CHECKING:
    from wisdom.brain.memory_manager import Message
    from wisdom.brain.user_profile import UserProfile
    from wisdom.core.llm_provider import LLMProvider

__all__ = ["ChatEngine"]

logger = logging.getLogger(__name__)


class ChatEngine:
    """LangChain-powered conversation engine.

    Handles message formatting, LLM invocation, and streaming responses.
    """

    def __init__(self, llm_provider: LLMProvider) -> None:
        self.llm_provider = llm_provider

    def generate(
        self,
        user_message: str,
        profile: UserProfile,
        history: list[Message] | None = None,
        tone_hints: dict | None = None,
        mode: str = "free_chat",
    ) -> str:
        """Generate a response from WISDOM.

        Args:
            user_message: The user's current message.
            profile: User's profile for personalization.
            history: Conversation history.
            tone_hints: Adaptation hints from ToneAdapter.
            mode: Operating mode (teacher, researcher, quiz_master, code_helper, free_chat).

        Returns:
            WISDOM's response text.
        """
        from wisdom.voice.prompt_templates import PromptTemplates

        # Build system prompt
        system_prompt = PromptTemplates.build_system_prompt(
            user_name=profile.name,
            user_language=profile.language,
            skill_level=profile.skill_level,
            current_goal=profile.goals[0] if profile.goals else "Explore AI",
            mode=mode,
        )

        # Add tone adaptation instructions
        if tone_hints and tone_hints.get("instructions"):
            system_prompt += f"\n\nAdaptation: {tone_hints['instructions']}"

        # Build message list
        messages = [SystemMessage(content=system_prompt)]

        # Add conversation history
        if history:
            for msg in history[-10:]:  # Last 10 messages for context
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                else:
                    messages.append(AIMessage(content=msg.content))

        # Add current message
        messages.append(HumanMessage(content=user_message))

        # Generate response
        llm = self.llm_provider.get_llm()
        response = llm.invoke(messages)

        return response.content

    def generate_stream(
        self,
        user_message: str,
        profile: UserProfile,
        history: list[Message] | None = None,
        tone_hints: dict | None = None,
        mode: str = "free_chat",
    ):
        """Generate a streaming response from WISDOM.

        Yields response chunks for real-time display.
        """
        from wisdom.voice.prompt_templates import PromptTemplates

        system_prompt = PromptTemplates.build_system_prompt(
            user_name=profile.name,
            user_language=profile.language,
            skill_level=profile.skill_level,
            mode=mode,
        )

        if tone_hints and tone_hints.get("instructions"):
            system_prompt += f"\n\nAdaptation: {tone_hints['instructions']}"

        messages = [SystemMessage(content=system_prompt)]

        if history:
            for msg in history[-10:]:
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                else:
                    messages.append(AIMessage(content=msg.content))

        messages.append(HumanMessage(content=user_message))

        llm = self.llm_provider.get_llm()
        for chunk in llm.stream(messages):
            if chunk.content:
                yield chunk.content
