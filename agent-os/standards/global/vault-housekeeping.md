---
name: vault-housekeeping
description: Configurable retention-based pruning for all time-stamped vault files, run as part of the dream cycle.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-06-phase6-memory-intelligence
---

# Vault Housekeeping Lifecycle

Time-stamped vault files (buffer archives, dream reports, completed tasks, processed raw files, episodic archives) are pruned based on a configurable retention period.

**Rules:**
- `HIPPO_RETENTION_DAYS` (default 90) controls the cutoff for all prunable file types.
- Housekeeping runs as part of each dream cycle, after the main consolidation.
- Files are deleted, not moved — they've already been consolidated into long-term memory.
- Episodic archives get special treatment: individual daily archive files are consolidated into monthly summaries before deletion.
- Housekeeping is blocking I/O; run via `asyncio.to_thread` from the dream runner.
- The function returns a stats dict so the dream report can log what was cleaned up.
