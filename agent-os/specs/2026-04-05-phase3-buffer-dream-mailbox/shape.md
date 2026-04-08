# Phase 3 — Shaping Notes

## Scope

Build Hippo Phase 3: the final roadmap item. Three sub-components:

1. **Short-Term Buffer** — `remember` tool, append-only JSONL
2. **Dream Cycle** — Sub-agent that consolidates buffer into long-term memory
3. **Inter-Bot Mailbox** — Filesystem-based messaging between bots

All three built together in one spec (user confirmed). Dream cycle triggered
by both the existing scheduler and a new `/dream` Telegram command.

## Decisions

- **All three sub-components together** — they build on each other; buffer
  feeds dream, dream processes inbox
- **Dream triggered by scheduler + manual `/dream`** — covers both nightly
  automation and on-demand runs
- **All six standards included** — coding-style, commenting, conventions,
  error-handling, tech-stack, validation
- **Bot registry as convention** — `bots.yaml` in project root, no `.env`
  config needed; `load_bot_registry()` returns empty dict if file missing
- **Separate dream model config** — `HIPPO_DREAM_MODEL` in `.env` allows
  using a cheaper model for consolidation
- **Dream runner owns cleanup** — Runner (not the LLM sub-agent) archives
  buffer and clears inbox in a `finally` block, ensuring it always happens

## Context

- **Visuals:** None
- **References:** Phase 1-2b stores; see `references.md`
- **Product alignment:** Phase 3 is the architectural centerpiece of Hippo —
  the hippocampus metaphor is the core reason the project exists

## Standards Applied

- coding-style — type hints, Pydantic, async/await
- commenting — minimal, evergreen; docstrings for public API
- conventions — UV lockfile, dependency groups, environment config
- error-handling — fail fast, specific exceptions, graceful degradation
- tech-stack — Claude Agent SDK, aiogram v3, JSONL + Markdown storage
- validation — Pydantic Field constraints, validate at boundaries

## Implementation Base

base_commit: 4f4e03298c84882c154a387c37015b9fd6ae9f82
captured_at: 2026-04-08T00:00:00Z
captured_by: finish-spec (legacy fallback)

## Deviations & Bugfixes

2026-04-08

### What was built as planned
- BufferEntry, MailboxMessage, DreamReport Pydantic models in types.py
- ObsidianBufferStore in buffer.py (Markdown-based, not JSONL as originally scoped — see below)
- ObsidianMailboxStore in mailbox.py with load_bot_registry()
- remember, send_message, read_inbox MCP tools in server.py
- create_dream_server() with subset of tools for the dream sub-agent
- hippo/dream/ package: runner.py (orchestrator) + prompts.py (system prompt)
- /dream Telegram command wired in telegram_bridge.py
- bots.yaml created with convention-based registry
- Tests: test_buffer.py, test_mailbox.py, test_dream.py
- Config: hippo_dream_model, .env.example updated

### What was built differently
- Buffer format is Markdown (H2 sections) rather than JSONL as originally scoped: aligns with Obsidian-readable vault philosophy.

### What was added beyond the plan
- Scheduler auto-dream trigger: scheduler.py gained buffer/mailbox awareness to trigger dream when buffer exceeds hippo_buffer_max_entries.
- Style fix commit (44e9e56): ruff format on test_buffer.py.

### What was not built
- Nothing: all deliverables complete.
