# Hippo Phase 1 — Semantic Memory + Telegram Bridge

## Context

Hippo is a Claude agent with multi-layered memory, using Telegram as frontend and an Obsidian vault as storage. Phase 1 ports the core knowledge-graph memory from the TypeScript reference (`obsidian-memory-mcp` by YuNaga224) to Python, wires it into the Claude Agent SDK as an in-process MCP server, and connects a Telegram bot. The result: a working bot that remembers facts across sessions, stored as human-readable Markdown in an Obsidian vault.

No source code exists yet — only planning docs, standards, and scaffolding.

## Key decisions

| Decision | Value |
|----------|-------|
| Layout | Flat (`hippo/` at project root, overrides src-layout convention) |
| Auth | Pre-auth via `claude login` on server (no API key in .env) |
| SDK | `claude-agent-sdk` — API verified, matches PLAN.md patterns |
| Storage subfolders | `semantic/<EntityType>/` (diverges from flat TS reference) |
| Entity name preservation | Store original name in YAML frontmatter `name` field (fixes TS lossy round-trip) |
| Created date | Preserve on updates (fixes TS bug) |
| Relation targets | Not validated (warn, don't block) |
| Standards | All six global standards apply |

---

## Sub-phases

### P1a: Project setup + config + data types

Bootstrap the project so `uv sync` works, types are importable, config loads from `.env`.

Files: `pyproject.toml`, `hippo/__init__.py`, `hippo/config.py`,
`hippo/memory/__init__.py`, `hippo/memory/types.py`, `hippo/memory/store.py`,
`hippo/__main__.py`, `tests/conftest.py`

### P1b: Semantic memory + MCP server

Implement all 9 knowledge-graph tools against the filesystem. Wire into SDK MCP server.

Files: `hippo/memory/semantic.py`, `hippo/memory/server.py`,
`tests/test_semantic.py`, `tests/test_memory_roundtrip.py`

### P1c: Telegram bridge + agent wiring + system prompt

Connect MCP server to ClaudeSDKClient, build Telegram bot, write system prompt.

Files: `hippo/agent.py`, `hippo/telegram_bridge.py`, `hippo/__main__.py` (update)

### P1d: Tests + acceptance verification + polish

Fill test gaps, verify acceptance criteria, update README, tag release.

Files: `tests/test_config.py`, `README.md` (update), `.env.example` (update)

---

## Acceptance criteria

1. `uv run hippo` starts the bot, Telegram is reachable
2. Non-whitelisted users silently ignored
3. Tell bot a fact → Markdown file created in vault
4. Obsidian graph view shows entity as node
5. Manual edits in Obsidian picked up on next read
6. Bot can search and recall stored facts
7. Hand-authored skill under `.claude/skills/` loads and affects behavior
8. All roundtrip tests pass

## Verification

1. `uv run pytest` — all tests green
2. `uv run ruff check && uv run ruff format --check` — clean
3. `uv run mypy hippo/` — clean
4. `uv run hippo` — bot starts, manual acceptance via Telegram
5. Tag `v0.1-phase1`

## Deviations & Bugfixes

2026-04-08

### What was built as planned
- P1a: Project setup — all files created as listed
- P1b: Semantic memory — all 9 MCP tools, ObsidianSemanticStore, full test suites
- P1c: Telegram bridge — agent wiring, system prompt, whitelist filter
- P1d: Tests + polish — config tests, README, .env.example

### What was built differently
- Nothing: plan reflects actual implementation.

### What was added beyond the plan
- PLAN.md historical design document
- agent-os/product/roadmap.md status update
- uv.lock (generated artifact)

### What was not built
- Nothing: all tasks complete.
