# Phase 5: Telegram Upgrade — Plan

## Context

Phases 1–4 are complete. The Telegram bridge handles text and `/dream` only. Voice messages and images are silently dropped. There are no quick-status commands. Phase 5 adds media input and direct-read commands.

## Scope

1. **Voice messages** — transcribe locally via `openai-whisper`, pass transcript to agent + buffer
2. **Images** — Claude vision describes the image, response sent + buffered (no file saved to vault)
3. **Other media** — polite rejection message
4. **Commands** — `/help`, `/status`, `/tasks`, `/memory N` (direct store reads, no agent query)

## Tasks

### Task 1: Dependencies + config
- `pyproject.toml`: add `openai-whisper>=20231117`
- `hippo/config.py`: add `hippo_whisper_model: str = "base"`
- `.env.example`: add `HIPPO_WHISPER_MODEL`
- `pyproject.toml` mypy overrides: add `whisper` module

### Task 2: Store plumbing
- `hippo/memory/server.py`: `create_memory_server` returns 5-tuple: `(server, scheduled_store, buffer_store, semantic_store, episodic_store)`
- `hippo/agent.py`: `create_agent` returns 6-tuple adding `semantic_store`, `episodic_store`
- `hippo/__main__.py`: unpack 6-tuple, pass all stores to `run_bot`
- `hippo/telegram_bridge.py`: `run_bot` accepts `scheduled_store`, `semantic_store`, `episodic_store`

### Task 3: New commands
All in `hippo/telegram_bridge.py`. No agent queries.
- `/help` — static listing
- `/status` — buffer count, last dream date, next task
- `/tasks` — list all scheduled tasks
- `/memory [N]` — last N entities + N episodes (default 5)

### Task 4: Other media rejection
Handler for document/sticker/animation/video/audio/etc → polite "I can't process this yet" message.

### Task 5: Voice messages
- New `hippo/voice.py`: lazy-loaded whisper singleton, `async transcribe()` via `asyncio.to_thread`
- Handler: download → transcribe → buffer → agent → reply

### Task 6: Image handling
- `query_agent_with_image()` function in `telegram_bridge.py`
- Handler: download → base64 → vision query → buffer → reply

## Acceptance Criteria

- `uv run pytest` passes (no regression)
- `/help`, `/status`, `/tasks`, `/memory` all respond without querying the agent
- Voice message → transcript shown + agent responds
- Image → Claude describes it + agent responds
- Document → polite rejection
- `/dream` still works

## Deviations & Bugfixes

2026-04-08

### What was built as planned
- Task 1: openai-whisper dep, hippo_whisper_model config, .env.example, mypy override
- Task 2: Store plumbing — server.py 5-tuple, agent.py 6-tuple, __main__.py unpacked
- Task 3: /help, /status, /tasks, /memory commands (direct store reads)
- Task 4: Other media rejection handler
- Task 5: hippo/voice.py with lazy-loaded Whisper singleton
- Task 6: query_agent_with_image() with base64 + vision

### What was built differently
- Nothing.

### What was added beyond the plan
- hippo_whisper_language config (optional language hint)
- Follow-up: ruff format + mypy type-ignore cleanup

### What was not built
- Nothing.
