---
name: public-bridge-api
description: telegram_bridge.py exposes query_agent() and convert_to_telegram() as public functions for reuse by scheduler and dream.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-05-phase2b-scheduler
---

# Public Bridge API

`hippo/telegram_bridge.py` exposes reusable functions that other modules (scheduler, dream) import:

- `query_agent(client, text) -> str` — send a message to the agent and collect the text response.
- `convert_to_telegram(markdown_text) -> list[dict]` — convert Claude's Markdown into Telegram-ready chunks with entities.

**Rules:**
- Functions intended for cross-module use have no underscore prefix.
- Internal-only helpers (whitelist filter, typing indicator) keep the underscore prefix.
- The scheduler and dream trigger import from `telegram_bridge` rather than duplicating agent-query or formatting logic.
