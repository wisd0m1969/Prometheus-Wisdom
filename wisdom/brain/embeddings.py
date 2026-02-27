"""Embedding operations — Ollama nomic-embed-text + Gemini fallback.

Provides text embedding, batch embedding, similarity scoring,
and ChromaDB collection management.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wisdom.core.llm_provider import LLMProvider

__all__ = ["EmbeddingManager"]

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Manages text embedding operations and ChromaDB collections.

    Priority: Ollama nomic-embed-text (local) → Gemini text-embedding-004
    """

    def __init__(self, llm_provider: LLMProvider) -> None:
        self.llm_provider = llm_provider
        self._embeddings = None
        self._chroma_client = None

    def _get_model(self):
        if self._embeddings is None:
            self._embeddings = self.llm_provider.get_embeddings()
        return self._embeddings

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding vector for a single text (768-dim)."""
        model = self._get_model()
        return model.embed_query(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
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

    # ─── ChromaDB Collection Management ───────────────────────

    def init_chroma(self, persist_path: str = "./data/chroma") -> None:
        """Initialize ChromaDB client."""
        try:
            import chromadb
            self._chroma_client = chromadb.PersistentClient(path=persist_path)
            logger.info("EmbeddingManager: ChromaDB initialized at %s", persist_path)
        except Exception as e:
            logger.warning("ChromaDB unavailable: %s", e)

    def get_or_create_collection(self, name: str):
        """Get or create a named ChromaDB collection."""
        if not self._chroma_client:
            return None
        return self._chroma_client.get_or_create_collection(name=name)

    def add_documents(
        self,
        collection,
        texts: list[str],
        metadatas: list[dict] | None = None,
        ids: list[str] | None = None,
    ) -> None:
        """Add documents to a ChromaDB collection."""
        if collection is None:
            return
        if ids is None:
            from datetime import datetime, timezone
            ids = [f"doc_{i}_{datetime.now(timezone.utc).isoformat()}" for i in range(len(texts))]
        collection.add(
            documents=texts,
            metadatas=metadatas or [{} for _ in texts],
            ids=ids,
        )

    def query(
        self,
        collection,
        query_text: str,
        top_k: int = 5,
        where: dict | None = None,
    ) -> dict:
        """Query a ChromaDB collection for similar documents."""
        if collection is None:
            return {"documents": [[]], "distances": [[]], "metadatas": [[]]}
        kwargs = {"query_texts": [query_text], "n_results": top_k}
        if where:
            kwargs["where"] = where
        return collection.query(**kwargs)
