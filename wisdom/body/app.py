"""Streamlit main application — WISDOM chat interface.

Features: onboarding flow, chat with streaming, dashboard,
settings panel with language selector and difficulty slider.
"""

from __future__ import annotations

import streamlit as st

from wisdom.core.config import Config
from wisdom.core.constants import APP_NAME, APP_TAGLINE, SUPPORTED_LANGUAGES, SKILL_LEVELS
from wisdom.core.llm_provider import LLMProvider
from wisdom.brain.user_profile import UserProfileManager
from wisdom.brain.memory_manager import MemoryManager
from wisdom.voice.language_detect import LanguageDetector
from wisdom.voice.tone_adapter import ToneAdapter
from wisdom.voice.chat_engine import ChatEngine
from wisdom.heart.privacy_manager import PrivacyManager
from wisdom.heart.federated_core import FederatedCore
from wisdom.heart.community_knowledge import CommunityKnowledge
from wisdom.soul.adaptation_engine import AdaptationEngine
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
    if "federated" not in st.session_state:
        st.session_state.federated = FederatedCore()
    if "community" not in st.session_state:
        st.session_state.community = CommunityKnowledge(st.session_state.config.db_path)
    if "chat_engine" not in st.session_state:
        st.session_state.chat_engine = ChatEngine(st.session_state.llm_provider)
    if "adaptation_engine" not in st.session_state:
        st.session_state.adaptation_engine = AdaptationEngine()
    if "user_id" not in st.session_state:
        st.session_state.user_id = "default"
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "page" not in st.session_state:
        st.session_state.page = "chat"
    if "onboarded" not in st.session_state:
        st.session_state.onboarded = False


def render_sidebar() -> None:
    """Render the sidebar with user info, navigation, and settings."""
    with st.sidebar:
        st.title(f"🔥 {APP_NAME}")
        st.caption(APP_TAGLINE)
        st.divider()

        # User info
        profile = st.session_state.profile_manager.get_or_create(st.session_state.user_id)
        if profile.name:
            st.write(f"👤 **{profile.name}**")
        lang_info = SUPPORTED_LANGUAGES.get(profile.language, {})
        st.write(f"🌍 {lang_info.get('name', profile.language)}")
        level_desc = SKILL_LEVELS.get(int(profile.skill_level), "")
        st.write(f"📊 Level {profile.skill_level:.0f}/10")
        if level_desc:
            st.caption(level_desc)

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
        if st.button("💻 Code Playground", use_container_width=True):
            st.session_state.page = "code_playground"
        if st.button("🌍 Community Q&A", use_container_width=True):
            st.session_state.page = "community"

        st.divider()

        # Settings expander
        with st.expander("⚙️ Settings"):
            # Language selector
            lang_options = {code: info["name"] for code, info in SUPPORTED_LANGUAGES.items()}
            current_lang_idx = list(lang_options.keys()).index(profile.language) if profile.language in lang_options else 0
            selected_lang = st.selectbox(
                "Language",
                options=list(lang_options.keys()),
                format_func=lambda x: lang_options[x],
                index=current_lang_idx,
            )
            if selected_lang != profile.language:
                profile.language = selected_lang
                st.session_state.profile_manager.update(profile)

            # Difficulty slider
            new_level = st.slider(
                "Difficulty Level",
                min_value=0.0,
                max_value=10.0,
                value=float(profile.skill_level),
                step=0.5,
            )
            if new_level != profile.skill_level:
                profile.skill_level = new_level
                st.session_state.profile_manager.update(profile)

            # Chat mode
            mode = st.selectbox(
                "Chat Mode",
                options=["free_chat", "teacher", "researcher", "quiz_master", "code_helper"],
                format_func=lambda x: x.replace("_", " ").title(),
            )
            st.session_state.chat_engine.set_mode(mode)

            st.divider()

            # Federated learning opt-in
            user_id = st.session_state.user_id
            fed = st.session_state.federated
            is_opted = fed.is_opted_in(user_id)
            federated_toggle = st.toggle(
                "Community Learning",
                value=is_opted,
                help="Share anonymized learning patterns to help improve WISDOM for everyone. "
                     "No personal data is ever shared.",
            )
            if federated_toggle and not is_opted:
                fed.opt_in(user_id)
            elif not federated_toggle and is_opted:
                fed.opt_out(user_id)

            if federated_toggle:
                preview = fed.preview_shared_data()
                if preview:
                    st.caption(f"Interactions shared: {preview.get('confusion_count', 0)} confusion points")

        st.divider()

        # LLM status with offline mode indicator
        health = st.session_state.llm_provider.health_check()
        provider = health.get("provider", "none")
        latency = health.get("latency_ms")
        if provider == "none":
            st.warning("⚡ Offline Mode — No LLM available. Cached content only.")
        else:
            status_text = f"LLM: {provider}"
            if health.get("ollama_available"):
                status_text += " | 🟢 Local (Private)"
            else:
                status_text += " | ☁️ Cloud"
            if latency:
                status_text += f" | {latency}ms"
            st.caption(status_text)

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
    elif st.session_state.page == "code_playground":
        from wisdom.body.components.code_playground import render_code_playground
        render_code_playground()
    elif st.session_state.page == "community":
        from wisdom.body.components.community import render_community
        render_community()
    else:
        render_chat()


if __name__ == "__main__":
    main()
