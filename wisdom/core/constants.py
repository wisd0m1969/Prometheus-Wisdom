"""Application constants for PROMETHEUS WISDOM."""

__all__ = [
    "APP_NAME",
    "APP_VERSION",
    "SUPPORTED_LANGUAGES",
    "DEFAULT_OLLAMA_MODEL",
    "DEFAULT_GEMINI_MODEL",
    "DEFAULT_EMBED_MODEL",
    "SKILL_CATEGORIES",
    "LEARNING_LEVELS",
]

APP_NAME = "PROMETHEUS WISDOM"
APP_VERSION = "1.0.0"
APP_TAGLINE = "AI Companion for Humanity"

# Supported languages — Phase 1 (10 languages covering ~5B people)
SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "script": "Latin", "greeting": "Hello!"},
    "th": {"name": "Thai", "script": "Thai", "greeting": "สวัสดีครับ!"},
    "hi": {"name": "Hindi", "script": "Devanagari", "greeting": "नमस्ते!"},
    "es": {"name": "Spanish", "script": "Latin", "greeting": "¡Hola!"},
    "zh": {"name": "Chinese", "script": "CJK", "greeting": "你好!"},
    "ar": {"name": "Arabic", "script": "Arabic", "greeting": "مرحبا!"},
    "pt": {"name": "Portuguese", "script": "Latin", "greeting": "Olá!"},
    "sw": {"name": "Swahili", "script": "Latin", "greeting": "Habari!"},
    "id": {"name": "Indonesian", "script": "Latin", "greeting": "Halo!"},
    "fr": {"name": "French", "script": "Latin", "greeting": "Bonjour!"},
}

# LLM defaults
DEFAULT_OLLAMA_MODEL = "llama3:latest"
DEFAULT_OLLAMA_EMBED_MODEL = "nomic-embed-text"
DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"
DEFAULT_GEMINI_EMBED_MODEL = "models/text-embedding-004"

# Skill assessment categories with weights
SKILL_CATEGORIES = {
    "ai_awareness": {"weight": 0.30, "label": "AI Awareness"},
    "prompt_skills": {"weight": 0.25, "label": "Prompt Skills"},
    "digital_literacy": {"weight": 0.20, "label": "Digital Literacy"},
    "coding_ability": {"weight": 0.15, "label": "Coding Ability"},
    "domain_knowledge": {"weight": 0.10, "label": "Domain Knowledge"},
}

# Learning path levels
LEARNING_LEVELS = {
    1: {"name": "Hello AI", "description": "What is AI? First conversation."},
    2: {"name": "Talk to AI", "description": "Learn to prompt effectively."},
    3: {"name": "AI in Daily Life", "description": "Practical AI applications."},
    4: {"name": "How AI Thinks", "description": "Understanding AI internals."},
    5: {"name": "Code with AI", "description": "Introduction to coding."},
    6: {"name": "Build with AI", "description": "Building applications."},
    7: {"name": "Create AI Tools", "description": "Mastery — build your own AI."},
}

# Achievement badges
BADGES = {
    "first_contact": {"name": "First Contact", "trigger": "Complete first conversation"},
    "polyglot": {"name": "Polyglot", "trigger": "Use WISDOM in 2+ languages"},
    "curious_mind": {"name": "Curious Mind", "trigger": "Ask 50 questions"},
    "level_up": {"name": "Level Up", "trigger": "Complete any learning module"},
    "perfect_score": {"name": "Perfect Score", "trigger": "Get 100% on a quiz"},
    "streak_master": {"name": "Streak Master", "trigger": "Use WISDOM 7 days in a row"},
    "code_rookie": {"name": "Code Rookie", "trigger": "Write first code with WISDOM"},
    "builder": {"name": "Builder", "trigger": "Complete Level 6 project"},
    "creator": {"name": "Creator", "trigger": "Complete Level 7 project"},
    "helper": {"name": "Helper", "trigger": "Contribute to community knowledge"},
    "pioneer": {"name": "Pioneer", "trigger": "Be among first 1000 users"},
}
