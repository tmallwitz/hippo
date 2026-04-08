---
name: dash-tolerant-parsing
description: Markdown parsers must handle em-dash, en-dash, and plain hyphen interchangeably in headings and separators.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-05-phase2-episodic-memory
---

# Dash-Tolerant Markdown Parsing

When parsing Markdown headings or separators that use dashes, always accept em-dash (—), en-dash (–), and plain hyphen (-).

```python
# Good: handles all three dash types
_H2_RE = re.compile(r"^##\s+(\d{2}:\d{2})\s*[—–\-]\s*(.+)$", re.MULTILINE)

# Bad: only matches plain hyphen
_H2_RE = re.compile(r"^##\s+(\d{2}:\d{2})\s*-\s*(.+)$", re.MULTILINE)
```

**Why:** Obsidian, text editors, and autocorrect features silently convert between dash types. A parser that only handles one will break on files edited in a different tool.
