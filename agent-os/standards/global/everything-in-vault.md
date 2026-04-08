---
name: everything-in-vault
description: All bot-generated files (skills, personality, index, reports) live under HIPPO_VAULT_PATH; agents use cwd=vault_path for relative paths.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-05-phase4-dream-completion
---

# Everything in the Vault

All files the bot generates at runtime live under `HIPPO_VAULT_PATH`. No generated content goes into the repository.

**What lives in the vault:**
- `semantic/` — knowledge graph entities
- `episodic/` — daily journal notes
- `short_term/` — buffer and processed archives
- `dream_reports/` — consolidation reports
- `raw/` and `raw/processed/` — document ingest
- `personality/prompt_ext.md` — learnt personality extensions
- `.claude/skills/` — skills (both bundled and dream-created)
- `semantic/index.md` — auto-maintained entity index
- `inbox/` — inter-bot messages
- `scheduled/` — task definitions

**Rules:**
- Both the main agent and dream sub-agent run with `cwd=vault_path`, so relative paths like `.claude/skills/` resolve inside the vault.
- Never write generated files to the repo directory.
- The vault directory structure is created on startup by `hippo/setup.py`.
