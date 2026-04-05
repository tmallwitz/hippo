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
