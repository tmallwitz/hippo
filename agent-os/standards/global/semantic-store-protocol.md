---
name: semantic-store-protocol
description: All memory backends implement the SemanticStore Protocol so tools remain backend-agnostic.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-05-phase1-semantic-memory-telegram
---

# SemanticStore Protocol

Define memory backends as implementations of a `typing.Protocol`, not as concrete base classes.

```python
class SemanticStore(Protocol):
    async def create_entities(self, entities: list[Entity]) -> list[Entity]: ...
    async def search_nodes(self, query: str) -> KnowledgeGraph: ...
    async def read_graph(self) -> KnowledgeGraph: ...
    # ... all 9 tool operations
```

**Rules:**
- MCP tool functions call the protocol interface, never the concrete `ObsidianSemanticStore` directly.
- New backends (e.g., SQLite, vector DB) implement the same protocol and can be swapped without changing tool code.
- The protocol lives in `hippo/memory/store.py`; implementations live in their own modules.
