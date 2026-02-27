"""5-question adaptive skill assessment (0-10 scale).

Categories: AI Awareness (30%), Prompt Skills (25%),
Digital Literacy (20%), Coding Ability (15%), Domain Knowledge (10%)
"""

from __future__ import annotations

from wisdom.core.constants import SKILL_CATEGORIES

__all__ = ["SkillAssessor"]

# Assessment questions by category and difficulty
_QUESTIONS = {
    "ai_awareness": [
        {"q": "Have you ever heard of ChatGPT or AI assistants?", "difficulty": 1},
        {"q": "Can you name one thing AI can do?", "difficulty": 2},
        {"q": "What is the difference between AI and a regular computer program?", "difficulty": 5},
        {"q": "How does a language model generate text?", "difficulty": 8},
    ],
    "prompt_skills": [
        {"q": "If you wanted AI to help you write an email, how would you ask?", "difficulty": 2},
        {"q": "What makes a good question to ask an AI?", "difficulty": 4},
        {"q": "How would you use context and examples to improve AI output?", "difficulty": 6},
        {"q": "Explain the concept of few-shot prompting.", "difficulty": 9},
    ],
    "digital_literacy": [
        {"q": "How comfortable are you using a computer or smartphone?", "difficulty": 1},
        {"q": "Have you ever used apps like Google Maps or YouTube?", "difficulty": 2},
        {"q": "Can you explain what a web browser does?", "difficulty": 4},
        {"q": "What is an API?", "difficulty": 7},
    ],
    "coding_ability": [
        {"q": "Have you ever written any code or used a spreadsheet formula?", "difficulty": 1},
        {"q": "Do you know what 'if-else' means in programming?", "difficulty": 3},
        {"q": "Can you write a simple loop in any language?", "difficulty": 6},
        {"q": "Explain the difference between a class and a function.", "difficulty": 8},
    ],
    "domain_knowledge": [
        {"q": "What is your area of expertise?", "difficulty": 1},
        {"q": "How could AI potentially help in your field?", "difficulty": 3},
    ],
}


class SkillAssessor:
    """Adaptive assessment to determine user's AI knowledge level.

    Runs 5 questions (one per category), adapting difficulty
    based on previous answers.
    """

    def __init__(self) -> None:
        self.scores: dict[str, float] = {}
        self.current_category_idx = 0
        self._categories = list(SKILL_CATEGORIES.keys())

    def get_next_question(self, previous_score: float | None = None) -> dict | None:
        """Get the next assessment question.

        Args:
            previous_score: Score (0-10) for the previous answer.

        Returns:
            Dict with 'category', 'question', 'difficulty' or None if done.
        """
        # Record previous score
        if previous_score is not None and self.current_category_idx > 0:
            prev_cat = self._categories[self.current_category_idx - 1]
            self.scores[prev_cat] = previous_score

        if self.current_category_idx >= len(self._categories):
            return None

        category = self._categories[self.current_category_idx]
        questions = _QUESTIONS[category]

        # Choose difficulty based on previous performance
        if self.scores:
            avg = sum(self.scores.values()) / len(self.scores)
            target_diff = avg
        else:
            target_diff = 2  # Start easy

        # Find closest difficulty question
        best = min(questions, key=lambda q: abs(q["difficulty"] - target_diff))

        self.current_category_idx += 1

        return {
            "category": category,
            "category_label": SKILL_CATEGORIES[category]["label"],
            "question": best["q"],
            "difficulty": best["difficulty"],
            "question_number": self.current_category_idx,
            "total_questions": len(self._categories),
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
        else:
            return 6

    def get_results(self) -> dict:
        """Get full assessment results."""
        return {
            "category_scores": dict(self.scores),
            "composite_score": self.calculate_composite_score(),
            "starting_level": self.get_starting_level(),
        }
