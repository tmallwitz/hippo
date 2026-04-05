# References for Phase 2

## Phase 1 Semantic Memory (primary reference)

- **Location:** `hippo/memory/semantic.py`
- **Relevance:** Identical file I/O patterns, frontmatter parsing, async wrapping
- **Key patterns to reuse:**
  - `asyncio.to_thread()` for sync I/O
  - `asyncio.Lock()` for write concurrency
  - `python-frontmatter` for YAML frontmatter
  - Private `_sync` methods called from public async methods
  - `Path.mkdir(parents=True, exist_ok=True)` for safe dirs

## MCP Tool Wiring (server.py)

- **Location:** `hippo/memory/server.py`
- **Relevance:** Same pattern for adding tools
- **Key patterns:**
  - `@tool(name, description, schema)` decorator
  - Module-level store + getter function
  - `_text()` and `_json_result()` response helpers
  - Factory function updates tool list
