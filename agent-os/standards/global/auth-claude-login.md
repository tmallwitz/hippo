---
name: auth-claude-login
description: Authenticate with Claude via `claude login` on the server, not via API keys in .env.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-05-phase1-semantic-memory-telegram
---

# Auth via `claude login`

The Claude Agent SDK spawns the Claude Code CLI as a subprocess. Authentication comes from having run `claude login` on the server ahead of time.

**Rules:**
- No `ANTHROPIC_API_KEY` or similar credential in `.env`.
- Deployment requires an interactive `claude login` step (handled by `scripts/deploy.ps1` step 4).
- If auth is missing at startup, the SDK will fail with a clear error — do not add fallback logic or default keys.
