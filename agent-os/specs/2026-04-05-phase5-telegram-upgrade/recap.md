# Recap: Phase 5 — Telegram Upgrade

**Completed:** 2026-04-08
**Base commit:** 68e84ebaa7932d4341e999c1e387c985bca8a990
**Final commit:** f5b5b0a9c603a59743d61fb9acbe5864d51b3c25
**Milestone:** m1-foundation

## What this spec delivered

The Telegram bridge now handles voice messages (transcribed locally via Whisper), images (described via Claude vision), and politely rejects unsupported media types. Four new commands (`/help`, `/status`, `/tasks`, `/memory N`) give the user instant access to bot state without querying the agent. The store plumbing was extended so that all five memory stores are accessible from the Telegram handlers.

## Key decisions

- **Local Whisper transcription** — uses `openai-whisper` (not the API) to avoid an API key requirement; model size configurable via `HIPPO_WHISPER_MODEL`.
- **Commands bypass the agent** — `/status`, `/tasks`, `/memory` read directly from stores for instant response with no rate-limit cost.
- **Image description only, no storage** — Claude receives the image via base64 and responds; the description is buffered but the image file is not saved to the vault.
- **Lazy-loaded Whisper singleton** — the model is loaded on first voice message, not at startup, to avoid slowing down boot time.

## Surprises and lessons

- Windows temp file handling required a workaround: `NamedTemporaryFile` holds an exclusive lock on Windows, preventing ffmpeg from reading the file. The fix uses `mktemp` + manual cleanup.
- The store return tuple grew from 3 to 5 items (server.py) and the agent return tuple from 4 to 6 — a sign that a structured return type (e.g., a `Stores` dataclass) might be worth introducing.

## Carry-over candidates

- Replace growing store tuples with a `Stores` dataclass for cleaner plumbing
- Video message support (currently rejected)
- Whisper model auto-download on first run (currently requires manual install or ffmpeg)

## Files touched

 .env.example                                       |  10 +
 agent-os/product/roadmap.md                        |   2 +-
 agent-os/specs/2026-04-05-phase5.../plan.md        |  53 ++
 agent-os/specs/2026-04-05-phase5.../references.md  |  29 +
 agent-os/specs/2026-04-05-phase5.../shape.md       |  29 +
 agent-os/specs/2026-04-05-phase5.../standards.md   |  21 +
 hippo/__main__.py                                  |  15 +-
 hippo/agent.py                                     |  30 +-
 hippo/config.py                                    |   2 +
 hippo/memory/server.py                             |   4 +-
 hippo/telegram_bridge.py                           | 300 +++++++-
 hippo/voice.py                                     |  51 ++
 pyproject.toml                                     |   3 +-
 uv.lock                                            | 793 +++++++++++++
 14 files changed, 1314 insertions(+), 28 deletions(-)
