# Recap: Phase 7 — Multi-Bot Deployment

**Completed:** 2026-04-08
**Base commit:** 629b89d8dc7dde62ddf64684d1ce3574ee584127
**Final commit:** 41e2ef573b98af4f80d11222ab94f3e6c2cda1fa
**Milestone:** m1-foundation

## What this spec delivered

Hippo can now host multiple named bots simultaneously as independent OS processes (`uv run hippo Alice`, `uv run hippo Bob`). Each bot resolves its own config via pydantic-settings with a two-layer prefixed env var strategy, writes to its own log file with daily rotation, and has a fully isolated vault and scheduler. Three PowerShell scripts (`start-bots.ps1`, `install-tasks.ps1`, `deploy.ps1`) make the setup reproducible on a fresh Windows 11 Pro machine.

## Key decisions

- **Separate processes, not threads** — each `uv run hippo <BotName>` is an independent OS process; module-level globals stay naturally isolated with zero refactoring of the runtime modules.
- **pydantic-settings two-layer resolution** — `settings_customise_sources()` with `{BOT_NAME}_` prefix first, then unprefixed fallback; type-safe, zero manual parsing, no breaking change to `.env` for single-bot users.
- **`TimedRotatingFileHandler` in Python** — daily log rotation per bot handled in Python, not PowerShell; `start-bots.ps1` only captures process-level startup errors.
- **`project_root` fix for `send_message`** — agent ran with `cwd=vault_path`, so `Path.cwd()` returned the vault; fixed by passing `Path(__file__).parent.parent` from `agent.py`.

## Surprises and lessons

- The spec was shaped retrospectively (folder created 20 minutes after the implementation commit), so there were no surprises during implementation — the plan is a faithful record of what was built.
- Breaking CLI change (`uv run hippo` → `uv run hippo <BotName>`) was smoothed by the env var fallback layer: single-bot users need only update the command, not their `.env`.

## Carry-over candidates

- Linux/systemd deployment path (explicitly out of scope for Windows-only target; could become M2 if Linux support is desired)
- Health-check endpoint per bot (useful for `start-bots.ps1` smoke test but not implemented)

## Files touched

 .env.example                                       |  72 +++--
 README.md                                          |  87 ++++-
 agent-os/product/roadmap.md                        |   2 +-
 agent-os/specs/2026-04-06-phase7.../plan.md        |  99 ++++++
 agent-os/specs/2026-04-06-phase7.../references.md  |  58 ++++
 agent-os/specs/2026-04-06-phase7.../shape.md       |  59 ++++
 agent-os/specs/2026-04-06-phase7.../standards.md   |  49 +++
 agent-os/standards/global/tech-stack.md            |  15 +-
 hippo/__main__.py                                  |  50 ++-
 hippo/agent.py                                     |   1 +
 hippo/config.py                                    |  66 +++-
 hippo/memory/server.py                             |   8 +-
 scripts/deploy.ps1                                 | 351 +++++++++++++++++++++
 scripts/install-tasks.ps1                          | 100 ++++++
 scripts/start-bots.ps1                             |  81 +++++
 tests/test_config.py                               |  95 +++++-
 tests/test_main.py                                 |  54 ++++
 17 files changed, 1192 insertions(+), 55 deletions(-)
