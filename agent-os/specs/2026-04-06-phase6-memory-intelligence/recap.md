# Recap: Phase 6 — Memory Intelligence

**Completed:** 2026-04-08
**Base commit:** ccdf6efbae8b15fc58bca6688613761b3a0f293c
**Final commit:** 629b89d8dc7dde62ddf64684d1ce3574ee584127
**Milestone:** m1-foundation

## What this spec delivered

Hippo's semantic search now uses embedding-based cosine similarity (via local `sentence-transformers` with `all-MiniLM-L6-v2`) instead of naive substring matching, with an automatic fallback when embeddings are unavailable. The dream cycle can detect near-duplicate entities using fuzzy matching (threshold 0.7) before creating new ones, and automatically summarizes old episodic daily notes (>30 days, >2000 chars) by archiving the originals and writing condensed summaries. A new housekeeping module prunes old buffer archives, dream reports, completed tasks, and raw processed files based on a configurable retention period.

## Key decisions

- **Local sentence-transformers** (`all-MiniLM-L6-v2`, ~80MB) — consistent with local-first Whisper approach; no API key, works offline.
- **Embeddings stored in vault** (`semantic/embeddings.json`) — vault-first principle; `.json` extension naturally excluded from `_load_all()`'s `rglob("*.md")`.
- **Two thresholds** — search uses 0.4 (permissive, finds related content), fuzzy entity matching uses 0.7 (conservative, avoids false merges).
- **Embedding failures never block** — all embedding operations are wrapped in try/except and degrade gracefully to substring search.
- **Housekeeping module** — emerged during implementation as a natural extension of episodic summarization; handles full vault lifecycle.

## Surprises and lessons

- Housekeeping (buffer archive pruning, report cleanup, etc.) was a significant addition beyond the original plan — the need became obvious once episodic summarization was in place.
- Dream-time full rebuild of embeddings.json is simple but could become expensive as the entity count grows; incremental updates at write time handle the common case.

## Carry-over candidates

- Incremental embedding updates may need optimization if entity count exceeds ~10k
- Housekeeping dry-run mode for debugging retention policies
- Embedding model upgrade path (how to re-embed when switching models)

## Files touched

 .env.example                                       |  19 ++
 agent-os/product/roadmap.md                        |   2 +-
 agent-os/specs/2026-04-06-phase6.../plan.md        |  59 ++++
 agent-os/specs/2026-04-06-phase6.../references.md  |  38 +++
 agent-os/specs/2026-04-06-phase6.../shape.md       |  42 +++
 agent-os/specs/2026-04-06-phase6.../standards.md   |  30 ++
 hippo/__main__.py                                  |   9 +-
 hippo/agent.py                                     |   2 +
 hippo/config.py                                    |   4 +
 hippo/dream/housekeeping.py                        | 218 +++++++++++++
 hippo/dream/prompts.py                             |  14 +-
 hippo/dream/runner.py                              | 267 ++++++++++---
 hippo/memory/embeddings.py                         | 253 +++++++++++++
 hippo/memory/episodic.py                           |  70 ++++
 hippo/memory/semantic.py                           | 101 +++++-
 hippo/memory/server.py                             |  30 +-
 hippo/scheduler.py                                 |   7 +-
 hippo/telegram_bridge.py                           |  31 +-
 tests/test_config.py                               |  25 ++
 tests/test_embeddings.py                           | 206 ++++++++++++
 tests/test_episodic.py                             | 103 +++++
 tests/test_housekeeping.py                         | 350 +++++++++++++++
 25 files changed, 2152 insertions(+), 66 deletions(-)
