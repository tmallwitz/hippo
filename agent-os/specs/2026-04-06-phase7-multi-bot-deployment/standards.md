# Standards for Phase 7: Multi-Bot Deployment

The following standards apply to this work.

---

## coding-style

- Consistent Naming Conventions: snake_case for Python, PascalCase for classes
- Type Hints for all function signatures and class attributes
- Small, Focused Functions: `_parse_args()`, `_add_file_handler()` etc.
- DRY Principle: bot name regex defined once in `config.py`, re-used in `__main__.py`
- Async/Await: all I/O-bound operations remain async

---

## conventions

- Package Manager: `uv` only (never pip)
- Project Config: `pyproject.toml`, src-layout under `hippo/`
- UV Lock File: commit `uv.lock` for reproducible builds
- Version Control: feature branch, Conventional Commits, squash-merge to main

---

## error-handling

- Fail Fast and Explicitly: `get_config()` raises `ValueError` immediately for invalid
  bot name; `__main__.py` calls `parser.error()` for bad names
- User-Friendly Messages: error messages name the invalid value and explain the rule
- No silent fallbacks: a missing required config raises `ValidationError` loudly

---

## tech-stack

- Language: Python 3.12+, `uv` package manager
- Config: `pydantic-settings` v2 — `settings_customise_sources` for prefix layering
- Deployment (updated): Windows 11 Pro, PowerShell scripts, optional Task Scheduler
- Logs: `logging.handlers.TimedRotatingFileHandler` to `logs/{BotName}.log`

---

## validation

- Pydantic Validation: `HippoConfig` validates vault path, parses comma-separated IDs
- Allowlist for bot names: regex `^[A-Za-z][A-Za-z0-9_]*$` prevents injection via
  env var prefix construction
- Fail Early: bot name validated before config loading begins
