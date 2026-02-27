"""
PROMETHEUS WISDOM — AI Companion for Humanity
=============================================

An open-source AI personal companion designed to democratize AI access
for the 6.8 billion people who have never interacted with AI.

Usage:
    from wisdom import Wisdom
    # or
    from wisdom import WISDOM

    w = Wisdom()
    response = w.chat("Hello!")
"""

__version__ = "1.0.0"
__author__ = "Project PROMETHEUS"

__all__ = ["Wisdom", "WISDOM"]


class Wisdom:
    """Main WISDOM AI Companion interface.

    Orchestrates all subsystems (Brain, Voice, Heart, Soul, Body)
    to provide a personalized, multilingual AI experience.
    """

    def __init__(self, user_id: str | None = None):
        from wisdom.core.config import Config
        from wisdom.core.llm_provider import LLMProvider
        from wisdom.brain.user_profile import UserProfileManager
        from wisdom.brain.memory_manager import MemoryManager
        from wisdom.brain.knowledge_graph import KnowledgeGraph
        from wisdom.brain.embeddings import EmbeddingManager
        from wisdom.voice.language_detect import LanguageDetector
        from wisdom.voice.tone_adapter import ToneAdapter
        from wisdom.heart.privacy_manager import PrivacyManager
        from wisdom.heart.federated_core import FederatedCore
        from wisdom.heart.community_knowledge import CommunityKnowledge
        from wisdom.plugins import PluginManager
        from wisdom.core.orchestrator import Orchestrator

        self.config = Config()
        self.llm_provider = LLMProvider(self.config)
        self.profile_manager = UserProfileManager(self.config.db_path)
        self.memory = MemoryManager(
            max_messages=self.config.max_memory_messages,
            db_path=self.config.db_path,
        )
        self.knowledge_graph = KnowledgeGraph(
            neo4j_uri=self.config.neo4j_uri,
            neo4j_user=self.config.neo4j_username,
            neo4j_password=self.config.neo4j_password,
            sqlite_path=self.config.db_path,
        )
        self.embedding_manager = EmbeddingManager(self.llm_provider)
        self.language_detector = LanguageDetector()
        self.tone_adapter = ToneAdapter()
        self.privacy_manager = PrivacyManager()
        self.federated = FederatedCore()
        self.community = CommunityKnowledge(self.config.db_path)
        self.plugin_manager = PluginManager()
        self.plugin_manager.discover_plugins()

        # Initialize ChromaDB for long-term memory (lazy, non-fatal)
        self.memory.init_vector_store(str(self.config.chroma_path))

        # Wire custom embedding function (nomic-embed-text / Gemini) into ChromaDB
        try:
            embed_fn = self.embedding_manager.as_chroma_function()
            self.memory.set_embedding_function(embed_fn)
        except Exception:
            pass  # Fall back to ChromaDB default embedder

        self.orchestrator = Orchestrator(
            llm_provider=self.llm_provider,
            memory=self.memory,
            profile_manager=self.profile_manager,
            language_detector=self.language_detector,
            tone_adapter=self.tone_adapter,
            privacy_manager=self.privacy_manager,
            knowledge_graph=self.knowledge_graph,
            federated=self.federated,
            community=self.community,
        )

        self.user_id = user_id

    def chat(self, message: str, user_id: str | None = None) -> str:
        """Send a message to WISDOM and get a response.

        Args:
            message: User's message in any supported language.
            user_id: Optional user identifier. Uses default if not provided.

        Returns:
            WISDOM's response in the user's detected language.
        """
        uid = user_id or self.user_id or "default"
        return self.orchestrator.process_message(uid, message)

    def chat_stream(self, message: str, user_id: str | None = None):
        """Send a message and get a streaming response.

        Yields:
            Response text chunks.
        """
        uid = user_id or self.user_id or "default"
        yield from self.orchestrator.process_message_stream(uid, message)

    def health_check(self) -> dict:
        """Check the health of all WISDOM subsystems."""
        return {
            "status": "ok",
            "version": __version__,
            "llm": self.llm_provider.health_check(),
        }

    def export_user_data(self, user_id: str | None = None) -> dict:
        """Export all data for a user (GDPR compliance)."""
        uid = user_id or self.user_id or "default"
        return self.orchestrator.export_user_data(uid)

    def delete_user_data(self, user_id: str | None = None) -> bool:
        """Delete all data for a user (right to be forgotten)."""
        uid = user_id or self.user_id or "default"
        return self.orchestrator.delete_user_data(uid)


# Alias for convenience
WISDOM = Wisdom
