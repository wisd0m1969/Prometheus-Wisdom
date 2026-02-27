"""Streamlit main application — WISDOM chat interface."""

from __future__ import annotations

import streamlit as st

from wisdom.core.config import Config
from wisdom.core.constants import APP_NAME, APP_TAGLINE, SUPPORTED_LANGUAGES
from wisdom.core.llm_provider import LLMProvider
from wisdom.brain.user_profile import UserProfileManager
from wisdom.brain.memory_manager import MemoryManager
from wisdom.voice.language_detect import LanguageDetector
from wisdom.voice.prompt_templates import PromptTemplates
from wisdom.voice.tone_adapter import ToneAdapter
from wisdom.voice.chat_engine import ChatEngine
from wisdom.heart.privacy_manager import PrivacyManager
from wisdom.body.components.chat import render_chat, render_onboarding
from wisdom.body.components.dashboard import render_dashboard


def init_session_state() -> None:
    """Initialize Streamlit session state."""
    if "config" not in st.session_state:
        st.session_state.config = Config()
    if "llm_provider" not in st.session_state:
        st.session_state.llm_provider = LLMProvider(st.session_state.config)
    if "profile_manager" not in st.session_state:
        st.session_state.profile_manager = UserProfileManager(st.session_state.config.db_path)
    if "memory" not in st.session_state:
        st.session_state.memory = MemoryManager(max_messages=st.session_state.config.max_memory_messages)
    if "language_detector" not in st.session_state:
        st.session_state.language_detector = LanguageDetector()
    if "tone_adapter" not in st.session_state:
        st.session_state.tone_adapter = ToneAdapter()
    if "privacy_manager" not in st.session_state:
        st.session_state.privacy_manager = PrivacyManager()
    if "chat_engine" not in st.session_state:
        st.session_state.chat_engine = ChatEngine(st.session_state.llm_provider)
    if "user_id" not in st.session_state:
        st.session_state.user_id = "default"
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "page" not in st.session_state:
        st.session_state.page = "chat"
    if "onboarded" not in st.session_state:
        st.session_state.onboarded = False


def render_sidebar() -> None:
    """Render the sidebar with user info and navigation."""
    with st.sidebar:
        st.title(f"🔥 {APP_NAME}")
        st.caption(APP_TAGLINE)
        st.divider()

        # User info
        profile = st.session_state.profile_manager.get_or_create(st.session_state.user_id)
        if profile.name:
            st.write(f"👤 **{profile.name}**")
        st.write(f"🌍 {SUPPORTED_LANGUAGES.get(profile.language, {}).get('name', profile.language)}")
        st.write(f"📊 Level: {profile.skill_level:.0f}/10")

        # Progress bar
        st.progress(profile.skill_level / 10, text="Skill Level")

        st.divider()

        # Navigation
        st.subheader("Quick Actions")
        if st.button("💬 Chat", use_container_width=True):
            st.session_state.page = "chat"
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
        if st.button("🎯 Goals", use_container_width=True):
            st.session_state.page = "goals"

        st.divider()

        # LLM status
        health = st.session_state.llm_provider.health_check()
        provider = health.get("provider", "none")
        st.caption(f"LLM: {provider} | {'🟢 Local' if health.get('ollama_available') else '☁️ Cloud'}")

        st.divider()
        st.caption("Open Source | MIT License")
        st.caption("Made with ♥ for Humanity")


def main() -> None:
    """Main Streamlit application entry point."""
    st.set_page_config(
        page_title=APP_NAME,
        page_icon="🔥",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    init_session_state()

    # Check if user has been onboarded
    profile = st.session_state.profile_manager.get_or_create(st.session_state.user_id)

    if not st.session_state.onboarded and not profile.name:
        render_onboarding()
        return

    render_sidebar()

    # Route to page
    if st.session_state.page == "dashboard":
        render_dashboard()
    else:
        render_chat()


if __name__ == "__main__":
    main()
