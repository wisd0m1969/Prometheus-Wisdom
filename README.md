# 🔥 PROMETHEUS WISDOM

**AI Companion for Humanity**

> An open-source AI personal companion designed to democratize AI access for the 6.8 billion people who have never interacted with AI.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-171%20passing-brightgreen.svg)](#testing)

---

## Why WISDOM?

84% of the world's population has never used AI. Not because they can't — but because no one built AI **for them**.

WISDOM is different:
- **Zero-config**: Works locally with Ollama (free, private) or falls back to Google Gemini
- **Multilingual**: Auto-detects and responds in 10 languages covering ~5 billion people
- **Adaptive**: Adjusts complexity from "explain like I'm 5" to full technical depth
- **Privacy-first**: PII sanitization, local-first processing, opt-in data sharing
- **Guided learning**: 7-level curriculum from "What is AI?" to "Build your own AI tool"

---

## Quick Start

### 1. Install

```bash
git clone https://github.com/wisd0m1969/Prometheus-Wisdom.git
cd Prometheus-Wisdom
make install
```

### 2. Set up LLM (choose one)

**Option A — Ollama (recommended, free, private)**
```bash
# Install Ollama: https://ollama.com
ollama pull llama3:latest
ollama serve
```

**Option B — Google Gemini (cloud, free tier)**
```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### 3. Run

```bash
# Web UI (Streamlit)
make run

# REST API (FastAPI)
make api
```

### 4. Or use as a library

```python
from wisdom import Wisdom

w = Wisdom()
response = w.chat("What is AI?")
print(response)

# Streaming
for chunk in w.chat_stream("Explain machine learning"):
    print(chunk, end="")
```

---

## Architecture

WISDOM uses a **modular monolith** design inspired by the human body:

```
🔥 PROMETHEUS WISDOM
├── 🧠 Brain    — Memory, profiles, knowledge graph, embeddings
├── 🗣️ Voice    — Language detection, chat engine, tone adaptation
├── ❤️ Heart    — Privacy, federated learning, community knowledge
├── 👻 Soul     — Adaptation, skill assessment, learning paths
├── 🏋️ Body     — Streamlit UI, FastAPI API
└── ⚙️ Core     — Config, LLM provider, orchestrator
```

### Pipeline (13 steps)

```
User Message → Language Detection → Profile Load → Context Retrieval
→ Adaptation Analysis → Tone Analysis → Privacy Sanitization
→ Prompt Building → LLM Generation → Post-Processing
→ Memory Update → Knowledge Graph Update → Badge Check → Response
```

---

## Supported Languages

| Language | Script | Greeting |
|----------|--------|----------|
| English | Latin | Hello! |
| Thai | Thai | สวัสดีครับ! |
| Hindi | Devanagari | नमस्ते! |
| Spanish | Latin | ¡Hola! |
| Chinese | CJK | 你好! |
| Arabic | Arabic | مرحبا! |
| Portuguese | Latin | Olá! |
| Swahili | Latin | Habari! |
| Indonesian | Latin | Halo! |
| French | Latin | Bonjour! |

Language is auto-detected from user input using Unicode range analysis and trigram frequency profiling.

---

## Learning Path

A 7-level curriculum that takes users from zero to building AI tools:

| Level | Name | What You'll Learn |
|-------|------|-------------------|
| 1 | **Hello AI** | What is AI? First conversation |
| 2 | **Talk to AI** | Prompting, context, common mistakes |
| 3 | **AI in Daily Life** | Practical applications for work, learning, creativity |
| 4 | **How AI Thinks** | Tokens, training data, bias, hallucinations, ethics |
| 5 | **Code with AI** | Python basics, AI-assisted coding |
| 6 | **Build with AI** | Web apps, APIs, testing, deployment |
| 7 | **Create AI Tools** | Prompt engineering, LangChain, RAG, open source |

Each level includes lessons, exercises, and quizzes with LLM-graded open questions.

### Skill Assessment

5-category adaptive assessment (10 questions):

| Category | Weight |
|----------|--------|
| AI Awareness | 30% |
| Prompt Skills | 25% |
| Digital Literacy | 20% |
| Coding Ability | 15% |
| Domain Knowledge | 10% |

### Achievement Badges

| Badge | Trigger |
|-------|---------|
| 🤝 First Contact | Complete first conversation |
| 🌍 Polyglot | Use WISDOM in 2+ languages |
| 💡 Curious Mind | Ask 50 questions |
| ⬆️ Level Up | Complete any learning module |
| ⭐ Perfect Score | Get 100% on a quiz |
| 🔥 Streak Master | Use WISDOM 7 days in a row |
| 💻 Code Rookie | Write first code with WISDOM |
| 🔨 Builder | Complete Level 6 project |
| 🚀 Creator | Complete Level 7 project |
| ❤️ Helper | Contribute to community knowledge |
| 🏁 Pioneer | Be among first 1000 users |

---

## Chat Modes

WISDOM auto-detects the best mode from your message, or you can set it manually:

| Mode | Description |
|------|-------------|
| 💬 **Free Chat** | Natural conversation |
| 📚 **Teacher** | Step-by-step explanations with analogies |
| 🔍 **Researcher** | Thorough, source-cited research |
| ❓ **Quiz Master** | Interactive quizzes with feedback |
| 💻 **Code Helper** | Write, explain, and debug code |

---

## REST API

### Endpoints

```
POST   /api/v1/chat                  # Send message, get response
POST   /api/v1/chat/stream           # SSE streaming response

POST   /api/v1/profile               # Create user profile
GET    /api/v1/profile/{user_id}     # Get profile
PUT    /api/v1/profile/{user_id}     # Update profile
DELETE /api/v1/profile/{user_id}     # Delete profile & data

GET    /api/v1/learning-path/{user_id}  # Personalized learning path
GET    /api/v1/progress/{user_id}       # Learning progress
POST   /api/v1/assessment/start         # Start skill assessment

GET    /api/v1/profile/{user_id}/export  # Export all user data (GDPR)

POST   /api/v1/feedback              # Submit feedback (1-5 stars)
GET    /api/v1/feedback/stats         # Feedback statistics

GET    /api/v1/health                 # System health check
```

### Example

```bash
# Chat
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user1", "message": "What is AI?"}'

# Create profile
curl -X POST http://localhost:8000/api/v1/profile \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user1", "name": "Somchai", "language": "th"}'

# Streaming (SSE)
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user1", "message": "Explain machine learning"}'
```

Rate limit: 60 requests/minute per IP.

---

## Privacy

WISDOM is privacy-first:

- **Local-first**: Ollama runs entirely on your machine. No data leaves your device.
- **PII sanitization**: Emails, phone numbers, credit cards, SSNs, Thai national IDs, and IP addresses are automatically masked before sending to cloud LLMs.
- **Federated learning**: Community insights are opt-in only, anonymized with differential privacy, and users can preview exactly what would be shared.
- **Content moderation**: Community Q&A includes voting and reporting (3+ reports auto-hides content).
- **GDPR compliance**: Export and delete all user data via API or code.

```python
w = Wisdom()
w.export_user_data("user1")   # Export all data
w.delete_user_data("user1")   # Right to be forgotten
```

---

## Project Structure

```
Prometheus-Wisdom/
├── wisdom/
│   ├── __init__.py              # Wisdom class entry point
│   ├── core/
│   │   ├── config.py            # Environment configuration
│   │   ├── constants.py         # Languages, levels, badges
│   │   ├── llm_provider.py      # Ollama + Gemini dual provider
│   │   └── orchestrator.py      # 13-step conversation pipeline
│   ├── brain/
│   │   ├── user_profile.py      # User profile management (SQLite)
│   │   ├── memory_manager.py    # Short-term + long-term memory
│   │   ├── knowledge_graph.py   # Neo4j / SQLite knowledge graph
│   │   └── embeddings.py        # ChromaDB vector embeddings
│   ├── voice/
│   │   ├── language_detect.py   # 10-language auto-detection
│   │   ├── chat_engine.py       # LangChain streaming chat
│   │   ├── tone_adapter.py      # Emotion & complexity adaptation
│   │   └── prompt_templates.py  # Mode & language prompts
│   ├── heart/
│   │   ├── privacy_manager.py   # PII detection & sanitization
│   │   ├── federated_core.py    # Anonymous federated learning
│   │   ├── community_knowledge.py  # Community Q&A with voting
│   │   └── feedback_loop.py     # Feedback & improvement pipeline
│   ├── soul/
│   │   ├── adaptation_engine.py # Personalization engine
│   │   ├── skill_assessor.py    # 5-category adaptive assessment
│   │   ├── learning_path.py     # 7-level curriculum
│   │   └── goal_tracker.py      # Goals, milestones, badges
│   ├── body/
│   │   ├── app.py               # Streamlit web application
│   │   ├── api.py               # FastAPI REST API
│   │   └── components/
│   │       ├── chat.py          # Chat UI with streaming + voice input
│   │       ├── dashboard.py     # Progress dashboard
│   │       ├── code_playground.py # In-browser Python code editor
│   │       └── community.py     # Community Q&A browser
│   ├── plugins/                 # Plugin system
│   │   ├── __init__.py          # Plugin interface + PluginManager
│   │   └── example_plugin.py   # Example plugin
│   └── tests/                   # 171 unit tests
│       ├── test_brain.py
│       ├── test_voice.py
│       ├── test_heart.py
│       ├── test_soul.py
│       ├── test_body.py
│       └── test_plugins.py
├── WISDOM_DOCS/                 # Architecture & design docs
├── Procfile                     # Deployment config
├── Makefile                     # Dev commands
├── requirements.txt
├── setup.py
├── .env.example
└── LICENSE                      # MIT
```

---

## Testing

```bash
make test
```

171 tests across all modules:

| Module | Tests | Covers |
|--------|-------|--------|
| Brain | 29 | Profiles, memory, knowledge graph, embeddings, SQLite persistence |
| Voice | 26 | Language detection, prompts, tone, chat engine, voice input |
| Heart | 36 | Privacy, federated learning, community wiring, feedback |
| Soul | 43 | Adaptation, assessment, learning, goals, badges, progress tracking |
| Body | 20 | API endpoints, profiles, feedback, learning, export, code playground, offline mode |
| Plugins | 17 | Plugin system, hooks, discovery, enable/disable |

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| LLM (local) | Ollama + LLaMA 3 |
| LLM (cloud) | Google Gemini 2.0 Flash |
| Framework | LangChain |
| Vector DB | ChromaDB |
| Graph DB | Neo4j Aura (SQLite fallback) |
| Database | SQLite |
| Web UI | Streamlit |
| REST API | FastAPI |
| Charts | Plotly |
| Testing | pytest |

---

## Configuration

Copy `.env.example` to `.env` and configure:

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | — | Gemini API key (optional if using Ollama) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3:latest` | Ollama model name |
| `WISDOM_DB_PATH` | `./data/wisdom.db` | SQLite database path |
| `CHROMA_DB_PATH` | `./data/chroma` | ChromaDB storage path |
| `MAX_MEMORY_MESSAGES` | `20` | Conversation history limit |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## License

MIT License — Copyright 2026 Project PROMETHEUS

Built with ♥ for humanity.
