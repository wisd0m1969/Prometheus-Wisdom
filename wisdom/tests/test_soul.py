"""Tests for WISDOM Soul module — adaptation, assessment, learning, goals."""

import tempfile

import pytest

from wisdom.soul.adaptation_engine import AdaptationEngine
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


class TestSkillAssessor:
    def setup_method(self):
        self.assessor = SkillAssessor()

    def test_get_first_question(self):
        q = self.assessor.get_next_question()
        assert q is not None
        assert "question" in q
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
        for i in range(5):
            self.assessor.get_next_question(previous_score=5)
        q = self.assessor.get_next_question(previous_score=5)
        assert q is None


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
