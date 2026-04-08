# Phase 2b: Scheduler — Plan

## Deliverables

- `ScheduledTask` model in types.py
- `ObsidianScheduledStore` in scheduled.py (new)
- 3 new MCP tools: schedule_task, list_scheduled_tasks, cancel_scheduled_task
- Background scheduler loop in scheduler.py (new)
- Restructured telegram_bridge.py (public API, lock support)
- Restructured __main__.py (concurrent bot + scheduler via asyncio.gather)
- System prompt extension for scheduling
- HIPPO_TIMEZONE config field
- ~20 new tests

## Acceptance Criteria

1. "Erinner mich in 1 Stunde ans Wasser" → bot sends reminder on time
2. Recurring tasks fire reliably on schedule
3. list_scheduled_tasks shows upcoming tasks
4. Tasks survive bot restarts (persisted in vault)
5. Tasks visible and editable in Obsidian

## Deviations & Bugfixes

2026-04-08

### What was built as planned
- ScheduledTask model in types.py
- ObsidianScheduledStore in scheduled.py (246 lines, one-file-per-task)
- 3 MCP tools in server.py (schedule_task, list_scheduled_tasks, cancel_scheduled_task)
- Background scheduler loop in scheduler.py (30s interval)
- telegram_bridge.py: query_agent + convert_to_telegram made public, lock param
- __main__.py: asyncio.gather for concurrent bot + scheduler
- System prompt scheduling section with timezone placeholder
- HIPPO_TIMEZONE config, test_scheduled.py (221 lines)

### What was built differently
- Nothing.

### What was added beyond the plan
- Nothing notable.

### What was not built
- Nothing.
