"""7-level learning curriculum — from AI basics to building AI tools.

Each level has 3-4 lessons with objectives, exercises, and quiz questions.
Content is personalized to user's language, interests, and pace.
Includes SQLite-backed learning_progress table for persistence.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from wisdom.core.constants import LEARNING_LEVELS

__all__ = ["LearningPath", "LearningProgressTracker"]

# Full module definitions with lessons, objectives, exercises, quizzes
_MODULES = {
    1: {
        "name": "Hello AI",
        "estimated_time": "1-2 hours",
        "objectives": ["Understand what AI is", "Know what AI can and cannot do", "Have your first AI conversation"],
        "lessons": [
            {"id": "1.1", "title": "What is AI?", "description": "AI explained with real-life examples",
             "content_prompt": "Explain what AI is using simple analogies from {user_interest}. Like a helpful assistant that learned from millions of books."},
            {"id": "1.2", "title": "AI is NOT magic", "description": "Setting realistic expectations",
             "content_prompt": "Explain what AI cannot do. It doesn't think, feel, or know everything. It makes mistakes. Use examples from {user_interest}."},
            {"id": "1.3", "title": "Your first AI conversation", "description": "Practice talking to WISDOM",
             "content_prompt": "Guide the user through their first AI conversation. Suggest 3 things to try asking about {user_interest}."},
            {"id": "1.4", "title": "Quiz: Basic AI concepts", "description": "Test your understanding", "is_quiz": True},
        ],
        "quiz_questions": [
            {"q": "What is AI?", "type": "multiple_choice",
             "options": ["A robot that thinks like a human", "A program that learns from data to help with tasks", "Magic software", "A search engine"],
             "correct": 1, "explanation": "AI is software that learns patterns from data to help with tasks — not magic, not a human brain."},
            {"q": "Can AI make mistakes?", "type": "true_false", "correct": True,
             "explanation": "Yes! AI can make mistakes, give wrong information, or misunderstand your question. Always verify important information."},
            {"q": "What is one thing AI is good at?", "type": "open",
             "scoring_hints": "Any reasonable answer: writing, translating, answering questions, summarizing, coding, etc. Score 0-10."},
        ],
    },
    2: {
        "name": "Talk to AI",
        "estimated_time": "2-3 hours",
        "objectives": ["Write clear prompts", "Give AI useful context", "Avoid common mistakes"],
        "lessons": [
            {"id": "2.1", "title": "How to ask good questions", "description": "The art of prompting",
             "content_prompt": "Teach prompt basics: be specific, give context, state what you want. Use {user_interest} examples."},
            {"id": "2.2", "title": "Context and specificity", "description": "Giving AI useful information",
             "content_prompt": "Show how adding context improves AI responses. Compare vague vs specific prompts about {user_interest}."},
            {"id": "2.3", "title": "Common mistakes", "description": "What NOT to do with AI",
             "content_prompt": "Common prompt mistakes: too vague, too long, assuming AI knows your situation, not iterating."},
            {"id": "2.4", "title": "Practice: 10 prompt challenges", "description": "Hands-on exercises", "is_exercise": True},
        ],
        "quiz_questions": [
            {"q": "Which is a better prompt?", "type": "multiple_choice",
             "options": ["Tell me about food", "What are 3 healthy breakfast recipes that take under 15 minutes?", "Food help", "I'm hungry"],
             "correct": 1, "explanation": "Specific prompts with context (healthy, breakfast, 15 min) get much better results."},
            {"q": "Should you give AI context about your situation?", "type": "true_false", "correct": True,
             "explanation": "Yes! The more relevant context you provide, the better AI can help you."},
            {"q": "Write a good prompt asking AI for help with something in your daily life.", "type": "open",
             "scoring_hints": "Look for: specificity, context, clear ask. Vague = 2, some detail = 5, excellent = 9. Score 0-10."},
        ],
    },
    3: {
        "name": "AI in Daily Life",
        "estimated_time": "2-3 hours",
        "objectives": ["Use AI for learning", "Use AI for work productivity", "Use AI for creativity"],
        "lessons": [
            {"id": "3.1", "title": "AI for learning", "description": "Use AI as a study buddy",
             "content_prompt": "Show how to use AI for learning: ask explanations, get summaries, practice Q&A. {user_interest} examples."},
            {"id": "3.2", "title": "AI for work", "description": "Productivity with AI",
             "content_prompt": "Practical work uses: emails, reports, brainstorming, analysis. Relate to {user_interest}."},
            {"id": "3.3", "title": "AI for creativity", "description": "Art, music, writing with AI",
             "content_prompt": "Creative uses: writing stories, brainstorming ideas, planning events. {user_interest} examples."},
            {"id": "3.4", "title": "Project: Solve a real problem", "description": "Apply AI to your life", "is_exercise": True},
        ],
        "quiz_questions": [
            {"q": "Name 3 ways AI can help in daily life.", "type": "open",
             "scoring_hints": "Each valid use case = 3 points. Max 10. Examples: writing, learning, planning, translating."},
            {"q": "AI can help you learn new things faster.", "type": "true_false", "correct": True,
             "explanation": "AI is excellent at explaining concepts, answering questions, and creating practice exercises."},
        ],
    },
    4: {
        "name": "How AI Thinks",
        "estimated_time": "3-4 hours",
        "objectives": ["Understand tokens and language models", "Know about training data and bias", "Recognize limitations"],
        "lessons": [
            {"id": "4.1", "title": "How language models work", "description": "Tokens, attention, generation",
             "content_prompt": "Explain LLMs simply: text → tokens → prediction → next word. Like autocomplete but 1000x smarter."},
            {"id": "4.2", "title": "Training data and bias", "description": "Where AI knowledge comes from",
             "content_prompt": "Explain training data, internet text, bias. AI reflects its training data — both good and bad."},
            {"id": "4.3", "title": "Limitations and hallucinations", "description": "When AI gets it wrong",
             "content_prompt": "Explain hallucinations, knowledge cutoff, reasoning limits. AI is confident even when wrong."},
            {"id": "4.4", "title": "Ethics and responsible use", "description": "Being a good AI citizen",
             "content_prompt": "Ethics: don't spread AI misinformation, verify facts, respect privacy, don't use AI to deceive."},
        ],
        "quiz_questions": [
            {"q": "What is a 'hallucination' in AI?", "type": "multiple_choice",
             "options": ["When AI sees things", "When AI generates confident but incorrect information", "When AI dreams", "A type of AI model"],
             "correct": 1, "explanation": "AI 'hallucination' = generating text that sounds confident but is factually wrong."},
            {"q": "AI always gives correct answers.", "type": "true_false", "correct": False,
             "explanation": "AI can be wrong! Always verify important information from reliable sources."},
        ],
    },
    5: {
        "name": "Code with AI",
        "estimated_time": "4-5 hours",
        "objectives": ["Understand what programming is", "Write simple Python", "Use AI to write and debug code"],
        "lessons": [
            {"id": "5.1", "title": "What is programming?", "description": "Code explained simply",
             "content_prompt": "Explain programming: instructions for computers. Like a recipe, but for machines. Use {user_interest} analogy."},
            {"id": "5.2", "title": "Your first Python program", "description": "Hello World and beyond",
             "content_prompt": "Guide: print(), variables, input(). Write a simple program related to {user_interest}."},
            {"id": "5.3", "title": "Using AI to write code", "description": "AI as your coding assistant",
             "content_prompt": "Show how to ask AI for code: describe what you want, get code, understand it, modify it."},
            {"id": "5.4", "title": "Project: Build a calculator", "description": "Your first real program", "is_exercise": True},
        ],
        "quiz_questions": [
            {"q": "What does print('Hello') do in Python?", "type": "multiple_choice",
             "options": ["Prints a document", "Shows 'Hello' on screen", "Sends an email", "Creates a file"],
             "correct": 1, "explanation": "print() displays text on the screen — it's the most basic Python command."},
            {"q": "Write a Python line that stores your name in a variable.", "type": "open",
             "scoring_hints": "Correct: name = 'something' or any valid variable assignment. Score 0-10."},
        ],
    },
    6: {
        "name": "Build with AI",
        "estimated_time": "5-7 hours",
        "objectives": ["Understand web app basics", "Work with APIs", "Build and deploy a personal tool"],
        "lessons": [
            {"id": "6.1", "title": "Web app fundamentals", "description": "HTML, CSS, Python basics",
             "content_prompt": "Explain web apps: frontend (what you see) vs backend (server logic). Streamlit makes it easy."},
            {"id": "6.2", "title": "Working with APIs", "description": "Connect to the world",
             "content_prompt": "What are APIs: like a waiter taking your order to the kitchen. REST, JSON, requests."},
            {"id": "6.3", "title": "Testing and debugging", "description": "Make your code reliable",
             "content_prompt": "Testing basics: try your code, check edge cases, use AI to find bugs."},
            {"id": "6.4", "title": "Project: Build a personal tool", "description": "Your first web app", "is_exercise": True},
        ],
        "quiz_questions": [
            {"q": "What is an API?", "type": "open",
             "scoring_hints": "Interface for programs to communicate. Good analogy = 7+. Technical detail = 9+. Score 0-10."},
        ],
    },
    7: {
        "name": "Create AI Tools",
        "estimated_time": "7-10 hours",
        "objectives": ["Master prompt engineering", "Build AI-powered apps", "Contribute to open source"],
        "lessons": [
            {"id": "7.1", "title": "LLMs and prompt engineering", "description": "Advanced AI techniques",
             "content_prompt": "Advanced prompting: system prompts, few-shot, chain-of-thought, RAG. Practical examples."},
            {"id": "7.2", "title": "Building AI applications", "description": "LangChain, APIs, RAG",
             "content_prompt": "Build AI apps with LangChain: chains, memory, tools, RAG pipeline. Step-by-step."},
            {"id": "7.3", "title": "Contributing to open source", "description": "Join the community",
             "content_prompt": "How to contribute: find repos, read issues, fork, branch, PR. Start with WISDOM itself!"},
            {"id": "7.4", "title": "Project: Deploy your AI tool", "description": "Share with the world", "is_exercise": True},
        ],
        "quiz_questions": [
            {"q": "What is RAG (Retrieval-Augmented Generation)?", "type": "open",
             "scoring_hints": "Combining retrieval (search) with LLM generation. Mentions vector DB, context injection = 8+. Score 0-10."},
        ],
    },
}


class LearningPath:
    """Personalized 7-level learning curriculum.

    Each level has 3-4 lessons with content prompts for LLM-generated
    personalized content. Includes exercises and quizzes.
    """

    def __init__(self) -> None:
        self.modules = _MODULES

    def get_module(self, level: int) -> dict | None:
        """Get a learning module by level."""
        return self.modules.get(level)

    def get_all_modules(self) -> dict:
        """Get all learning modules with metadata."""
        result = {}
        for level, module in self.modules.items():
            meta = LEARNING_LEVELS.get(level, {})
            result[level] = {**module, **meta}
        return result

    def get_lesson(self, level: int, lesson_index: int) -> dict | None:
        """Get a specific lesson from a module."""
        module = self.get_module(level)
        if not module or lesson_index >= len(module["lessons"]):
            return None
        return module["lessons"][lesson_index]

    def get_lesson_content_prompt(self, level: int, lesson_index: int, user_interest: str = "general topics") -> str | None:
        """Get the content generation prompt for a lesson, personalized."""
        lesson = self.get_lesson(level, lesson_index)
        if not lesson or "content_prompt" not in lesson:
            return None
        return lesson["content_prompt"].replace("{user_interest}", user_interest)

    def take_quiz(self, level: int) -> list[dict] | None:
        """Get quiz questions for a module."""
        module = self.get_module(level)
        if not module:
            return None
        return module.get("quiz_questions", [])

    def grade_quiz(self, level: int, answers: list) -> dict:
        """Grade quiz answers for a module.

        Args:
            level: Module level.
            answers: List of answers (int index for MC, bool for T/F, str for open).

        Returns:
            Dict with score, passed, details.
        """
        questions = self.take_quiz(level)
        if not questions:
            return {"score": 0, "passed": False, "details": []}

        total_points = 0
        max_points = len(questions) * 10
        details = []

        for i, (q, answer) in enumerate(zip(questions, answers)):
            if q["type"] == "multiple_choice":
                correct = answer == q["correct"]
                points = 10 if correct else 0
                details.append({
                    "question": q["q"], "correct": correct, "points": points,
                    "explanation": q.get("explanation", ""),
                })
            elif q["type"] == "true_false":
                correct = answer == q["correct"]
                points = 10 if correct else 0
                details.append({
                    "question": q["q"], "correct": correct, "points": points,
                    "explanation": q.get("explanation", ""),
                })
            elif q["type"] == "open":
                # Open questions need LLM grading — placeholder score
                points = answer if isinstance(answer, (int, float)) else 5
                details.append({
                    "question": q["q"], "points": points,
                    "needs_llm_grading": True,
                    "scoring_hints": q.get("scoring_hints", ""),
                })
            total_points += points

        score_pct = round(total_points / max_points * 100) if max_points > 0 else 0
        return {
            "score": score_pct,
            "total_points": total_points,
            "max_points": max_points,
            "passed": score_pct >= 70,
            "details": details,
        }

    def get_progress(self, completed_lessons: list[str]) -> dict:
        """Calculate learning progress."""
        progress = {}
        total_lessons = 0
        total_completed = 0

        for level, module in self.modules.items():
            lessons = module["lessons"]
            completed = [l for l in lessons if l["id"] in completed_lessons]
            total_lessons += len(lessons)
            total_completed += len(completed)

            progress[level] = {
                "name": module["name"],
                "total": len(lessons),
                "completed": len(completed),
                "percentage": round(len(completed) / len(lessons) * 100) if lessons else 0,
            }

        progress["overall"] = {
            "total": total_lessons,
            "completed": total_completed,
            "percentage": round(total_completed / total_lessons * 100) if total_lessons else 0,
        }
        return progress

    def get_next_lesson(self, completed_lessons: list[str]) -> dict | None:
        """Get the next uncompleted lesson."""
        for level in sorted(self.modules.keys()):
            for lesson in self.modules[level]["lessons"]:
                if lesson["id"] not in completed_lessons:
                    return {"level": level, **lesson}
        return None

    def generate_personalized_path(self, starting_level: int, interests: list[str]) -> dict:
        """Generate a personalized learning path based on assessment."""
        path = {}
        interest_str = ", ".join(interests) if interests else "general topics"
        for level in range(starting_level, 8):
            module = self.get_module(level)
            if module:
                path[level] = {
                    "name": module["name"],
                    "personalized_for": interest_str,
                    "lessons": [
                        {**l, "content_prompt": l.get("content_prompt", "").replace("{user_interest}", interest_str)}
                        for l in module["lessons"]
                    ],
                }
        return path


class LearningProgressTracker:
    """Persists learning progress to SQLite.

    Tracks which modules and lessons each user has started/completed,
    quiz scores, and timestamps — matching architecture.md §4.2.
    """

    def __init__(self, db_path: str | Path = "./data/wisdom.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS learning_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    module_id TEXT NOT NULL,
                    level INTEGER NOT NULL,
                    score REAL DEFAULT 0.0,
                    completed BOOLEAN DEFAULT 0,
                    started_at TEXT,
                    completed_at TEXT,
                    UNIQUE(user_id, module_id)
                )
            """)

    def start_lesson(self, user_id: str, lesson_id: str, level: int) -> None:
        """Mark a lesson as started."""
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO learning_progress "
                "(user_id, module_id, level, started_at) VALUES (?, ?, ?, ?)",
                (user_id, lesson_id, level, now),
            )

    def complete_lesson(self, user_id: str, lesson_id: str, level: int, score: float = 0.0) -> None:
        """Mark a lesson as completed with optional score."""
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(str(self.db_path)) as conn:
            # Upsert: insert or update
            conn.execute(
                "INSERT INTO learning_progress (user_id, module_id, level, score, completed, started_at, completed_at) "
                "VALUES (?, ?, ?, ?, 1, ?, ?) "
                "ON CONFLICT(user_id, module_id) DO UPDATE SET "
                "score = excluded.score, completed = 1, completed_at = excluded.completed_at",
                (user_id, lesson_id, level, score, now, now),
            )

    def get_completed_lessons(self, user_id: str) -> list[str]:
        """Get list of completed lesson IDs for a user."""
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(
                "SELECT module_id FROM learning_progress WHERE user_id = ? AND completed = 1",
                (user_id,),
            ).fetchall()
        return [r[0] for r in rows]

    def get_progress(self, user_id: str) -> list[dict]:
        """Get all progress records for a user."""
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(
                "SELECT module_id, level, score, completed, started_at, completed_at "
                "FROM learning_progress WHERE user_id = ? ORDER BY level, module_id",
                (user_id,),
            ).fetchall()
        return [
            {
                "module_id": r[0], "level": r[1], "score": r[2],
                "completed": bool(r[3]), "started_at": r[4], "completed_at": r[5],
            }
            for r in rows
        ]

    def get_level_score(self, user_id: str, level: int) -> float | None:
        """Get average score for a completed level."""
        with sqlite3.connect(str(self.db_path)) as conn:
            row = conn.execute(
                "SELECT AVG(score) FROM learning_progress "
                "WHERE user_id = ? AND level = ? AND completed = 1",
                (user_id, level),
            ).fetchone()
        return row[0] if row and row[0] is not None else None
