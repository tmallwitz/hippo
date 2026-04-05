"""Integration tests: full roundtrips through the semantic memory store."""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
import pytest

from hippo.memory.semantic import ObsidianSemanticStore
from hippo.memory.types import Entity, Relation


@pytest.fixture()
def store(tmp_vault: Path) -> ObsidianSemanticStore:
    return ObsidianSemanticStore(tmp_vault)


# ---------------------------------------------------------------------------
# Full roundtrips
# ---------------------------------------------------------------------------


class TestFullRoundtrip:
    async def test_create_observe_search(self, store: ObsidianSemanticStore) -> None:
        """Create an entity, add observations, then search for it."""
        await store.create_entities([Entity(name="The Dispossessed", entity_type="topic")])
        await store.add_observations(
            "The Dispossessed",
            ["Science fiction novel by Ursula K. Le Guin", "User's favorite book"],
        )

        result = await store.search_nodes("Le Guin")
        assert len(result.entities) == 1
        entity = result.entities[0]
        assert entity.name == "The Dispossessed"
        assert "Science fiction novel by Ursula K. Le Guin" in entity.observations
        assert "User's favorite book" in entity.observations

    async def test_relation_roundtrip(self, store: ObsidianSemanticStore) -> None:
        """Create two entities, relate them, read graph, verify."""
        await store.create_entities(
            [
                Entity(name="Alice", entity_type="person"),
                Entity(name="ACME Corp", entity_type="organization"),
            ]
        )
        rel = Relation(from_entity="Alice", to_entity="ACME Corp", relation_type="Works at")
        await store.create_relations([rel])

        graph = await store.read_graph()
        assert len(graph.entities) == 2
        assert len(graph.relations) == 1
        assert graph.relations[0] == rel

    async def test_delete_cascade(self, store: ObsidianSemanticStore) -> None:
        """Delete an entity and verify inbound relations are cleaned up."""
        await store.create_entities(
            [
                Entity(name="Alice", entity_type="person"),
                Entity(name="Bob", entity_type="person"),
                Entity(name="Project X", entity_type="project"),
            ]
        )
        await store.create_relations(
            [
                Relation(from_entity="Alice", to_entity="Project X", relation_type="Works on"),
                Relation(from_entity="Bob", to_entity="Project X", relation_type="Leads"),
                Relation(from_entity="Alice", to_entity="Bob", relation_type="Collaborates with"),
            ]
        )

        # Delete Project X
        await store.delete_entities(["Project X"])

        graph = await store.read_graph()
        assert len(graph.entities) == 2
        # Only the Alice→Bob relation should remain
        assert len(graph.relations) == 1
        assert graph.relations[0].to_entity == "Bob"

    async def test_multi_step_evolution(self, store: ObsidianSemanticStore) -> None:
        """Simulate a realistic multi-turn conversation memory evolution."""
        # Turn 1: User mentions a book
        await store.create_entities(
            [
                Entity(
                    name="The Dispossessed",
                    entity_type="topic",
                    observations=("User's favorite book",),
                )
            ]
        )

        # Turn 2: More details
        await store.add_observations(
            "The Dispossessed",
            ["Written by Ursula K. Le Guin", "Anarchist utopia theme"],
        )

        # Turn 3: A related entity
        await store.create_entities(
            [
                Entity(
                    name="Ursula K. Le Guin",
                    entity_type="person",
                    observations=("Science fiction author",),
                )
            ]
        )
        await store.create_relations(
            [
                Relation(
                    from_entity="The Dispossessed",
                    to_entity="Ursula K. Le Guin",
                    relation_type="Written by",
                )
            ]
        )

        # Verify the graph
        graph = await store.open_nodes(["The Dispossessed", "Ursula K. Le Guin"])
        assert len(graph.entities) == 2
        assert len(graph.relations) == 1

        book = next(e for e in graph.entities if e.name == "The Dispossessed")
        assert len(book.observations) == 3

        # Turn 4: Correct a fact
        await store.delete_observations("The Dispossessed", ["Anarchist utopia theme"])
        await store.add_observations(
            "The Dispossessed", ["Explores anarchist vs. capitalist societies"]
        )

        result = await store.search_nodes("Dispossessed")
        book = result.entities[0]
        assert "Anarchist utopia theme" not in book.observations
        assert "Explores anarchist vs. capitalist societies" in book.observations
