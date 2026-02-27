"""Personal knowledge graph — Neo4j Aura (free) with SQLite fallback.

Stores user-topic-goal relationships for personalized learning paths.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path

__all__ = ["KnowledgeGraph"]

logger = logging.getLogger(__name__)


class KnowledgeGraph:
    """Graph database for user learning relationships.

    Uses Neo4j Aura (free tier) when available, falls back
    to a SQLite-based graph simulation.
    """

    def __init__(
        self,
        neo4j_uri: str = "",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "",
        sqlite_path: str | Path = "./data/wisdom.db",
    ) -> None:
        self._driver = None
        self._sqlite_path = Path(sqlite_path)

        if neo4j_uri and neo4j_password:
            try:
                from neo4j import GraphDatabase

                self._driver = GraphDatabase.driver(
                    neo4j_uri, auth=(neo4j_user, neo4j_password)
                )
                self._driver.verify_connectivity()
                logger.info("Connected to Neo4j: %s", neo4j_uri)
            except Exception as e:
                logger.warning("Neo4j unavailable (%s), using SQLite fallback", e)
                self._driver = None

        if not self._driver:
            self._init_sqlite()

    def _init_sqlite(self) -> None:
        """Initialize SQLite-based graph tables."""
        self._sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(self._sqlite_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS graph_nodes (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    properties TEXT DEFAULT '{}'
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS graph_edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_id TEXT NOT NULL,
                    to_id TEXT NOT NULL,
                    relationship TEXT NOT NULL,
                    properties TEXT DEFAULT '{}',
                    FOREIGN KEY (from_id) REFERENCES graph_nodes(id),
                    FOREIGN KEY (to_id) REFERENCES graph_nodes(id)
                )
            """)

    @property
    def is_neo4j(self) -> bool:
        return self._driver is not None

    def add_node(self, node_id: str, node_type: str, properties: dict | None = None) -> None:
        """Add a node to the graph."""
        props = properties or {}
        if self._driver:
            with self._driver.session() as session:
                session.run(
                    f"MERGE (n:{node_type} {{id: $id}}) SET n += $props",
                    id=node_id,
                    props=props,
                )
        else:
            with sqlite3.connect(str(self._sqlite_path)) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO graph_nodes (id, type, properties) VALUES (?, ?, ?)",
                    (node_id, node_type, json.dumps(props)),
                )

    def add_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: dict | None = None,
    ) -> None:
        """Add a relationship between two nodes."""
        props = properties or {}
        if self._driver:
            with self._driver.session() as session:
                session.run(
                    f"MATCH (a {{id: $from_id}}), (b {{id: $to_id}}) "
                    f"MERGE (a)-[r:{rel_type}]->(b) SET r += $props",
                    from_id=from_id,
                    to_id=to_id,
                    props=props,
                )
        else:
            with sqlite3.connect(str(self._sqlite_path)) as conn:
                conn.execute(
                    "INSERT INTO graph_edges (from_id, to_id, relationship, properties) VALUES (?, ?, ?, ?)",
                    (from_id, to_id, rel_type, json.dumps(props)),
                )

    def get_user_topics(self, user_id: str) -> list[dict]:
        """Get all topics a user has learned."""
        if self._driver:
            with self._driver.session() as session:
                result = session.run(
                    "MATCH (u:User {id: $uid})-[r:LEARNED]->(t:Topic) "
                    "RETURN t.id AS id, t.name AS name, r.score AS score",
                    uid=user_id,
                )
                return [dict(record) for record in result]
        else:
            with sqlite3.connect(str(self._sqlite_path)) as conn:
                rows = conn.execute(
                    """SELECT gn.id, gn.properties, ge.properties
                       FROM graph_edges ge
                       JOIN graph_nodes gn ON ge.to_id = gn.id
                       WHERE ge.from_id = ? AND ge.relationship = 'LEARNED'""",
                    (user_id,),
                ).fetchall()
                return [
                    {"id": r[0], **json.loads(r[1]), "edge": json.loads(r[2])}
                    for r in rows
                ]

    def get_related_topics(self, topic_id: str) -> list[dict]:
        """Get topics related to a given topic."""
        if self._driver:
            with self._driver.session() as session:
                result = session.run(
                    "MATCH (t:Topic {id: $tid})-[:PREREQUISITE_OF]->(related:Topic) "
                    "RETURN related.id AS id, related.name AS name",
                    tid=topic_id,
                )
                return [dict(record) for record in result]
        else:
            with sqlite3.connect(str(self._sqlite_path)) as conn:
                rows = conn.execute(
                    """SELECT gn.id, gn.properties
                       FROM graph_edges ge
                       JOIN graph_nodes gn ON ge.to_id = gn.id
                       WHERE ge.from_id = ? AND ge.relationship = 'PREREQUISITE_OF'""",
                    (topic_id,),
                ).fetchall()
                return [{"id": r[0], **json.loads(r[1])} for r in rows]

    def close(self) -> None:
        if self._driver:
            self._driver.close()
