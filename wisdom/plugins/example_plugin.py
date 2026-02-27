"""Example WISDOM plugin — demonstrates the plugin API.

This plugin adds a polite greeting prefix and a learning tip suffix
to every response. It also provides context about the current time.
"""

from __future__ import annotations

from datetime import datetime, timezone

from wisdom.plugins import WisdomPlugin, hook


class LearningTipsPlugin(WisdomPlugin):
    """Adds contextual learning tips to responses."""

    name = "learning_tips"
    version = "1.0.0"
    description = "Adds helpful learning tips and time-aware context"

    @hook("context_provider", priority=50)
    def provide_time_context(self, **kwargs) -> str:
        """Add current time context for time-sensitive responses."""
        now = datetime.now(timezone.utc)
        return f"Current UTC time: {now.strftime('%Y-%m-%d %H:%M')}"
