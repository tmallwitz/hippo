# Phase 2b: Scheduler — Shaping Notes

## Scope

Make Hippo proactive. Three new tools let the agent schedule one-shot
and recurring tasks. A background loop executes due tasks by querying
the agent and sending results via Telegram. Tasks persist as Markdown
files in the vault, editable in Obsidian.

## Decisions

- **Natural language input**: User speaks naturally, agent converts to
  ISO datetime or cron expression before calling schedule_task
- **Agent-query execution**: When task fires, scheduler prompts the agent
  with the task description. Agent responds freely using memory tools.
- **One file per task**: `scheduled/task-{id}.md`, frontmatter-only
- **Concurrency**: asyncio.Lock shared between Telegram handler and
  scheduler prevents simultaneous agent queries
- **Timezone**: HIPPO_TIMEZONE in config, default Europe/Berlin
- **New dependency**: croniter for cron expression evaluation

## Context

- **Visuals:** None
- **References:** Phase 1+2 store patterns (semantic.py, episodic.py)
- **Product alignment:** Matches Phase 2b in roadmap.md

## Implementation Base

base_commit: 14c26667582776a9b035122bf11c967520166154
captured_at: 2026-04-08T00:00:00Z
captured_by: finish-spec (legacy fallback)

## Deviations & Bugfixes

2026-04-08

### What was built as planned
- ScheduledTask Pydantic model in types.py
- ObsidianScheduledStore in scheduled.py (one Markdown file per task, frontmatter-only)
- 3 MCP tools (schedule_task, list_scheduled_tasks, cancel_scheduled_task) in server.py
- Background scheduler loop in scheduler.py with 30s interval and get_due_tasks()
- telegram_bridge.py restructured: query_agent and convert_to_telegram made public, lock parameter added
- __main__.py restructured: asyncio.gather for concurrent bot + scheduler
- System prompt extended with scheduling instructions and timezone placeholder
- HIPPO_TIMEZONE config field (default Europe/Berlin)
- 221 lines of tests in test_scheduled.py

### What was built differently
- Nothing: spec was written retrospectively; plan reflects actual implementation.

### What was added beyond the plan
- Nothing notable beyond spec documentation files.

### What was not built
- Nothing: all deliverables complete.
