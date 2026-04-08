---
name: embedding-failures-never-block
description: Embedding operations must never block core memory operations; always degrade gracefully to substring fallback.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-06-phase6-memory-intelligence
---

# Embedding Failures Never Block

All embedding operations (encode, search, rebuild) are optional enhancements. If they fail — model not installed, corrupt embeddings file, out of memory — core memory operations must continue with substring fallback.

```python
async def search_nodes(self, query: str) -> KnowledgeGraph:
    if self._embedding_model:
        try:
            results = await self._embedding_search(query)
            if results:
                return results
        except Exception:
            log.warning("Embedding search failed, falling back to substring", exc_info=True)
    return await self._substring_search(query)
```

**Rules:**
- Wrap every embedding call in try/except at the call site.
- Log at WARNING, not ERROR — the fallback is working as designed.
- If `HIPPO_EMBEDDING_MODEL` is empty, skip all embedding code paths entirely (not even a try/except).
- The user should never see an error caused by embeddings; they should see slightly worse search results.
