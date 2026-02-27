"""Tests for WISDOM Heart module — privacy, federated learning, community."""

import tempfile

import pytest

from wisdom.heart.privacy_manager import PrivacyManager
from wisdom.heart.federated_core import FederatedCore
from wisdom.heart.community_knowledge import CommunityKnowledge
from wisdom.heart.feedback_loop import FeedbackLoop


class TestPrivacyManager:
    def setup_method(self):
        self.pm = PrivacyManager()

    def test_sanitize_email(self):
        text = "My email is test@example.com please help"
        result = self.pm.sanitize(text)
        assert "[EMAIL]" in result
        assert "test@example.com" not in result

    def test_sanitize_phone(self):
        text = "Call me at +1-555-123-4567"
        result = self.pm.sanitize(text)
        assert "[PHONE]" in result

    def test_sanitize_credit_card(self):
        text = "My card is 4532-1234-5678-9012"
        result = self.pm.sanitize(text)
        assert "[CARD]" in result

    def test_sanitize_ssn(self):
        text = "My SSN is 123-45-6789"
        result = self.pm.sanitize(text)
        assert "[ID]" in result

    def test_no_pii(self):
        text = "Hello, how are you today?"
        assert self.pm.sanitize(text) == text

    def test_disabled(self):
        pm = PrivacyManager(enabled=False)
        text = "email: test@example.com"
        assert pm.sanitize(text) == text

    def test_detect_pii(self):
        text = "Email: a@b.com and phone 555-123-4567"
        findings = self.pm.detect_pii(text)
        assert len(findings) >= 1
        types = [f["type"] for f in findings]
        assert "email" in types


class TestFederatedCore:
    def setup_method(self):
        self.fc = FederatedCore()

    def test_opt_in_out(self):
        assert not self.fc.opted_in
        self.fc.opt_in()
        assert self.fc.opted_in
        self.fc.opt_out()
        assert not self.fc.opted_in

    def test_record_topic(self):
        self.fc.record_topic_interaction("AI Basics", 7.5)
        assert self.fc._local_metrics["topic_counts"]["AI Basics"] == 1

    def test_shareable_summary_requires_opt_in(self):
        self.fc.record_topic_interaction("test", 5.0)
        assert self.fc.get_shareable_summary() is None
        self.fc.opt_in()
        summary = self.fc.get_shareable_summary()
        assert summary is not None
        assert "topic_frequencies" in summary


class TestCommunityKnowledge:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.ck = CommunityKnowledge(self.tmp.name)

    def test_submit_and_search(self):
        qa_id = self.ck.submit("What is AI?", "AI is artificial intelligence", "en")
        assert qa_id > 0
        results = self.ck.search("AI", "en")
        assert len(results) >= 1
        assert results[0]["question"] == "What is AI?"

    def test_voting(self):
        qa_id = self.ck.submit("Test?", "Test answer", "en")
        self.ck.vote(qa_id, upvote=True)
        self.ck.vote(qa_id, upvote=True)
        top = self.ck.get_top("en")
        assert any(q["upvotes"] == 2 for q in top)


class TestFeedbackLoop:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.fb = FeedbackLoop(self.tmp.name)

    def test_submit_feedback(self):
        fb_id = self.fb.submit(5, "Great!", "user1")
        assert fb_id > 0

    def test_average_rating(self):
        self.fb.submit(5)
        self.fb.submit(3)
        avg = self.fb.get_average_rating()
        assert avg == 4.0

    def test_recent_feedback(self):
        self.fb.submit(4, "Good")
        recent = self.fb.get_recent()
        assert len(recent) == 1
