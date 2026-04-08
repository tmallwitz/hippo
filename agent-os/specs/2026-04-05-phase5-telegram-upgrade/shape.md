# Phase 5: Telegram Upgrade — Shaping Notes

## Scope

Extend `hippo/telegram_bridge.py` (and add `hippo/voice.py`) to handle:
- Voice messages via local Whisper transcription
- Images via Claude vision
- Other media types with a polite rejection
- Four new Telegram commands: `/help`, `/status`, `/tasks`, `/memory N`

## Decisions

- **Whisper backend**: local `openai-whisper` (not the OpenAI API). Avoids API key requirement, runs on the same host. Model size configurable via `HIPPO_WHISPER_MODEL` (default `base`, ~150MB). User must have `ffmpeg` installed.
- **Image storage**: description only — no images saved to vault. Claude receives the image via base64 and responds; the response summary is appended to the buffer.
- **Commands are direct reads**: `/status`, `/tasks`, `/memory` bypass the agent entirely and read from stores directly. Fast, no rate-limit cost.
- **`/help`**: static text, hardcoded in the handler.
- **Store access**: `create_memory_server` is extended to return the semantic + episodic stores alongside the existing three, propagated through `create_agent` and `__main__.py` to `run_bot`.

## Context

- **Visuals**: None
- **References**: `hippo/telegram_bridge.py` (existing text + /dream handlers), `hippo/memory/server.py` (store factory)
- **Product alignment**: Phase 5 is explicitly on the roadmap. No feature additions beyond the spec.

## Standards Applied

- `global/coding-style` — type hints, async/await, small focused functions
- `global/tech-stack` — aiogram v3 patterns, uv for deps, no pip
- `global/conventions` — Conventional Commits, feature branch, squash merge

## Implementation Base

base_commit: 68e84ebaa7932d4341e999c1e387c985bca8a990
captured_at: 2026-04-08T00:00:00Z
captured_by: finish-spec (legacy fallback)

## Deviations & Bugfixes

2026-04-08

### What was built as planned
- Voice transcription via local openai-whisper with lazy-loaded model singleton (hippo/voice.py)
- Image handling via Claude vision with base64 encoding (query_agent_with_image)
- Other media rejection handler for unsupported types
- /help, /status, /tasks, /memory N commands — all bypass the agent, read from stores directly
- Store plumbing: create_memory_server returns 5-tuple, create_agent returns 6-tuple
- Config: hippo_whisper_model added to HippoConfig

### What was built differently
- Nothing: plan reflects actual implementation.

### What was added beyond the plan
- hippo_whisper_language config field: optional language hint for Whisper (None = auto-detect).
- Follow-up commits: ruff format + mypy cleanup (989a4c2), roadmap status update (ccdf6ef).

### What was not built
- Nothing: all tasks complete.
