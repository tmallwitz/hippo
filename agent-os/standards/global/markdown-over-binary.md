---
name: markdown-over-binary
description: All vault data uses Markdown format for Obsidian readability, even when append-only binary/JSON formats would be more efficient.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-05-phase3-buffer-dream-mailbox
---

# Markdown Over Binary Formats

Every piece of data in the vault must be a Markdown file readable in Obsidian. Do not use JSONL, SQLite, or other binary/structured formats.

**Why:** The vault is the user's brain — they browse it in Obsidian, edit it manually, and review it in graph view. Binary or machine-only formats break this contract.

**Rules:**
- Buffer entries: Markdown with H2 sections per entry (not JSONL).
- Mailbox messages: Markdown with YAML frontmatter.
- Dream reports: Markdown with timestamped sections.
- Episodic memory: Markdown daily notes.
- Semantic memory: Markdown with YAML frontmatter.
- The only exception is generated index files (e.g., embedding vectors) that are clearly marked as derived data and can be regenerated.
