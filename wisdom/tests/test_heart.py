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

    def test_sanitize_thai_national_id(self):
        text = "บัตรประชาชน 1-1234-56789-01-2"
        result = self.pm.sanitize(text)
        assert "[THAI_ID]" in result

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

    def test_is_safe_for_cloud_clean(self):
        assert self.pm.is_safe_for_cloud("Hello, how are you?")

    def test_is_safe_for_cloud_with_pii(self):
        assert not self.pm.is_safe_for_cloud("My email is test@example.com")

    def test_is_safe_for_cloud_sensitive_keyword(self):
        assert not self.pm.is_safe_for_cloud("What is my password?")

    def test_sanitize_for_cloud(self):
        text = "Email: a@b.com"
        sanitized, findings = self.pm.sanitize_for_cloud(text)
        assert "[EMAIL]" in sanitized
        assert len(findings) >= 1

    def test_whitelist(self):
        self.pm.add_whitelist("test@example.com")
        self.pm.remove_whitelist("test@example.com")
        # Just verify methods don't error


class TestFederatedCore:
    def setup_method(self):
        self.fc = FederatedCore()

    def test_opt_in_out(self):
        assert not self.fc.opted_in
        self.fc.opt_in()
        assert self.fc.opted_in
        self.fc.opt_out()
        assert not self.fc.opted_in

    def test_opt_in_with_user_id(self):
        self.fc.opt_in("user1")
        assert self.fc.is_opted_in("user1")
        assert not self.fc.is_opted_in("user2")
        self.fc.opt_out("user1")
        assert not self.fc.is_opted_in("user1")

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

    def test_collect_local_metrics(self):
        self.fc.record_topic_interaction("AI", 8.0)
        self.fc.record_topic_interaction("AI", 6.0)
        self.fc.record_confusion("AI")
        metrics = self.fc.collect_local_metrics()
        assert metrics["topic_counts"]["AI"] == 2
        assert metrics["avg_scores"]["AI"] == 7.0
        assert metrics["confusion_count"] == 1
        assert metrics["total_interactions"] == 2

    def test_preview_shared_data(self):
        self.fc.record_topic_interaction("test", 5.0)
        assert self.fc.preview_shared_data() is None
        self.fc.opt_in("user1")
        preview = self.fc.preview_shared_data()
        assert preview is not None
        assert "opted_in_users" in preview

    def test_record_effective_explanation(self):
        self.fc.record_effective_explanation("AI", "analogy")
        assert len(self.fc._local_metrics["effective_explanations"]) == 1


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

    def test_report(self):
        qa_id = self.ck.submit("Bad Q?", "Bad A", "en")
        self.ck.report(qa_id, "inappropriate")
        self.ck.report(qa_id, "inappropriate")
        self.ck.report(qa_id, "inappropriate")
        # Reported items should be hidden from search
        results = self.ck.search("Bad", "en")
        assert len(results) == 0

    def test_submit_sanitizes_pii(self):
        qa_id = self.ck.submit(
            "My email is test@example.com",
            "Answer about email",
            "en",
        )
        results = self.ck.search("EMAIL", "en")
        assert len(results) >= 1
        assert "test@example.com" not in results[0]["question"]

    def test_get_by_category(self):
        self.ck.submit("Q?", "A", "en", "coding")
        results = self.ck.get_by_category("coding", "en")
        assert len(results) == 1


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

    def test_improvement_suggestions_empty(self):
        suggestions = self.fb.get_improvement_suggestions()
        assert len(suggestions) >= 1
        assert "Not enough" in suggestions[0]

    def test_improvement_suggestions_low_rating(self):
        for _ in range(5):
            self.fb.submit(2, "Bad")
        suggestions = self.fb.get_improvement_suggestions()
        assert any("low" in s.lower() or "satisfaction" in s.lower() for s in suggestions)

    def test_get_stats(self):
        self.fb.submit(5)
        self.fb.submit(3)
        stats = self.fb.get_stats()
        assert stats["total"] == 2
        assert stats["average"] == 4.0
        assert stats["distribution"][5] == 1
        assert stats["distribution"][3] == 1

    def test_submit_with_category(self):
        fb_id = self.fb.submit(4, "UI is nice", category="ui")
        assert fb_id > 0
