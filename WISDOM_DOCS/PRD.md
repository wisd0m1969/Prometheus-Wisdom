# PRD — PROMETHEUS WISDOM
## Product Requirements Document v1.0

---

## 1. Executive Summary

**Product Name:** PROMETHEUS WISDOM
**Codename:** Project Grey-to-Green
**Version:** 1.0.0
**Origin:** Project PROMETHEUS Invention #637 (Score 7.85/10, Oracle 8/10, Confidence 0.9)
**SDG Alignment:** SDG4 Quality Education
**License:** MIT Open Source

PROMETHEUS WISDOM is an open-source AI personal companion designed to democratize AI access for the **6.8 billion people (84% of humanity)** who have never interacted with artificial intelligence. It combines a personal Knowledge Graph, multilingual NLP, federated learning, and adaptive curriculum into a single free web application.

---

## 2. Problem Statement

### 2.1 The Data (February 2026)

| Segment | Population | % of 8.1B | AI Interaction Level |
|---------|-----------|-----------|---------------------|
| Never used AI | ~6.8 Billion | 84% | None |
| Free chatbot user | ~1.3 Billion | 16% | Basic |
| Pays $20/mo for AI | ~15-25 Million | 0.3% | Moderate |
| Uses coding scaffold | ~2-5 Million | 0.04% | Advanced |

### 2.2 Root Causes (5 Barriers)

1. **Language Barrier** — 75% of the world does not speak English fluently. Most AI tools are English-first. Thai farmers, Hindi artisans, Swahili teachers are locked out.

2. **Cost Barrier** — $20/month (ChatGPT Plus, Claude Pro) exceeds daily income for 3.4 billion people living on <$6.85/day. Even "free tiers" require credit cards for signup.

3. **Knowledge Barrier** — People don't know what AI is, what it can do, or that it could help their daily lives. There is no "on-ramp" for the uninitiated.

4. **Complexity Barrier** — Current AI tools assume literacy in English, typing skills, understanding of "prompts", and technical context. The UX is designed for knowledge workers.

5. **Infrastructure Barrier** — Slow internet, old devices, no app stores, intermittent electricity. Cloud-only AI is inaccessible to billions.

### 2.3 Existing Gap

Current AI products (ChatGPT, Claude, Gemini) are designed for:
- English speakers
- Knowledge workers
- People who already understand what AI is
- Users with reliable internet and modern devices
- People who can pay $20/month

**No product exists** that specifically targets the 6.8 billion who have never used AI, with a progressive learning journey from "What is AI?" to "Build your own software."

---

## 3. Product Vision

> **"Every human on Earth deserves a personal AI companion — a WISDOM — that speaks their language, knows their context, and grows with them from curious beginner to empowered creator."**

### 3.1 WISDOM Analogy

Like Tony Stark's WISDOM in Iron Man:
- **Remembers everything** about you (Knowledge Graph)
- **Speaks naturally** in your language (Multilingual NLP)
- **Adapts** to your skill level and goals (Adaptive Engine)
- **Protects** your privacy (Federated Learning)
- **Empowers** you to build (Progressive Learning Path)

Unlike Iron Man's WISDOM:
- **Free** — no billionaire budget required
- **Open Source** — community-owned, not proprietary
- **For everyone** — not just for geniuses in labs

---

## 4. Target Users

### 4.1 Primary Personas

**Persona 1: "Somchai" — Thai Farmer, Age 45**
- Has a smartphone with LINE app
- Speaks only Thai, no English
- Has never heard of ChatGPT
- Wants: better crop yields, weather info, market prices
- WISDOM journey: Learn what AI is → Ask farming questions → Get personalized advice

**Persona 2: "Priya" — Indian Student, Age 19**
- Has Android phone, limited data plan
- Speaks Hindi + basic English
- Has seen AI in news, never tried it
- Wants: learn coding, get a tech job
- WISDOM journey: Explore AI basics → Learn prompt engineering → Build a simple app

**Persona 3: "Maria" — Brazilian Teacher, Age 32**
- Has laptop, moderate internet
- Speaks Portuguese + some English
- Used ChatGPT once, confused by it
- Wants: create better lesson plans, help students
- WISDOM journey: Understand AI → Use AI for teaching → Create AI-powered study tools

**Persona 4: "Ahmed" — Kenyan Entrepreneur, Age 28**
- Has smartphone, spotty internet
- Speaks Swahili + English
- Tech-savvy but never used AI tools
- Wants: automate business tasks, reach more customers
- WISDOM journey: AI basics → Business automation → Build customer service bot

### 4.2 Secondary Users

- **Developers** who want to contribute to open source
- **NGOs/educators** who want to deploy WISDOM for their communities
- **Researchers** studying AI accessibility and digital divide

---

## 5. Product Goals & Success Criteria

### 5.1 North Star Metric

**Grey-to-Green Conversion Rate** — % of first-time AI users who complete Level 1 ("What is AI?") and return for a second session.

### 5.2 Goals (6 Months Post-Launch)

| Goal | Target | Measurement |
|------|--------|-------------|
| Active monthly users | 10,000+ | Streamlit analytics |
| Countries reached | 50+ | Anonymous geolocation |
| Languages actively used | 10+ | Language detection logs |
| Level 1 completion rate | 70%+ | Learning path tracker |
| User satisfaction | 4.5/5.0 | In-app feedback |
| GitHub stars | 1,000+ | GitHub API |
| Community contributors | 50+ | GitHub insights |
| Average session duration | 8+ minutes | Session tracking |
| Return rate (7-day) | 40%+ | User profile timestamps |

### 5.3 Anti-Goals (What WISDOM is NOT)

- NOT a ChatGPT clone (it has a learning mission, not just Q&A)
- NOT a paid product (must always have a 100% free tier)
- NOT English-only (multilingual from day 1)
- NOT cloud-dependent (must work with local LLM)
- NOT a data harvester (privacy-first, federated design)

---

## 6. Feature Requirements

### 6.1 MVP (Minimum Viable Product) — Phase 1

| ID | Feature | Priority | Description |
|----|---------|----------|-------------|
| F01 | Multilingual Chat | P0 | Chat with WISDOM in any language, auto-detected |
| F02 | User Profile | P0 | Name, language, skill level stored locally |
| F03 | Conversation Memory | P0 | Remember last 50 messages per session |
| F04 | Long-term Memory | P0 | Remember key facts across sessions |
| F05 | Dual LLM Backend | P0 | Ollama (local) + Gemini (cloud) auto-fallback |
| F06 | Streamlit Web UI | P0 | Clean chat interface, mobile-friendly |
| F07 | Skill Assessment | P1 | 5-question quiz to determine user level |
| F08 | Learning Path L1-L3 | P1 | What is AI → Using chatbots → AI for daily life |
| F09 | Progress Tracking | P1 | Visual progress bar, completion percentage |
| F10 | Beginner Mode | P1 | Simplified language, heavy use of analogies |

### 6.2 Version 1.1 — Phase 2

| ID | Feature | Priority | Description |
|----|---------|----------|-------------|
| F11 | Knowledge Graph | P1 | Neo4j/SQLite personal knowledge storage |
| F12 | RAG Pipeline | P1 | Retrieve relevant past context for better answers |
| F13 | Learning Path L4-L5 | P1 | How AI works → Intro to coding |
| F14 | Goal Setting | P2 | Users set goals, WISDOM tracks progress |
| F15 | Tone Adaptation | P2 | Auto-adjust formality and complexity |
| F16 | REST API | P2 | FastAPI endpoints for integration |
| F17 | Achievement System | P2 | Badges, milestones, celebrations |
| F18 | Export Profile | P2 | Download your data as JSON |

### 6.3 Version 2.0 — Phase 3-4

| ID | Feature | Priority | Description |
|----|---------|----------|-------------|
| F19 | Federated Learning | P2 | Privacy-preserving community learning |
| F20 | Learning Path L6-L7 | P2 | Build apps → Build AI tools |
| F21 | Code Playground | P2 | In-browser code editor with AI help |
| F22 | Community Knowledge | P3 | Shared FAQ and learning materials |
| F23 | Voice Input | P3 | Speech-to-text via Whisper |
| F24 | Offline Mode | P3 | Core features work without internet |
| F25 | Plugin System | P3 | Community-built extensions |

---

## 7. User Flows

### 7.1 First-Time User Flow

```
[User opens WISDOM URL]
    → Welcome screen (auto-detect language)
    → "Hi! I'm WISDOM. What's your name?" (in detected language)
    → User enters name
    → "Nice to meet you, [Name]! What would you like to do?"
        → [Learn about AI] → Skill Assessment → Learning Path
        → [Just chat] → Free conversation mode
        → [Help me with something] → Goal-oriented assistant
    → WISDOM remembers choice, adapts next session
```

### 7.2 Returning User Flow

```
[User opens WISDOM]
    → "Welcome back, [Name]! Last time we talked about [topic]."
    → "Would you like to continue, or try something new?"
        → [Continue] → Resume from last point
        → [Something new] → New topic/goal
    → WISDOM recalls context from Knowledge Graph
```

### 7.3 Learning Module Flow

```
[User starts Level 1: "What is AI?"]
    → Lesson 1: AI explained with real-life examples
    → Interactive Q&A (WISDOM asks questions to check understanding)
    → Mini-quiz (3 questions)
    → Score + feedback
    → If pass: Unlock Level 2 + achievement badge
    → If fail: Retry with simpler explanations
    → Progress saved to profile
```

---

## 8. Non-Functional Requirements

### 8.1 Performance
- Chat response time: < 5 seconds (cloud LLM), < 10 seconds (local Ollama)
- Page load time: < 3 seconds
- Memory usage: < 500MB RAM for local deployment

### 8.2 Scalability
- Support 1,000 concurrent users on Streamlit Cloud
- Knowledge Graph handles 100K+ nodes per user instance
- Stateless API design for horizontal scaling

### 8.3 Security & Privacy
- No PII transmitted to LLM providers (sanitization layer)
- All user data stored locally (SQLite) or in user-controlled Neo4j
- No tracking, no analytics cookies, no ad networks
- HTTPS only for deployed instances
- Input sanitization against XSS/injection

### 8.4 Accessibility
- WCAG 2.1 AA compliance target
- Works on 3G internet connections
- Mobile-first responsive design
- Large text option (16px minimum)
- High contrast mode
- Screen reader compatible labels

### 8.5 Internationalization
- UTF-8 everywhere
- RTL language support (Arabic, Hebrew)
- Date/number formatting per locale
- No hardcoded English strings in UI

---

## 9. Technical Constraints

| Constraint | Reason |
|-----------|--------|
| Zero cost for end users | Target audience cannot afford subscriptions |
| Must work with Ollama locally | Internet is unreliable for many users |
| Python only | Largest developer community, most AI libraries |
| No mandatory sign-up | Reduce friction for first-time users |
| SQLite as default DB | Zero configuration, works everywhere |
| MIT License | Maximum adoption, no legal barriers |

---

## 10. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Ollama too slow on old devices | High | Medium | Gemini cloud fallback, model size options |
| Free API rate limits | Medium | High | Multi-provider fallback, caching, local-first |
| Low adoption | Medium | High | Partner with NGOs, educators, open source community |
| Content quality in non-English | Medium | Medium | Community translations, LLM-generated content |
| Privacy concerns | Low | High | Federated design, no cloud data storage, open audit |
| Abuse/misuse | Low | Medium | Content moderation in prompts, usage guidelines |

---

## 11. Release Plan

| Version | Codename | Timeline | Key Features |
|---------|----------|----------|-------------|
| 0.1-alpha | "First Light" | Week 2 | Basic chat + memory + Streamlit |
| 0.5-beta | "Grey Awakens" | Week 4 | Knowledge Graph + Learning L1-L3 |
| 1.0 | "Green Wave" | Week 6 | Full learning path + adaptation + API |
| 1.1 | "Community" | Week 8 | Federated learning + community features |
| 2.0 | "Builder" | Month 4 | Code playground + L6-L7 + plugins |

---

## 12. Stakeholders

| Role | Responsibility |
|------|---------------|
| Creator / Maintainer | Architecture, core development, vision |
| Claude Code | AI pair programmer, implementation partner |
| Open Source Community | Contributions, translations, bug reports |
| NGO Partners | Distribution, user feedback, local deployment |
| End Users | Feedback, testing, community knowledge |

---

*Document generated by Project PROMETHEUS AGI System*
*Origin: Invention #637 — Federated Learning for Personalized Education with Decentralized Knowledge Graph and AI-Driven Curriculum Adaptation*
