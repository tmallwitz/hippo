---
name: warn-dont-block-refs
description: Unresolved references (e.g., relation targets) log a warning but do not raise; prefer loose coupling over strict enforcement.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-05-phase1-semantic-memory-telegram
---

# Warn, Don't Block for Unresolved References

When creating a relation to an entity that doesn't exist yet, log a warning but allow the operation to succeed.

```python
if not target_path.exists():
    log.warning("Relation target %r does not exist (yet)", relation.to_entity)
    # proceed anyway — target may be created later
```

**Why:** The knowledge graph is built incrementally during conversation. Strict validation would force the agent to create entities in dependency order, which is fragile and unnatural.

**Rules:**
- Log at WARNING level so it's visible but not fatal.
- Never raise on missing relation targets during `create_relations`.
- The same principle applies to other cross-references in the vault (e.g., skill references, inbox messages).
