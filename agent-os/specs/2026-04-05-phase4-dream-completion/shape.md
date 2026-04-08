# Phase 4: Dream Completion — Shaping Notes

## Scope

Complete the dream cycle's capabilities so it becomes a fully autonomous memory-management engine. Six deliverables:

1. Dream report append — fix overwrite bug so multiple same-day dreams accumulate
2. Scheduler → buffer pipeline — feed task results into the dream cycle
3. Raw document ingest — `raw/` folder in the vault for ad-hoc document processing
4. Dream skills — dream agent creates `.claude/skills/` files using the official skill-creator format
5. Semantic index auto-maintenance — `semantic/index.md` regenerated after every run
6. Self-evolving personality — `personality/prompt_ext.md` polished after every run

## Decisions

- **No git autocommit for the vault.** The vault is runtime data (what the bot learns), not source code. Git tracks only the codebase. Dropped from roadmap.
- **Everything in the vault.** All bot-generated files (skills, personality, index, reports) live under `HIPPO_VAULT_PATH`. Both the main agent and dream agent have `cwd=vault_path`, so relative paths like `.claude/skills/` resolve inside the vault.
- **Skill creation uses the official skill-creator skill.** The `anthropics/skills` skill-creator is installed into the vault at `.claude/skills/skill-creator/`. The dream agent reads it at runtime rather than having the format hard-coded in the dream prompt.
- **Raw ingest: Python scans, agent classifies.** Raw files are read in Python and passed in the dream query, not scanned by the agent itself. More reliable than having the agent read the filesystem.
- **No dedicated MCP write tool for skills.** The dream agent already has built-in file tools (`bypassPermissions` + `cwd=vault_path`). A dedicated tool would add code complexity for no benefit.

## Context

- **Visuals:** None
- **References:** Phase 3 spec + dream cycle code (`hippo/dream/runner.py`, `hippo/dream/prompts.py`)
- **Product alignment:** Phase 4 is defined in `agent-os/product/roadmap.md` as the next planned phase after Phase 3

## Standards Applied

- coding-style — all new Python follows existing naming/formatting/type-hint conventions
- conventions — no new deps; vault-first principle for all generated files
- error-handling — git/subprocess errors caught and logged, not raised; raw file errors tolerated
- tech-stack — filesystem storage, Claude Agent SDK sub-agent pattern, uv tooling

## Implementation Base

base_commit: 44e9e560b08f92e83790df3fecb1858390eb8190
captured_at: 2026-04-08T00:00:00Z
captured_by: finish-spec (legacy fallback)

## Deviations & Bugfixes

2026-04-08

### What was built as planned
- Dream report append: multiple same-day runs produce timestamped sections with separators
- Scheduler → buffer pipeline: task results appended to buffer with session="scheduler-{id}"
- Raw document ingest: _scan_raw_documents(), _format_raw_documents(), _move_raw_to_processed()
- Dream skills: skill-creator format with YAML frontmatter, evals.json, 3-occurrence threshold
- Semantic index: prompt updated to prefer semantic/index.md over read_graph
- Self-evolving personality: _load_personality_ext() in agent.py, dream prompt updated

### What was built differently
- Skill-creator bundled as hippo/assets/skill-creator/ and copied to vault on startup via setup.py, rather than downloaded from GitHub at runtime (more reliable, works offline).

### What was added beyond the plan
- hippo/setup.py: vault setup module that creates dirs (raw/, personality/) and installs bundled skills on first run.
- Git autocommit explicitly dropped from roadmap (vault is runtime data, not code).

### What was not built
- Git autocommit: intentionally dropped per shaping decision (vault is runtime data).
