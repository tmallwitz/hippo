---
name: commands-bypass-agent
description: Status and info Telegram commands read directly from stores without querying the LLM agent.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-05-phase5-telegram-upgrade
---

# Commands Bypass the Agent

Telegram commands that display status or list data (`/status`, `/tasks`, `/memory`, `/help`) must read directly from the memory stores. They never query the LLM agent.

**Why:** Instant response (<100ms vs seconds), no rate-limit or token cost, predictable output format.

**Rules:**
- Handlers for info commands receive store references directly and format the output in Python.
- The agent is only queried for open-ended user messages, voice, and images.
- `/dream` is a special case: it calls `run_dream()` directly (also bypasses the conversational agent).
