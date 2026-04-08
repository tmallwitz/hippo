---
name: two-threshold-search
description: Use a permissive threshold (0.4) for search/recall and a conservative threshold (0.7) for entity deduplication to avoid false merges.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-06-phase6-memory-intelligence
---

# Two-Threshold Search Strategy

Different operations need different confidence levels for embedding similarity:

| Operation | Threshold | Why |
|-----------|-----------|-----|
| `search_nodes` | 0.4 | Permissive — better to surface a loosely related entity than miss one |
| `find_similar_entities` | 0.7 | Conservative — merging entities is destructive and hard to undo |

**Rules:**
- Search thresholds are configurable via `HIPPO_SEARCH_THRESHOLD` (default 0.4).
- Dedup threshold is hardcoded at 0.7 — this should not be user-configurable without careful thought, since lowering it risks false merges.
- When in doubt, return more results at search time and fewer matches at dedup time.
