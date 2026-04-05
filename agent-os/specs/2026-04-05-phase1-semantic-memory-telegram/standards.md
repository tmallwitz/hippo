# Standards for Phase 1

The following standards apply to this work.

---

## global/coding-style

- **Consistent Naming Conventions**: Establish and follow naming conventions for variables, functions, classes, and files across the codebase
- **Automated Formatting**: Maintain consistent code style (indenting, line breaks, etc.)
- **Meaningful Names**: Choose descriptive names that reveal intent; avoid abbreviations and single-letter variables except in narrow contexts
- **Small, Focused Functions**: Keep functions small and focused on a single task for better readability and testability
- **Consistent Indentation**: Use consistent indentation (spaces or tabs) and configure your editor/linter to enforce it
- **Remove Dead Code**: Delete unused code, commented-out blocks, and imports rather than leaving them as clutter
- **Backward compatibility only when required:** Unless specifically instructed otherwise, assume you do not need to write additional code logic to handle backward compatibility.
- **DRY Principle**: Avoid duplication by extracting common logic into reusable functions or modules
- **Type Hints**: Use type hints for all function signatures and class attributes
- **Pydantic Models**: Use Pydantic BaseModel for data structures and DTOs
- **Async/Await**: Prefer async functions for I/O-bound operations

---

## global/conventions

- **Consistent Project Structure**: Organize files and directories in a predictable, logical structure that team members can navigate easily
- **Clear Documentation**: Maintain up-to-date README files with setup instructions, architecture overview, and contribution guidelines
- **Version Control Best Practices**: Use clear commit messages, feature branches, and meaningful pull/merge requests with descriptions
- **Environment Configuration**: Use environment variables for configuration; never commit secrets or API keys to version control
- **Dependency Management**: Keep dependencies up-to-date and minimal; document why major dependencies are used
- **Testing Requirements**: Define what level of testing is required before merging (unit tests, integration tests, etc.)
- **Project Structure**: Flat layout (`hippo/` at project root) — overrides the src-layout default per user decision
- **Dependency Groups**: Separate dev dependencies in `pyproject.toml` (`[dependency-groups]`)
- **UV Lock File**: Commit `uv.lock` for reproducible builds

---

## global/commenting

- **Self-Documenting Code**: Write code that explains itself through clear structure and naming
- **Minimal, helpful comments**: Add concise, minimal comments to explain large sections of code logic.
- **Don't comment changes or fixes**: Do not leave code comments that speak to recent or temporary changes or fixes.
- **Docstrings**: Use Google-style or NumPy-style docstrings for public functions and classes
- **Type Hints over Comments**: Prefer type hints over comments to describe parameter types

---

## global/error-handling

- **User-Friendly Messages**: Provide clear, actionable error messages to users without exposing technical details or security information
- **Fail Fast and Explicitly**: Validate input and check preconditions early; fail with clear error messages rather than allowing invalid state
- **Specific Exception Types**: Use specific exception/error types rather than generic ones to enable targeted handling
- **Centralized Error Handling**: Handle errors at appropriate boundaries rather than scattering try-catch blocks everywhere
- **Graceful Degradation**: Design systems to degrade gracefully when non-critical services fail
- **Clean Up Resources**: Always clean up resources (file handles, connections) in finally blocks or equivalent mechanisms
- **Custom Exception Classes**: Define project-specific exception classes inheriting from `Exception`
- **Structured Error Logging**: Log exceptions with context

---

## global/tech-stack

- **Agent SDK:** Claude Agent SDK (Python)
- **MCP Server:** In-process via `@tool` + `create_sdk_mcp_server`
- **Auth:** Pre-authenticated via `claude login`
- **Frontend:** Telegram via aiogram v3
- **Storage:** Obsidian vault (Markdown + YAML frontmatter)
- **Language:** Python 3.12+, `uv` package manager
- **Linter/Formatter:** ruff
- **Type Checker:** mypy
- **Tests:** pytest + pytest-asyncio

---

## global/validation

- **Fail Early**: Validate input as early as possible and reject invalid data before processing
- **Allowlists Over Blocklists**: When possible, define what is allowed rather than trying to block everything that's not
- **Type and Format Validation**: Check data types, formats, ranges, and required fields systematically
- **Pydantic Validation**: Use Pydantic models with Field constraints for input validation
