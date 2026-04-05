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
