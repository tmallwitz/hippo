# Hippo

> Experimental Claude agent with multi-layered memory. Obsidian vault as
> brain, Telegram as mouth, and a nightly dream cycle that consolidates
> short-term impressions into long-term knowledge and self-written skills.

**Status:** Phase 7 (Multi-Bot Deployment) complete. All planned phases done.

## What it is

Hippo is a personal Claude agent built on the [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python).
Unlike typical chat agents, Hippo treats memory as a first-class concern with
distinct layers that mirror how biological memory works:

- **Short-term memory** — an append-only buffer for impressions during conversation
- **Semantic memory** — a knowledge graph stored as Markdown in an Obsidian vault
- **Episodic memory** — daily journal entries of things that happened
- **Procedural memory** — handled as Claude Agent Skills (`SKILL.md`)

A nightly **dream cycle** runs as a sub-agent, consolidating the short-term
buffer into the appropriate long-term layers, and can even write new skills
autonomously when it detects recurring patterns.

One installation can run **multiple independent bots** simultaneously — each
with its own vault, Telegram token, and dream cycle.

The name comes from the **hippocampus**, the brain region that performs
memory consolidation during sleep in mammals.

## What it isn't

- Production-ready. This is an experimentation platform.
- A general-purpose framework. It's built for a specific setup
  (one user per bot, local deployment, Claude Pro OAuth).

## Getting started

### Prerequisites

- Windows 11 Pro (recommended) or Linux
- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) package manager
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- Claude Code CLI authenticated (`claude login`)
- An Obsidian vault directory (or any empty directory)

### Quick setup (Windows)

Run the interactive deployment wizard for a guided setup:

```powershell
.\scripts\deploy.ps1
```

The wizard checks prerequisites, installs dependencies, configures your bots,
scaffolds vault directories, runs a smoke test, and optionally registers
auto-start Task Scheduler tasks — all in one go.

### Manual setup

```bash
git clone https://github.com/tmallwitz/hippo.git
cd hippo
cp .env.example .env
# Edit .env with your bot config (see .env.example for the format)
uv sync
```

### Run

Each bot runs as an independent process. Pass the bot name as the first argument:

```bash
uv run hippo Alice
```

To run multiple bots simultaneously, open separate terminals:

```bash
# Terminal 1
uv run hippo Alice

# Terminal 2
uv run hippo Bob
```

Or start all bots at once with the launcher script:

```powershell
.\scripts\start-bots.ps1
```

### Multi-bot configuration

Per-bot config in `.env` uses the bot name as a prefix (uppercased):

```ini
# Shared settings (apply to all bots)
HIPPO_MODEL=claude-sonnet-4-5
HIPPO_TIMEZONE=Europe/Berlin

# Bot: Alice
ALICE_TELEGRAM_BOT_TOKEN=<token from @BotFather>
ALICE_ALLOWED_TELEGRAM_IDS=123456
ALICE_HIPPO_VAULT_PATH=C:/Users/you/vaults/alice

# Bot: Bob
BOB_TELEGRAM_BOT_TOKEN=<different token>
BOB_ALLOWED_TELEGRAM_IDS=123456
BOB_HIPPO_VAULT_PATH=C:/Users/you/vaults/bob
```

Per-bot overrides (e.g. `ALICE_HIPPO_MODEL`) take precedence over shared defaults.

**Backward compatibility:** unprefixed single-bot vars (`TELEGRAM_BOT_TOKEN`,
`HIPPO_VAULT_PATH`, etc.) still work as the fallback layer.

### Auto-start on login

```powershell
.\scripts\install-tasks.ps1
```

Creates a Windows Task Scheduler task for each bot in `bots.yaml`.

### Test

```bash
uv run pytest
uv run ruff check
uv run mypy hippo/
```

## Architecture

See [PLAN.md](./PLAN.md) for the original design document.
Day-to-day development uses [Agent OS](https://buildermethods.com/agent-os)
for spec-driven workflow and standards management; specs and standards live
under `agent-os/`.

## Inspired by

- [`obsidian-memory-mcp`](https://github.com/YuNaga224/obsidian-memory-mcp)
  by YuNaga224 — the original idea of storing AI memories as Obsidian-linkable
  Markdown. Hippo ports this concept to Python and extends it with the
  short-term buffer and dream-cycle model.
- Anthropic's [memory server](https://github.com/modelcontextprotocol/servers/tree/main/src/memory)
  for the underlying knowledge-graph primitives.

## License

MIT. See [LICENSE](./LICENSE).
