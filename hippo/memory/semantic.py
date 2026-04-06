"""Obsidian-vault-backed semantic memory store (knowledge graph as Markdown files)."""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import date
from pathlib import Path
from typing import Any

import frontmatter

from hippo.memory.types import Entity, KnowledgeGraph, Relation

log = logging.getLogger(__name__)

# Characters forbidden in filenames on Windows / most filesystems
_FORBIDDEN_CHARS = re.compile(r'[/<>:"\\|?*\x00-\x1f]')
_RELATION_RE = re.compile(r"^\s*-\s*\[\[([^:\]]+)::([^\]]+)\]\]\s*$")
_WINDOWS_RESERVED = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{i}" for i in range(10)),
        *(f"LPT{i}" for i in range(10)),
    }
)
_MAX_FILENAME_LEN = 200


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _sanitize_filename(name: str) -> str:
    """Turn an entity name into a safe filename (without extension)."""
    result = _FORBIDDEN_CHARS.sub("_", name)
    result = re.sub(r"_+", "_", result).strip(" ._")
    if not result:
        result = "unnamed"
    if result.upper() in _WINDOWS_RESERVED:
        result = f"_{result}"
    if len(result) > _MAX_FILENAME_LEN:
        result = result[:_MAX_FILENAME_LEN]
    return result


def _entity_dir(vault_path: Path, entity_type: str) -> Path:
    """Return (and create if needed) the subfolder for an entity type."""
    d = vault_path / "semantic" / entity_type
    d.mkdir(parents=True, exist_ok=True)
    return d


def _entity_path(vault_path: Path, entity_type: str, name: str) -> Path:
    return _entity_dir(vault_path, entity_type) / f"{_sanitize_filename(name)}.md"


def _find_entity_file(vault_path: Path, name: str) -> Path | None:
    """Scan semantic/**/*.md for an entity whose frontmatter `name` matches."""
    semantic_dir = vault_path / "semantic"
    if not semantic_dir.is_dir():
        return None
    for md_file in semantic_dir.rglob("*.md"):
        try:
            post = frontmatter.load(str(md_file))
            if post.metadata.get("name") == name:
                return md_file
        except Exception:
            log.debug("Skipping unparseable file: %s", md_file)
    return None


def _parse_entity_file(path: Path) -> tuple[Entity, list[Relation]]:
    """Parse a Markdown entity file into an Entity and its outgoing Relations."""
    post = frontmatter.load(str(path))
    meta = post.metadata
    entity_name: str = meta.get("name", path.stem)
    entity_type: str = meta.get("entityType", "unknown")

    observations: list[str] = []
    relations: list[Relation] = []

    in_observations = False
    in_relations = False

    for line in post.content.splitlines():
        stripped = line.strip()

        if stripped.startswith("## "):
            heading = stripped[3:].strip().lower()
            in_observations = heading == "observations"
            in_relations = heading == "relations"
            continue

        if in_observations and (stripped.startswith("- ") or stripped.startswith("* ")):
            observations.append(stripped[2:].strip())

        if in_relations:
            m = _RELATION_RE.match(line)
            if m:
                relations.append(
                    Relation(
                        from_entity=entity_name,
                        to_entity=m.group(2).strip(),
                        relation_type=m.group(1).strip(),
                    )
                )

    entity = Entity(
        name=entity_name,
        entity_type=entity_type,
        observations=tuple(observations),
    )
    return entity, relations


def _write_entity_file(
    path: Path,
    entity: Entity,
    relations: list[Relation],
    *,
    created: date | None = None,
) -> None:
    """Write an entity to a Markdown file, preserving created date if given."""
    today = date.today().isoformat()
    meta = {
        "name": entity.name,
        "entityType": entity.entity_type,
        "created": created.isoformat() if created else today,
        "updated": today,
    }

    lines: list[str] = [f"# {entity.name}", ""]

    if entity.observations:
        lines.append("## Observations")
        for obs in entity.observations:
            lines.append(f"- {obs}")
        lines.append("")

    if relations:
        lines.append("## Relations")
        for rel in relations:
            lines.append(f"- [[{rel.relation_type}::{rel.to_entity}]]")
        lines.append("")

    post = frontmatter.Post("\n".join(lines), **meta)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frontmatter.dumps(post), encoding="utf-8")


def _load_all(vault_path: Path) -> tuple[list[Entity], list[Relation]]:
    """Load every entity and relation from the vault."""
    semantic_dir = vault_path / "semantic"
    entities: list[Entity] = []
    relations: list[Relation] = []
    if not semantic_dir.is_dir():
        return entities, relations
    for md_file in semantic_dir.rglob("*.md"):
        try:
            entity, rels = _parse_entity_file(md_file)
            entities.append(entity)
            relations.extend(rels)
        except Exception:
            log.warning("Skipping unparseable file: %s", md_file)
    return entities, relations


def _get_created_date(path: Path) -> date | None:
    """Read the 'created' field from an existing file's frontmatter."""
    try:
        post = frontmatter.load(str(path))
        raw = post.metadata.get("created")
        if isinstance(raw, date):
            return raw
        if isinstance(raw, str):
            return date.fromisoformat(raw)
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Public store class
# ---------------------------------------------------------------------------


class ObsidianSemanticStore:
    """Knowledge-graph memory backed by Markdown files in an Obsidian vault."""

    def __init__(
        self,
        vault_path: Path,
        embedding_model: str | None = None,
        search_threshold: float = 0.4,
    ) -> None:
        self._vault = vault_path
        self._lock = asyncio.Lock()
        self._embedding_model = embedding_model or None
        self._search_threshold = search_threshold

    # -- Create ---------------------------------------------------------------

    async def create_entities(self, entities: list[Entity]) -> list[Entity]:
        async with self._lock:
            return await asyncio.to_thread(self._create_entities_sync, entities)

    def _create_entities_sync(self, entities: list[Entity]) -> list[Entity]:
        created: list[Entity] = []
        for entity in entities:
            if _find_entity_file(self._vault, entity.name) is not None:
                log.debug("Entity already exists, skipping: %s", entity.name)
                continue
            path = _entity_path(self._vault, entity.entity_type, entity.name)
            _write_entity_file(path, entity, [])
            created.append(entity)
        if created and self._embedding_model:
            try:
                from hippo.memory.embeddings import update_entity_embeddings

                update_entity_embeddings(self._vault, created, self._embedding_model)
            except Exception:
                log.warning("Failed to update embeddings after entity creation", exc_info=True)
        return created

    async def create_relations(self, relations: list[Relation]) -> list[Relation]:
        async with self._lock:
            return await asyncio.to_thread(self._create_relations_sync, relations)

    def _create_relations_sync(self, relations: list[Relation]) -> list[Relation]:
        created: list[Relation] = []
        for rel in relations:
            source_path = _find_entity_file(self._vault, rel.from_entity)
            if source_path is None:
                log.warning("Source entity not found for relation, skipping: %s", rel.from_entity)
                continue

            # Warn if target doesn't exist (but don't block)
            if _find_entity_file(self._vault, rel.to_entity) is None:
                log.warning("Relation target does not exist: %s", rel.to_entity)

            # Check for duplicate
            existing_entity, existing_rels = _parse_entity_file(source_path)
            if rel in existing_rels:
                log.debug("Relation already exists, skipping: %s", rel)
                continue

            # Preserve created date and rebuild file
            created_date = _get_created_date(source_path)
            existing_rels.append(rel)
            _write_entity_file(source_path, existing_entity, existing_rels, created=created_date)
            created.append(rel)
        return created

    async def add_observations(self, entity_name: str, observations: list[str]) -> list[str]:
        async with self._lock:
            return await asyncio.to_thread(self._add_observations_sync, entity_name, observations)

    def _add_observations_sync(self, entity_name: str, observations: list[str]) -> list[str]:
        path = _find_entity_file(self._vault, entity_name)
        if path is None:
            msg = f"Entity not found: {entity_name}"
            raise ValueError(msg)

        entity, rels = _parse_entity_file(path)
        existing = set(entity.observations)
        added = [o for o in observations if o not in existing]
        if not added:
            return []

        created_date = _get_created_date(path)
        updated = Entity(
            name=entity.name,
            entity_type=entity.entity_type,
            observations=(*entity.observations, *added),
        )
        _write_entity_file(path, updated, rels, created=created_date)
        if self._embedding_model:
            try:
                from hippo.memory.embeddings import update_entity_embeddings

                update_entity_embeddings(self._vault, [updated], self._embedding_model)
            except Exception:
                log.warning("Failed to update embeddings after observation update", exc_info=True)
        return added

    # -- Delete ---------------------------------------------------------------

    async def delete_entities(self, names: list[str]) -> None:
        async with self._lock:
            await asyncio.to_thread(self._delete_entities_sync, names)

    def _delete_entities_sync(self, names: list[str]) -> None:
        deleted_names: set[str] = set()
        for name in names:
            path = _find_entity_file(self._vault, name)
            if path is not None:
                path.unlink()
                deleted_names.add(name)
            else:
                log.debug("Entity not found for deletion, skipping: %s", name)

        if not deleted_names:
            return

        if self._embedding_model:
            try:
                from hippo.memory.embeddings import load_embeddings, save_embeddings

                data = load_embeddings(self._vault)
                stored: dict[str, Any] = data.get("entities", {})
                changed = False
                for name in deleted_names:
                    if name in stored:
                        del stored[name]
                        changed = True
                if changed:
                    save_embeddings(self._vault, data)
            except Exception:
                log.warning("Failed to remove embeddings for deleted entities", exc_info=True)

        # Clean up inbound relations pointing to deleted entities
        semantic_dir = self._vault / "semantic"
        if not semantic_dir.is_dir():
            return
        for md_file in semantic_dir.rglob("*.md"):
            try:
                entity, rels = _parse_entity_file(md_file)
                original_count = len(rels)
                rels = [r for r in rels if r.to_entity not in deleted_names]
                if len(rels) < original_count:
                    created_date = _get_created_date(md_file)
                    _write_entity_file(md_file, entity, rels, created=created_date)
            except Exception:
                log.warning("Skipping file during relation cleanup: %s", md_file)

    async def delete_observations(self, entity_name: str, observations: list[str]) -> None:
        async with self._lock:
            await asyncio.to_thread(self._delete_observations_sync, entity_name, observations)

    def _delete_observations_sync(self, entity_name: str, observations: list[str]) -> None:
        path = _find_entity_file(self._vault, entity_name)
        if path is None:
            log.debug("Entity not found for observation deletion: %s", entity_name)
            return

        entity, rels = _parse_entity_file(path)
        to_remove = set(observations)
        kept = tuple(o for o in entity.observations if o not in to_remove)
        if len(kept) == len(entity.observations):
            return

        created_date = _get_created_date(path)
        updated = Entity(
            name=entity.name,
            entity_type=entity.entity_type,
            observations=kept,
        )
        _write_entity_file(path, updated, rels, created=created_date)

    async def delete_relations(self, relations: list[Relation]) -> None:
        async with self._lock:
            await asyncio.to_thread(self._delete_relations_sync, relations)

    def _delete_relations_sync(self, relations: list[Relation]) -> None:
        for rel in relations:
            source_path = _find_entity_file(self._vault, rel.from_entity)
            if source_path is None:
                log.debug("Source entity not found for relation deletion: %s", rel.from_entity)
                continue

            entity, existing_rels = _parse_entity_file(source_path)
            updated_rels = [r for r in existing_rels if r != rel]
            if len(updated_rels) == len(existing_rels):
                continue

            created_date = _get_created_date(source_path)
            _write_entity_file(source_path, entity, updated_rels, created=created_date)

    # -- Read -----------------------------------------------------------------

    async def read_graph(self) -> KnowledgeGraph:
        return await asyncio.to_thread(self._read_graph_sync)

    def _read_graph_sync(self) -> KnowledgeGraph:
        entities, relations = _load_all(self._vault)
        return KnowledgeGraph(
            entities=tuple(entities),
            relations=tuple(relations),
        )

    async def search_nodes(self, query: str) -> KnowledgeGraph:
        return await asyncio.to_thread(self._search_nodes_sync, query)

    def _search_nodes_sync(self, query: str) -> KnowledgeGraph:
        all_entities, all_relations = _load_all(self._vault)

        matched: list[Entity] = []

        if self._embedding_model:
            try:
                from hippo.memory.embeddings import search_by_embedding

                hits = search_by_embedding(
                    query, self._vault, self._embedding_model, self._search_threshold
                )
                if hits:
                    hit_names = {name for name, _ in hits}
                    matched = [e for e in all_entities if e.name in hit_names]
            except Exception:
                log.warning(
                    "Embedding search failed, falling back to substring: %s",
                    query,
                    exc_info=True,
                )

        if not matched:
            q = query.lower()
            matched = [
                e
                for e in all_entities
                if q in e.name.lower()
                or q in e.entity_type.lower()
                or any(q in obs.lower() for obs in e.observations)
            ]

        matched_names = {e.name for e in matched}
        filtered_rels = [
            r
            for r in all_relations
            if r.from_entity in matched_names and r.to_entity in matched_names
        ]
        return KnowledgeGraph(
            entities=tuple(matched),
            relations=tuple(filtered_rels),
        )

    async def find_similar_entities(
        self, name: str, threshold: float = 0.7
    ) -> list[tuple[str, float]]:
        """Find entities with names similar to ``name`` using embeddings.

        Returns list of (entity_name, score) sorted by score descending.
        Returns empty list if embedding model is not configured.
        """
        if not self._embedding_model:
            return []
        try:
            return await asyncio.to_thread(self._find_similar_entities_sync, name, threshold)
        except Exception:
            log.warning("find_similar_entities failed for '%s'", name, exc_info=True)
            return []

    def _find_similar_entities_sync(self, name: str, threshold: float) -> list[tuple[str, float]]:
        from hippo.memory.embeddings import find_similar_names

        return find_similar_names(name, self._vault, self._embedding_model, threshold)  # type: ignore[arg-type]

    async def open_nodes(self, names: list[str]) -> KnowledgeGraph:
        return await asyncio.to_thread(self._open_nodes_sync, names)

    def _open_nodes_sync(self, names: list[str]) -> KnowledgeGraph:
        name_set = set(names)
        all_entities, all_relations = _load_all(self._vault)

        matched = [e for e in all_entities if e.name in name_set]
        matched_names = {e.name for e in matched}
        filtered_rels = [
            r
            for r in all_relations
            if r.from_entity in matched_names and r.to_entity in matched_names
        ]
        return KnowledgeGraph(
            entities=tuple(matched),
            relations=tuple(filtered_rels),
        )
