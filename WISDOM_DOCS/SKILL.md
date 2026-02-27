# SKILL.md — PROMETHEUS WISDOM
## AI Companion Skill Tree & Capability Map v1.0

---

## 1. WISDOM Core Skills (What WISDOM Can Do)

### Skill Category Map

```
PROMETHEUS WISDOM — Skill Tree
│
├── COMMUNICATION (Voice Module)
│   ├── SK01: Multilingual Conversation
│   ├── SK02: Language Auto-Detection
│   ├── SK03: Tone & Complexity Adaptation
│   ├── SK04: Emotional Intelligence
│   └── SK05: Voice Input Processing
│
├── MEMORY (Brain Module)
│   ├── SK06: Short-term Conversation Memory
│   ├── SK07: Long-term Fact Recall (RAG)
│   ├── SK08: Personal Knowledge Graph
│   ├── SK09: Context-Aware Retrieval
│   └── SK10: User Preference Learning
│
├── TEACHING (Soul Module)
│   ├── SK11: Skill Assessment
│   ├── SK12: Adaptive Curriculum Generation
│   ├── SK13: Interactive Quizzing
│   ├── SK14: Progress Tracking
│   ├── SK15: Goal Setting & Milestones
│   └── SK16: Encouragement & Motivation
│
├── MODES (Core Module)
│   ├── SK17: Teacher Mode
│   ├── SK18: Researcher Mode
│   ├── SK19: Quiz Master Mode
│   ├── SK20: Code Helper Mode
│   └── SK21: Free Chat Mode
│
├── PRIVACY (Heart Module)
│   ├── SK22: PII Sanitization
│   ├── SK23: Local-First Data Storage
│   ├── SK24: Federated Learning
│   └── SK25: Data Export/Delete (GDPR)
│
└── INTEGRATION (Body Module)
    ├── SK26: Web Chat Interface
    ├── SK27: REST API
    ├── SK28: Dashboard & Visualization
    └── SK29: Plugin System
```

---

## 2. Skill Specifications

### COMMUNICATION SKILLS

#### SK01: Multilingual Conversation
```yaml
id: SK01
name: Multilingual Conversation
module: voice/chat_engine.py
priority: P0
phase: 1

description: >
  WISDOM communicates fluently in the user's language.
  Not just translation — culturally appropriate responses
  with local idioms and natural phrasing.

languages:
  tier_1: [English, Thai, Hindi, Spanish, Chinese]
  tier_2: [Arabic, Portuguese, Swahili, Indonesian, French]
  tier_3: [Japanese, Korean, Vietnamese, Turkish, German]

implementation:
  - LLM handles language generation natively
  - System prompt forces response in detected language
  - Cultural context hints in prompt (e.g., Thai politeness particles)
  - No external translation API needed

example:
  user: "AI คืออะไร"
  wisdom: "AI หรือปัญญาประดิษฐ์ ก็เหมือนกับสมองเทียมที่เรียนรู้จากข้อมูลครับ
           ลองนึกภาพว่ามีผู้ช่วยที่อ่านหนังสือมาล้านเล่ม แล้วสามารถตอบ
           คำถามเราได้ทุกเรื่อง นั่นแหละครับคือ AI"
```

#### SK02: Language Auto-Detection
```yaml
id: SK02
name: Language Auto-Detection
module: voice/language_detect.py
priority: P0
phase: 1

description: >
  Detect user's language from the first message.
  Use character set analysis + LLM confirmation.
  Store preference and allow manual override.

detection_methods:
  - Unicode range analysis (Thai: U+0E00-U+0E7F, etc.)
  - Trigram frequency analysis
  - LLM-based confirmation for ambiguous cases

accuracy_target: ">95% for messages with 5+ words"

output:
  language_code: "th"
  language_name: "Thai"
  confidence: 0.98
  script: "Thai"
```

#### SK03: Tone & Complexity Adaptation
```yaml
id: SK03
name: Tone & Complexity Adaptation
module: voice/tone_adapter.py
priority: P1
phase: 2

description: >
  Dynamically adjust WISDOM's communication style based on
  real-time signals from the user's messages.

complexity_levels:
  level_1_basic:
    vocabulary: "everyday words only"
    sentences: "short, simple"
    analogies: "real-life, familiar"
    example: "AI is like a very smart helper that can answer questions"

  level_2_intermediate:
    vocabulary: "some technical terms with explanations"
    sentences: "moderate complexity"
    analogies: "mix of familiar and abstract"
    example: "Large Language Models process text using attention mechanisms
              — think of it like reading a book and highlighting the important parts"

  level_3_advanced:
    vocabulary: "full technical terminology"
    sentences: "complex, nuanced"
    analogies: "domain-specific"
    example: "Transformer architectures use multi-head self-attention
              with O(n²) complexity relative to sequence length"

adaptation_signals:
  increase_complexity:
    - User asks technical follow-up questions
    - User uses technical terminology correctly
    - User completes quizzes with high scores
    - User requests "more detail"

  decrease_complexity:
    - User says "I don't understand"
    - User gives very short confused responses
    - User asks to "explain simpler"
    - Long pauses between messages
    - Quiz scores below 50%
```

#### SK04: Emotional Intelligence
```yaml
id: SK04
name: Emotional Intelligence
module: voice/tone_adapter.py
priority: P2
phase: 2

description: >
  Detect user's emotional state from message patterns
  and respond with appropriate empathy and support.

emotional_states:
  confused:
    signals: ["?", "I don't get it", short responses, repeated questions]
    response: "Simplify, use different analogy, offer step back"
  frustrated:
    signals: ["this is stupid", "doesn't work", aggressive punctuation]
    response: "Acknowledge difficulty, offer help, be extra patient"
  excited:
    signals: ["wow!", "cool!", "amazing!", exclamation marks]
    response: "Match enthusiasm, suggest next challenge"
  bored:
    signals: ["ok", "sure", minimal engagement, long delays]
    response: "Change topic, offer something interactive, ask about interests"
  proud:
    signals: ["I did it!", "it works!", sharing accomplishments]
    response: "Celebrate, give badge, suggest next goal"
```

#### SK05: Voice Input Processing
```yaml
id: SK05
name: Voice Input Processing
module: voice/chat_engine.py
priority: P3
phase: 4

description: >
  Accept voice input via Web Speech API or Whisper.
  Enables interaction for users who can't type easily.

implementation:
  browser_api:
    method: "Web Speech API (built into Chrome/Edge)"
    cost: "Free"
    languages: "All major languages supported"

  whisper_api:
    method: "OpenAI Whisper (local or API)"
    cost: "Free (local) or pay-per-use"
    accuracy: "Higher, especially for accents"

  flow:
    1: "User presses microphone button"
    2: "Browser captures audio"
    3: "Speech-to-text converts to text"
    4: "Text displayed for user confirmation"
    5: "User confirms → sent to WISDOM"
```

---

### MEMORY SKILLS

#### SK06: Short-term Conversation Memory
```yaml
id: SK06
name: Short-term Conversation Memory
module: brain/memory_manager.py
priority: P0
phase: 1

description: >
  Maintain last 20 messages in current session.
  Enables coherent multi-turn conversations.

implementation:
  storage: "In-memory Python list"
  capacity: "20 messages (user + wisdom)"
  overflow: "Summarize oldest 5 messages, keep summary + newest 15"
  token_management: "Auto-trim to stay within LLM context window"

context_window_budget:
  system_prompt: "~500 tokens"
  retrieved_memory: "~500 tokens"
  conversation_history: "~2000 tokens"
  user_query: "~200 tokens"
  response_space: "~800 tokens"
  total: "~4000 tokens (fits in any model)"
```

#### SK07: Long-term Fact Recall (RAG)
```yaml
id: SK07
name: Long-term Fact Recall (RAG)
module: brain/memory_manager.py
priority: P0
phase: 2

description: >
  Store important facts as vector embeddings in ChromaDB.
  Retrieve relevant past context for current conversation.

pipeline:
  storage:
    1: "Extract key facts from conversation (LLM summarization)"
    2: "Generate embedding (nomic-embed-text, 768-dim)"
    3: "Store in ChromaDB with metadata (user_id, timestamp, topic)"

  retrieval:
    1: "Embed current user query"
    2: "Search ChromaDB for top 5 similar entries"
    3: "Filter by user_id and recency"
    4: "Inject as context into system prompt"

collections:
  - name: "conversation_summaries"
    description: "Summaries of past conversations"
  - name: "user_facts"
    description: "Key facts about the user (interests, skills, etc.)"
  - name: "learning_notes"
    description: "Notes from learning modules"
```

#### SK08: Personal Knowledge Graph
```yaml
id: SK08
name: Personal Knowledge Graph
module: brain/knowledge_graph.py
priority: P1
phase: 2

description: >
  Graph database storing relationships between user,
  topics, goals, and learning progress. The "brain map"
  that makes WISDOM truly personal.

operations:
  - add_node(type, properties)
  - add_relationship(from_node, to_node, relationship_type)
  - get_user_knowledge(user_id) → list of learned topics
  - get_learning_path(user_id) → recommended next topics
  - get_related_topics(topic_id) → connected topics
  - get_prerequisites(module_id) → required prior knowledge

backends:
  primary: "Neo4j Aura (free tier — 200K nodes, 400K rels)"
  fallback: "SQLite with nodes/edges tables"
```

---

### TEACHING SKILLS

#### SK11: Skill Assessment
```yaml
id: SK11
name: Skill Assessment
module: soul/skill_assessor.py
priority: P1
phase: 2

description: >
  Assess user's AI knowledge level through 5 adaptive
  questions. Results determine starting point on learning path.

categories:
  ai_awareness:
    weight: 0.30
    sample_questions:
      - "Have you ever heard of ChatGPT or AI assistants?"
      - "Can you name one thing AI can do?"

  prompt_skills:
    weight: 0.25
    sample_questions:
      - "If you wanted AI to help you write an email, how would you ask?"
      - "What makes a good question to ask an AI?"

  digital_literacy:
    weight: 0.20
    sample_questions:
      - "How comfortable are you using a computer or smartphone?"
      - "Have you ever used apps like Google Maps or YouTube?"

  coding_ability:
    weight: 0.15
    sample_questions:
      - "Have you ever written any code or used a spreadsheet formula?"
      - "Do you know what 'if-else' means in programming?"

  domain_knowledge:
    weight: 0.10
    sample_questions:
      - "What is your area of expertise?"
      - "How could AI potentially help in your field?"

scoring:
  0-2: "Complete beginner — start at Level 1"
  3-4: "Some awareness — start at Level 2"
  5-6: "Intermediate — start at Level 3"
  7-8: "Advanced — start at Level 5"
  9-10: "Expert — start at Level 6"
```

#### SK12: Adaptive Curriculum Generation
```yaml
id: SK12
name: Adaptive Curriculum Generation
module: soul/learning_path.py
priority: P1
phase: 2

description: >
  Generate personalized learning paths based on user's
  assessment, interests, goals, and learning pace.

algorithm:
  1: "Get user's skill assessment score"
  2: "Get user's stated goals and interests"
  3: "Determine starting level from score"
  4: "Generate curriculum from module graph"
  5: "Prioritize topics related to user's interests"
  6: "Add prerequisite topics if needed"
  7: "Create timeline with milestones"
  8: "Adapt in real-time based on progress"

personalization_factors:
  - Current skill level
  - Stated goals (e.g., "learn coding" vs "use AI at work")
  - Interests (farming, teaching, business, etc.)
  - Learning pace (fast/slow completions)
  - Preferred depth (theory vs practice)
  - Available time (casual vs intensive)

example_path_farmer:
  level_1: "What is AI? (with farming examples)"
  level_2: "Asking AI about crop problems"
  level_3: "AI for weather, market prices, soil analysis"
  level_4: "How AI prediction models work (crop yield example)"
  level_5: "Simple data analysis with Python (farm data)"

example_path_teacher:
  level_1: "What is AI? (with education examples)"
  level_2: "Using AI to create lesson plans"
  level_3: "AI for grading, student feedback, content creation"
  level_4: "How AI language models work"
  level_5: "Build a simple quiz app with AI"
```

#### SK13: Interactive Quizzing
```yaml
id: SK13
name: Interactive Quizzing
module: soul/learning_path.py
priority: P1
phase: 2

description: >
  Generate and grade quizzes at end of each learning module.
  Adaptive difficulty. Multiple question types.

question_types:
  - multiple_choice: "4 options, 1 correct"
  - true_false: "Statement + true/false"
  - open_ended: "Free text, LLM-graded"
  - practical: "Do this task with AI and show result"

grading:
  pass_threshold: 70
  scoring:
    correct: "+20 points"
    partially_correct: "+10 points"
    incorrect: "0 points, explanation provided"
  on_pass: "Unlock next module + achievement badge"
  on_fail: "Review key concepts + retry option"

adaptive_difficulty:
  - "If user scores 100%: next quiz harder"
  - "If user scores < 50%: next quiz easier"
  - "Questions selected from question pool by difficulty"
```

---

### MODE SKILLS

#### SK17-SK21: Operating Modes
```yaml
modes:
  teacher:
    id: SK17
    trigger: "User clicks 'Teach me' or asks to learn"
    behavior:
      - "Structured lesson delivery"
      - "Step-by-step explanations"
      - "Check understanding after each concept"
      - "Use analogies and examples"
      - "Patient, never rushed"
    prompt_modifier: "You are in TEACHER mode. Explain step by step."

  researcher:
    id: SK18
    trigger: "User asks factual questions or 'search for...'"
    behavior:
      - "Search knowledge base and memory"
      - "Provide comprehensive answers with sources"
      - "Admit when unsure"
      - "Suggest follow-up questions"
    prompt_modifier: "You are in RESEARCHER mode. Be thorough and cite sources."

  quiz_master:
    id: SK19
    trigger: "User clicks 'Quiz me' or completes a module"
    behavior:
      - "Generate contextual quiz questions"
      - "Grade answers with explanations"
      - "Track scores"
      - "Encourage and motivate"
    prompt_modifier: "You are in QUIZ mode. Ask questions and grade answers."

  code_helper:
    id: SK20
    trigger: "User asks about coding or shares code"
    behavior:
      - "Write code with explanations"
      - "Debug user's code"
      - "Explain code line by line"
      - "Suggest improvements"
      - "Always explain WHY, not just WHAT"
    prompt_modifier: "You are in CODE mode. Write clean code with explanations."

  free_chat:
    id: SK21
    trigger: "Default mode, general conversation"
    behavior:
      - "Natural, warm conversation"
      - "Answer any question"
      - "Suggest learning topics when appropriate"
      - "Remember and build on past conversations"
    prompt_modifier: "You are in CHAT mode. Be friendly and helpful."
```

---

### PRIVACY SKILLS

#### SK22: PII Sanitization
```yaml
id: SK22
name: PII Sanitization
module: heart/privacy_manager.py
priority: P0
phase: 1

description: >
  Remove or mask Personally Identifiable Information
  before sending data to cloud LLM providers.

patterns_detected:
  - email: "regex for email addresses → [EMAIL]"
  - phone: "regex for phone numbers → [PHONE]"
  - credit_card: "regex for CC numbers → [CARD]"
  - id_numbers: "regex for SSN, national ID → [ID]"
  - addresses: "heuristic for physical addresses → [ADDRESS]"

when_applied:
  - "Before sending to Gemini API (cloud)"
  - "NOT applied for Ollama (local) — data stays on device"
  - "Before storing in community knowledge base"

user_control:
  - "Toggle PII sanitization on/off"
  - "View what was sanitized in each message"
  - "Whitelist specific data (e.g., 'my email is ok to share')"
```

#### SK24: Federated Learning
```yaml
id: SK24
name: Federated Learning
module: heart/federated_core.py
priority: P2
phase: 4

description: >
  Privacy-preserving community learning.
  Users contribute anonymous insights to improve WISDOM
  for everyone. Differential privacy ensures no individual
  data can be extracted.

what_is_shared:
  - "Popular question categories (not actual questions)"
  - "Average difficulty level per topic"
  - "Common confusion points"
  - "Effective explanation patterns"

what_is_never_shared:
  - "Actual conversation content"
  - "User names or profiles"
  - "Personal goals or interests"
  - "Any PII"

implementation:
  1: "Aggregate local metrics (topic frequency, scores)"
  2: "Apply differential privacy noise (epsilon=1.0)"
  3: "Hash and anonymize all identifiers"
  4: "Submit to community aggregation endpoint"
  5: "Community model updated weekly"
  6: "Updated model distributed back to all users"
```

---

## 3. Skill Dependencies Graph

```
SK05 (Voice) ─────────────────────────────────┐
                                                │
SK02 (Lang Detect) ──► SK01 (Chat) ──────────► SK03 (Tone)
                         │                       │
                         ▼                       ▼
SK06 (Short Memory) ──► SK07 (Long Memory) ──► SK09 (Context)
                         │                       │
                         ▼                       ▼
SK03 (Tone) ──────────► SK04 (Emotion) ──────► SK21 (Free Chat)
                                                 │
SK08 (KG) ──► SK11 (Assess) ──► SK12 (Curriculum) ──► SK13 (Quiz)
                                    │                     │
                                    ▼                     ▼
SK15 (Goals) ──────────────────► SK14 (Progress) ──► SK16 (Motivate)
                                                       │
SK17 (Teacher) ◄──────────────────────────────────────┘
SK18 (Research) ◄─────────────────────────────────────┘
SK19 (Quiz Master) ◄─────────────────────────────────┘
SK20 (Code Helper) ◄─────────────────────────────────┘
                         │
                         ▼
SK22 (Privacy) ──► SK23 (Local) ──► SK24 (Federated) ──► SK25 (Export)
                                                           │
SK26 (Web UI) ──► SK27 (API) ──► SK28 (Dashboard) ──► SK29 (Plugins)
```

---

## 4. User Skill Tree (What Users Learn)

### User Learning Progression

```
USER SKILL TREE
│
├── Level 1: AI Awareness ────────── "I know what AI is"
│   ├── What is AI?
│   ├── What can AI do?
│   ├── What can AI NOT do?
│   └── My first AI conversation
│
├── Level 2: Prompt Literacy ─────── "I can talk to AI effectively"
│   ├── How to ask good questions
│   ├── Giving context and specificity
│   ├── Iterating on responses
│   └── Common prompt patterns
│
├── Level 3: AI Application ─────── "I use AI in daily life"
│   ├── AI for learning
│   ├── AI for work productivity
│   ├── AI for creativity
│   └── AI for problem-solving
│
├── Level 4: AI Understanding ────── "I understand how AI works"
│   ├── How language models think
│   ├── Training data and bias
│   ├── Hallucinations and limits
│   └── Ethics and responsibility
│
├── Level 5: Code Basics ─────────── "I can write simple code"
│   ├── What is programming?
│   ├── My first Python program
│   ├── Using AI to write code
│   └── Debugging with AI help
│
├── Level 6: App Building ─────────── "I can build applications"
│   ├── Web app fundamentals
│   ├── Working with APIs
│   ├── Testing and deployment
│   └── Build a personal tool
│
└── Level 7: AI Creation ──────────── "I can create AI tools"
    ├── LLMs and prompt engineering
    ├── Building AI applications
    ├── Open source contribution
    └── Deploy my own AI tool
```

### User Badges & Achievements

| Badge | Trigger | Icon Concept |
|-------|---------|-------------|
| First Contact | Complete first conversation | Handshake |
| Polyglot | Use WISDOM in 2+ languages | Globe |
| Curious Mind | Ask 50 questions | Lightbulb |
| Level Up | Complete any learning module | Arrow Up |
| Perfect Score | Get 100% on a quiz | Star |
| Streak Master | Use WISDOM 7 days in a row | Fire |
| Code Rookie | Write first code with WISDOM | Terminal |
| Builder | Complete Level 6 project | Hammer |
| Creator | Complete Level 7 project | Rocket |
| Helper | Contribute to community knowledge | Heart |
| Pioneer | Be among first 1000 users | Flag |

---

## 5. Technical Skills Required (For Developers)

### To Contribute to WISDOM, You Need:

| Skill | Level | Where Used |
|-------|-------|-----------|
| Python 3.12+ | Intermediate | Everywhere |
| LangChain | Beginner+ | Voice, Core |
| Streamlit | Beginner+ | Body |
| FastAPI | Beginner | Body/API |
| SQLite | Beginner | Brain |
| ChromaDB | Beginner | Brain/Memory |
| Neo4j (optional) | Beginner | Brain/KG |
| pytest | Beginner | Tests |
| Git/GitHub | Beginner | Contribution |
| Prompt Engineering | Intermediate | Voice, Soul |

---

*Every skill WISDOM has exists for one purpose: to turn grey dots into green dots.*
*Built with love for the 6.8 billion. — Project PROMETHEUS*
