# Phase 1: Semantic Memory + Telegram Bridge — Shaping Notes

## Scope

Port the core knowledge-graph memory system from the TypeScript reference
project (`obsidian-memory-mcp` by YuNaga224) to Python. Wire it into the
Claude Agent SDK as an in-process MCP server. Connect a Telegram bot as
the sole user interface. Deliver a working bot that remembers facts across
sessions, stored as human-readable Markdown in an Obsidian vault.

Nine semantic memory tools, one Telegram bridge, one system prompt.
No dream cycle, no episodic memory, no short-term buffer (those are
Phase 2 and Phase 3).

## Decisions

- **Flat layout** chosen over src-layout (`hippo/` at project root).
  The conventions standard says src-layout, but PLAN.md shows flat and
  the user confirmed this choice. Simpler for a single-package project.
- **Category subfolders** (`semantic/<EntityType>/`) instead of the
  TS reference's flat directory. Maps naturally to Obsidian folder
  structure and makes the vault more navigable.
- **Entity name in YAML frontmatter** — store original `name` field
  to fix the TS reference's lossy filename round-trip.
- **Preserve `created` date** on updates — fix the TS bug where every
  save overwrites the creation timestamp.
- **Relation targets not validated** — creating a relation to a
  nonexistent entity logs a warning but doesn't block. Matches the
  loose TS behavior but adds observability.
- **Auth via `claude login`** — the SDK spawns the Claude Code CLI
  as a subprocess. Auth comes from having run `claude login` on the
  server. No API key in `.env`.
- **Break Phase 1 into sub-phases** (P1a–P1d) for incremental shipping.

## Context

- **Visuals:** None — this is a CLI/Telegram bot with no UI to mock up.
- **References:** TypeScript `obsidian-memory-mcp` repo studied in detail
  (see references.md).
- **Product alignment:** Matches Phase 1 in roadmap.md. Strict phase
  boundaries: no Phase 2/3 features pulled forward.

## Standards Applied

- global/coding-style — type hints, small functions, Pydantic models
- global/conventions — flat layout (override), uv.lock committed, dev deps separated
- global/commenting — self-documenting code, Google-style docstrings
- global/error-handling — fail fast, specific exceptions, structured logging
- global/tech-stack — Claude Agent SDK, aiogram v3, python-frontmatter, Pydantic
- global/validation — Pydantic models for config, validate early
