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
