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


# Offline cached content — served when no LLM is available
_OFFLINE_CONTENT = {
    "en": {
        "greeting": "I'm currently in offline mode. I can still show you cached learning content!",
        "ai": "**What is AI?**\n\nArtificial Intelligence (AI) is when computers learn to do things that usually require human intelligence — like understanding language, recognizing images, or making decisions.\n\n**Key concepts:**\n- **Machine Learning**: Computers learn from data instead of being explicitly programmed\n- **Neural Networks**: Inspired by the brain, layers of connected nodes process information\n- **Large Language Models**: AI that understands and generates human language (like me!)",
        "prompt": "**Tips for Good Prompts:**\n1. Be specific about what you want\n2. Provide context and examples\n3. Break complex tasks into steps\n4. Tell the AI what format you want\n5. Review and iterate on the output",
        "default": "I'm offline right now — no AI model is available.\n\n**You can still:**\n- Browse the **Learning Path** for lessons\n- Try the **Code Playground** to practice Python\n- Read **Community Q&A** answers\n\nTo go online, start Ollama (`ollama serve`) or set GOOGLE_API_KEY in .env",
    },
    "th": {
        "greeting": "ขณะนี้ WISDOM อยู่ในโหมดออฟไลน์ แต่ยังดูเนื้อหาที่เก็บไว้ได้!",
        "ai": "**AI คืออะไร?**\n\nปัญญาประดิษฐ์ (AI) คือเมื่อคอมพิวเตอร์เรียนรู้ที่จะทำสิ่งที่ปกติต้องใช้สติปัญญาของมนุษย์ เช่น เข้าใจภาษา จดจำรูปภาพ หรือตัดสินใจ\n\n**แนวคิดสำคัญ:**\n- **Machine Learning**: คอมพิวเตอร์เรียนรู้จากข้อมูลแทนการเขียนโปรแกรมทุกขั้นตอน\n- **Neural Networks**: เลียนแบบสมอง ประมวลผลข้อมูลผ่านชั้นของโหนดที่เชื่อมต่อกัน\n- **Large Language Models**: AI ที่เข้าใจและสร้างภาษามนุษย์ได้",
        "default": "ขณะนี้ WISDOM ออฟไลน์ — ไม่มี AI model ที่พร้อมใช้งาน\n\n**คุณยังสามารถ:**\n- ดู **เส้นทางการเรียนรู้** สำหรับบทเรียน\n- ลอง **Code Playground** เพื่อฝึก Python\n- อ่านคำตอบ **Community Q&A**\n\nเพื่อออนไลน์ ให้เริ่ม Ollama (`ollama serve`) หรือตั้ง GOOGLE_API_KEY ใน .env",
    },
}


def _offline_fallback(message: str, language: str = "en") -> str:
    """Return cached content when no LLM is available (offline mode).

    Matches user message to cached educational content or returns
    a helpful offline guide.
    """
    content = _OFFLINE_CONTENT.get(language, _OFFLINE_CONTENT["en"])
    lower = message.lower()

    # Try to match keywords to cached content
    if any(kw in lower for kw in ["ai", "artificial intelligence", "ปัญญาประดิษฐ์", "คืออะไร"]):
        return content.get("ai", content["default"])
    if any(kw in lower for kw in ["prompt", "how to ask", "ถาม"]):
        return content.get("prompt", content["default"])

    # Try community knowledge fallback
    try:
        from wisdom.heart.community_knowledge import CommunityKnowledge
        ck = CommunityKnowledge(st.session_state.config.db_path)
        results = ck.search(message, language=language, limit=3)
        if results:
            parts = [f"*Found in community knowledge (offline):*\n"]
            for qa in results:
                parts.append(f"**Q:** {qa['question']}\n**A:** {qa['answer']}\n")
            return "\n".join(parts)
    except Exception:
        pass

    return content["default"]


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

        # Generate streaming response (or offline fallback)
        with st.chat_message("assistant"):
            if st.session_state.llm_provider.is_offline():
                full_response = _offline_fallback(prompt, profile.language)
                st.markdown(full_response)
            else:
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
                    full_response = _offline_fallback(prompt, profile.language)
                    st.markdown(full_response)

        # Update memory
        st.session_state.memory.add_message(st.session_state.user_id, "user", prompt, language)
        st.session_state.memory.add_message(st.session_state.user_id, "wisdom", full_response, language)
        st.session_state.messages.append({"role": "wisdom", "content": full_response})


def render_onboarding() -> None:
    """Render first-time user onboarding flow.

    Multi-step onboarding:
    1. Welcome + language selection + name
    2. Experience level selection
    3. Goal choice → personalized welcome
    Awards first_contact badge on completion.
    """
    st.set_page_config(page_title="Welcome to WISDOM", page_icon="🔥", layout="centered")

    if "onboarding_step" not in st.session_state:
        st.session_state.onboarding_step = 1

    step = st.session_state.onboarding_step

    # Step indicator
    steps = ["Welcome", "Experience", "Goals"]
    cols = st.columns(len(steps))
    for i, (col, label) in enumerate(zip(cols, steps)):
        if i + 1 < step:
            col.markdown(f"~~**{i+1}. {label}** ✅~~")
        elif i + 1 == step:
            col.markdown(f"**{i+1}. {label}** ←")
        else:
            col.markdown(f"{i+1}. {label}")
    st.divider()

    # ─── Step 1: Welcome + Language + Name ───────────────────
    if step == 1:
        st.title("🔥 Welcome to PROMETHEUS WISDOM")
        st.subheader("Your Personal AI Companion")
        st.write("")

        # Greeting in multiple languages
        greet_cols = st.columns(5)
        greetings = ["Hello! 👋", "สวัสดี!", "नमस्ते!", "¡Hola!", "你好!"]
        for col, greeting in zip(greet_cols, greetings):
            col.markdown(f"**{greeting}**")

        greet_cols2 = st.columns(5)
        greetings2 = ["مرحبا!", "Olá!", "Habari!", "Halo!", "Bonjour!"]
        for col, greeting in zip(greet_cols2, greetings2):
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
        if st.button("Next →", type="primary", use_container_width=True):
            st.session_state.onboarding_name = name
            st.session_state.onboarding_lang = selected_lang
            st.session_state.onboarding_step = 2
            st.rerun()

    # ─── Step 2: Experience Level ────────────────────────────
    elif step == 2:
        st.title("📊 Tell us about yourself")
        st.write("This helps WISDOM adapt to your level. You can always change this later.")
        st.write("")

        experience = st.radio(
            "How much do you know about AI?",
            options=[
                "🌱 Complete beginner — I've never used AI before",
                "🌿 Some experience — I've tried ChatGPT or similar tools",
                "🌳 Intermediate — I understand prompts and use AI regularly",
                "🚀 Advanced — I build with AI or understand how it works",
            ],
            index=0,
        )

        level_map = {
            "🌱": 0.0,
            "🌿": 3.0,
            "🌳": 6.0,
            "🚀": 8.0,
        }
        skill_level = level_map.get(experience[:2], 0.0)

        st.write("")
        col_back, col_next = st.columns(2)
        with col_back:
            if st.button("← Back", use_container_width=True):
                st.session_state.onboarding_step = 1
                st.rerun()
        with col_next:
            if st.button("Next →", type="primary", use_container_width=True):
                st.session_state.onboarding_skill = skill_level
                st.session_state.onboarding_step = 3
                st.rerun()

    # ─── Step 3: Goal Choice ─────────────────────────────────
    elif step == 3:
        st.title("🎯 What would you like to do?")
        st.write("")

        col1, col2, col3 = st.columns(3)
        choice = None
        with col1:
            if st.button("📚 Learn about AI\n\nStep-by-step lessons", use_container_width=True):
                choice = "learn"
        with col2:
            if st.button("💬 Just chat\n\nFree conversation", use_container_width=True):
                choice = "chat"
        with col3:
            if st.button("🎯 Help me with\nsomething specific", use_container_width=True):
                choice = "help"

        st.write("")
        if st.button("← Back", use_container_width=True):
            st.session_state.onboarding_step = 2
            st.rerun()

        if choice:
            # Save profile with all collected data
            name = st.session_state.get("onboarding_name", "")
            selected_lang = st.session_state.get("onboarding_lang", "en")
            skill_level = st.session_state.get("onboarding_skill", 0.0)

            profile = st.session_state.profile_manager.get_or_create(st.session_state.user_id)
            if name:
                profile.name = name
            profile.language = selected_lang
            profile.skill_level = skill_level
            if choice == "learn":
                profile.goals = ["Learn about AI"]
            elif choice == "help":
                profile.goals = ["Get help with a task"]
            st.session_state.profile_manager.update(profile)
            st.session_state.onboarded = True

            # Award first_contact badge
            from wisdom.soul.goal_tracker import GoalTracker
            tracker = GoalTracker(st.session_state.config.db_path)
            tracker.award_badge(st.session_state.user_id, "first_contact")

            # Set personalized welcome message
            greeting = PromptTemplates.get_greeting(selected_lang)
            if name:
                greeting = greeting.replace("WISDOM", f"WISDOM, {name}! 🎉")

            # Add experience-aware welcome
            if skill_level <= 1:
                greeting += "\n\nI'll start from the very basics — no experience needed!"
            elif skill_level <= 5:
                greeting += "\n\nGreat that you have some experience! I'll build on what you know."
            else:
                greeting += "\n\nAwesome, you're already experienced! Let's dive into advanced topics."

            st.session_state.messages = [{"role": "wisdom", "content": greeting}]

            # Clean up onboarding state
            for key in ["onboarding_step", "onboarding_name", "onboarding_lang", "onboarding_skill"]:
                st.session_state.pop(key, None)

            st.rerun()
