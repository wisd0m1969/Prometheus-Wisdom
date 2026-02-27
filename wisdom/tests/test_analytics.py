"""Tests for WISDOM Analytics module."""

import tempfile
from datetime import datetime, timezone, timedelta

import pytest

from wisdom.core.analytics import Analytics


class TestAnalytics:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.analytics = Analytics(self.tmp.name)

    def test_track_event(self):
        self.analytics.track("user1", "chat_message", {"mode": "teacher"})
        counts = self.analytics.get_event_counts()
        assert "chat_message" in counts
        assert counts["chat_message"] == 1

    def test_track_multiple_events(self):
        self.analytics.track("user1", "chat_message")
        self.analytics.track("user1", "chat_message")
        self.analytics.track("user1", "lesson_start")
        counts = self.analytics.get_event_counts()
        assert counts["chat_message"] == 2
        assert counts["lesson_start"] == 1

    def test_total_users(self):
        self.analytics.track("user1", "chat_message")
        self.analytics.track("user2", "chat_message")
        self.analytics.track("user1", "chat_message")
        assert self.analytics.get_total_users() == 2

    def test_daily_active_users(self):
        self.analytics.track("user1", "chat_message")
        self.analytics.track("user2", "chat_message")
        dau = self.analytics.get_daily_active_users(days=7)
        assert len(dau) >= 1
        assert dau[0]["active_users"] == 2

    def test_lesson_completion_rate(self):
        self.analytics.track("user1", "lesson_start")
        self.analytics.track("user1", "lesson_complete")
        self.analytics.track("user2", "lesson_start")
        rate = self.analytics.get_lesson_completion_rate()
        assert rate == 50.0

    def test_lesson_completion_rate_no_data(self):
        rate = self.analytics.get_lesson_completion_rate()
        assert rate == 0.0

    def test_retention_rate_no_data(self):
        rate = self.analytics.get_retention_rate()
        assert rate == 0.0

    def test_avg_session_duration_no_data(self):
        avg = self.analytics.get_avg_session_duration()
        assert avg == 0.0

    def test_get_summary(self):
        self.analytics.track("user1", "chat_message")
        summary = self.analytics.get_summary(days=30)
        assert "total_users" in summary
        assert "daily_active_users" in summary
        assert "event_counts" in summary
        assert "retention_rate_7d" in summary
        assert "lesson_completion_rate" in summary
        assert "avg_session_minutes" in summary
        assert summary["total_users"] == 1
