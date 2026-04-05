"""Data types for Hippo's memory system."""

from __future__ import annotations

from pydantic import BaseModel


class Entity(BaseModel, frozen=True):
    """A node in the knowledge graph."""

    name: str
    entity_type: str
    observations: tuple[str, ...] = ()


class Relation(BaseModel, frozen=True):
    """A directed edge in the knowledge graph."""

    from_entity: str
    to_entity: str
    relation_type: str


class KnowledgeGraph(BaseModel, frozen=True):
    """The complete knowledge graph."""

    entities: tuple[Entity, ...] = ()
    relations: tuple[Relation, ...] = ()
