"""Tests for WISDOM Soul module — adaptation, assessment, learning, goals."""

import tempfile

import pytest

from wisdom.soul.adaptation_engine import AdaptationEngine, AdaptationResult
from wisdom.soul.skill_assessor import SkillAssessor
from wisdom.soul.learning_path import LearningPath
from wisdom.soul.goal_tracker import GoalTracker
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
