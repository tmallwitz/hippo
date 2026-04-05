# Phase 3: Short-Term Buffer + Dream Cycle + Inter-Bot Mailbox

## Goal

Introduce the hippocampus-inspired two-stage memory model: raw impressions
accumulate in a short-term buffer during conversation, then a dream cycle
consolidates them into structured long-term memory. Plus inter-bot messaging
via filesystem mailboxes.

## Deliverables

### A) Short-Term Buffer

- `BufferEntry` Pydantic model in `types.py`
- `ObsidianBufferStore` in `hippo/memory/buffer.py`:
  - `append(entry)` — JSONL append to `short_term/buffer.jsonl`
  - `read_buffer()` — parse all lines into `tuple[BufferEntry, ...]`
  - `archive_buffer(date)` — move to `short_term/processed/YYYY-MM-DD.jsonl`, reset
- `remember(content, tags?)` MCP tool registered in `server.py`

### B) Dream Cycle (sub-agent)

- `MailboxMessage` and `DreamReport` Pydantic models in `types.py`
- `hippo/dream/` package:
  - `prompts.py` — `DREAM_SYSTEM_PROMPT` constant
  - `runner.py` — `run_dream(config, buffer_store, mailbox_store) -> str`
- Dream MCP server via `create_dream_server()` in `server.py`:
  - Subset: semantic (9) + episodic (2) + `read_inbox` tools only
- Dream sub-agent creates ephemeral `ClaudeSDKClient` per run
- Concurrent dream prevention via `asyncio.Event`
- Empty buffer/inbox: skip LLM, write minimal report
- Dream report at `dream_reports/YYYY-MM-DD.md`
- Buffer archived to `short_term/processed/`, inbox cleared

### C) Inter-Bot Mailbox

- `ObsidianMailboxStore` in `hippo/memory/mailbox.py`:
  - `send_message(target_vault, from_bot, subject, content)`
  - `read_inbox()` — parse all `.md` in `inbox/`
  - `clear_inbox()` — delete all processed messages
- `send_message` and `read_inbox` MCP tools
- `load_bot_registry(project_root)` reads `bots.yaml` convention
- `bots.yaml` example in project root

## Implementation Order

1. Save spec documentation (this task)
2. Add `BufferEntry`, `MailboxMessage`, `DreamReport` to `types.py`
3. Implement `ObsidianBufferStore` + tests
4. Implement `ObsidianMailboxStore` + tests
5. Add MCP tools + `create_dream_server()` to `server.py`
6. Implement `hippo/dream/` package + tests
7. Wire config (`hippo_dream_model`), agent system prompt, `.env.example`
8. Wire `/dream` command in `telegram_bridge.py`, update `__main__.py`
9. Update `tests/conftest.py` fixtures
10. Update `README.md`, `roadmap.md`
11. Lint, type-check, full test pass

## Acceptance Criteria

1. Buffer fills during normal conversation without agent pausing to structure info
2. `/dream` produces a report: new entities, observations, episodes, skills, discarded
3. After dream: buffer archived and empty
4. Autonomously written skill is loaded and applied in the next session
5. Message sent from one bot is consolidated by receiving bot's next dream cycle
6. All tests pass, ruff and mypy clean

## Key Design Decisions

| Decision | Choice |
|----------|--------|
| Dream client | Ephemeral per run, disposed after |
| Dream MCP server | Subset: semantic + episodic + read_inbox only |
| `/dream` trigger | Bypasses main agent, calls `run_dream()` directly |
| Dream model | Separate `HIPPO_DREAM_MODEL` config field |
| Bot registry | Convention: `bots.yaml` in project root (no config) |
| Cleanup responsibility | Runner (not agent) archives buffer + clears inbox |
| Empty buffer handling | Skip LLM, write minimal report, still archive |
