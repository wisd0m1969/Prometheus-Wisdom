"""Tests for WISDOM Brain module — profiles, memory, knowledge graph, embeddings."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from wisdom.brain.user_profile import UserProfileManager, UserProfile
from wisdom.brain.memory_manager import MemoryManager
from wisdom.brain.knowledge_graph import KnowledgeGraph
from wisdom.brain.embeddings import EmbeddingManager, WisdomEmbeddingFunction


class TestUserProfileManager:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.manager = UserProfileManager(self.tmp.name)

    def test_create_profile(self):
        profile = self.manager.create("user1")
        assert profile.id == "user1"
        assert profile.language == "en"
        assert profile.skill_level == 0.0

    def test_create_profile_with_params(self):
        profile = self.manager.create("user_named", name="Test", language="th")
        assert profile.name == "Test"
        assert profile.language == "th"

    def test_get_profile(self):
        self.manager.create("user2")
        profile = self.manager.get("user2")
        assert profile is not None
        assert profile.id == "user2"

    def test_get_nonexistent(self):
        assert self.manager.get("nobody") is None

    def test_update_profile(self):
        profile = self.manager.create("user3")
        profile.name = "Somchai"
        profile.language = "th"
        profile.skill_level = 3.5
        self.manager.update(profile)

        updated = self.manager.get("user3")
        assert updated.name == "Somchai"
        assert updated.language == "th"
        assert updated.skill_level == 3.5

    def test_delete_profile(self):
        self.manager.create("user4")
        self.manager.delete("user4")
        assert self.manager.get("user4") is None

    def test_get_or_create(self):
        profile = self.manager.get_or_create("user5")
        assert profile.id == "user5"
        # Second call should return the same profile
        profile2 = self.manager.get_or_create("user5")
        assert profile2.id == "user5"

    def test_export_json(self):
        self.manager.create("user6")
        json_str = self.manager.export_json("user6")
        assert json_str is not None
        assert '"user6"' in json_str

    def test_list_users(self):
        self.manager.create("user_a")
        self.manager.create("user_b")
        users = self.manager.list_users()
        assert len(users) >= 2


class TestMemoryManager:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.memory = MemoryManager(max_messages=5, db_path=self.tmp.name)

    def test_add_and_get_message(self):
        self.memory.add_message("u1", "user", "Hello")
        history = self.memory.get_history("u1")
        assert len(history) == 1
        assert history[0].content == "Hello"

    def test_max_messages(self):
        for i in range(10):
            self.memory.add_message("u2", "user", f"msg {i}")
        history = self.memory.get_history("u2")
        assert len(history) == 5
        assert history[0].content == "msg 5"

    def test_clear_session(self):
        self.memory.add_message("u3", "user", "test")
        self.memory.clear_session("u3")
        assert self.memory.get_history("u3") == []

    def test_context_string(self):
        self.memory.add_message("u4", "user", "Hi")
        self.memory.add_message("u4", "wisdom", "Hello!")
        ctx = self.memory.get_context_string("u4")
        assert "User: Hi" in ctx
        assert "WISDOM: Hello!" in ctx

    def test_empty_history(self):
        assert self.memory.get_history("unknown") == []
        assert self.memory.get_context_string("unknown") == ""

    def test_get_history_text(self):
        self.memory.add_message("u5", "user", "Hi there")
        self.memory.add_message("u5", "wisdom", "Hello!")
        text = self.memory.get_history_text("u5")
        assert "Hi there" in text
        assert "Hello!" in text

    def test_persist_to_sqlite(self):
        """Messages are persisted to SQLite conversations table."""
        self.memory.add_message("persist_user", "user", "Hello SQLite")
        self.memory.add_message("persist_user", "wisdom", "Hi back")
        count = self.memory.get_conversation_count("persist_user")
        assert count == 2

    def test_clear_deletes_from_sqlite(self):
        """Clearing session removes messages from SQLite too."""
        self.memory.add_message("clear_user", "user", "test")
        self.memory.clear_session("clear_user")
        count = self.memory.get_conversation_count("clear_user")
        assert count == 0

    def test_session_start_loads_from_sqlite(self):
        """on_session_start loads recent messages from SQLite into memory."""
        self.memory.add_message("reload_user", "user", "message 1")
        self.memory.add_message("reload_user", "wisdom", "reply 1")
        # Clear in-memory only
        self.memory._sessions.pop("reload_user", None)
        assert self.memory.get_history("reload_user") == []
        # Reload from SQLite
        self.memory.on_session_start("reload_user")
        history = self.memory.get_history("reload_user")
        assert len(history) == 2
        assert history[0].content == "message 1"


class TestKnowledgeGraph:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.kg = KnowledgeGraph(sqlite_path=self.tmp.name)

    def test_sqlite_fallback(self):
        assert not self.kg.is_neo4j

    def test_add_node(self):
        self.kg.add_node("user1", "User", {"name": "Test"})
        # No error means success

    def test_add_relationship(self):
        self.kg.add_node("user1", "User", {"name": "Test"})
        self.kg.add_node("topic1", "Topic", {"name": "AI Basics"})
        self.kg.add_relationship("user1", "topic1", "LEARNED", {"score": 8})

    def test_get_user_topics(self):
        self.kg.add_node("u1", "User", {"name": "Test"})
        self.kg.add_node("t1", "Topic", {"name": "AI"})
        self.kg.add_relationship("u1", "t1", "LEARNED", {"score": 7})
        topics = self.kg.get_user_topics("u1")
        assert len(topics) == 1


class TestEmbeddingManager:
    def test_init(self):
        mock_provider = MagicMock()
        em = EmbeddingManager(mock_provider)
        assert em.llm_provider is mock_provider

    def test_as_chroma_function(self):
        mock_provider = MagicMock()
        em = EmbeddingManager(mock_provider)
        fn = em.as_chroma_function()
        assert isinstance(fn, WisdomEmbeddingFunction)

    def test_chroma_function_callable(self):
        mock_provider = MagicMock()
        mock_embed = MagicMock()
        mock_embed.embed_documents.return_value = [[0.1, 0.2], [0.3, 0.4]]
        mock_provider.get_embeddings.return_value = mock_embed

        em = EmbeddingManager(mock_provider)
        fn = em.as_chroma_function()
        result = fn(["hello", "world"])
        assert len(result) == 2

    def test_similarity(self):
        mock_provider = MagicMock()
        mock_embed = MagicMock()
        mock_embed.embed_query.side_effect = [[1.0, 0.0], [1.0, 0.0]]
        mock_provider.get_embeddings.return_value = mock_embed

        em = EmbeddingManager(mock_provider)
        sim = em.similarity("a", "b")
        assert sim == 1.0

    def test_chroma_function_handles_error(self):
        mock_provider = MagicMock()
        mock_embed = MagicMock()
        mock_embed.embed_documents.side_effect = RuntimeError("fail")
        mock_provider.get_embeddings.return_value = mock_embed

        em = EmbeddingManager(mock_provider)
        fn = em.as_chroma_function()
        result = fn(["hello"])
        assert result == [[]]


class TestMemoryManagerEmbedding:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.memory = MemoryManager(max_messages=5, db_path=self.tmp.name)

    def test_set_embedding_function(self):
        mock_fn = MagicMock()
        self.memory.set_embedding_function(mock_fn)
        assert self.memory._embedding_function is mock_fn

    def test_set_embedding_clears_collections(self):
        self.memory._collections["test"] = "cached"
        mock_fn = MagicMock()
        self.memory.set_embedding_function(mock_fn)
        assert len(self.memory._collections) == 0
