---
name: convention-file-registry
description: Use convention files (bots.yaml, etc.) in the project root for registries; return empty dict if missing rather than requiring configuration.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-05-phase3-buffer-dream-mailbox
---

# Convention-File Registry

Store registries (bot list, shared config) as YAML files in the project root, not as `.env` variables.

```python
def load_bot_registry(project_root: Path) -> dict[str, Path]:
    path = project_root / "bots.yaml"
    if not path.exists():
        return {}
    # parse and return
```

**Rules:**
- Convention files are optional: if missing, return an empty/default value — never raise.
- Human-readable format (YAML or Markdown), not JSON.
- No `.env` configuration needed for the file's location — it's always at the project root by convention.
- Document the expected structure in comments within the file itself.
