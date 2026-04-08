---
name: process-isolation
description: Prefer OS-level process isolation over in-process threading when running multiple independent agent instances on the same host.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-06-phase7-multi-bot-deployment
---

# Process Isolation for Independent Agent Instances

When one host runs multiple independent agent instances, use separate OS processes — not threads or async tasks within one process.

**Why:** Module-level globals (loggers, MCP server state, in-memory caches, scheduler loops) are naturally isolated between processes. No locking, no refactoring of existing modules, no subtle shared-state bugs.

**Pattern:**

```
# Each instance is a separate invocation
uv run hippo Alice   # independent process, own vault, own scheduler
uv run hippo Bob     # independent process, own vault, own scheduler
```

**Rules:**
- Each process reads its own config, writes to its own vault, and has its own scheduler loop.
- Processes do not share memory. Inter-instance communication uses the filesystem mailbox (`inbox/`).
- Do not introduce threading or `asyncio.create_task` to run multiple bot loops within a single process — it creates implicit coupling.
- The launcher script (`start-bots.ps1`) starts each bot as a separate process and captures stdout/stderr per-process to separate log files.
