# Phase 2: Episodic Memory — Shaping Notes

## Scope

Add a time-ordered journal layer alongside the semantic knowledge graph.
Two new tools: `log_episode` and `recall_episodes`. Daily notes stored
as Markdown in `episodic/YYYY-MM-DD.md` with H2 sections per episode.

No delete/update tools — editing happens manually in Obsidian.

## Decisions

- **Verbose logging:** The agent logs detailed summaries of every meaningful
  exchange, not just noteworthy events. The dream cycle (Phase 3) will
  later decide what's worth keeping and prune the rest.
- **No CRUD beyond log+recall:** Editing and deleting episodes is done
  manually in Obsidian. Keeps the tool surface minimal.
- **Optional timestamp parameter:** `log_episode` accepts an optional
  `timestamp` for testing and future Phase 3 (dream cycle) use.
- **Dash-tolerant parsing:** H2 heading regex handles em-dash, en-dash,
  and plain hyphen for resilience against different editors.
- **One shot:** Phase 2 is small enough to ship without sub-phases.

## Context

- **Visuals:** None
- **References:** Phase 1 semantic memory (same file I/O, frontmatter,
  async patterns in semantic.py)
- **Product alignment:** Matches Phase 2 in roadmap.md exactly

## Standards Applied

- All six global standards (same as Phase 1)

## Implementation Base

base_commit: dca03f0deb735a8b3e055d78cf4216014c37c485
captured_at: 2026-04-08T00:00:00Z
captured_by: finish-spec (legacy fallback)

## Deviations & Bugfixes

2026-04-08

### What was built as planned
- Episode Pydantic model added to types.py
- EpisodicStore protocol added to store.py
- ObsidianEpisodicStore implemented in new episodic.py (daily notes, H2 sections, tag parsing)
- 2 MCP tools (log_episode, recall_episodes) wired into server.py
- System prompt extended in agent.py with verbose episodic logging instructions
- ~15 tests in new test_episodic.py

### What was built differently
- Nothing: spec was written retrospectively; plan reflects actual implementation.

### What was added beyond the plan
- Nothing notable beyond spec documentation files.

### What was not built
- Nothing: all deliverables complete.
