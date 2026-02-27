"""Chat UI component — message bubbles, streaming, voice input, and onboarding flow.

Provides polished onboarding with multilingual greetings,
real-time streaming responses, voice input via Web Speech API,
and mode-aware chat display.
"""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from wisdom.core.constants import SUPPORTED_LANGUAGES
from wisdom.voice.prompt_templates import PromptTemplates


# Web Speech API JavaScript component for voice input
_VOICE_INPUT_HTML = """
<div id="voice-container" style="display:inline-block;">
    <button id="voice-btn" onclick="toggleVoice()" style="
        background: #ff4b4b; color: white; border: none; border-radius: 50%;
        width: 40px; height: 40px; font-size: 18px; cursor: pointer;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2); transition: all 0.3s;">
        🎤
    </button>
    <span id="voice-status" style="margin-left:8px; font-size:12px; color:#666;"></span>
</div>
<script>
let recognition = null;
let isListening = false;

function toggleVoice() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        document.getElementById('voice-status').textContent = 'Speech recognition not supported in this browser';
        return;
    }

    if (isListening) {
        recognition.stop();
        return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = '%LANG%';

    recognition.onstart = function() {
        isListening = true;
        document.getElementById('voice-btn').style.background = '#ff0000';
        document.getElementById('voice-btn').style.animation = 'pulse 1s infinite';
        document.getElementById('voice-status').textContent = 'Listening...';
    };

    recognition.onresult = function(event) {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
        }
        if (event.results[event.results.length - 1].isFinal) {
            // Send transcript to Streamlit via query params
            window.parent.postMessage({type: 'voice_input', text: transcript}, '*');
            document.getElementById('voice-status').textContent = 'Heard: ' + transcript;
        } else {
            document.getElementById('voice-status').textContent = transcript + '...';
        }
    };

    recognition.onerror = function(event) {
        document.getElementById('voice-status').textContent = 'Error: ' + event.error;
        isListening = false;
        document.getElementById('voice-btn').style.background = '#ff4b4b';
        document.getElementById('voice-btn').style.animation = '';
    };

    recognition.onend = function() {
        isListening = false;
        document.getElementById('voice-btn').style.background = '#ff4b4b';
        document.getElementById('voice-btn').style.animation = '';
    };

    recognition.start();
}
</script>
<style>
@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.1); }
    100% { transform: scale(1); }
}
</style>
"""

# Language code mapping for Web Speech API
_SPEECH_LANG_MAP = {
    "en": "en-US", "th": "th-TH", "hi": "hi-IN", "es": "es-ES",
    "zh": "zh-CN", "ar": "ar-SA", "pt": "pt-BR", "sw": "sw-KE",
    "id": "id-ID", "fr": "fr-FR",
}


def _render_voice_input(language: str = "en") -> None:
    """Render the voice input button using Web Speech API."""
    speech_lang = _SPEECH_LANG_MAP.get(language, "en-US")
    html = _VOICE_INPUT_HTML.replace("%LANG%", speech_lang)
    components.html(html, height=50)


def render_chat() -> None:
    """Render the main chat interface with streaming and voice input support."""
    mode = st.session_state.chat_engine.get_mode()
    mode_labels = {
        "free_chat": "💬 Free Chat",
        "teacher": "📚 Teacher Mode",
        "researcher": "🔍 Researcher Mode",
        "quiz_master": "❓ Quiz Master",
        "code_helper": "💻 Code Helper",
    }
    st.header(mode_labels.get(mode, "💬 Chat with WISDOM"))

    # Voice input button
    profile = st.session_state.profile_manager.get_or_create(st.session_state.user_id)
    _render_voice_input(profile.language)

    # Display message history
    for msg in st.session_state.messages:
        role = msg["role"]
        with st.chat_message("assistant" if role == "wisdom" else "user"):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Type your message here (or use 🎤 voice input)..."):
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

        # Auto-detect mode via adaptation engine
        if hasattr(st.session_state, "adaptation_engine"):
            adaptation = st.session_state.adaptation_engine.adapt(profile, prompt, history)
            if adaptation.recommended_mode != mode:
                st.session_state.chat_engine.set_mode(adaptation.recommended_mode)

        # Sanitize if using cloud LLM
        safe_message = prompt
        if not st.session_state.llm_provider.is_local():
            safe_message = st.session_state.privacy_manager.sanitize(prompt)

        # Generate streaming response
        with st.chat_message("assistant"):
            try:
                message_placeholder = st.empty()
                full_response = ""
                for chunk in st.session_state.chat_engine.generate_stream(
                    user_message=safe_message,
                    profile=profile,
                    history=history,
                    tone_hints=tone_hints,
                ):
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
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
    st.write("No experience needed. No judgment. Just learning together. 🤝")
    st.write("")

    # Name input
    name = st.text_input("What's your name? (optional — you can skip this)")

    # Language selector
    lang_options = {code: info["name"] for code, info in SUPPORTED_LANGUAGES.items()}
    selected_lang = st.selectbox(
        "Preferred language",
        options=list(lang_options.keys()),
        format_func=lambda x: f"{lang_options[x]} {SUPPORTED_LANGUAGES[x].get('greeting', '')}",
        index=0,
    )

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
        profile.language = selected_lang
        if choice == "learn":
            profile.goals = ["Learn about AI"]
        elif choice == "help":
            profile.goals = ["Get help with a task"]
        st.session_state.profile_manager.update(profile)
        st.session_state.onboarded = True

        # Set welcome message
        greeting = PromptTemplates.get_greeting(selected_lang)
        if name:
            greeting = greeting.replace("WISDOM", f"WISDOM, {name}! 🎉")
        st.session_state.messages = [{"role": "wisdom", "content": greeting}]

        st.rerun()
