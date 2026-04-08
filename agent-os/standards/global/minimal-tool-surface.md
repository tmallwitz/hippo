---
name: minimal-tool-surface
description: Memory tools expose only create+read operations; editing and deleting happens manually in Obsidian.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-05-phase2-episodic-memory
---

# Minimal Tool Surface

Expose only the operations the agent needs during conversation. Editing and deleting memory content is a human activity done in Obsidian.

**Rules:**
- Episodic memory: `log_episode` (create) and `recall_episodes` (read) only. No update/delete tools.
- Short-term buffer: `remember` (append) only. No edit/remove tools.
- Semantic memory has delete tools because the agent needs them for deduplication during the dream cycle, but casual conversation should prefer `add_observations` over delete-and-recreate.
- Manual edits in Obsidian are picked up on next read — this is a feature, not a bug.
