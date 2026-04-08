---
name: verbose-log-deferred-prune
description: Memory tools log verbosely; pruning and summarization are deferred to the dream cycle, not done at write time.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-05-phase2-episodic-memory
---

# Verbose Logging with Deferred Pruning

When writing to the short-term buffer or episodic journal, capture as much detail as possible. Do not filter or summarize at write time.

**Why:** The agent cannot judge in the moment what will be important later. The dream cycle has full context (buffer + long-term memory) and can make better decisions about what to keep, merge, or discard.

**Rules:**
- `log_episode` and `remember` capture full detail — who said what, decisions made, mood, context.
- The system prompt explicitly instructs the agent to err on the side of logging too much.
- The dream cycle is the only process that prunes, summarizes, or discards entries.
- Never add filtering logic to write-path tools.
