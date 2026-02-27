"""Dual-path LLM provider: Ollama (local) → Gemini (cloud fallback).

Automatically detects the best available LLM and provides a
LangChain-compatible interface for both chat and embeddings.
Singleton pattern ensures one shared instance across the app.
"""

from __future__ import annotations

import logging
import time
import threading
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings
    from langchain_core.language_models import BaseChatModel

    from wisdom.core.config import Config

__all__ = ["LLMProvider"]

logger = logging.getLogger(__name__)

_instance: LLMProvider | None = None
_lock = threading.Lock()


class LLMProvider:
    """LLM abstraction layer with automatic Ollama/Gemini switching.

    Singleton: use LLMProvider.get_instance(config) for shared access.

    Priority:
        1. Ollama (local, free, private)
        2. Gemini 2.0 Flash (cloud, free tier)
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self._ollama_available: bool | None = None
        self._llm_cache: BaseChatModel | None = None
        self._embed_cache: Embeddings | None = None
        self._provider_name: str = "none"
        self._detect_provider()

    @classmethod
    def get_instance(cls, config: Config | None = None) -> LLMProvider:
        """Get or create the singleton LLMProvider instance."""
        global _instance
        if _instance is None:
            with _lock:
                if _instance is None:
                    if config is None:
                        from wisdom.core.config import Config
                        config = Config()
                    _instance = cls(config)
        return _instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing)."""
        global _instance
        _instance = None

    def _detect_provider(self) -> None:
        """Auto-detect the best available LLM provider."""
        if self._check_ollama():
            self._provider_name = "ollama"
            logger.info(
                "LLM Provider: Ollama (local) at %s — model: %s",
                self.config.ollama_base_url,
                self.config.ollama_model,
            )
        elif self.config.has_gemini:
            self._provider_name = "gemini"
            logger.info(
                "LLM Provider: Gemini (cloud) — model: %s "
                "(Ollama not available, using cloud fallback)",
                self.config.gemini_model,
            )
        else:
            self._provider_name = "none"
            logger.warning(
                "No LLM provider available! "
                "Start Ollama (https://ollama.ai) or set GOOGLE_API_KEY in .env"
            )

    def _check_ollama(self) -> bool:
        """Check if Ollama is running on localhost."""
        try:
            resp = httpx.get(
                f"{self.config.ollama_base_url}/api/tags", timeout=2.0
            )
            self._ollama_available = resp.status_code == 200
            if self._ollama_available:
                models = [m.get("name", "") for m in resp.json().get("models", [])]
                logger.debug("Ollama models available: %s", models)
        except (httpx.ConnectError, httpx.TimeoutException, httpx.ReadError):
            self._ollama_available = False
        return self._ollama_available

    def is_ollama_available(self) -> bool:
        """Check if Ollama is running on localhost."""
        if self._ollama_available is not None:
            return self._ollama_available
        return self._check_ollama()

    def get_llm(self) -> BaseChatModel:
        """Return the best available LangChain ChatModel.

        Tries Ollama first, falls back to Gemini. Caches the result.
        """
        if self._llm_cache is not None:
            return self._llm_cache

        if self.is_ollama_available():
            self._llm_cache = self._get_ollama_llm()
        elif self.config.has_gemini:
            self._llm_cache = self._get_gemini_llm()
        else:
            raise RuntimeError(
                "No LLM available. Either:\n"
                "  1. Start Ollama: brew install ollama && ollama pull llama3\n"
                "  2. Set GOOGLE_API_KEY in .env (free: https://aistudio.google.com/apikey)"
            )
        return self._llm_cache

    def get_embeddings(self) -> Embeddings:
        """Return the best available embedding model. Caches the result."""
        if self._embed_cache is not None:
            return self._embed_cache

        if self.is_ollama_available():
            self._embed_cache = self._get_ollama_embeddings()
        elif self.config.has_gemini:
            self._embed_cache = self._get_gemini_embeddings()
        else:
            raise RuntimeError("No embedding model available.")
        return self._embed_cache

    def is_local(self) -> bool:
        """True if currently using Ollama (local), False if cloud."""
        return self._provider_name == "ollama"

    def invalidate_cache(self) -> None:
        """Force re-detection of provider on next call."""
        self._ollama_available = None
        self._llm_cache = None
        self._embed_cache = None
        self._detect_provider()

    def health_check(self) -> dict:
        """Return provider status with latency measurement."""
        start = time.perf_counter()
        ollama_ok = self._check_ollama()
        latency_ms = round((time.perf_counter() - start) * 1000, 1)

        provider = "ollama" if ollama_ok else ("gemini" if self.config.has_gemini else "none")
        model = (
            self.config.ollama_model if ollama_ok
            else self.config.gemini_model if self.config.has_gemini
            else "none"
        )

        return {
            "status": "ok" if provider != "none" else "no_provider",
            "provider": provider,
            "model": model,
            "ollama_available": ollama_ok,
            "gemini_configured": self.config.has_gemini,
            "latency_ms": latency_ms,
            "local": ollama_ok,
        }

    # -- Private helpers --

    def _get_ollama_llm(self) -> BaseChatModel:
        from langchain_ollama import ChatOllama

        logger.info("Creating Ollama ChatModel: %s", self.config.ollama_model)
        return ChatOllama(
            model=self.config.ollama_model,
            base_url=self.config.ollama_base_url,
            temperature=0.7,
        )

    def _get_gemini_llm(self) -> BaseChatModel:
        from langchain_google_genai import ChatGoogleGenerativeAI

        logger.info("Creating Gemini ChatModel: %s", self.config.gemini_model)
        return ChatGoogleGenerativeAI(
            model=self.config.gemini_model,
            google_api_key=self.config.google_api_key,
            temperature=0.7,
        )

    def _get_ollama_embeddings(self) -> Embeddings:
        from langchain_ollama import OllamaEmbeddings

        logger.info("Creating Ollama Embeddings: %s", self.config.ollama_embed_model)
        return OllamaEmbeddings(
            model=self.config.ollama_embed_model,
            base_url=self.config.ollama_base_url,
        )

    def _get_gemini_embeddings(self) -> Embeddings:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        logger.info("Creating Gemini Embeddings: text-embedding-004")
        return GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=self.config.google_api_key,
        )
