---
name: vault-is-runtime-data
description: The vault is runtime data (what the bot learns), not source code. Never git-track or autocommit it.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-05-phase4-dream-completion
---

# Vault Is Runtime Data

The Obsidian vault contains what the bot learns at runtime. It is not source code and must never be version-controlled alongside the codebase.

**Rules:**
- The vault directory is excluded from the repo's `.gitignore`.
- No git autocommit for vault changes — this was explicitly dropped from the roadmap.
- The user may independently choose to git-track their vault, but that is their decision and outside Hippo's scope.
- Test fixtures create temporary vaults via `tmp_path` (pytest) with synthetic content — never copy from a real vault.
