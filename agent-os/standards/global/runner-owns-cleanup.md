---
name: runner-owns-cleanup
description: Orchestrator code (not the LLM sub-agent) owns side-effect cleanup like buffer archival and inbox clearing, using finally blocks.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-05-phase3-buffer-dream-mailbox
---

# Runner Owns Cleanup

Side-effect cleanup (archiving buffers, clearing inboxes, writing reports) must happen in the orchestrator's `finally` block, not as LLM tool calls.

```python
async def run_dream(config, buffer_store, mailbox_store):
    try:
        # ... run the LLM sub-agent
    finally:
        await buffer_store.archive_buffer(today)
        await mailbox_store.clear_inbox()
        _write_dream_report(report_path, report)
```

**Why:** The LLM may fail, time out, or produce unexpected output. Cleanup that depends on LLM cooperation is unreliable. The runner guarantees it happens.

**Rules:**
- Buffer archival, inbox clearing, and report writing happen in `finally`.
- The LLM sub-agent only reads the buffer/inbox and writes to long-term memory.
- If the LLM fails, the runner still archives (preventing infinite re-processing of the same entries).
