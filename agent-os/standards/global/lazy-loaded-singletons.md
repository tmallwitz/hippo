---
name: lazy-loaded-singletons
description: Heavy resources (ML models, DB connections) are loaded on first use, not at startup, using a module-level singleton pattern.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-05-phase5-telegram-upgrade
---

# Lazy-Loaded Singletons

Resources that are expensive to initialize (ML models, large file indexes, external connections) must be loaded on first use, not at import or startup time.

```python
_loaded: tuple[str, Any] | None = None

def _load_model(model_name: str) -> Any:
    global _loaded
    if _loaded is None or _loaded[0] != model_name:
        _loaded = (model_name, whisper.load_model(model_name))
    return _loaded[1]
```

**Rules:**
- Store the loaded resource in a module-level variable.
- Guard with a `None` check; reload only if the config changed.
- Use `asyncio.to_thread` for blocking initialization in async contexts.
- The bot must start and respond to `/help` without waiting for the Whisper model to download.
