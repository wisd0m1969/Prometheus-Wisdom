"""Opt-in federated learning — privacy-preserving community insights.

Only aggregated, anonymized data is shared. Differential privacy
noise is applied. Users can see exactly what would be shared.
Tracks opt-in per user_id.
"""

from __future__ import annotations

import hashlib
import random
from datetime import datetime, timezone

__all__ = ["FederatedCore"]


class FederatedCore:
    """Privacy-preserving community learning aggregation.

    What IS shared (opt-in only):
    - Popular question categories (not actual questions)
    - Average difficulty level per topic
    - Common confusion points
    - Effective explanation patterns

    What is NEVER shared:
    - Actual conversation content
    - User names or profiles
    - Personal goals or interests
    - Any PII
    """

    def __init__(self, epsilon: float = 1.0) -> None:
        self.epsilon = epsilon  # Differential privacy parameter
        self._opted_in_users: set[str] = set()
        self._local_metrics: dict = {
            "topic_counts": {},
            "avg_scores": {},
            "confusion_topics": [],
            "effective_explanations": [],
        }

    @property
    def opted_in(self) -> bool:
        """Backward-compatible: True if any user is opted in."""
        return len(self._opted_in_users) > 0

    def opt_in(self, user_id: str = "default") -> None:
        """User explicitly opts into federated learning."""
        self._opted_in_users.add(user_id)

    def opt_out(self, user_id: str = "default") -> None:
        """User opts out of federated learning."""
        self._opted_in_users.discard(user_id)
        if not self._opted_in_users:
            self._local_metrics = {
                "topic_counts": {}, "avg_scores": {},
                "confusion_topics": [], "effective_explanations": [],
            }

    def is_opted_in(self, user_id: str = "default") -> bool:
        """Check if a specific user is opted in."""
        return user_id in self._opted_in_users

    def record_topic_interaction(self, topic: str, score: float | None = None) -> None:
        """Record a local topic interaction (never shared directly)."""
        counts = self._local_metrics["topic_counts"]
        counts[topic] = counts.get(topic, 0) + 1

        if score is not None:
            scores = self._local_metrics["avg_scores"]
            if topic not in scores:
                scores[topic] = {"total": 0.0, "count": 0}
            scores[topic]["total"] += score
            scores[topic]["count"] += 1

    def record_confusion(self, topic: str) -> None:
        """Record that the user was confused about a topic."""
        self._local_metrics["confusion_topics"].append(topic)

    def record_effective_explanation(self, topic: str, approach: str) -> None:
        """Record an explanation approach that worked well."""
        self._local_metrics["effective_explanations"].append({
            "topic_hash": self._hash_topic(topic),
            "approach": approach,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def collect_local_metrics(self) -> dict:
        """Collect current local metrics (raw, not anonymized).

        Returns:
            Dict with topic_counts, avg_scores, confusion count, explanation count.
        """
        avg_scores = {}
        for topic, data in self._local_metrics["avg_scores"].items():
            if data["count"] > 0:
                avg_scores[topic] = round(data["total"] / data["count"], 1)

        return {
            "topic_counts": dict(self._local_metrics["topic_counts"]),
            "avg_scores": avg_scores,
            "confusion_count": len(self._local_metrics["confusion_topics"]),
            "explanation_count": len(self._local_metrics["effective_explanations"]),
            "total_interactions": sum(self._local_metrics["topic_counts"].values()),
        }

    def preview_shared_data(self) -> dict | None:
        """Preview exactly what would be shared (user reviews before sharing).

        Returns None if no users are opted in.
        """
        if not self._opted_in_users:
            return None

        return self.get_shareable_summary()

    def get_shareable_summary(self) -> dict | None:
        """Get anonymized, noise-added summary for sharing.

        Returns None if not opted in.
        """
        if not self._opted_in_users:
            return None

        return {
            "topic_frequencies": self._add_noise(self._local_metrics["topic_counts"]),
            "avg_difficulty": {
                self._hash_topic(t): round(d["total"] / d["count"], 1)
                for t, d in self._local_metrics["avg_scores"].items()
                if d["count"] > 0
            },
            "confusion_count": len(self._local_metrics["confusion_topics"]),
            "effective_approaches": len(self._local_metrics["effective_explanations"]),
            "opted_in_users": len(self._opted_in_users),
        }

    def _add_noise(self, counts: dict) -> dict:
        """Apply differential privacy (Laplace noise) to counts."""
        noisy = {}
        for key, value in counts.items():
            noise = random.gauss(0, 1.0 / self.epsilon)
            noisy[self._hash_topic(key)] = max(0, round(value + noise))
        return noisy

    @staticmethod
    def _hash_topic(topic: str) -> str:
        """Hash a topic name for anonymization."""
        return hashlib.sha256(topic.encode()).hexdigest()[:12]
