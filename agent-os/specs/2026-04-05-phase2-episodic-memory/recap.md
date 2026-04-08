# Recap: Phase 2 — Episodic Memory

**Completed:** 2026-04-08
**Base commit:** dca03f0deb735a8b3e055d78cf4216014c37c485
**Final commit:** 14c26667582776a9b035122bf11c967520166154
**Milestone:** m1-foundation

## What this spec delivered

Hippo gained a time-ordered journal layer alongside its semantic knowledge graph. The bot can now log detailed episode summaries to daily Markdown notes (`episodic/YYYY-MM-DD.md`) and recall them by date range and text query. The system prompt instructs the agent to log verbosely after every meaningful exchange, with the expectation that the dream cycle (Phase 3) will later prune what's not worth keeping.

## Key decisions

- **Verbose logging by default** — the agent logs detailed summaries of every meaningful exchange, not just noteworthy events; pruning is deferred to the dream cycle.
- **No CRUD beyond log+recall** — editing and deleting episodes is done manually in Obsidian, keeping the tool surface minimal.
- **Dash-tolerant H2 parsing** — regex handles em-dash, en-dash, and plain hyphen for resilience against Obsidian editor normalization.

## Surprises and lessons

- Phase 2 was small enough to ship in a single commit without sub-phases, confirming that the sub-phase approach from Phase 1 was a one-time complexity management tool rather than a mandatory pattern.

## Carry-over candidates

- Episode summarization/compression for old daily notes (Phase 6 later delivered this)
- Dream cycle integration to prune verbose logs (Phase 3 delivered this)

## Files touched

 agent-os/specs/2026-04-05-phase2.../plan.md        |  21 ++
 agent-os/specs/2026-04-05-phase2.../references.md  |  22 +++
 agent-os/specs/2026-04-05-phase2.../shape.md       |  33 ++++
 agent-os/specs/2026-04-05-phase2.../standards.md   |   8 +
 hippo/agent.py                                     |  31 +++
 hippo/memory/__init__.py                           |   4 +-
 hippo/memory/episodic.py                           | 218 +++++++++++++++
 hippo/memory/server.py                             |  71 ++++-
 hippo/memory/store.py                              |  26 ++-
 hippo/memory/types.py                              |  10 +
 tests/conftest.py                                  |   6 +-
 tests/test_episodic.py                             | 220 +++++++++++++++
 12 files changed, 661 insertions(+), 9 deletions(-)
