"""Unit tests for ObsidianSemanticStore."""

from __future__ import annotations

from pathlib import Path

import frontmatter
import pytest

from hippo.memory.semantic import ObsidianSemanticStore, _sanitize_filename
from hippo.memory.types import Entity, Relation

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def store(tmp_vault: Path) -> ObsidianSemanticStore:
    return ObsidianSemanticStore(tmp_vault)


# Helpers
def _read_meta(path: Path) -> dict[str, str]:
    return dict(frontmatter.load(str(path)).metadata)


# ---------------------------------------------------------------------------
# _sanitize_filename
# ---------------------------------------------------------------------------


class TestSanitizeFilename:
    def test_simple_name(self) -> None:
        assert _sanitize_filename("Alice") == "Alice"

    def test_special_chars(self) -> None:
        # ?" each become _, then collapsed to single _
        assert _sanitize_filename('A/B\\C:D*E?"F') == "A_B_C_D_E_F"

    def test_empty_becomes_unnamed(self) -> None:
        assert _sanitize_filename("") == "unnamed"

    def test_windows_reserved(self) -> None:
        assert _sanitize_filename("CON") == "_CON"
        assert _sanitize_filename("com3") == "_com3"

    def test_truncation(self) -> None:
        long_name = "x" * 300
        assert len(_sanitize_filename(long_name)) <= 200


# ---------------------------------------------------------------------------
# create_entities
# ---------------------------------------------------------------------------


class TestCreateEntities:
    async def test_create_single(self, store: ObsidianSemanticStore, tmp_vault: Path) -> None:
        entity = Entity(name="Alice", entity_type="person", observations=("Works at ACME",))
        created = await store.create_entities([entity])

        assert len(created) == 1
        assert created[0].name == "Alice"

        # File should exist in the right subfolder
        expected = tmp_vault / "semantic" / "person" / "Alice.md"
        assert expected.exists()

        meta = _read_meta(expected)
        assert meta["name"] == "Alice"
        assert meta["entityType"] == "person"

    async def test_skip_duplicate(self, store: ObsidianSemanticStore) -> None:
        entity = Entity(name="Alice", entity_type="person")
        await store.create_entities([entity])
        created = await store.create_entities([entity])
        assert len(created) == 0

    async def test_subfolder_by_type(self, store: ObsidianSemanticStore, tmp_vault: Path) -> None:
        await store.create_entities(
            [
                Entity(name="Alice", entity_type="person"),
                Entity(name="Hippo", entity_type="project"),
            ]
        )
        assert (tmp_vault / "semantic" / "person" / "Alice.md").exists()
        assert (tmp_vault / "semantic" / "project" / "Hippo.md").exists()

    async def test_special_chars_in_name(
        self, store: ObsidianSemanticStore, tmp_vault: Path
    ) -> None:
        entity = Entity(name="Alice & Bob: A Story", entity_type="topic")
        await store.create_entities([entity])

        # : is forbidden, & is not. Sanitized: "Alice & Bob_ A Story"
        path = tmp_vault / "semantic" / "topic" / "Alice & Bob_ A Story.md"
        assert path.exists()

        # But frontmatter preserves original
        meta = _read_meta(path)
        assert meta["name"] == "Alice & Bob: A Story"


# ---------------------------------------------------------------------------
# add_observations / delete_observations
# ---------------------------------------------------------------------------


class TestObservations:
    async def test_add_observations(self, store: ObsidianSemanticStore) -> None:
        await store.create_entities([Entity(name="Alice", entity_type="person")])
        added = await store.add_observations("Alice", ["Likes cats", "Likes dogs"])
        assert added == ["Likes cats", "Likes dogs"]

    async def test_skip_duplicate_observations(self, store: ObsidianSemanticStore) -> None:
        await store.create_entities(
            [Entity(name="Alice", entity_type="person", observations=("Likes cats",))]
        )
        added = await store.add_observations("Alice", ["Likes cats", "Likes dogs"])
        assert added == ["Likes dogs"]

    async def test_add_to_nonexistent_raises(self, store: ObsidianSemanticStore) -> None:
        with pytest.raises(ValueError, match="Entity not found"):
            await store.add_observations("Nobody", ["test"])

    async def test_delete_observations(self, store: ObsidianSemanticStore) -> None:
        await store.create_entities(
            [
                Entity(
                    name="Alice",
                    entity_type="person",
                    observations=("Likes cats", "Likes dogs", "Lives in Berlin"),
                )
            ]
        )
        await store.delete_observations("Alice", ["Likes dogs"])

        graph = await store.read_graph()
        alice = next(e for e in graph.entities if e.name == "Alice")
        assert "Likes cats" in alice.observations
        assert "Lives in Berlin" in alice.observations
        assert "Likes dogs" not in alice.observations


# ---------------------------------------------------------------------------
# create_relations / delete_relations
# ---------------------------------------------------------------------------


class TestRelations:
    async def test_create_relation(self, store: ObsidianSemanticStore) -> None:
        await store.create_entities(
            [
                Entity(name="Alice", entity_type="person"),
                Entity(name="ACME", entity_type="organization"),
            ]
        )
        rel = Relation(from_entity="Alice", to_entity="ACME", relation_type="Works at")
        created = await store.create_relations([rel])
        assert len(created) == 1

        graph = await store.read_graph()
        assert rel in graph.relations

    async def test_skip_duplicate_relation(self, store: ObsidianSemanticStore) -> None:
        await store.create_entities(
            [
                Entity(name="Alice", entity_type="person"),
                Entity(name="ACME", entity_type="organization"),
            ]
        )
        rel = Relation(from_entity="Alice", to_entity="ACME", relation_type="Works at")
        await store.create_relations([rel])
        created = await store.create_relations([rel])
        assert len(created) == 0

    async def test_relation_missing_source_skipped(self, store: ObsidianSemanticStore) -> None:
        rel = Relation(from_entity="Nobody", to_entity="ACME", relation_type="Works at")
        created = await store.create_relations([rel])
        assert len(created) == 0

    async def test_delete_relation(self, store: ObsidianSemanticStore) -> None:
        await store.create_entities(
            [
                Entity(name="Alice", entity_type="person"),
                Entity(name="ACME", entity_type="organization"),
            ]
        )
        rel = Relation(from_entity="Alice", to_entity="ACME", relation_type="Works at")
        await store.create_relations([rel])
        await store.delete_relations([rel])

        graph = await store.read_graph()
        assert rel not in graph.relations


# ---------------------------------------------------------------------------
# delete_entities (cascade cleanup)
# ---------------------------------------------------------------------------


class TestDeleteEntities:
    async def test_delete_entity(self, store: ObsidianSemanticStore, tmp_vault: Path) -> None:
        await store.create_entities([Entity(name="Alice", entity_type="person")])
        await store.delete_entities(["Alice"])
        assert not (tmp_vault / "semantic" / "person" / "Alice.md").exists()

    async def test_inbound_relations_cleaned(self, store: ObsidianSemanticStore) -> None:
        await store.create_entities(
            [
                Entity(name="Alice", entity_type="person"),
                Entity(name="ACME", entity_type="organization"),
            ]
        )
        await store.create_relations(
            [
                Relation(from_entity="Alice", to_entity="ACME", relation_type="Works at"),
            ]
        )
        # Delete ACME — the relation in Alice's file should be cleaned up
        await store.delete_entities(["ACME"])

        graph = await store.read_graph()
        assert len(graph.relations) == 0
        assert len(graph.entities) == 1


# ---------------------------------------------------------------------------
# read_graph / search_nodes / open_nodes
# ---------------------------------------------------------------------------


class TestReadAndSearch:
    async def test_read_graph(self, store: ObsidianSemanticStore) -> None:
        await store.create_entities(
            [
                Entity(name="Alice", entity_type="person", observations=("Likes cats",)),
                Entity(name="ACME", entity_type="organization"),
            ]
        )
        graph = await store.read_graph()
        assert len(graph.entities) == 2
        names = {e.name for e in graph.entities}
        assert names == {"Alice", "ACME"}

    async def test_search_by_name(self, store: ObsidianSemanticStore) -> None:
        await store.create_entities(
            [
                Entity(name="Alice", entity_type="person"),
                Entity(name="Bob", entity_type="person"),
            ]
        )
        result = await store.search_nodes("alice")
        assert len(result.entities) == 1
        assert result.entities[0].name == "Alice"

    async def test_search_by_type(self, store: ObsidianSemanticStore) -> None:
        await store.create_entities(
            [
                Entity(name="Alice", entity_type="person"),
                Entity(name="Hippo", entity_type="project"),
            ]
        )
        result = await store.search_nodes("project")
        assert len(result.entities) == 1
        assert result.entities[0].name == "Hippo"

    async def test_search_by_observation(self, store: ObsidianSemanticStore) -> None:
        await store.create_entities(
            [
                Entity(name="Alice", entity_type="person", observations=("Likes cats",)),
                Entity(name="Bob", entity_type="person", observations=("Likes dogs",)),
            ]
        )
        result = await store.search_nodes("cats")
        assert len(result.entities) == 1
        assert result.entities[0].name == "Alice"

    async def test_open_nodes(self, store: ObsidianSemanticStore) -> None:
        await store.create_entities(
            [
                Entity(name="Alice", entity_type="person"),
                Entity(name="Bob", entity_type="person"),
                Entity(name="Carol", entity_type="person"),
            ]
        )
        result = await store.open_nodes(["Alice", "Bob"])
        assert len(result.entities) == 2
        names = {e.name for e in result.entities}
        assert names == {"Alice", "Bob"}


# ---------------------------------------------------------------------------
# Metadata preservation
# ---------------------------------------------------------------------------


class TestMetadataPreservation:
    async def test_created_date_preserved(
        self, store: ObsidianSemanticStore, tmp_vault: Path
    ) -> None:
        await store.create_entities([Entity(name="Alice", entity_type="person")])
        path = tmp_vault / "semantic" / "person" / "Alice.md"

        original_created = _read_meta(path)["created"]

        # Add observations — should preserve created date
        await store.add_observations("Alice", ["New observation"])
        updated_meta = _read_meta(path)
        assert str(updated_meta["created"]) == str(original_created)

    async def test_manual_edit_picked_up(
        self, store: ObsidianSemanticStore, tmp_vault: Path
    ) -> None:
        await store.create_entities(
            [Entity(name="Alice", entity_type="person", observations=("Initial fact",))]
        )
        path = tmp_vault / "semantic" / "person" / "Alice.md"

        # Manually edit the file (simulating Obsidian edit)
        content = path.read_text(encoding="utf-8")
        content = content.replace("- Initial fact", "- Initial fact\n- Manually added fact")
        path.write_text(content, encoding="utf-8")

        # The store should see the change
        graph = await store.read_graph()
        alice = next(e for e in graph.entities if e.name == "Alice")
        assert "Manually added fact" in alice.observations
        assert "Initial fact" in alice.observations


# ---------------------------------------------------------------------------
# Empty graph
# ---------------------------------------------------------------------------


class TestEmptyGraph:
    async def test_read_empty(self, store: ObsidianSemanticStore) -> None:
        graph = await store.read_graph()
        assert len(graph.entities) == 0
        assert len(graph.relations) == 0

    async def test_search_empty(self, store: ObsidianSemanticStore) -> None:
        result = await store.search_nodes("anything")
        assert len(result.entities) == 0

    async def test_delete_nonexistent(self, store: ObsidianSemanticStore) -> None:
        # Should not raise
        await store.delete_entities(["Nobody"])
