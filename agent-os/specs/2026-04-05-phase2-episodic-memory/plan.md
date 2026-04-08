# Phase 2: Episodic Memory — Plan

See the full plan at the Claude Code plan file. This is a summary.

## Deliverables

- `Episode` Pydantic model in types.py
- `EpisodicStore` protocol in store.py
- `ObsidianEpisodicStore` in episodic.py (new file)
- 2 new MCP tools in server.py: `log_episode`, `recall_episodes`
- Extended system prompt in agent.py for verbose episodic logging
- ~15 new tests in test_episodic.py

## Acceptance Criteria

1. Bot proactively logs detailed episode summaries during chat
2. "What did we discuss on date X?" returns correct episodes
3. Manual edits in Obsidian picked up on next read
4. Daily notes have correct YAML frontmatter and H2 structure
5. Multiple episodes per day properly separated
6. Tags are searchable

## Deviations & Bugfixes

2026-04-08

### What was built as planned
- Episode model in types.py (Deliverable 1)
- EpisodicStore protocol in store.py (Deliverable 2)
- ObsidianEpisodicStore in episodic.py (Deliverable 3)
- log_episode + recall_episodes MCP tools in server.py (Deliverable 4)
- System prompt extended in agent.py (Deliverable 5)
- Tests in test_episodic.py (Deliverable 6)

### What was built differently
- Nothing.

### What was added beyond the plan
- Nothing notable.

### What was not built
- Nothing.
