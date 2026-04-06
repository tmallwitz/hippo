# Standards for Phase 6: Memory Intelligence

## global/coding-style

- Type hints on all function signatures
- Async/await for all I/O; blocking ops via `asyncio.to_thread`
- Small, focused functions
- Lazy imports for heavy dependencies (sentence-transformers, torch)
- No dead code or commented-out blocks

## global/conventions

- **Package manager**: `uv` only — never `pip`
- Conventional Commits: `feat(memory): ...`
- Feature branch, squash-merge to main
- No private data in code or commits

## global/error-handling

- Embedding failures (model not loaded, file corrupt) must fall back gracefully
  to substring matching — never crash or block entity creation
- Wrap all embedding operations in try/except with `log.warning`
- Episodic archival: if summary fails for a note, skip it and log; don't abort dream

## global/tech-stack

- **New dependency**: `sentence-transformers>=2.0` (brings `torch` transitively)
- No new databases — embeddings stored as JSON in the Obsidian vault
- `mypy`: add `sentence_transformers` to `ignore_missing_imports`
- Tests: `pytest-asyncio`, `tmp_path` vaults; slow tests marked `@pytest.mark.slow`
