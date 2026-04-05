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
