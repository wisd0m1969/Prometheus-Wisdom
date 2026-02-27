"""Embedding operations — Ollama nomic-embed-text + Gemini fallback."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wisdom.core.llm_provider import LLMProvider

__all__ = ["EmbeddingManager"]

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Manages text embedding operations using the best available model.

    Priority: Ollama nomic-embed-text (local) → Gemini text-embedding-004
    """

    def __init__(self, llm_provider: LLMProvider) -> None:
        self.llm_provider = llm_provider
        self._embeddings = None

    def _get_model(self):
        if self._embeddings is None:
            self._embeddings = self.llm_provider.get_embeddings()
        return self._embeddings

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding vector for a single text."""
        model = self._get_model()
        return model.embed_query(text)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for multiple texts."""
        model = self._get_model()
        return model.embed_documents(texts)

    def similarity(self, text_a: str, text_b: str) -> float:
        """Compute cosine similarity between two texts."""
        vec_a = self.embed_text(text_a)
        vec_b = self.embed_text(text_b)
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = sum(a * a for a in vec_a) ** 0.5
        norm_b = sum(b * b for b in vec_b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
