# Standards for Phase 4: Dream Completion

The following standards apply to this work.

---

## coding-style

Python naming, formatting, type hints, and DRY principles.

- Consistent naming conventions for variables, functions, classes, and files
- Automated formatting via `ruff format`
- Meaningful, intent-revealing names; avoid abbreviations
- Small, focused functions (single task)
- Type hints on all function signatures
- Prefer async functions for I/O-bound operations
- DRY: extract common logic into reusable functions

---

## conventions

Project structure, dependency management, git workflow, and UV/uv.lock.

- Environment variables for configuration; never commit secrets
- No new dependencies unless justified; prefer the standard library
- Commit `uv.lock` for reproducible builds
- Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`, `spec:`)
- Squash-merge to keep `main` linear

---

## error-handling

Exception types, structured logging, graceful degradation.

- User-friendly error messages without exposing technical details
- Fail fast and explicitly; validate preconditions early
- Use specific exception types (e.g., `FileNotFoundError`) for targeted handling
- Clean up resources in `finally` blocks
- Graceful degradation for non-critical failures (e.g., raw file read errors)
- Log exceptions with context via `logging` (this project uses stdlib logging, not structlog)

---

## tech-stack

Full Hippo stack — Claude Agent SDK, aiogram, filesystem storage, uv tooling.

- Agent SDK: `ClaudeSDKClient` + `create_sdk_mcp_server` + `@tool` decorator
- Storage: Obsidian vault, Markdown files with YAML frontmatter
- All bot-produced files live in the vault (`HIPPO_VAULT_PATH`); nothing generated outside
- Language: Python 3.12+; package manager: `uv` only (never `pip`)
- Tests: `pytest` with `pytest-asyncio`; run with `uv run pytest`
