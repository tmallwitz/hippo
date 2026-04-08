---
name: vault-storage-layout
description: Vault storage uses category subfolders (semantic/<EntityType>/, episodic/, etc.) for Obsidian navigability.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-05-phase1-semantic-memory-telegram
---

# Vault Storage Layout

Store memory files in category subfolders within the vault, not in a flat directory.

```
vault/
  semantic/
    person/
      Alice.md
    topic/
      The_Dispossessed.md
  episodic/
    2026-04-05.md
  short_term/
    buffer.jsonl
```

**Rules:**
- Each entity type gets its own subfolder under `semantic/`. Created on demand by `_entity_dir()`.
- Other memory layers (`episodic/`, `short_term/`, `scheduled/`, etc.) each have a top-level subfolder.
- Subfolder names are lowercase. Entity type names from the knowledge graph map directly to folder names.
- This layout makes Obsidian's folder tree and graph view useful without configuration.
