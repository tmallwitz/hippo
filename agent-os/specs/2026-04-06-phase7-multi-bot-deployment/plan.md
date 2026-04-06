# Phase 7: Multi-Bot Deployment — Plan

## Context

All six prior Hippo phases are complete. Phase 7 makes one Hippo installation host
multiple named bots simultaneously and provides a guided deployment wizard for
Windows 11 Pro.

**Key insight:** each bot runs as a separate OS process (`uv run hippo Alice` in
one terminal, `uv run hippo Bob` in another). Module-level globals in `server.py`,
`runner.py` etc. are naturally isolated. Work centres on CLI arg parsing, config
layering, PowerShell scripts, and the deployment wizard.

---

## Task 1: Save spec documentation ✓

`agent-os/specs/2026-04-06-phase7-multi-bot-deployment/` — this folder.

---

## Task 2: Extend `HippoConfig` with bot-name-prefixed env var resolution ✓

**File:** `hippo/config.py`

- Removed `@functools.lru_cache` singleton; `get_config()` now takes `bot_name: str`.
- `get_config()` creates a `_BotConfig` subclass that overrides
  `settings_customise_sources` with two `EnvSettingsSource` layers:
  1. `{BOT_NAME}_` prefix (e.g. `ALICE_TELEGRAM_BOT_TOKEN`) — per-bot
  2. No prefix (e.g. `TELEGRAM_BOT_TOKEN`) — shared fallback
- Same layering for `DotEnvSettingsSource` against `.env`.
- `hippo_bot_name` is set from the CLI arg via init kwargs (highest priority).
- Bot name validated against `[A-Za-z][A-Za-z0-9_]*`.

---

## Task 3: Add CLI argument parsing to `__main__.py` ✓

**File:** `hippo/__main__.py`

- `argparse` with one positional argument `bot_name`.
- Bot name validated against the same regex.
- `_add_file_handler()` adds `TimedRotatingFileHandler` to `logs/{bot_name}.log`
  (daily rotation, 30-day retention) alongside the stream handler.
- `_async_main(bot_name)` passes the name to `get_config(bot_name)`.

---

## Task 4: Fix `load_bot_registry` path in `server.py` ✓

**File:** `hippo/memory/server.py`, `hippo/agent.py`

- Added `_project_root: Path | None` module global to `server.py`.
- `create_memory_server()` accepts `project_root: Path | None = None` and sets it.
- `send_message` tool uses `_project_root or Path.cwd()`.
- `agent.py` passes `project_root=Path(__file__).parent.parent` (the repo root).

---

## Task 5: Update `.env.example` ✓

**File:** `.env.example`

- Restructured with shared `HIPPO_*` defaults section and per-bot `ALICE_*` section.
- Migration note for single-bot users.
- Bob section commented out as template.

---

## Task 6: PowerShell scripts ✓

**Files:** `scripts/start-bots.ps1`, `scripts/install-tasks.ps1`, `scripts/deploy.ps1`

See shape.md for design details.

---

## Task 7: Tests ✓

**Files:** `tests/test_config.py` (extended), `tests/test_main.py` (new)

Multi-bot config tests with `monkeypatch.setenv`; CLI arg validation tests.

---

## Task 8: Documentation ✓

**Files:** `README.md`, `agent-os/product/roadmap.md`, `agent-os/standards/global/tech-stack.md`

---

## Verification

1. `uv run pytest tests/test_config.py tests/test_main.py -v`
2. `uv run ruff check hippo/ && uv run mypy hippo/`
3. Manual two-bot test: `uv run hippo Alice` + `uv run hippo Bob` in separate terminals
4. Check `logs/Alice.log` and `logs/Bob.log` exist
5. Run `scripts/start-bots.ps1`
6. Run `scripts/deploy.ps1` step-by-step
