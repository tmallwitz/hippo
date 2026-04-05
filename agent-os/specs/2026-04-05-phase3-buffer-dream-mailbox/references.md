# References for Phase 3

## Similar Implementations

### ObsidianEpisodicStore (Phase 2)

- **Location:** `hippo/memory/episodic.py`
- **Relevance:** Pattern to follow for ObsidianBufferStore: vault_path constructor,
  asyncio.Lock, asyncio.to_thread delegation, pre-create directory in __init__
- **Key patterns:** Daily file pattern, regex-based parsing, append-then-rewrite

### ObsidianScheduledStore (Phase 2b)

- **Location:** `hippo/memory/scheduled.py`
- **Relevance:** UUID-based file naming (relevant for mailbox message files),
  frontmatter-only files, frozen Pydantic with optional fields
- **Key patterns:** `uuid.uuid4().hex[:8]` for IDs, YAML frontmatter via python-frontmatter,
  immutable update pattern (read → construct new model → rewrite)

### MCP server tool registration (server.py)

- **Location:** `hippo/memory/server.py`
- **Relevance:** Exact pattern for registering new Phase 3 tools: module-level globals,
  `_get_*()` accessors, `@tool` decorator, `_text()` / `_json_result()` helpers,
  `create_memory_server()` factory
- **Key patterns:** Tools are module-level functions; stores initialized once via factory

### Scheduler loop (scheduler.py)

- **Location:** `hippo/scheduler.py`
- **Relevance:** Pattern for the dream cycle: the `/dream` command handler follows
  the same acquire-lock → execute → send-result flow as `_execute_task`
- **Key patterns:** `client_lock` ensures one active agent query at a time

### Existing type definitions

- **Location:** `hippo/memory/types.py`
- **Relevance:** All new types (BufferEntry, MailboxMessage, DreamReport) must match
  the existing convention: `frozen=True`, tuple collections, string dates/times
