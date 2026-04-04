# Contributing

Hippo is currently an experimental personal project, but contributions and
discussion are welcome.

## Before you open a PR

- Read [PLAN.md](./PLAN.md) to understand the current phase and scope.
  The architecture is deliberately phase-gated to avoid premature complexity.
- Open an issue first for any non-trivial change.
- Keep PRs focused. One concern per PR.
- Do not add features from a later phase into an earlier phase.
  Phase boundaries are there for a reason.

## Development setup

Requires:

- Python 3.12+
- [`uv`](https://github.com/astral-sh/uv) for package management
- An Obsidian vault (created empty is fine, Hippo will populate it)
- A Telegram bot token (from [@BotFather](https://t.me/BotFather))
- Claude Pro subscription with `claude setup-token` completed

Detailed setup instructions will follow once Phase 1 implementation lands.
Until then, see [PLAN.md](./PLAN.md) for the intended structure.

## Code style

- `ruff` for linting and formatting
- Type hints everywhere, checked with `mypy`
- Tests for memory operations are mandatory, for glue code optional

## Privacy

Hippo stores personal information in Obsidian vaults. Vault content must
**never** be committed to the repository. The `.gitignore` excludes common
vault directory patterns, but double-check before pushing.

If you contribute test fixtures, use only synthetic data.

## Code of conduct

Be kind. No other rules yet.
