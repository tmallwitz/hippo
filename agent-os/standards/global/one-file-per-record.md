---
name: one-file-per-record
description: Each scheduled task (and similar records) is stored as one Markdown file with YAML frontmatter, not appended to a shared file.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-05-phase2b-scheduler
---

# One File Per Record

Records that have individual identities and lifecycles (scheduled tasks, inbox messages) are stored as one Markdown file each, not as sections in a shared file.

```
scheduled/
  task-a1b2c3d4.md   # one task
  task-e5f6g7h8.md   # another task
```

**Why:** Individual files are independently editable in Obsidian, deletable, and parseable without worrying about section boundaries. They also produce clean git diffs.

**When to use one-file-per-record:**
- Records with their own lifecycle (create, update, complete, delete)
- Records the user might want to edit individually in Obsidian

**When to use append-to-shared-file instead:**
- Time-ordered streams (episodic daily notes, buffer entries) where records are logically grouped by date
