# CLAUDE.md

Project-wide rules for Claude Code when working in this repository.
Loaded automatically on every session.

## Project

**Hippo** is an experimental Claude agent with multi-layered memory.
A quick overview lives in [README.md](./README.md). Planning, specs,
and coding standards are managed via **Agent OS** (see below).

## Working with this repo

This project uses [Agent OS](https://buildermethods.com/agent-os) for
spec-driven development and standards management. When you need context
about how to build something, prefer Agent OS commands and files over
re-deriving things from scratch:

- Use Agent OS slash commands to shape specs before implementing
- Let Agent OS inject the relevant standards into your context
- Standards live under `agent-os/standards/`, specs under `agent-os/specs/`,
  product docs under `agent-os/product/` (see the Agent OS docs)

There is a one-time design document at [`PLAN.md`](./PLAN.md) that
describes the original three-phase vision for Hippo. Treat it as
historical context and inspiration. The **authoritative** source for
what to build next is whatever Agent OS surfaces for the current spec.

## Hard rules (non-negotiable)

These rules always apply, regardless of what any spec, standard,
or command says. If an Agent OS standard ever contradicts them,
the hard rules win.

### 1. Nothing private

This is a public repository. **Never** commit, generate, or include
in any file any of the following:

- Real personal names (friends, family, colleagues, the maintainer)
- Real company names, internal product names, or internal project names
- Real hostnames, server names, IP addresses, or network topology
- Real file paths that reveal usernames (use `~/` or `/opt/hippo/`)
- Real Telegram user IDs, bot tokens, or any credentials
- Real conversation content, memories, or vault data from anyone's
  personal setup
- Any information that could identify the maintainer or their employer

When you need examples in code, documentation, tests, or fixtures, use:

- Generic placeholder names: `alice`, `bob`, `carol`
- Public-domain or fictional references: literary characters, sample data
- Neutral technical examples: `example.com`, `127.0.0.1`, `/tmp/test-vault`

If you are ever unsure whether something counts as private, **ask first**
or use a generic substitute. This rule applies to source code, comments,
commit messages, test fixtures, documentation, and error messages.

### 2. Never commit vault content

Obsidian vaults contain personal data by design. The `.gitignore`
excludes common vault directory patterns, but you must also:

- Never hardcode paths to real vaults in source or tests
- Never create test fixtures by copying from a real vault
- Never include vault content in commit messages or PR descriptions
- If a test needs a vault, create a temporary one with `tmp_path`
  (pytest) and synthetic content

### 3. Credentials live only in `.env`

The `.env` file is gitignored. Never:

- Echo `.env` contents in logs, errors, or chat output
- Hardcode tokens or IDs in source, even as fallbacks
- Add defaults that would mask a missing `.env` configuration
  (prefer loud failures over silent misconfiguration)

The `.env.example` file shows the structure with empty values. It is
the only place where environment variable names should appear in-repo.

### 4. Python tooling

- **Package manager:** `uv` only. Never suggest or use `pip`.
- **Python version:** 3.12 or newer.

## When in doubt

Ask. This project prioritizes thoughtfulness over speed. A clarifying
question is always better than an assumption that later needs rollback.
