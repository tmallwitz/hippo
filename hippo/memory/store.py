"""MemoryStore protocol for Hippo's memory backends."""

from __future__ import annotations

from typing import Protocol

from hippo.memory.types import Entity, KnowledgeGraph, Relation


class SemanticStore(Protocol):
    """Protocol for semantic (knowledge-graph) memory backends."""

    async def create_entities(
        self,
        entities: list[Entity],
    ) -> list[Entity]:
        """Create entities, skipping those that already exist. Returns created."""
        ...

    async def create_relations(
        self,
        relations: list[Relation],
    ) -> list[Relation]:
        """Create relations, skipping duplicates. Returns created."""
        ...

    async def add_observations(
        self,
        entity_name: str,
        observations: list[str],
    ) -> list[str]:
        """Add observations to an entity, skipping duplicates. Returns added."""
        ...

    async def delete_entities(
        self,
        names: list[str],
    ) -> None:
        """Delete entities and clean up inbound relations."""
        ...

    async def delete_observations(
        self,
        entity_name: str,
        observations: list[str],
    ) -> None:
        """Remove specific observations from an entity."""
        ...

    async def delete_relations(
        self,
        relations: list[Relation],
    ) -> None:
        """Remove specific relations."""
        ...

    async def read_graph(self) -> KnowledgeGraph:
        """Load and return the entire knowledge graph."""
        ...

    async def search_nodes(self, query: str) -> KnowledgeGraph:
        """Search entities by name, type, and observation content."""
        ...

    async def open_nodes(self, names: list[str]) -> KnowledgeGraph:
        """Load specific entities by name with their inter-relations."""
        ...
