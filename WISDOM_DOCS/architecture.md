# Architecture — PROMETHEUS WISDOM
## System Architecture Document v1.0

---

## 1. Architecture Overview

PROMETHEUS WISDOM follows a **modular monolith** architecture with 5 core subsystems inspired by the human body metaphor. Each module is independently testable and replaceable, but deployed as a single application for simplicity.

```
┌─────────────────────────────────────────────────────────────────┐
│                     PROMETHEUS WISDOM v1.0                       │
│                  "AI Companion for Humanity"                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │    VOICE    │   │    BRAIN    │   │    SOUL     │           │
│  │  NLP Engine │◄─►│  Knowledge  │◄─►│  Adaptive   │           │
│  │  Chat I/O   │   │  Graph +    │   │  Engine     │           │
│  │  Multilang  │   │  Memory     │   │  Learning   │           │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘           │
│         │                 │                  │                   │
│         ▼                 ▼                  ▼                   │
│  ┌────────────────────────────────────────────────────┐         │
│  │                   CORE ENGINE                       │         │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │         │
│  │  │   LLM    │  │  Config  │  │  Orchestrator    │ │         │
│  │  │ Provider │  │  Manager │  │  (Conversation   │ │         │
│  │  │ Ollama/  │  │          │  │   Flow Control)  │ │         │
│  │  │ Gemini   │  │          │  │                  │ │         │
│  │  └──────────┘  └──────────┘  └──────────────────┘ │         │
│  └────────────────────────────────────────────────────┘         │
│         │                 │                  │                   │
│         ▼                 ▼                  ▼                   │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │    HEART    │   │    BODY     │   │   STORAGE   │           │
│  │  Privacy    │   │  Streamlit  │   │  SQLite     │           │
│  │  Federated  │   │  FastAPI    │   │  ChromaDB   │           │
│  │  Community  │   │  Web UI     │   │  Neo4j      │           │
│  └─────────────┘   └─────────────┘   └─────────────┘           │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  LLM Layer: Ollama (local) ──fallback──► Gemini 2.0 Flash      │
│  Embeddings: nomic-embed-text (local) ──fallback──► Gemini     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Design Principles

| Principle | Rule | Reason |
|-----------|------|--------|
| **Local-First** | Default to local storage/compute, cloud is fallback | 84% of users have unreliable internet |
| **Zero-Config** | Must work with `pip install && streamlit run` | Target users are non-technical |
| **Modular** | Each subsystem has clean interfaces | Easy to test, replace, contribute |
| **Progressive** | Start simple, unlock complexity as user grows | Don't overwhelm beginners |
| **Privacy-by-Design** | No PII leaves the device by default | Trust is earned, not assumed |
| **Fail-Graceful** | If a component fails, others keep working | Reliability for poor infrastructure |

---

## 3. Subsystem Details

### 3.1 CORE — Engine & Orchestration

The Core is the central nervous system. It manages LLM connections, configuration, and the conversation orchestration flow.

```
wisdom/core/
├── llm_provider.py      # LLM abstraction layer
├── config.py            # Configuration management
├── constants.py         # Application constants
└── orchestrator.py      # Conversation flow controller
```

#### 3.1.1 LLM Provider — Dual-Path Architecture

```
                    ┌──────────────────┐
                    │   get_llm()      │
                    │   get_embeddings()│
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  Is Ollama       │
                    │  running?        │
                    └───┬──────────┬───┘
                   YES  │          │  NO
                        ▼          ▼
               ┌──────────┐  ┌──────────┐
               │  Ollama   │  │  Gemini  │
               │  Llama3   │  │  2.0     │
               │  Local    │  │  Flash   │
               │  Free     │  │  Free    │
               └──────────┘  └──────────┘
```

**LLM Provider Contract:**
```python
class LLMProvider:
    def get_llm(self) -> BaseChatModel:
        """Returns LangChain ChatModel (Ollama or Gemini)"""

    def get_embeddings(self) -> Embeddings:
        """Returns embedding model (nomic-embed or Gemini)"""

    def is_local(self) -> bool:
        """True if using Ollama (local), False if cloud"""

    def health_check(self) -> dict:
        """Returns provider status and latency"""
```

**Supported Models:**
| Provider | Model | Parameters | Speed | Use Case |
|----------|-------|-----------|-------|----------|
| Ollama | llama3:8b | 8B | ~15 tok/s | Default local |
| Ollama | phi3:mini | 3.8B | ~25 tok/s | Low-spec devices |
| Ollama | gemma2:2b | 2B | ~35 tok/s | Very low-spec |
| Gemini | gemini-2.0-flash | - | ~80 tok/s | Cloud fallback |
| Ollama | nomic-embed-text | 137M | ~100ms | Local embeddings |
| Gemini | text-embedding-004 | - | ~50ms | Cloud embeddings |

#### 3.1.2 Orchestrator — Conversation Flow

```
User Message
    │
    ▼
[1. Language Detection] ──► voice/language_detect.py
    │
    ▼
[2. Context Retrieval] ──► brain/memory_manager.py
    │                       brain/knowledge_graph.py
    ▼
[3. Profile Loading] ──► brain/user_profile.py
    │
    ▼
[4. Prompt Adaptation] ──► soul/adaptation_engine.py
    │                       voice/tone_adapter.py
    │                       voice/prompt_templates.py
    ▼
[5. LLM Generation] ──► core/llm_provider.py
    │                    (streaming response)
    ▼
[6. Response Post-Process] ──► heart/privacy_manager.py
    │
    ▼
[7. Memory Update] ──► brain/memory_manager.py
    │                   brain/knowledge_graph.py
    │                   soul/goal_tracker.py
    ▼
[8. Display to User] ──► body/components/chat.py
```

---

### 3.2 BRAIN — Knowledge & Memory

The Brain handles all persistent knowledge about the user and their learning journey.

```
wisdom/brain/
├── knowledge_graph.py   # Graph database operations
├── memory_manager.py    # Short-term + long-term memory
├── user_profile.py      # User data management
└── embeddings.py        # Vector embedding operations
```

#### 3.2.1 Memory Architecture

```
┌─────────────────────────────────────────────────┐
│                   MEMORY SYSTEM                  │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────────┐  ┌──────────────────────┐ │
│  │  SHORT-TERM       │  │  LONG-TERM           │ │
│  │  (In-Memory)      │  │  (Persisted)         │ │
│  │                   │  │                      │ │
│  │  • Last 20 msgs   │  │  • User profile      │ │
│  │  • Current topic   │  │  • Key facts         │ │
│  │  • Session state   │  │  • Learning progress │ │
│  │  • Temp context    │  │  • Conversation      │ │
│  │                   │  │    summaries          │ │
│  │  Storage: List     │  │  Storage: SQLite +   │ │
│  │                   │  │  ChromaDB vectors     │ │
│  └──────────────────┘  └──────────────────────┘ │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │  KNOWLEDGE GRAPH (Relational Memory)     │   │
│  │                                           │   │
│  │  (User)──LEARNED──►(Topic: AI Basics)    │   │
│  │    │                    │                 │   │
│  │    ├──INTERESTED_IN──►(Goal: Learn Code) │   │
│  │    │                    │                 │   │
│  │    ├──SPEAKS──►(Language: Thai)           │   │
│  │    │                                      │   │
│  │    └──COMPLETED──►(Module: Level 1)      │   │
│  │                                           │   │
│  │  Storage: Neo4j Aura (free) OR SQLite    │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
└─────────────────────────────────────────────────┘
```

#### 3.2.2 Knowledge Graph Schema

**Nodes:**
```
(:User {id, name, language, skill_level, created_at, last_seen})
(:Topic {id, name, category, difficulty, description})
(:Module {id, name, level, objectives, content_hash})
(:Goal {id, description, target_date, status})
(:Conversation {id, summary, timestamp, sentiment})
```

**Relationships:**
```
(User)-[:SPEAKS {fluency}]->(Language)
(User)-[:LEARNED {score, date}]->(Topic)
(User)-[:COMPLETED {score, date}]->(Module)
(User)-[:HAS_GOAL {priority}]->(Goal)
(User)-[:HAD_CONVERSATION {date}]->(Conversation)
(Topic)-[:PREREQUISITE_OF]->(Topic)
(Module)-[:CONTAINS]->(Topic)
(Goal)-[:REQUIRES]->(Module)
```

#### 3.2.3 RAG Pipeline (Retrieval-Augmented Generation)

```
User Query: "How do I make my crops grow better?"
    │
    ▼
[Embed Query] ──► nomic-embed-text ──► vector (768-dim)
    │
    ▼
[Search ChromaDB] ──► Top 5 similar past conversations
    │
    ▼
[Search Knowledge Graph] ──► User's known topics, skill level
    │
    ▼
[Build Context] ──► Combine: relevant memory + user profile + learning state
    │
    ▼
[Inject into Prompt] ──► System prompt + context + user query
    │
    ▼
[LLM generates personalized response]
```

---

### 3.3 VOICE — Communication Layer

The Voice handles all human-AI communication including language, tone, and complexity.

```
wisdom/voice/
├── chat_engine.py       # Core conversation with LLM
├── language_detect.py   # Auto language detection
├── prompt_templates.py  # Multilingual system prompts
└── tone_adapter.py      # Complexity/formality adaptation
```

#### 3.3.1 Language Detection Flow

```
User Message
    │
    ▼
[Character Set Analysis]
    │ Thai: ก-ฮ    Hindi: अ-ह    Arabic: ع-ي
    │ CJK: 一-龥    Latin: a-z
    ▼
[LLM Confirmation] ──► "What language is this message?"
    │
    ▼
[Store in Profile] ──► user.language = "th"
    │
    ▼
[Load Language Template] ──► prompt_templates.THAI
```

**Supported Languages (Phase 1):**
| Code | Language | Script | Population |
|------|----------|--------|-----------|
| en | English | Latin | 1.5B |
| th | Thai | Thai | 70M |
| hi | Hindi | Devanagari | 600M |
| es | Spanish | Latin | 550M |
| zh | Chinese | CJK | 1.1B |
| ar | Arabic | Arabic | 400M |
| pt | Portuguese | Latin | 260M |
| sw | Swahili | Latin | 100M |
| id | Indonesian | Latin | 200M |
| fr | French | Latin | 300M |

#### 3.3.2 Prompt Template Architecture

```python
WISDOM_SYSTEM_PROMPT = """
You are WISDOM — a personal AI companion created by Project PROMETHEUS.

Your mission: Help humans who have NEVER used AI before. You are their
first AI friend. Be warm, patient, and encouraging.

About the user:
- Name: {user_name}
- Language: {user_language} (ALWAYS respond in this language)
- Skill Level: {skill_level}/10
- Current Goal: {current_goal}
- Learning Progress: {learning_progress}

Context from memory:
{retrieved_context}

Rules:
1. ALWAYS respond in the user's language ({user_language})
2. Adapt complexity to skill level {skill_level}:
   - Level 1-3: Use simple words, analogies, real-life examples
   - Level 4-6: Include technical terms with explanations
   - Level 7-10: Full technical depth, code examples
3. Be encouraging. Celebrate progress. Never make the user feel stupid.
4. If the user seems confused, simplify. If bored, increase depth.
5. Remember: you may be this person's FIRST interaction with AI.
   Make it magical.
"""
```

#### 3.3.3 Tone Adaptation Matrix

| User Signal | Detected State | WISDOM Response Style |
|-------------|---------------|----------------------|
| Short answers, "?" | Confused | Simplify, use analogies, ask clarifying Qs |
| "I don't understand" | Lost | Back up, re-explain differently, use visuals |
| Long detailed questions | Engaged | Match depth, provide thorough answers |
| "Wow", "Cool" | Excited | Encourage, suggest next steps, celebrate |
| Silence (long pause) | Disengaged | Gently prompt, change topic, ask about goals |
| Code snippets | Advanced | Technical mode, show code examples |
| Typos, broken grammar | Beginner | Don't correct, understand intent, be patient |

---

### 3.4 SOUL — Adaptation & Learning

The Soul personalizes WISDOM to each individual user.

```
wisdom/soul/
├── adaptation_engine.py # Core adaptation logic
├── skill_assessor.py    # User level assessment
├── learning_path.py     # Personalized curriculum
└── goal_tracker.py      # Progress & milestones
```

#### 3.4.1 Skill Assessment System

```
Assessment Categories (each scored 0-10):

1. AI Awareness     — Do they know what AI is?
2. Prompt Skills    — Can they formulate good questions?
3. Digital Literacy — Comfortable with technology?
4. Coding Ability   — Any programming experience?
5. Domain Knowledge — Expert in their own field?

Composite Score = weighted average
    AI Awareness: 30%
    Prompt Skills: 25%
    Digital Literacy: 20%
    Coding Ability: 15%
    Domain Knowledge: 10%
```

#### 3.4.2 Learning Path — 7 Levels

```
Level 1: "Hello AI" (Grey → Light Green)
├── What is AI? (with real-life examples)
├── AI is NOT magic (setting expectations)
├── Your first conversation with AI
└── Quiz: Basic AI concepts

Level 2: "Talk to AI" (Learning to Prompt)
├── How to ask good questions
├── The art of context and specificity
├── Common mistakes and how to fix them
└── Practice: 10 prompt challenges

Level 3: "AI in Daily Life" (Practical Applications)
├── AI for learning and education
├── AI for work and productivity
├── AI for creativity and fun
└── Project: Solve a real problem with AI

Level 4: "How AI Thinks" (Understanding)
├── How language models work (simple explanation)
├── Training data and bias
├── Limitations and hallucinations
└── Ethics and responsible use

Level 5: "Code with AI" (Introduction)
├── What is programming? (with WISDOM help)
├── Your first Python program
├── Using AI to write and debug code
└── Project: Build a simple calculator

Level 6: "Build with AI" (Application)
├── Building a web app with AI assistance
├── Working with APIs and data
├── Testing and debugging with AI
└── Project: Build a personal tool

Level 7: "Create AI Tools" (Mastery)
├── Understanding LLMs and prompt engineering
├── Building AI-powered applications
├── Contributing to open source
└── Project: Build and deploy your own AI tool
```

#### 3.4.3 Adaptive Difficulty Algorithm

```python
def adapt_difficulty(user_profile, conversation_history):
    """
    Adjusts difficulty based on user performance signals.

    Signals that increase difficulty:
    - Correct quiz answers
    - Asking deeper follow-up questions
    - Using technical terminology correctly
    - Completing modules quickly

    Signals that decrease difficulty:
    - Incorrect answers
    - "I don't understand" messages
    - Long pauses between messages
    - Requesting simpler explanations
    - Abandoning modules

    Returns: adjusted_level (float, 0.0-10.0)
    """
```

---

### 3.5 HEART — Privacy & Community

The Heart protects user privacy and enables collective learning.

```
wisdom/heart/
├── privacy_manager.py      # Data sanitization
├── federated_core.py       # Federated learning
├── community_knowledge.py  # Shared knowledge base
└── feedback_loop.py        # User feedback processing
```

#### 3.5.1 Privacy Architecture

```
┌──────────────────────────────────────────────────┐
│              PRIVACY LAYERS                       │
├──────────────────────────────────────────────────┤
│                                                   │
│  Layer 1: Local Storage (Default)                │
│  ├── All user data in local SQLite               │
│  ├── Embeddings in local ChromaDB                │
│  └── Nothing leaves the device                   │
│                                                   │
│  Layer 2: Sanitization (Before LLM)              │
│  ├── Strip PII (names, emails, phones)           │
│  ├── Anonymize location data                     │
│  └── Remove sensitive patterns (CC, SSN)         │
│                                                   │
│  Layer 3: Federated Learning (Opt-in)            │
│  ├── Only aggregated, anonymous insights shared  │
│  ├── Differential privacy noise added            │
│  └── User can see exactly what is shared         │
│                                                   │
│  Layer 4: Community Knowledge (Opt-in)           │
│  ├── User can share Q&A pairs anonymously        │
│  ├── Community votes on quality                  │
│  └── No personal context attached                │
│                                                   │
└──────────────────────────────────────────────────┘
```

#### 3.5.2 Data Flow — What Goes Where

| Data Type | Stored Where | Shared? | With LLM? |
|-----------|-------------|---------|-----------|
| User name | Local SQLite | Never | As "{name}" in prompt |
| Conversation history | Local SQLite + ChromaDB | Never | Last 20 msgs as context |
| Skill scores | Local SQLite | Anonymized aggregate only | In system prompt |
| Learning progress | Local SQLite | Anonymized aggregate only | In system prompt |
| User feedback | Local SQLite | Anonymous rating only | Never |
| Community Q&A | Shared DB (opt-in) | Yes, anonymous | As RAG context |

---

### 3.6 BODY — Interface Layer

The Body provides the user interface (web and API).

```
wisdom/body/
├── app.py                 # Streamlit main application
├── api.py                 # FastAPI REST API
└── components/
    ├── chat.py            # Chat UI component
    └── dashboard.py       # Progress dashboard
```

#### 3.6.1 Streamlit UI Layout

```
┌─────────────────────────────────────────────────┐
│  PROMETHEUS WISDOM — AI Companion for Humanity   │
├──────────┬──────────────────────────────────────┤
│ SIDEBAR  │  MAIN AREA                           │
│          │                                       │
│ [Avatar] │  ┌─────────────────────────────────┐ │
│ Name     │  │ WISDOM: สวัสดีครับ! ผมชื่อ WISDOM │ │
│ Level: 3 │  │ ผมจะเป็นเพื่อนคู่คิดของคุณ        │ │
│          │  └─────────────────────────────────┘ │
│ Progress │                                       │
│ ████░░ 60%│  ┌─────────────────────────────────┐ │
│          │  │ You: สอนเรื่อง AI ให้หน่อย         │ │
│ ───────  │  └─────────────────────────────────┘ │
│ Quick:   │                                       │
│ [Teach]  │  ┌─────────────────────────────────┐ │
│ [Quiz]   │  │ WISDOM: ได้เลยครับ! ลองนึกภาพ...  │ │
│ [Code]   │  │ AI เหมือนเด็กที่เรียนรู้จาก         │ │
│ [Goals]  │  │ ตัวอย่างนับล้าน...               │ │
│          │  └─────────────────────────────────┘ │
│ ───────  │                                       │
│ Settings │  ┌─────────────────────────────────┐ │
│ Language  │  │ [Type your message here...]      │ │
│ Theme    │  │                        [Send ►]  │ │
│          │  └─────────────────────────────────┘ │
├──────────┴──────────────────────────────────────┤
│  Open Source | GitHub | Made with ♥ for Humanity │
└─────────────────────────────────────────────────┘
```

#### 3.6.2 REST API Endpoints

```
Base URL: http://localhost:8000/api/v1

POST   /chat
       Body: { "user_id": "abc", "message": "Hello" }
       Response: { "response": "สวัสดี!", "language": "th" }

GET    /profile/{user_id}
       Response: { "name": "...", "level": 3, "language": "th" }

PUT    /profile/{user_id}
       Body: { "language": "en", "difficulty": 5 }

GET    /progress/{user_id}
       Response: { "level": 3, "modules_completed": [...], "score": 65 }

GET    /learning-path/{user_id}
       Response: { "current_level": 3, "next_module": {...}, "progress": 0.6 }

POST   /feedback
       Body: { "user_id": "abc", "rating": 5, "comment": "Great!" }

GET    /health
       Response: { "status": "ok", "llm": "ollama", "uptime": 3600 }
```

---

## 4. Data Architecture

### 4.1 Storage Strategy

```
┌──────────────────────────────────────┐
│          STORAGE LAYERS              │
├──────────────────────────────────────┤
│                                      │
│  PRIMARY: SQLite (wisdom.db)         │
│  ├── users table                     │
│  ├── conversations table             │
│  ├── learning_progress table         │
│  ├── goals table                     │
│  └── feedback table                  │
│                                      │
│  VECTORS: ChromaDB (local)           │
│  ├── conversation_embeddings         │
│  ├── knowledge_embeddings            │
│  └── community_embeddings            │
│                                      │
│  GRAPH: Neo4j Aura (optional)        │
│  ├── User-Topic relationships        │
│  ├── Learning path graph             │
│  └── Knowledge connections           │
│                                      │
│  FALLBACK: SQLite for graph          │
│  ├── nodes table (id, type, data)    │
│  ├── edges table (from, to, type)    │
│  └── Simulates graph operations      │
│                                      │
└──────────────────────────────────────┘
```

### 4.2 SQLite Schema

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    name TEXT,
    language TEXT DEFAULT 'en',
    skill_level REAL DEFAULT 0.0,
    interests TEXT,  -- JSON array
    goals TEXT,      -- JSON array
    preferences TEXT, -- JSON object
    created_at TEXT NOT NULL,
    last_seen TEXT NOT NULL
);

CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'user' or 'wisdom'
    content TEXT NOT NULL,
    language TEXT,
    sentiment REAL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE learning_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    module_id TEXT NOT NULL,
    level INTEGER NOT NULL,
    score REAL,
    completed BOOLEAN DEFAULT FALSE,
    started_at TEXT,
    completed_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    description TEXT NOT NULL,
    milestones TEXT,  -- JSON array
    progress REAL DEFAULT 0.0,
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    rating INTEGER,
    comment TEXT,
    context TEXT,
    created_at TEXT NOT NULL
);
```

---

## 5. Deployment Architecture

### 5.1 Streamlit Cloud (Primary — Free)

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│   GitHub     │────►│  Streamlit Cloud │────►│   Users     │
│   (source)   │     │  (auto-deploy)   │     │  (browser)  │
└─────────────┘     └────────┬─────────┘     └─────────────┘
                             │
                    ┌────────▼─────────┐
                    │  Gemini API      │
                    │  (LLM backend)   │
                    │  Free tier       │
                    └──────────────────┘
```

### 5.2 Self-Hosted (Advanced — Full Privacy)

```
┌──────────────────────────────────────────────┐
│              User's Machine                   │
│                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Streamlit │  │  Ollama   │  │ SQLite   │  │
│  │ :8501     │  │  :11434   │  │ wisdom.db│  │
│  │ (UI)      │  │  (LLM)   │  │ (data)   │  │
│  └──────────┘  └──────────┘  └──────────┘  │
│                                               │
│  100% offline, 100% private, 100% free       │
└──────────────────────────────────────────────┘
```

---

## 6. Error Handling & Resilience

| Failure | Detection | Recovery |
|---------|----------|----------|
| Ollama not running | Connection timeout | Auto-switch to Gemini |
| Gemini rate limit | HTTP 429 | Queue + retry with backoff |
| Both LLMs down | Both fail | Show cached responses + offline message |
| Neo4j unavailable | Connection error | Fall back to SQLite graph |
| ChromaDB corrupt | Read error | Rebuild from conversation logs |
| SQLite locked | Busy timeout | Retry with exponential backoff |
| Network offline | DNS/HTTP fail | Switch to full offline mode |

---

## 7. Testing Strategy

| Layer | Test Type | Framework | Target |
|-------|-----------|-----------|--------|
| Core | Unit tests | pytest | 90% coverage |
| Brain | Unit + Integration | pytest + fixtures | All CRUD operations |
| Voice | Unit + Mock LLM | pytest + unittest.mock | Prompt generation, detection |
| Soul | Unit tests | pytest | Adaptation logic, paths |
| Heart | Unit tests | pytest | Privacy sanitization |
| Body | Integration | pytest + httpx | API endpoints |
| E2E | End-to-end | pytest + Streamlit testing | Full conversation flow |

---

*Architecture designed for the 6.8 billion. Built with love by Project PROMETHEUS.*
