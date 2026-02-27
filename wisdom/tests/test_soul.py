"""Tests for WISDOM Soul module — adaptation, assessment, learning, goals, preferences."""

import tempfile
from datetime import datetime, timezone

import pytest

from wisdom.soul.adaptation_engine import AdaptationEngine, AdaptationResult
from wisdom.soul.skill_assessor import SkillAssessor
from wisdom.soul.learning_path import LearningPath, LearningProgressTracker
from wisdom.soul.goal_tracker import GoalTracker
from wisdom.soul.preference_learner import PreferenceLearner
from wisdom.brain.user_profile import UserProfile
from wisdom.brain.memory_manager import Message


class TestAdaptationEngine:
    def setup_method(self):
        self.engine = AdaptationEngine()

    def test_base_difficulty(self):
        profile = UserProfile(id="test", skill_level=5.0)
        level = self.engine.adapt_difficulty(profile, [])
        assert level == 5.0

    def test_decrease_on_confusion(self):
        profile = UserProfile(id="test", skill_level=5.0)
        history = [
            Message(role="user", content="I don't understand", timestamp=""),
            Message(role="user", content="confused", timestamp=""),
        ]
        level = self.engine.adapt_difficulty(profile, history)
        assert level < 5.0

    def test_increase_on_code(self):
        profile = UserProfile(id="test", skill_level=5.0)
        history = [
            Message(role="user", content="def hello(): print('hi')", timestamp=""),
        ]
        level = self.engine.adapt_difficulty(profile, history)
        assert level > 5.0

    def test_recommendations_beginner(self):
        profile = UserProfile(id="test", skill_level=1.0)
        recs = self.engine.get_recommendations(profile)
        assert len(recs) > 0
        assert "What is AI?" in recs

    def test_recommendations_advanced(self):
        profile = UserProfile(id="test", skill_level=9.0)
        recs = self.engine.get_recommendations(profile)
        assert any("AI tool" in r for r in recs)

    def test_full_adaptation(self):
        profile = UserProfile(id="test", skill_level=3.0, name="Test", goals=["Learn AI"])
        history = [Message(role="user", content="hi", timestamp="")]
        result = self.engine.adapt(profile, "teach me about AI", history)
        assert isinstance(result, AdaptationResult)
        assert result.recommended_mode == "teacher"
        assert result.difficulty_level >= 0
        assert isinstance(result.prompt_modifiers, list)

    def test_adapt_to_dict(self):
        profile = UserProfile(id="test", skill_level=5.0)
        result = self.engine.adapt(profile, "hello", [])
        d = result.to_dict()
        assert "recommended_mode" in d
        assert "difficulty_level" in d

    def test_detect_code_mode(self):
        profile = UserProfile(id="test", skill_level=5.0, name="Test")
        history = [Message(role="user", content="hi", timestamp="")]
        result = self.engine.adapt(profile, "def hello(): pass", history)
        assert result.recommended_mode == "code_helper"

    def test_detect_quiz_mode(self):
        profile = UserProfile(id="test", skill_level=5.0, name="Test")
        history = [Message(role="user", content="hi", timestamp="")]
        result = self.engine.adapt(profile, "quiz me on AI", history)
        assert result.recommended_mode == "quiz_master"

    def test_interest_recommendations(self):
        profile = UserProfile(id="test", skill_level=3.0, interests=["farming"])
        recs = self.engine.get_recommendations(profile)
        assert any("crop" in r.lower() or "farm" in r.lower() for r in recs)


class TestSkillAssessor:
    def setup_method(self):
        self.assessor = SkillAssessor()

    def test_get_first_question(self):
        q = self.assessor.get_next_question()
        assert q is not None
        assert "question_number" in q
        assert q["question_number"] == 1

    def test_full_assessment(self):
        scores = [3, 4, 5, 2, 6]
        q = self.assessor.get_next_question()
        for score in scores:
            q = self.assessor.get_next_question(previous_score=score)

        results = self.assessor.get_results()
        assert "composite_score" in results
        assert 0 <= results["composite_score"] <= 10
        assert results["starting_level"] >= 1

    def test_done_returns_none(self):
        # 10 questions: 2 per 5 categories
        q = self.assessor.get_next_question()
        while q is not None:
            q = self.assessor.get_next_question(previous_score=5)
        assert q is None

    def test_is_completed(self):
        assert not self.assessor.is_completed
        q = self.assessor.get_next_question()
        while q is not None:
            q = self.assessor.get_next_question(previous_score=5)
        assert self.assessor.is_completed

    def test_answer_choice_question(self):
        self.assessor.start_assessment()
        # First question is ai_awareness choice with options
        result = self.assessor.answer_question("Yes")
        # Should return next question or grading info
        assert result is not None

    def test_adaptive_skip_on_zero(self):
        self.assessor.start_assessment()
        # Score 0 on first question should skip second in category
        next_q = self.assessor.get_next_question(previous_score=0)
        if next_q:
            # Should have moved to next category
            assert next_q["category"] != "ai_awareness" or next_q["question_number"] > 2

    def test_starting_level_mapping(self):
        self.assessor.scores = {
            "ai_awareness": 0, "prompt_skills": 0,
            "digital_literacy": 0, "coding_ability": 0, "domain_knowledge": 0,
        }
        assert self.assessor.get_starting_level() == 1

        self.assessor.scores = {
            "ai_awareness": 10, "prompt_skills": 10,
            "digital_literacy": 10, "coding_ability": 10, "domain_knowledge": 10,
        }
        assert self.assessor.get_starting_level() >= 6


class TestLearningPath:
    def setup_method(self):
        self.path = LearningPath()

    def test_get_module(self):
        module = self.path.get_module(1)
        assert module is not None
        assert module["name"] == "Hello AI"
        assert len(module["lessons"]) == 4

    def test_all_7_levels(self):
        for level in range(1, 8):
            assert self.path.get_module(level) is not None

    def test_get_lesson(self):
        lesson = self.path.get_lesson(1, 0)
        assert lesson is not None
        assert lesson["id"] == "1.1"

    def test_progress_empty(self):
        progress = self.path.get_progress([])
        assert progress["overall"]["percentage"] == 0

    def test_progress_partial(self):
        progress = self.path.get_progress(["1.1", "1.2"])
        assert progress[1]["completed"] == 2
        assert progress[1]["percentage"] == 50

    def test_next_lesson(self):
        next_l = self.path.get_next_lesson([])
        assert next_l is not None
        assert next_l["level"] == 1
        assert next_l["id"] == "1.1"

    def test_next_lesson_after_some(self):
        next_l = self.path.get_next_lesson(["1.1", "1.2"])
        assert next_l["id"] == "1.3"

    def test_take_quiz(self):
        questions = self.path.take_quiz(1)
        assert questions is not None
        assert len(questions) >= 2

    def test_grade_quiz_mc(self):
        # Answer all questions for level 1
        result = self.path.grade_quiz(1, [1, True, 5])
        assert "score" in result
        assert "passed" in result
        assert result["max_points"] > 0

    def test_lesson_content_prompt(self):
        prompt = self.path.get_lesson_content_prompt(1, 0, "farming")
        assert prompt is not None
        assert "farming" in prompt

    def test_generate_personalized_path(self):
        path = self.path.generate_personalized_path(1, ["farming", "coding"])
        assert 1 in path
        assert "personalized_for" in path[1]
        assert "farming" in path[1]["personalized_for"]


class TestGoalTracker:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tracker = GoalTracker(self.tmp.name)

    def test_create_goal(self):
        goal_id = self.tracker.create_goal("user1", "Learn AI basics", ["Read intro", "Try chatbot"])
        assert goal_id > 0

    def test_get_goals(self):
        self.tracker.create_goal("user1", "Learn Python")
        goals = self.tracker.get_goals("user1")
        assert len(goals) == 1
        assert goals[0]["description"] == "Learn Python"

    def test_update_progress(self):
        goal_id = self.tracker.create_goal("user1", "Test goal")
        self.tracker.update_progress(goal_id, 0.5)
        goals = self.tracker.get_goals("user1")
        assert goals[0]["progress"] == 0.5

    def test_complete_milestone(self):
        goal_id = self.tracker.create_goal("user1", "Goal", ["Step 1", "Step 2"])
        self.tracker.complete_milestone(goal_id, 0)
        goals = self.tracker.get_goals("user1")
        assert goals[0]["milestones"][0]["done"] is True
        assert goals[0]["progress"] == 0.5

    def test_award_badge(self):
        awarded = self.tracker.award_badge("user1", "first_contact")
        assert awarded is True
        # Can't earn same badge twice
        awarded2 = self.tracker.award_badge("user1", "first_contact")
        assert awarded2 is False

    def test_get_badges(self):
        self.tracker.award_badge("user1", "first_contact")
        self.tracker.award_badge("user1", "curious_mind")
        badges = self.tracker.get_badges("user1")
        assert len(badges) == 2

    def test_celebration_message(self):
        msg = self.tracker.get_celebration_message("first_contact")
        assert "first AI conversation" in msg.lower() or "welcome" in msg.lower()

    def test_celebration_message_unknown(self):
        msg = self.tracker.get_celebration_message("unknown_badge")
        assert "congratulations" in msg.lower()

    def test_milestone_celebration(self):
        msg = self.tracker.get_milestone_celebration(1, 0)
        assert len(msg) > 0

    def test_award_badge_with_message(self):
        awarded, msg = self.tracker.award_badge_with_message("user_cel", "first_contact")
        assert awarded is True
        assert len(msg) > 0
        # Second time should not award
        awarded2, msg2 = self.tracker.award_badge_with_message("user_cel", "first_contact")
        assert awarded2 is False
        assert msg2 == ""


class TestLearningProgressTracker:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tracker = LearningProgressTracker(self.tmp.name)

    def test_start_lesson(self):
        self.tracker.start_lesson("user1", "1.1", 1)
        progress = self.tracker.get_progress("user1")
        assert len(progress) == 1
        assert progress[0]["module_id"] == "1.1"
        assert progress[0]["completed"] is False

    def test_complete_lesson(self):
        self.tracker.complete_lesson("user1", "1.1", 1, score=8.0)
        completed = self.tracker.get_completed_lessons("user1")
        assert "1.1" in completed

    def test_get_completed_lessons(self):
        self.tracker.complete_lesson("user1", "1.1", 1, score=9.0)
        self.tracker.complete_lesson("user1", "1.2", 1, score=7.0)
        self.tracker.start_lesson("user1", "1.3", 1)
        completed = self.tracker.get_completed_lessons("user1")
        assert len(completed) == 2
        assert "1.3" not in completed

    def test_get_level_score(self):
        self.tracker.complete_lesson("user1", "1.1", 1, score=8.0)
        self.tracker.complete_lesson("user1", "1.2", 1, score=6.0)
        avg = self.tracker.get_level_score("user1", 1)
        assert avg == 7.0

    def test_get_level_score_no_data(self):
        avg = self.tracker.get_level_score("nobody", 1)
        assert avg is None


class TestPreferenceLearner:
    def setup_method(self):
        self.learner = PreferenceLearner()
        self.profile = UserProfile(id="test", skill_level=3.0)

    def test_default_preferences(self):
        result = self.learner.analyze(self.profile, [])
        assert result["learning_style"] == "balanced"
        assert result["response_length"] == "balanced"
        assert result["preferred_topics"] == []

    def test_learn_coding_topic(self):
        now = datetime.now(timezone.utc).isoformat()
        history = [
            Message(role="user", content="How do I write Python code?", timestamp=now),
            Message(role="user", content="Show me a Python function", timestamp=now),
            Message(role="user", content="Help me code a loop", timestamp=now),
        ]
        result = self.learner.analyze(self.profile, history)
        assert "coding" in result["preferred_topics"]

    def test_learn_step_by_step_style(self):
        now = datetime.now(timezone.utc).isoformat()
        history = [
            Message(role="user", content="Explain step by step how AI works", timestamp=now),
            Message(role="user", content="Show me step by step", timestamp=now),
        ]
        result = self.learner.analyze(self.profile, history)
        assert result["learning_style"] == "step_by_step"

    def test_learn_concise_preference(self):
        now = datetime.now(timezone.utc).isoformat()
        history = [
            Message(role="user", content="Hi", timestamp=now),
            Message(role="user", content="OK", timestamp=now),
            Message(role="user", content="Yes", timestamp=now),
            Message(role="user", content="Next", timestamp=now),
        ]
        result = self.learner.analyze(self.profile, history)
        assert result["response_length"] == "concise"

    def test_learn_technical_complexity(self):
        now = datetime.now(timezone.utc).isoformat()
        profile = UserProfile(id="test", skill_level=8.0)
        history = [
            Message(role="user", content="Explain the neural network architecture", timestamp=now),
            Message(role="user", content="How does gradient descent work with embedding vectors?", timestamp=now),
        ]
        result = self.learner.analyze(profile, history)
        assert result["complexity"] == "technical"

    def test_update_profile(self):
        now = datetime.now(timezone.utc).isoformat()
        history = [
            Message(role="user", content="Show me an example of AI", timestamp=now),
            Message(role="user", content="Give me another example", timestamp=now),
        ]
        updated = self.learner.update_profile(self.profile, history)
        assert updated is True
        assert "learning_style" in self.profile.preferences

    def test_get_prompt_hints_empty(self):
        hints = self.learner.get_prompt_hints(self.profile)
        assert isinstance(hints, list)
        assert len(hints) == 0  # No preferences yet

    def test_get_prompt_hints_with_prefs(self):
        self.profile.preferences = {
            "learning_style": "examples",
            "response_length": "concise",
            "preferred_topics": ["coding", "ai_basics"],
        }
        hints = self.learner.get_prompt_hints(self.profile)
        assert any("examples" in h.lower() for h in hints)
        assert any("short" in h.lower() for h in hints)
        assert any("coding" in h.lower() for h in hints)

    def test_learn_active_hours(self):
        morning = datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc).isoformat()
        history = [
            Message(role="user", content="Hello", timestamp=morning),
            Message(role="user", content="Good morning", timestamp=morning),
        ]
        result = self.learner.analyze(self.profile, history)
        assert result["active_hours"] == "morning"
