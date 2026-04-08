---
name: no-media-storage
description: Non-text media (images, voice) is described/transcribed for the agent but never saved as binary files in the vault.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-05-phase5-telegram-upgrade
---

# No Media Storage in the Vault

The vault stores only Markdown text. Binary media files (images, audio, video) are never saved to the vault.

**How media is handled:**
- **Voice messages:** Transcribed to text via Whisper. The transcript (not the audio) is buffered and sent to the agent.
- **Images:** Described by Claude vision via base64. The description (not the image) is buffered and sent to the agent.
- **Other media:** Politely rejected with a message explaining the limitation.

**Why:** The vault is designed for Obsidian readability (see `markdown-over-binary` standard). Binary files would break graph view, search, and manual editing workflows.
