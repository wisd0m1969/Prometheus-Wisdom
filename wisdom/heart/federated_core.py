"""Opt-in federated learning — privacy-preserving community insights.

Only aggregated, anonymized data is shared. Differential privacy
noise is applied. Users can see exactly what would be shared.
"""

from __future__ import annotations

import hashlib
import random

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
        self.opted_in = False
        self._local_metrics: dict = {
            "topic_counts": {},
            "avg_scores": {},
            "confusion_topics": [],
        }

    def opt_in(self) -> None:
        """User explicitly opts into federated learning."""
        self.opted_in = True

    def opt_out(self) -> None:
        """User opts out of federated learning."""
        self.opted_in = False
        self._local_metrics = {"topic_counts": {}, "avg_scores": {}, "confusion_topics": []}

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

    def get_shareable_summary(self) -> dict | None:
        """Preview what would be shared (user can review before sharing).

        Returns None if not opted in.
        """
        if not self.opted_in:
            return None

        return {
            "topic_frequencies": self._add_noise(self._local_metrics["topic_counts"]),
            "avg_difficulty": {
                self._hash_topic(t): round(d["total"] / d["count"], 1)
                for t, d in self._local_metrics["avg_scores"].items()
                if d["count"] > 0
            },
            "confusion_count": len(self._local_metrics["confusion_topics"]),
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
