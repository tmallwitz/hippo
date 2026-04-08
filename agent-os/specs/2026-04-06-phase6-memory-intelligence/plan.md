# Phase 6: Memory Intelligence — Plan

## Context

Hippo's semantic search (`search_nodes`) currently uses naive substring matching.
This misses semantically related terms and produces false negatives. Entity
deduplication in the dream cycle relies on exact name lookups, so near-duplicate
entities can coexist. Old episodic daily notes accumulate without bound.

Phase 6 adds:
1. Embedding-based semantic search (cosine similarity via `sentence-transformers`)
2. Fuzzy entity matching for the dream agent (near-duplicate detection)
3. Automatic episodic summarization with archival

## Tasks

### Task 1: Spec documentation
Create this spec folder.

### Task 2: Dependencies + Configuration
- `pyproject.toml` — add `sentence-transformers>=2.0`
- `hippo/config.py` — add `hippo_embedding_model`, `hippo_search_threshold`, `hippo_episodic_archive_days`
- `.env.example` — document new env vars
- `tests/test_config.py` — verify defaults

### Task 3: Embedding Manager Module
New `hippo/memory/embeddings.py` — lazy-loaded model, cosine similarity, vault-file
storage at `semantic/embeddings.json`, incremental + full rebuild.

### Task 4: Enhance search_nodes
Modify `hippo/memory/semantic.py` to use embeddings for search when available,
with substring fallback. Wire config through `server.py` and `agent.py`.

### Task 5: Fuzzy Entity Matching
New `find_similar_entities` method on `ObsidianSemanticStore`, exposed as a
dream-only MCP tool. Update dream system prompt to use it.

### Task 6: Episodic Summarization Infrastructure
New `find_archivable_notes()` and `archive_daily_note()` methods on
`ObsidianEpisodicStore`.

### Task 7: Wire Episodic Summarization into Dream Cycle
Extend `run_dream()` to summarize old notes. Thread `episodic_store` through
scheduler and `__main__.py`.

### Task 8: Dream-Time Embedding Rebuild
After each dream cycle, rebuild `semantic/embeddings.json` to include any
newly created or modified entities.

### Task 9: Update Roadmap
Mark Phase 6 as Done.

## Verification
1. `uv run pytest tests/ -v` — all tests pass
2. `uv run ruff check hippo/ tests/` — no errors
3. `uv run mypy hippo/` — no errors
4. Manual: create entity, verify `semantic/embeddings.json` written
5. Manual: semantic search finds entity without substring match
6. Manual: `/dream` report includes "Episodes summarized" line

## Deviations & Bugfixes

2026-04-08

### What was built as planned
- Task 2: Dependencies + config (sentence-transformers, 4 new config fields)
- Task 3: Embedding Manager in hippo/memory/embeddings.py
- Task 4: search_nodes enhanced with embedding search + substring fallback
- Task 5: find_similar_entities as dream MCP tool, dream prompt updated
- Task 6: find_archivable_notes + archive_daily_note on episodic store
- Task 7: Wired into dream cycle with episodic_store threading
- Task 8: Embedding rebuild after dream runs
- Task 9: Roadmap updated

### What was built differently
- Raw document scanning: recursive rglob instead of flat iterdir.

### What was added beyond the plan
- hippo/dream/housekeeping.py: vault lifecycle pruning (buffer archives, reports, tasks, raw)
- hippo_retention_days config (90-day default)
- test_embeddings.py + test_housekeeping.py

### What was not built
- Nothing.
