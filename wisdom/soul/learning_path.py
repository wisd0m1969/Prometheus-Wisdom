"""7-level learning curriculum — from AI basics to building AI tools."""

from __future__ import annotations

from wisdom.core.constants import LEARNING_LEVELS

__all__ = ["LearningPath"]

# Module definitions
_MODULES = {
    1: {
        "name": "Hello AI",
        "lessons": [
            {"id": "1.1", "title": "What is AI?", "description": "AI explained with real-life examples"},
            {"id": "1.2", "title": "AI is NOT magic", "description": "Setting realistic expectations"},
            {"id": "1.3", "title": "Your first AI conversation", "description": "Practice talking to WISDOM"},
            {"id": "1.4", "title": "Quiz: Basic AI concepts", "description": "Test your understanding"},
        ],
    },
    2: {
        "name": "Talk to AI",
        "lessons": [
            {"id": "2.1", "title": "How to ask good questions", "description": "The art of prompting"},
            {"id": "2.2", "title": "Context and specificity", "description": "Giving AI useful information"},
            {"id": "2.3", "title": "Common mistakes", "description": "What NOT to do with AI"},
            {"id": "2.4", "title": "Practice: 10 prompt challenges", "description": "Hands-on exercises"},
        ],
    },
    3: {
        "name": "AI in Daily Life",
        "lessons": [
            {"id": "3.1", "title": "AI for learning", "description": "Use AI as a study buddy"},
            {"id": "3.2", "title": "AI for work", "description": "Productivity with AI"},
            {"id": "3.3", "title": "AI for creativity", "description": "Art, music, writing with AI"},
            {"id": "3.4", "title": "Project: Solve a real problem", "description": "Apply AI to your life"},
        ],
    },
    4: {
        "name": "How AI Thinks",
        "lessons": [
            {"id": "4.1", "title": "How language models work", "description": "Tokens, attention, generation"},
            {"id": "4.2", "title": "Training data and bias", "description": "Where AI knowledge comes from"},
            {"id": "4.3", "title": "Limitations and hallucinations", "description": "When AI gets it wrong"},
            {"id": "4.4", "title": "Ethics and responsible use", "description": "Being a good AI citizen"},
        ],
    },
    5: {
        "name": "Code with AI",
        "lessons": [
            {"id": "5.1", "title": "What is programming?", "description": "Code explained simply"},
            {"id": "5.2", "title": "Your first Python program", "description": "Hello World and beyond"},
            {"id": "5.3", "title": "Using AI to write code", "description": "AI as your coding assistant"},
            {"id": "5.4", "title": "Project: Build a calculator", "description": "Your first real program"},
        ],
    },
    6: {
        "name": "Build with AI",
        "lessons": [
            {"id": "6.1", "title": "Web app fundamentals", "description": "HTML, CSS, Python basics"},
            {"id": "6.2", "title": "Working with APIs", "description": "Connect to the world"},
            {"id": "6.3", "title": "Testing and debugging", "description": "Make your code reliable"},
            {"id": "6.4", "title": "Project: Build a personal tool", "description": "Your first web app"},
        ],
    },
    7: {
        "name": "Create AI Tools",
        "lessons": [
            {"id": "7.1", "title": "LLMs and prompt engineering", "description": "Advanced AI techniques"},
            {"id": "7.2", "title": "Building AI applications", "description": "LangChain, APIs, RAG"},
            {"id": "7.3", "title": "Contributing to open source", "description": "Join the community"},
            {"id": "7.4", "title": "Project: Deploy your AI tool", "description": "Share with the world"},
        ],
    },
}


class LearningPath:
    """Personalized 7-level learning curriculum.

    Each level has 4 lessons with interactive exercises and quizzes.
    Content adapts to user's language, interests, and pace.
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

    def get_progress(self, completed_lessons: list[str]) -> dict:
        """Calculate learning progress.

        Args:
            completed_lessons: List of completed lesson IDs (e.g., ["1.1", "1.2"])

        Returns:
            Progress info per level and overall.
        """
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
