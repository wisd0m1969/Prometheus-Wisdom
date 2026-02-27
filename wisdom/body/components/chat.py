"""Chat UI component — bubbles, streaming, and onboarding flow."""

from __future__ import annotations

import streamlit as st

from wisdom.voice.prompt_templates import PromptTemplates


def render_chat() -> None:
    """Render the main chat interface."""
    st.header("💬 Chat with WISDOM")

    # Display message history
    for msg in st.session_state.messages:
        role = msg["role"]
        with st.chat_message("assistant" if role == "wisdom" else "user"):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Show user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Detect language
        language = st.session_state.language_detector.detect(prompt)

        # Get profile
        profile = st.session_state.profile_manager.get_or_create(st.session_state.user_id)
        if profile.language != language:
            profile.language = language
            st.session_state.profile_manager.update(profile)

        # Get conversation history
        history = st.session_state.memory.get_history(st.session_state.user_id)

        # Get tone adaptation
        tone_hints = st.session_state.tone_adapter.get_adaptation(profile, history)

        # Sanitize if using cloud LLM
        safe_message = prompt
        if not st.session_state.llm_provider.is_local():
            safe_message = st.session_state.privacy_manager.sanitize(prompt)

        # Generate streaming response
        with st.chat_message("assistant"):
            try:
                response_chunks = []
                with st.spinner("WISDOM is thinking..."):
                    for chunk in st.session_state.chat_engine.generate_stream(
                        user_message=safe_message,
                        profile=profile,
                        history=history,
                        tone_hints=tone_hints,
                    ):
                        response_chunks.append(chunk)

                full_response = "".join(response_chunks)
                st.markdown(full_response)
            except RuntimeError as e:
                full_response = f"⚠️ {e}\n\nPlease configure an LLM provider (Ollama or Gemini)."
                st.error(full_response)

        # Update memory
        st.session_state.memory.add_message(st.session_state.user_id, "user", prompt, language)
        st.session_state.memory.add_message(st.session_state.user_id, "wisdom", full_response, language)
        st.session_state.messages.append({"role": "wisdom", "content": full_response})


def render_onboarding() -> None:
    """Render first-time user onboarding flow."""
    st.set_page_config(page_title="Welcome to WISDOM", page_icon="🔥", layout="centered")

    st.title("🔥 Welcome to PROMETHEUS WISDOM")
    st.subheader("Your Personal AI Companion")
    st.write("")

    # Greeting in multiple languages
    cols = st.columns(5)
    greetings = ["Hello! 👋", "สวัสดี!", "नमस्ते!", "¡Hola!", "你好!"]
    for col, greeting in zip(cols, greetings):
        col.markdown(f"**{greeting}**")

    st.write("")
    st.write("I'm **WISDOM** — your AI friend. I'm here to help you learn about AI, step by step.")
    st.write("")

    # Name input
    name = st.text_input("What's your name? (optional — you can skip this)")

    st.write("")
    st.write("**What would you like to do?**")

    col1, col2, col3 = st.columns(3)
    choice = None
    with col1:
        if st.button("📚 Learn about AI", use_container_width=True):
            choice = "learn"
    with col2:
        if st.button("💬 Just chat", use_container_width=True):
            choice = "chat"
    with col3:
        if st.button("🎯 Help me with something", use_container_width=True):
            choice = "help"

    if choice:
        profile = st.session_state.profile_manager.get_or_create(st.session_state.user_id)
        if name:
            profile.name = name
        if choice == "learn":
            profile.goals = ["Learn about AI"]
        elif choice == "help":
            profile.goals = ["Get help with a task"]
        st.session_state.profile_manager.update(profile)
        st.session_state.onboarded = True

        # Set welcome message
        greeting = PromptTemplates.get_greeting(profile.language)
        if name:
            greeting = greeting.replace("WISDOM", f"WISDOM, {name}! 🎉")
        st.session_state.messages = [{"role": "wisdom", "content": greeting}]

        st.rerun()
