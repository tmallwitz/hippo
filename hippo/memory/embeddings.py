"""Local embedding infrastructure for semantic search and fuzzy entity matching.

Embeddings are stored in ``semantic/embeddings.json`` inside the vault.
The sentence-transformers model is lazy-loaded on first use.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import logging
import math
import tempfile
from pathlib import Path
from typing import Any

from hippo.memory.types import Entity

log = logging.getLogger(__name__)

# Module-level lazy-loaded model: (model_name, model_object) | None
_loaded_model: tuple[str, Any] | None = None

_EMBEDDINGS_FILE = "semantic/embeddings.json"


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------


def _load_model(model_name: str) -> Any:
    """Lazy-load and cache the SentenceTransformer model."""
    global _loaded_model
    if _loaded_model is not None and _loaded_model[0] == model_name:
        return _loaded_model[1]
    log.info("Loading embedding model '%s' (first use — may download ~80MB)…", model_name)
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)
    _loaded_model = (model_name, model)
    log.info("Embedding model '%s' loaded.", model_name)
    return model


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------


def _compose_entity_text(entity: Entity) -> str:
    """Build the text string to embed for an entity."""
    obs_text = ". ".join(entity.observations) if entity.observations else ""
    base = f"{entity.name} ({entity.entity_type})"
    return f"{base}: {obs_text}" if obs_text else base


def _compute_text_hash(text: str) -> str:
    """SHA-256 of text, truncated to 16 hex chars for staleness detection."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Cosine similarity (pure Python — numpy available but not required)
# ---------------------------------------------------------------------------


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two equal-length vectors."""
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------


def embed_text(text: str, model_name: str) -> list[float]:
    """Embed a single text string (blocking — designed for asyncio.to_thread)."""
    model = _load_model(model_name)
    vector = model.encode(text, convert_to_numpy=True)
    return vector.tolist()  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Vault storage
# ---------------------------------------------------------------------------


def load_embeddings(vault_path: Path) -> dict[str, Any]:
    """Load embeddings from vault. Returns empty structure if file missing."""
    path = vault_path / _EMBEDDINGS_FILE
    if not path.exists():
        return {"model": "", "entities": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))  # type: ignore[no-any-return]
    except Exception:
        log.warning("Could not read embeddings file, starting fresh: %s", path)
        return {"model": "", "entities": {}}


def save_embeddings(vault_path: Path, data: dict[str, Any]) -> None:
    """Write embeddings to vault atomically."""
    path = vault_path / _EMBEDDINGS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".json.tmp")
    try:
        import os

        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        Path(tmp).replace(path)
    except Exception:
        with contextlib.suppress(Exception):
            Path(tmp).unlink(missing_ok=True)
        raise


# ---------------------------------------------------------------------------
# Incremental and full rebuild
# ---------------------------------------------------------------------------


def update_entity_embeddings(vault_path: Path, entities: list[Entity], model_name: str) -> None:
    """Incrementally update embeddings for the given entities.

    Skips entities whose text hash has not changed.
    Blocking — run via asyncio.to_thread.
    """
    data = load_embeddings(vault_path)
    if data.get("model") != model_name:
        data = {"model": model_name, "entities": {}}

    stored = data["entities"]
    changed = False

    for entity in entities:
        text = _compose_entity_text(entity)
        text_hash = _compute_text_hash(text)
        existing = stored.get(entity.name, {})
        if existing.get("text_hash") == text_hash:
            continue  # unchanged
        vector = embed_text(text, model_name)
        stored[entity.name] = {"vector": vector, "text_hash": text_hash}
        changed = True

    if changed:
        save_embeddings(vault_path, data)


def rebuild_all_embeddings(vault_path: Path, entities: list[Entity], model_name: str) -> None:
    """Full rebuild — embed all entities and remove stale entries.

    Blocking — run via asyncio.to_thread.
    """
    data = load_embeddings(vault_path)
    current_names = {e.name for e in entities}
    stored = data.get("entities", {}) if data.get("model") == model_name else {}

    new_stored: dict[str, Any] = {}
    for entity in entities:
        text = _compose_entity_text(entity)
        text_hash = _compute_text_hash(text)
        existing = stored.get(entity.name, {})
        if existing.get("text_hash") == text_hash and "vector" in existing:
            new_stored[entity.name] = existing  # reuse unchanged
        else:
            vector = embed_text(text, model_name)
            new_stored[entity.name] = {"vector": vector, "text_hash": text_hash}

    # Remove embeddings for entities that no longer exist
    for name in list(stored.keys()):
        if name not in current_names:
            pass  # not added to new_stored — effectively removed

    save_embeddings(vault_path, {"model": model_name, "entities": new_stored})
    log.info("Rebuilt embeddings for %d entities.", len(new_stored))


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


def search_by_embedding(
    query: str,
    vault_path: Path,
    model_name: str,
    threshold: float,
) -> list[tuple[str, float]]:
    """Embed query and return entity names above the similarity threshold.

    Returns list of (entity_name, score) sorted by score descending.
    Blocking — run via asyncio.to_thread.
    """
    data = load_embeddings(vault_path)
    stored = data.get("entities", {})
    if not stored:
        return []

    query_vector = embed_text(query, model_name)
    results: list[tuple[str, float]] = []

    for name, entry in stored.items():
        vec = entry.get("vector")
        if not vec:
            continue
        score = cosine_similarity(query_vector, vec)
        if score >= threshold:
            results.append((name, score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


def find_similar_names(
    name: str,
    vault_path: Path,
    model_name: str,
    threshold: float,
) -> list[tuple[str, float]]:
    """Embed just the entity name and find similar names in stored embeddings.

    Used for near-duplicate detection before entity creation.
    Returns list of (entity_name, score) above threshold, sorted descending.
    Blocking — run via asyncio.to_thread.
    """
    data = load_embeddings(vault_path)
    stored = data.get("entities", {})
    if not stored:
        return []

    name_vector = embed_text(name, model_name)
    results: list[tuple[str, float]] = []

    for stored_name, entry in stored.items():
        if stored_name == name:
            continue
        vec = entry.get("vector")
        if not vec:
            continue
        score = cosine_similarity(name_vector, vec)
        if score >= threshold:
            results.append((stored_name, score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results
