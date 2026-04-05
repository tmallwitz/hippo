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
