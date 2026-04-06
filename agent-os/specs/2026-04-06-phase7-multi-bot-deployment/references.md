# References for Phase 7: Multi-Bot Deployment

## Core Python Files Modified

### `hippo/config.py`

- **Location:** `hippo/config.py`
- **Relevance:** `HippoConfig` and `get_config()` — the entire config layer
- **Key patterns:** `BaseSettings` with `model_config`, `field_validator`, pydantic-settings v2
- **Change:** Replaced `@lru_cache` singleton with `get_config(bot_name: str)` factory
  using `settings_customise_sources` for two-layer env prefix resolution

### `hippo/__main__.py`

- **Location:** `hippo/__main__.py`
- **Relevance:** Process entry point — where CLI args are parsed and the bot starts
- **Key patterns:** `asyncio.run(_async_main())`, `logging.basicConfig`
- **Change:** Added `argparse` for `bot_name` positional arg, `TimedRotatingFileHandler`

### `hippo/memory/server.py`

- **Location:** `hippo/memory/server.py`
- **Relevance:** MCP server with module-level store globals; `send_message` tool
- **Key patterns:** `@tool` decorator, `create_sdk_mcp_server`, module globals
- **Change:** Added `_project_root` global; `send_message` uses it instead of `Path.cwd()`

### `hippo/agent.py`

- **Location:** `hippo/agent.py`
- **Relevance:** Wires config → MCP server → ClaudeSDKClient
- **Change:** Passes `project_root=Path(__file__).parent.parent` to `create_memory_server()`

## Configuration Files

### `bots.yaml`

- **Location:** `bots.yaml` (project root)
- **Relevance:** Inter-bot mailbox registry; parsed by PowerShell scripts
- **Format:** YAML with `bots:` key mapping bot names to vault paths and roles

### `.env.example`

- **Location:** `.env.example`
- **Change:** Restructured with shared `HIPPO_*` section and per-bot `ALICE_*` section

## PowerShell Scripts (new)

### `scripts/start-bots.ps1`

One-shot launcher: reads `bots.yaml`, starts each bot via `Start-Process uv`.

### `scripts/install-tasks.ps1`

Windows Task Scheduler registration for auto-start on login.

### `scripts/deploy.ps1`

9-step idempotent deployment wizard for fresh Windows 11 Pro setup.
