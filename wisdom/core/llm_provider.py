"""Dual-path LLM provider: Ollama (local) → Gemini (cloud fallback).

Automatically detects the best available LLM and provides a
LangChain-compatible interface for both chat and embeddings.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings
    from langchain_core.language_models import BaseChatModel

    from wisdom.core.config import Config

__all__ = ["LLMProvider"]

logger = logging.getLogger(__name__)


class LLMProvider:
    """LLM abstraction layer with automatic Ollama/Gemini switching.

    Priority:
        1. Ollama (local, free, private)
        2. Gemini 2.0 Flash (cloud, free tier)
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self._ollama_available: bool | None = None

    def is_ollama_available(self) -> bool:
        """Check if Ollama is running on localhost."""
        if self._ollama_available is not None:
            return self._ollama_available
        try:
            resp = httpx.get(f"{self.config.ollama_base_url}/api/tags", timeout=3.0)
            self._ollama_available = resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            self._ollama_available = False
        return self._ollama_available

    def get_llm(self) -> BaseChatModel:
        """Return the best available LangChain ChatModel.

        Tries Ollama first, falls back to Gemini.
        """
        if self.is_ollama_available():
            return self._get_ollama_llm()
        if self.config.has_gemini:
            return self._get_gemini_llm()
        raise RuntimeError(
            "No LLM available. Either start Ollama (https://ollama.ai) "
            "or set GOOGLE_API_KEY in .env for Gemini."
        )

    def get_embeddings(self) -> Embeddings:
        """Return the best available embedding model."""
        if self.is_ollama_available():
            return self._get_ollama_embeddings()
        if self.config.has_gemini:
            return self._get_gemini_embeddings()
        raise RuntimeError("No embedding model available.")

    def is_local(self) -> bool:
        """True if currently using Ollama (local), False if cloud."""
        return self.is_ollama_available()

    def health_check(self) -> dict:
        """Return provider status."""
        ollama_ok = self.is_ollama_available()
        return {
            "provider": "ollama" if ollama_ok else "gemini",
            "ollama_available": ollama_ok,
            "gemini_configured": self.config.has_gemini,
            "model": self.config.ollama_model if ollama_ok else self.config.gemini_model,
        }

    # -- Private helpers --

    def _get_ollama_llm(self) -> BaseChatModel:
        from langchain_ollama import ChatOllama

        logger.info("Using Ollama LLM: %s", self.config.ollama_model)
        return ChatOllama(
            model=self.config.ollama_model,
            base_url=self.config.ollama_base_url,
            temperature=0.7,
        )

    def _get_gemini_llm(self) -> BaseChatModel:
        from langchain_google_genai import ChatGoogleGenerativeAI

        logger.info("Using Gemini LLM: %s", self.config.gemini_model)
        return ChatGoogleGenerativeAI(
            model=self.config.gemini_model,
            google_api_key=self.config.google_api_key,
            temperature=0.7,
        )

    def _get_ollama_embeddings(self) -> Embeddings:
        from langchain_ollama import OllamaEmbeddings

        return OllamaEmbeddings(
            model=self.config.ollama_embed_model,
            base_url=self.config.ollama_base_url,
        )

    def _get_gemini_embeddings(self) -> Embeddings:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        return GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=self.config.google_api_key,
        )
