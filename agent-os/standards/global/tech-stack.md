# Tech Stack

## Agent Framework

- **Agent SDK:** Claude Agent SDK (Python) — core agent runtime
- **MCP Server:** In-process SDK MCP server via `@tool` decorator and
  `create_sdk_mcp_server` (no external MCP processes)
- **Model Backend:** Claude Pro OAuth via `claude setup-token`. No API key.
  Pro subscription rate limits apply.

## Frontend

- **Chat Interface:** Telegram via `aiogram` v3 (fully async)
- **No web UI, no CLI chat** — Telegram is the sole user-facing channel
- **User Auth:** Telegram ID whitelist in `.env`

## Storage

All state lives in the filesystem as human-readable Markdown or JSONL.
There is no traditional database.

- **Memory Backend:** Obsidian vault, one per bot
- **Semantic Memory:** Markdown files in `semantic/` with YAML frontmatter,
  relations as `[[Typed::Target]]`
- **Episodic Memory:** Daily notes in `episodic/YYYY-MM-DD.md`
- **Short-Term Buffer:** Append-only JSONL at `short_term/buffer.jsonl`
- **Skills:** Claude Agent Skills under `.claude/skills/` inside the vault
- **Inter-Bot Mailbox:** Markdown files in each bot's `inbox/` folder

## Language & Tooling

- **Language:** Python 3.12+
- **Package Manager:** `uv` (never `pip`)
- **Project Config:** `pyproject.toml`, single-package repository
- **Linter:** `ruff check`
- **Formatter:** `ruff format`
- **Type Checker:** `mypy` (strict mode where practical)
- **Test Framework:** `pytest` with `pytest-asyncio`
- **Coverage:** `pytest-cov`

## Key Dependencies

- `claude-agent-sdk` — agent runtime and tool system
- `aiogram` >= 3.0 — async Telegram bot framework
- `python-frontmatter` >= 1.0 — YAML frontmatter for Markdown files
- `pydantic-settings` >= 2.0 — typed configuration from `.env`
- `python-dotenv` >= 1.0 — `.env` loading in development

Every new dependency needs justification. Prefer the standard library
when reasonable.

## Development Workflow

- **Spec-Driven Development:** [Agent OS](https://buildermethods.com/agent-os)
  for shaping specs and managing coding standards. Specs live under
  `agent-os/specs/`, standards under `agent-os/standards/`, product docs
  under `agent-os/product/`.
- **Version Control:** Git, public GitHub repository
- **Branching:** Feature branches with Conventional Commits
  (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`, `spec:`)
- **Merge Strategy:** Squash-merge to keep `main` linear
- **CI:** GitHub Actions (to be added in Phase 1)

## Deployment

- **Host:** Windows 11 Pro, self-hosted
- **Run:** `uv run hippo <BotName>` — one process per bot, independent
- **Multi-Bot:** Per-bot env vars with name prefix (e.g. `ALICE_TELEGRAM_BOT_TOKEN`);
  shared defaults via unprefixed `HIPPO_*` vars; bot names listed in `bots.yaml`
- **Process Management:** `scripts/start-bots.ps1` reads `bots.yaml` and starts
  all bots; `scripts/install-tasks.ps1` registers Windows Task Scheduler auto-start
- **Deployment Wizard:** `scripts/deploy.ps1` — idempotent 9-step interactive setup
- **Dream Trigger:** manual `/dream` command via Telegram, or automatic when buffer
  fills (no systemd — scheduler loop runs inside the bot process)
- **Secrets:** `.env` file, never committed
- **Logs:** `logs/<BotName>.log` with daily rotation via `TimedRotatingFileHandler`