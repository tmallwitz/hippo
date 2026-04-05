# Standards for Phase 3

The following global standards apply to this work.

---

## coding-style

- **Consistent Naming Conventions**: Establish and follow naming conventions for variables, functions, classes, and files across the codebase
- **Automated Formatting**: Maintain consistent code style (indenting, line breaks, etc.)
- **Meaningful Names**: Choose descriptive names that reveal intent; avoid abbreviations and single-letter variables except in narrow contexts
- **Small, Focused Functions**: Keep functions small and focused on a single task for better readability and testability
- **Remove Dead Code**: Delete unused code, commented-out blocks, and imports rather than leaving them as clutter
- **DRY Principle**: Avoid duplication by extracting common logic into reusable functions or modules
- **Type Hints**: Use type hints for all function signatures and class attributes
- **Pydantic Models**: Use Pydantic BaseModel for data structures and DTOs
- **Async/Await**: Prefer async functions for I/O-bound operations

---

## commenting

- **Self-Documenting Code**: Write code that explains itself through clear structure and naming
- **Minimal, helpful comments**: Add concise, minimal comments to explain large sections of code logic
- **Don't comment changes or fixes**: Comments should be evergreen informational texts relevant far into the future
- **Docstrings**: Use Google-style or NumPy-style docstrings for public functions and classes
- **Type Hints over Comments**: Prefer type hints over comments to describe parameter types

---

## conventions

- **Environment Configuration**: Use environment variables for configuration; never commit secrets or API keys
- **Dependency Management**: Keep dependencies minimal; document why major dependencies are used
- **Testing Requirements**: Unit tests required before merging
- **Project Structure**: Follow existing `hippo/` package structure
- **Dependency Groups**: Separate dev dependencies in `pyproject.toml`
- **UV Lock File**: Commit `uv.lock` for reproducible builds

---

## error-handling

- **Fail Fast and Explicitly**: Validate input and check preconditions early
- **Specific Exception Types**: Use specific exception/error types rather than generic ones
- **Graceful Degradation**: Design systems to degrade gracefully when non-critical services fail
- **Clean Up Resources**: Always clean up resources (file handles) in finally blocks

---

## tech-stack

- **Storage**: All state as Markdown or JSONL — no database
- **Short-Term Buffer**: Append-only JSONL at `short_term/buffer.jsonl`
- **Inter-Bot Mailbox**: Markdown files in each bot's `inbox/` folder
- **Dream Trigger**: `systemd` timer + manual `/dream` command via Telegram
- **Package Manager**: `uv` (never `pip`)
- **Language**: Python 3.12+
- **Linter/Formatter**: `ruff`; Type checker: `mypy` strict

---

## validation

- **Fail Early**: Validate input as early as possible
- **Pydantic Validation**: Use Pydantic models with Field constraints for input validation
- **Sanitize Input**: Sanitize user input to prevent injection attacks
