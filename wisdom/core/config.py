"""Environment-based configuration with sensible defaults."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

__all__ = ["Config"]

load_dotenv()


class Config:
    """Central configuration for WISDOM.

    All values fall back to sensible defaults so WISDOM
    works with zero configuration out of the box.
    """

    def __init__(self) -> None:
        # Google Gemini
        self.google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
        self.gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

        # Ollama
        self.ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3:latest")
        self.ollama_embed_model: str = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

        # Neo4j
        self.neo4j_uri: str = os.getenv("NEO4J_URI", "")
        self.neo4j_username: str = os.getenv("NEO4J_USERNAME", "neo4j")
        self.neo4j_password: str = os.getenv("NEO4J_PASSWORD", "")

        # Local storage
        self.db_path: Path = Path(os.getenv("WISDOM_DB_PATH", "./data/wisdom.db"))
        self.chroma_path: Path = Path(os.getenv("CHROMA_DB_PATH", "./data/chroma"))

        # Application
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.default_language: str = os.getenv("DEFAULT_LANGUAGE", "en")
        self.max_memory_messages: int = int(os.getenv("MAX_MEMORY_MESSAGES", "20"))

    @property
    def has_gemini(self) -> bool:
        return bool(self.google_api_key and self.google_api_key != "your-gemini-api-key-here")

    @property
    def has_neo4j(self) -> bool:
        return bool(self.neo4j_uri and self.neo4j_password)

    def ensure_data_dir(self) -> None:
        """Create data directories if they don't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.chroma_path.mkdir(parents=True, exist_ok=True)
