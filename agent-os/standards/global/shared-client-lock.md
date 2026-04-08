---
name: shared-client-lock
description: A single asyncio.Lock prevents concurrent agent queries from Telegram, scheduler, and dream triggers.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-05-phase2b-scheduler
---

# Shared Client Lock

All code paths that query the `ClaudeSDKClient` must acquire a shared `asyncio.Lock` first. The lock is created once in `__main__.py` and passed to all consumers.

```python
# __main__.py
client_lock = asyncio.Lock()
await asyncio.gather(
    run_bot(config, client, bot, client_lock, ...),
    run_scheduler(config, client, client_lock, bot, ...),
)
```

**Why:** The Claude SDK client is not concurrency-safe. Without the lock, the Telegram handler and scheduler could query simultaneously, corrupting the conversation state.

**Rules:**
- Create one `asyncio.Lock()` per bot process.
- Pass it explicitly to every function that calls `query_agent()`.
- Always use `async with client_lock:` — never manual acquire/release.
- The dream cycle uses its own ephemeral client (see `ephemeral-sub-agent` standard), so it does not need this lock.
