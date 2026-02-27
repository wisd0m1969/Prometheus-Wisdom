"""5-category adaptive skill assessment (0-10 scale).

Categories: AI Awareness (30%), Prompt Skills (25%),
Digital Literacy (20%), Coding Ability (15%), Domain Knowledge (10%)

10 total questions (2 per category), adaptive difficulty.
"""

from __future__ import annotations

from wisdom.core.constants import SKILL_CATEGORIES

__all__ = ["SkillAssessor"]

# Assessment questions: 2 per category, ordered easy → hard
_QUESTIONS = {
    "ai_awareness": [
        {
            "id": "ai1", "q": "Have you ever heard of AI assistants like ChatGPT?",
            "type": "choice", "options": ["Yes", "No", "What's that?"],
            "scoring": {"Yes": 5, "No": 2, "What's that?": 0},
            "difficulty": 1,
        },
        {
            "id": "ai2", "q": "Can you name one thing AI can do?",
            "type": "open", "difficulty": 3,
            "scoring_hints": "Good answers mention: translate, write, search, answer questions, generate images. Score 0-10.",
        },
    ],
    "prompt_skills": [
        {
            "id": "ps1", "q": "If you wanted AI to help you write an email, how would you ask?",
            "type": "open", "difficulty": 3,
            "scoring_hints": "Good answers include context (who, what, tone). Vague = low. Specific = high. Score 0-10.",
        },
        {
            "id": "ps2", "q": "What makes a good question to ask an AI?",
            "type": "open", "difficulty": 5,
            "scoring_hints": "Mentions: being specific, giving context, clear intent, examples. Score 0-10.",
        },
    ],
    "digital_literacy": [
        {
            "id": "dl1", "q": "How comfortable are you using a computer or smartphone? (1=not at all, 5=very comfortable)",
            "type": "scale", "min": 1, "max": 5, "difficulty": 1,
            "scoring": "multiply by 2",  # 1→2, 5→10
        },
        {
            "id": "dl2", "q": "What apps or websites do you use daily?",
            "type": "open", "difficulty": 2,
            "scoring_hints": "0 apps = 0, 1-2 basic (WhatsApp) = 3, 3-5 = 5, many varied = 8, technical tools = 10.",
        },
    ],
    "coding_ability": [
        {
            "id": "ca1", "q": "Have you ever written any code or used a spreadsheet formula?",
            "type": "choice", "options": ["Yes, I code regularly", "I've tried a little", "Never"],
            "scoring": {"Yes, I code regularly": 8, "I've tried a little": 4, "Never": 0},
            "difficulty": 1,
        },
        {
            "id": "ca2", "q": "Do you know what 'if-else' means in programming?",
            "type": "choice", "options": ["Yes, I can explain it", "I've heard of it", "No idea"],
            "scoring": {"Yes, I can explain it": 9, "I've heard of it": 4, "No idea": 0},
            "difficulty": 4,
        },
    ],
    "domain_knowledge": [
        {
            "id": "dk1", "q": "What is your field of work or study?",
            "type": "open", "difficulty": 1,
            "scoring_hints": "Any answer = 5 (everyone has domain knowledge). Detailed = 7. Expert-level description = 10.",
        },
        {
            "id": "dk2", "q": "How could AI potentially help in your field?",
            "type": "open", "difficulty": 3,
            "scoring_hints": "No idea = 2, vague = 4, specific use case = 7, multiple detailed ideas = 10.",
        },
    ],
}


class SkillAssessor:
    """Adaptive assessment to determine user's AI knowledge level.

    Runs up to 10 questions (2 per category), adapting based on answers.
    If Q1 in a category scores 0, Q2 is skipped (scored 0).
    """

    def __init__(self) -> None:
        self.scores: dict[str, float] = {}
        self._categories = list(SKILL_CATEGORIES.keys())
        self._current_cat_idx = 0
        self._current_q_idx = 0  # 0 or 1 within category
        self._answers: list[dict] = []
        self._started = False
        self._completed = False

    @property
    def is_completed(self) -> bool:
        return self._completed

    def start_assessment(self) -> dict:
        """Start or restart the assessment. Returns the first question."""
        self.scores = {}
        self._current_cat_idx = 0
        self._current_q_idx = 0
        self._answers = []
        self._started = True
        self._completed = False
        return self._current_question()

    def get_next_question(self, previous_score: float | None = None) -> dict | None:
        """Get the next assessment question.

        Args:
            previous_score: Score (0-10) for the previous answer.

        Returns:
            Dict with question details, or None if assessment is complete.
        """
        if not self._started:
            return self.start_assessment()

        # Record previous score
        if previous_score is not None:
            self._record_score(previous_score)

            # Adaptive: skip Q2 if Q1 scored 0
            if self._current_q_idx == 0 and previous_score == 0:
                self._record_score(0)  # auto-score Q2 as 0
                self._advance_category()
            else:
                self._current_q_idx += 1
                if self._current_q_idx >= 2:
                    self._advance_category()

        if self._current_cat_idx >= len(self._categories):
            self._completed = True
            return None

        return self._current_question()

    def answer_question(self, answer: str | int | float) -> dict | None:
        """Process an answer and return next question or None if done.

        For choice questions, auto-scores. For open questions, returns
        the question with scoring hints for LLM grading.
        """
        cat = self._categories[self._current_cat_idx]
        questions = _QUESTIONS[cat]
        q = questions[self._current_q_idx]

        # Auto-score choice/scale questions
        if q["type"] == "choice" and isinstance(q.get("scoring"), dict):
            score = q["scoring"].get(str(answer), 0)
            return self.get_next_question(previous_score=float(score))
        elif q["type"] == "scale":
            score = float(answer) * 2  # scale 1-5 → 0-10
            return self.get_next_question(previous_score=min(10, score))

        # Open questions need LLM grading — return scoring hints
        self._answers.append({"question": q["q"], "answer": answer, "category": cat})
        return {
            "needs_grading": True,
            "question": q["q"],
            "answer": answer,
            "scoring_hints": q.get("scoring_hints", "Score 0-10 based on quality."),
        }

    def calculate_composite_score(self) -> float:
        """Calculate weighted composite score (0-10)."""
        total = 0.0
        for category, weight_info in SKILL_CATEGORIES.items():
            score = self.scores.get(category, 0.0)
            total += score * weight_info["weight"]
        return round(total, 1)

    def get_starting_level(self) -> int:
        """Get recommended starting level (1-7) based on score."""
        score = self.calculate_composite_score()
        if score < 2:
            return 1
        elif score < 4:
            return 2
        elif score < 6:
            return 3
        elif score < 8:
            return 5
        return 6

    def get_results(self) -> dict:
        """Get full assessment results."""
        return {
            "category_scores": {
                cat: {
                    "score": self.scores.get(cat, 0.0),
                    "label": SKILL_CATEGORIES[cat]["label"],
                    "weight": SKILL_CATEGORIES[cat]["weight"],
                }
                for cat in self._categories
            },
            "composite_score": self.calculate_composite_score(),
            "starting_level": self.get_starting_level(),
            "total_questions_answered": len(self._answers),
        }

    # ─── Private Helpers ──────────────────────────────────────

    def _current_question(self) -> dict | None:
        if self._current_cat_idx >= len(self._categories):
            return None

        cat = self._categories[self._current_cat_idx]
        questions = _QUESTIONS[cat]
        if self._current_q_idx >= len(questions):
            return None

        q = questions[self._current_q_idx]
        q_number = self._current_cat_idx * 2 + self._current_q_idx + 1

        return {
            "category": cat,
            "category_label": SKILL_CATEGORIES[cat]["label"],
            "question_number": q_number,
            "total_questions": len(self._categories) * 2,
            **q,
        }

    def _record_score(self, score: float) -> None:
        cat = self._categories[self._current_cat_idx]
        if cat not in self.scores:
            self.scores[cat] = score
        else:
            self.scores[cat] = (self.scores[cat] + score) / 2

    def _advance_category(self) -> None:
        self._current_cat_idx += 1
        self._current_q_idx = 0
