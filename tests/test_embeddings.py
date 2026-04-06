"""Tests for the embedding manager module."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from hippo.memory.embeddings import (
    _compose_entity_text,
    _compute_text_hash,
    cosine_similarity,
    load_embeddings,
    save_embeddings,
    update_entity_embeddings,
)
from hippo.memory.types import Entity

# ---------------------------------------------------------------------------
# Pure helpers (no model required)
# ---------------------------------------------------------------------------


class TestComposeEntityText:
    def test_name_and_type_only(self) -> None:
        entity = Entity(name="Alice", entity_type="person")
        assert _compose_entity_text(entity) == "Alice (person)"

    def test_with_observations(self) -> None:
        entity = Entity(
            name="Alice", entity_type="person", observations=("likes cats", "works in Berlin")
        )
        result = _compose_entity_text(entity)
        assert result == "Alice (person): likes cats. works in Berlin"

    def test_single_observation(self) -> None:
        entity = Entity(name="Go", entity_type="topic", observations=("a compiled language",))
        assert _compose_entity_text(entity) == "Go (topic): a compiled language"


class TestComputeTextHash:
    def test_deterministic(self) -> None:
        assert _compute_text_hash("hello") == _compute_text_hash("hello")

    def test_different_inputs_differ(self) -> None:
        assert _compute_text_hash("hello") != _compute_text_hash("world")

    def test_length(self) -> None:
        assert len(_compute_text_hash("anything")) == 16

    def test_hex(self) -> None:
        h = _compute_text_hash("test")
        int(h, 16)  # raises ValueError if not valid hex


class TestCosineSimilarity:
    def test_identical_vectors(self) -> None:
        v = [1.0, 2.0, 3.0]
        assert cosine_similarity(v, v) == pytest.approx(1.0)

    def test_orthogonal_vectors(self) -> None:
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert cosine_similarity(a, b) == pytest.approx(0.0)

    def test_opposite_vectors(self) -> None:
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        assert cosine_similarity(a, b) == pytest.approx(-1.0)

    def test_zero_vector_returns_zero(self) -> None:
        a = [0.0, 0.0]
        b = [1.0, 2.0]
        assert cosine_similarity(a, b) == 0.0

    def test_similar_vectors(self) -> None:
        a = [1.0, 1.0]
        b = [1.0, 0.9]
        score = cosine_similarity(a, b)
        assert 0.9 < score < 1.0

    def test_unit_vectors_dot_product(self) -> None:
        angle = math.pi / 3  # 60 degrees
        a = [math.cos(angle), math.sin(angle)]
        b = [1.0, 0.0]
        assert cosine_similarity(a, b) == pytest.approx(math.cos(angle))


# ---------------------------------------------------------------------------
# Vault file storage (no model required)
# ---------------------------------------------------------------------------


class TestLoadSaveEmbeddings:
    def test_load_missing_file_returns_empty(self, tmp_path: Path) -> None:
        result = load_embeddings(tmp_path)
        assert result == {"model": "", "entities": {}}

    def test_roundtrip(self, tmp_path: Path) -> None:
        data = {
            "model": "test-model",
            "entities": {
                "Alice": {"vector": [0.1, 0.2, 0.3], "text_hash": "abc123"},
            },
        }
        save_embeddings(tmp_path, data)
        loaded = load_embeddings(tmp_path)
        assert loaded["model"] == "test-model"
        assert "Alice" in loaded["entities"]
        assert loaded["entities"]["Alice"]["text_hash"] == "abc123"

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        (tmp_path / "semantic").mkdir()
        data = {"model": "m", "entities": {}}
        save_embeddings(tmp_path, data)
        assert (tmp_path / "semantic" / "embeddings.json").exists()

    def test_load_corrupt_file_returns_empty(self, tmp_path: Path) -> None:
        (tmp_path / "semantic").mkdir(parents=True)
        (tmp_path / "semantic" / "embeddings.json").write_text("not json")
        result = load_embeddings(tmp_path)
        assert result == {"model": "", "entities": {}}


# ---------------------------------------------------------------------------
# Incremental update (model-free — use fake vectors)
# ---------------------------------------------------------------------------


class TestUpdateEntityEmbeddings:
    def test_skips_unchanged_entities(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Entity whose text hash matches should not trigger re-embedding."""
        call_count = 0

        def fake_embed(text: str, model_name: str) -> list[float]:
            nonlocal call_count
            call_count += 1
            return [0.1, 0.2, 0.3]

        monkeypatch.setattr("hippo.memory.embeddings.embed_text", fake_embed)

        entity = Entity(name="Alice", entity_type="person", observations=("likes cats",))

        # First call — should embed
        update_entity_embeddings(tmp_path, [entity], "test-model")
        assert call_count == 1

        # Second call — text hash unchanged, should skip
        update_entity_embeddings(tmp_path, [entity], "test-model")
        assert call_count == 1  # still 1

    def test_re_embeds_after_observation_change(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        call_count = 0

        def fake_embed(text: str, model_name: str) -> list[float]:
            nonlocal call_count
            call_count += 1
            return [float(call_count), 0.0, 0.0]

        monkeypatch.setattr("hippo.memory.embeddings.embed_text", fake_embed)

        entity_v1 = Entity(name="Bob", entity_type="person", observations=("works in Berlin",))
        entity_v2 = Entity(
            name="Bob", entity_type="person", observations=("works in Berlin", "likes Go")
        )

        update_entity_embeddings(tmp_path, [entity_v1], "test-model")
        update_entity_embeddings(tmp_path, [entity_v2], "test-model")
        assert call_count == 2

    def test_model_change_triggers_full_rebuild(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        call_count = 0

        def fake_embed(text: str, model_name: str) -> list[float]:
            nonlocal call_count
            call_count += 1
            return [0.5, 0.5]

        monkeypatch.setattr("hippo.memory.embeddings.embed_text", fake_embed)

        entity = Entity(name="Carol", entity_type="person")
        update_entity_embeddings(tmp_path, [entity], "model-a")
        assert call_count == 1

        # Switching model name means the stored hash is for a different model — re-embed
        update_entity_embeddings(tmp_path, [entity], "model-b")
        assert call_count == 2

    def test_writes_embeddings_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("hippo.memory.embeddings.embed_text", lambda t, m: [1.0, 0.0])
        entity = Entity(name="Dave", entity_type="person")
        update_entity_embeddings(tmp_path, [entity], "test-model")

        path = tmp_path / "semantic" / "embeddings.json"
        assert path.exists()
        data = json.loads(path.read_text())
        assert "Dave" in data["entities"]
        assert data["model"] == "test-model"
