"""Tests for WISDOM Voice module — language detection, prompts, tone."""

import pytest

from wisdom.voice.language_detect import LanguageDetector
from wisdom.voice.prompt_templates import PromptTemplates, GREETINGS
from wisdom.voice.tone_adapter import ToneAdapter, ToneAnalysis
from wisdom.voice.chat_engine import ChatEngine
from wisdom.body.components.chat import _SPEECH_LANG_MAP
from wisdom.brain.user_profile import UserProfile
from wisdom.brain.memory_manager import Message


class TestLanguageDetector:
    def setup_method(self):
        self.detector = LanguageDetector()

    def test_detect_thai(self):
        assert self.detector.detect("สวัสดีครับ AI คืออะไร") == "th"

    def test_detect_hindi(self):
        assert self.detector.detect("नमस्ते, AI क्या है?") == "hi"

    def test_detect_arabic(self):
        assert self.detector.detect("مرحبا، ما هو الذكاء الاصطناعي؟") == "ar"

    def test_detect_chinese(self):
        assert self.detector.detect("你好，什么是人工智能？") == "zh"

    def test_detect_english(self):
        assert self.detector.detect("Hello, what is artificial intelligence?") == "en"

    def test_detect_spanish(self):
        assert self.detector.detect("Hola, cómo está usted?") == "es"

    def test_empty_string(self):
        assert self.detector.detect("") == "en"

    def test_get_script(self):
        assert self.detector.get_script("th") == "Thai"
        assert self.detector.get_script("ar") == "Arabic"
        assert self.detector.get_script("en") == "Latin"


class TestPromptTemplates:
    def test_build_system_prompt(self):
        prompt = PromptTemplates.build_system_prompt(
            user_name="Somchai",
            user_language="th",
            skill_level=3.0,
        )
        assert "Somchai" in prompt
        assert "th" in prompt
        assert "3.0" in prompt

    def test_get_greeting(self):
        assert "WISDOM" in PromptTemplates.get_greeting("en")
        assert "WISDOM" in PromptTemplates.get_greeting("th")

    def test_all_languages_have_greetings(self):
        for lang in ["en", "th", "hi", "es", "zh", "ar", "pt", "sw", "id", "fr"]:
            assert lang in GREETINGS

    def test_mode_prompts(self):
        teacher = PromptTemplates.build_system_prompt(mode="teacher")
        assert "TEACHER" in teacher
        code = PromptTemplates.build_system_prompt(mode="code_helper")
        assert "CODE" in code

    def test_get_mode_prompt(self):
        mp = PromptTemplates.get_mode_prompt("teacher")
        assert "TEACHER" in mp

    def test_get_complexity_adapter(self):
        assert "beginner" in PromptTemplates.get_complexity_adapter(2.0).lower()
        assert "technical" in PromptTemplates.get_complexity_adapter(8.0).lower()


class TestToneAdapter:
    def setup_method(self):
        self.adapter = ToneAdapter()
        self.profile = UserProfile(id="test", skill_level=3.0)

    def test_basic_adaptation(self):
        result = self.adapter.get_adaptation(self.profile, [])
        assert result["complexity_level"] == "basic"
        assert "instructions" in result

    def test_confused_tone(self):
        history = [
            Message(role="user", content="I don't understand", timestamp=""),
            Message(role="user", content="what?", timestamp=""),
            Message(role="user", content="?", timestamp=""),
        ]
        result = self.adapter.get_adaptation(self.profile, history)
        assert result["tone"] == "confused"

    def test_excited_tone(self):
        history = [
            Message(role="user", content="Wow that's amazing!", timestamp=""),
            Message(role="user", content="Cool!", timestamp=""),
        ]
        result = self.adapter.get_adaptation(self.profile, history)
        assert result["tone"] == "excited"

    def test_advanced_complexity(self):
        profile = UserProfile(id="test", skill_level=8.0)
        result = self.adapter.get_adaptation(profile, [])
        assert result["complexity_level"] == "advanced"

    def test_analyze_user_message(self):
        analysis = self.adapter.analyze_user_message("Hello, how are you?")
        assert isinstance(analysis, ToneAnalysis)
        assert analysis.emotional_state in ["engaged", "confused", "excited", "frustrated", "bored"]
        assert analysis.formality in ["casual", "formal", "neutral"]

    def test_get_adapted_prompt(self):
        analysis = ToneAnalysis(
            estimated_level=2.0,
            emotional_state="confused",
            formality="casual",
            complexity_level="basic",
        )
        adapted = self.adapter.get_adapted_prompt("Tell me about AI", self.profile, analysis)
        assert "simple" in adapted.lower() or "Adaptation" in adapted

    def test_detect_frustration(self):
        history = [
            Message(role="user", content="This doesn't work", timestamp=""),
            Message(role="user", content="ugh stupid", timestamp=""),
        ]
        result = self.adapter.get_adaptation(self.profile, history)
        assert result["tone"] == "frustrated"


class TestChatEngine:
    def test_valid_modes(self):
        assert "teacher" in ChatEngine.VALID_MODES
        assert "free_chat" in ChatEngine.VALID_MODES
        assert "code_helper" in ChatEngine.VALID_MODES

    def test_set_invalid_mode_raises(self):
        from unittest.mock import MagicMock
        engine = ChatEngine(MagicMock())
        with pytest.raises(ValueError):
            engine.set_mode("invalid_mode")

    def test_set_and_get_mode(self):
        from unittest.mock import MagicMock
        engine = ChatEngine(MagicMock())
        engine.set_mode("teacher")
        assert engine.get_mode() == "teacher"


class TestVoiceInput:
    def test_speech_lang_map_covers_all_languages(self):
        expected = {"en", "th", "hi", "es", "zh", "ar", "pt", "sw", "id", "fr"}
        assert expected == set(_SPEECH_LANG_MAP.keys())

    def test_speech_lang_map_format(self):
        for code, speech_code in _SPEECH_LANG_MAP.items():
            # All speech codes should be in xx-XX format
            assert "-" in speech_code
            parts = speech_code.split("-")
            assert len(parts) == 2
