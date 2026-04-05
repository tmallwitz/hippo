# References for Phase 5: Telegram Upgrade

## Similar Implementations

### Existing Telegram handlers

- **Location**: `hippo/telegram_bridge.py`
- **Relevance**: Text handler and `/dream` command are the pattern to follow for new handlers
- **Key patterns**: `_WhitelistFilter`, `_keep_typing`, `query_agent`, `convert_to_telegram`

### Memory store factory

- **Location**: `hippo/memory/server.py` — `create_memory_server()`
- **Relevance**: Returns stores we need to expose for the new commands

### Buffer store

- **Location**: `hippo/memory/buffer.py` — `ObsidianBufferStore.read_buffer()`
- **Relevance**: Used by `/status` for buffer count and for appending voice/image entries

### Scheduled store

- **Location**: `hippo/memory/scheduled.py` — `ObsidianScheduledStore.list_tasks()`
- **Relevance**: Used by `/status` (next task) and `/tasks` (full list)

### Agent query pattern

- **Location**: `hippo/telegram_bridge.py:136` — `query_agent()`
- **Relevance**: Template for `query_agent_with_image()` with image content blocks
