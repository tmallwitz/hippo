# Phase 7: Multi-Bot Deployment — Shaping Notes

## Scope

Make one Hippo installation host multiple named bots simultaneously, and provide a
guided deployment wizard for Windows 11 Pro so the whole setup can be reproduced on
a new machine without manual steps.

Three sub-deliverables:
1. Multi-Bot Runtime (CLI arg, per-bot env vars, independent processes)
2. Windows Process Management (start-bots.ps1, install-tasks.ps1)
3. Deployment Wizard (deploy.ps1, 9-step interactive wizard)

## Decisions

- **Separate processes, not threads.** Each `uv run hippo Alice` is a fully independent
  OS process. Module-level globals in `server.py`, `runner.py` etc. are naturally
  isolated — no refactoring of those modules needed.

- **pydantic-settings two-layer env resolution.** `settings_customise_sources()` with
  `EnvSettingsSource(prefix=ALICE_)` then `EnvSettingsSource(prefix="")`. Automatic,
  type-safe, zero manual parsing. Per-bot override wins; shared default is fallback.

- **Field-name-based env vars.** User chose `ALICE_TELEGRAM_BOT_TOKEN` (matches field
  name) over `ALICE_TELEGRAM_TOKEN` (shorter but requires custom alias). Simpler code.

- **Windows-only deployment target.** User confirmed Windows 11 Pro; Linux/systemd
  path not maintained. Tech-stack standard updated to reflect this.

- **`argparse` for CLI.** Single positional `bot_name` argument. Gives `--help` for
  free. Bot name validated against `[A-Za-z][A-Za-z0-9_]*` (safe as env var prefix).

- **`TimedRotatingFileHandler` in Python.** Daily log rotation per bot handled in
  Python (`logs/{bot_name}.log`), not by PowerShell redirect. PowerShell `start-bots.ps1`
  uses separate `-error.log` for process-level startup errors only.

- **`project_root` fix for `send_message`.** The agent runs with `cwd=vault_path`,
  so `Path.cwd()` returned the vault, not the repo root where `bots.yaml` lives.
  Fixed by passing `Path(__file__).parent.parent` from `agent.py`.

- **Breaking change acknowledged.** CLI now requires a bot name argument. Single-bot
  users must update from `uv run hippo` to `uv run hippo alice`. Their unprefixed
  `.env` vars still work as the fallback layer — zero `.env` changes required.

## Context

- **Visuals:** None
- **References:** `hippo/config.py` (HippoConfig, get_config), `hippo/__main__.py`
  (entry point), `hippo/memory/server.py` (Path.cwd() bug), `bots.yaml` (registry)
- **Product alignment:** Final planned phase. Completes the multi-bot vision from the
  original PLAN.md. Windows 11 Pro is the maintainer's actual deployment environment.

## Standards Applied

- `coding-style` — Type hints throughout, small focused functions, no dead code
- `conventions` — uv, pyproject.toml, Conventional Commits, feature branch
- `error-handling` — Fail fast with clear messages for bad bot name / missing config
- `tech-stack` — Updated deployment section to Windows 11 Pro + PowerShell
- `validation` — Pydantic validation, regex allowlist for bot names
