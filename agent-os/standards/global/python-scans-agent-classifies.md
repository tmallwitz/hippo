---
name: python-scans-agent-classifies
description: Orchestrator code reads files and passes content to the LLM agent; the agent classifies, not scans.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-05-phase4-dream-completion
---

# Python Scans, Agent Classifies

When the dream cycle (or any batch process) needs to process files, the Python orchestrator reads and formats the file contents, then passes them to the LLM agent in the query. The agent decides what to do with the content — it does not scan the filesystem itself.

```python
# runner.py
docs = _scan_raw_documents(vault_path)  # Python reads files
formatted = _format_raw_documents(docs)  # Python formats for query
query = _build_query(buffer_entries, inbox_messages, raw_documents=formatted)
# Agent receives formatted content and classifies each item
```

**Why:** LLM filesystem scanning is unreliable (wrong paths, missed files, permission issues). Python file I/O is deterministic and testable.

**Rules:**
- The orchestrator handles all file I/O (read, move, archive).
- The agent receives pre-formatted content and decides how to classify/store it.
- The agent may write new files (skills, entities) via its MCP tools, but never reads raw input files directly.
