# Phase 6: Memory Intelligence — Shaping Notes

## Scope

Three deliverables:
1. **Embedding-based semantic search** — replace substring matching in `search_nodes`
   with cosine similarity using a local sentence-transformers model
2. **Fuzzy entity matching** — dream agent checks for near-duplicate entities
   before creating new ones
3. **Episodic summarization** — dream cycle compresses old daily notes (>30 days,
   >2000 chars) and archives originals to `episodic/archive/`

## Decisions

- **Embedding backend**: local `sentence-transformers` (model `all-MiniLM-L6-v2`,
  ~80MB). No API key required. Consistent with the local-first Whisper approach.
- **Storage**: `semantic/embeddings.json` in the vault (vault-first principle).
  `.json` extension naturally excluded from `_load_all()`'s `rglob("*.md")`.
- **Lazy loading**: model loaded on first use, not at startup (same pattern as
  `hippo/voice.py`). If `HIPPO_EMBEDDING_MODEL` is empty, all embedding features
  are disabled and substring fallback is used.
- **Fuzzy matching threshold**: 0.7 (higher than search threshold of 0.4 to avoid
  false merges — entity dedup needs higher confidence than search).
- **Episodic archive**: original verbose notes moved to `episodic/archive/`, replaced
  by a condensed summary. Nothing is lost; user can restore manually.
- **Dream-time rebuild**: after each dream cycle, `embeddings.json` is fully rebuilt
  to sync any new/modified entities.

## Context

- **Visuals**: None
- **References**: `hippo/voice.py` (lazy model loading), `hippo/memory/semantic.py`
  (current `search_nodes` at line 359), `hippo/dream/runner.py` (dream orchestration)
- **Product alignment**: Phase 6 is explicitly on the roadmap. Stays within the
  vault-first, no-database constraints defined in the mission.

## Standards Applied

- `global/coding-style` — type hints, lazy imports, asyncio.to_thread for blocking ops
- `global/conventions` — uv only, Conventional Commits, feature branch
- `global/error-handling` — embedding failures must never block core memory ops
- `global/tech-stack` — no new databases; new dep justified (embeddings are core feature)

## Implementation Base

base_commit: ccdf6efbae8b15fc58bca6688613761b3a0f293c
captured_at: 2026-04-08T00:00:00Z
captured_by: finish-spec (legacy fallback)

## Deviations & Bugfixes

2026-04-08

### What was built as planned
- Embedding Manager (hippo/memory/embeddings.py): lazy-loaded sentence-transformers, cosine similarity, vault-file storage at semantic/embeddings.json
- Enhanced search_nodes with embedding-based search + substring fallback
- Fuzzy entity matching via find_similar_entities (threshold 0.7), wired as dream MCP tool
- Episodic summarization: find_archivable_notes() + archive_daily_note() on ObsidianEpisodicStore
- Dream cycle wiring: episodic summarization + embedding rebuild after each run
- Config: hippo_embedding_model, hippo_search_threshold, hippo_episodic_archive_days
- Roadmap updated to mark Phase 6 as Done

### What was built differently
- Raw document scanning changed from flat (iterdir) to recursive (rglob) — better handles subdirectories in raw/.

### What was added beyond the plan
- hippo/dream/housekeeping.py (218 lines): full vault lifecycle pruning — buffer archives, dream reports, completed tasks, raw/processed files, episodic archive monthly consolidation.
- hippo_retention_days config field (default 90 days) for housekeeping.
- Comprehensive test suites: test_embeddings.py (206 lines), test_housekeeping.py (350 lines).

### What was not built
- Nothing: all tasks complete.
