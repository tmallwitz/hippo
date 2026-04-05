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


class Episode(BaseModel, frozen=True):
    """A single timestamped entry in the episodic journal."""

    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    title: str
    content: str
    tags: tuple[str, ...] = ()


class ScheduledTask(BaseModel, frozen=True):
    """A task scheduled for future execution."""

    id: str
    description: str
    time: str | None = None  # ISO datetime for one-shot
    recurring: bool = False
    cron: str | None = None  # cron expression for recurring
    status: str = "pending"  # pending | active | completed
    created: str  # ISO datetime
    last_run: str | None = None  # ISO datetime, recurring only


class BufferEntry(BaseModel, frozen=True):
    """A raw, unstructured entry in the short-term buffer."""

    ts: str  # ISO datetime (UTC)
    session: str  # e.g. "tg-12345" (telegram user ID)
    content: str
    tags: tuple[str, ...] = ()


class MailboxMessage(BaseModel, frozen=True):
    """An inter-bot message deposited in a bot's inbox."""

    from_bot: str
    to_bot: str
    ts: str  # ISO datetime (UTC)
    subject: str
    content: str


class DreamReport(BaseModel, frozen=True):
    """Summary produced by a dream cycle run."""

    date: str  # YYYY-MM-DD
    entries_processed: int
    entities_created: tuple[str, ...] = ()
    observations_added: int = 0
    episodes_logged: int = 0
    skills_created: tuple[str, ...] = ()
    messages_processed: int = 0
    entries_discarded: int = 0
    summary: str = ""
