# Recap: Phase 2b — Scheduler

**Completed:** 2026-04-08
**Base commit:** 14c26667582776a9b035122bf11c967520166154
**Final commit:** 4f4e03298c84882c154a387c37015b9fd6ae9f82
**Milestone:** m1-foundation

## What this spec delivered

Hippo became proactive. Three new MCP tools (`schedule_task`, `list_scheduled_tasks`, `cancel_scheduled_task`) let the agent create one-shot or recurring tasks from natural language. A background scheduler loop checks for due tasks every 30 seconds, executes them by querying the agent with the task description, and sends results to all whitelisted Telegram users. Tasks persist as individual Markdown files in the vault's `scheduled/` folder, editable in Obsidian. The architecture was restructured so the Telegram bot and scheduler run concurrently via `asyncio.gather` with a shared `asyncio.Lock` preventing simultaneous agent queries.

## Key decisions

- **Agent-query execution** — when a task fires, the scheduler prompts the agent with the task description; the agent responds freely using all memory tools, making scheduled tasks as capable as live conversation.
- **One file per task** (`scheduled/task-{id}.md`) — frontmatter-only Markdown files, consistent with the vault-first storage philosophy.
- **Shared asyncio.Lock** — prevents the Telegram handler and scheduler from querying the agent simultaneously, avoiding race conditions in the SDK client.
- **croniter for cron evaluation** — lightweight, well-tested library for recurring task scheduling.

## Surprises and lessons

- Making `query_agent` and `convert_to_telegram` public (removing the underscore prefix) was a small but significant refactor — it established the pattern of the Telegram bridge exposing a reusable public API, which later phases (dream /dream command, scheduler) all built on.
- The `asyncio.gather` pattern for concurrent bot + scheduler in `__main__.py` became the foundation for all subsequent concurrent features.

## Carry-over candidates

- Scheduler → buffer pipeline (Phase 3 delivered this — task results fed into dream cycle)
- Scheduler-triggered dream cycle (Phase 3 delivered this)

## Files touched

 .env.example                                       |   4 +
 agent-os/specs/2026-04-05-phase2b.../plan.md       |  21 ++
 agent-os/specs/2026-04-05-phase2b.../references.md |  12 +
 agent-os/specs/2026-04-05-phase2b.../shape.md      |  26 +++
 agent-os/specs/2026-04-05-phase2b.../standards.md  |   3 +
 hippo/__main__.py                                  |  15 +-
 hippo/agent.py                                     |  45 +++-
 hippo/config.py                                    |   1 +
 hippo/memory/__init__.py                           |   4 +-
 hippo/memory/scheduled.py                          | 246 +++++++++++++++
 hippo/memory/server.py                             |  89 ++++++-
 hippo/memory/types.py                              |  13 ++
 hippo/scheduler.py                                 |  93 ++++++
 hippo/telegram_bridge.py                           |  22 +-
 pyproject.toml                                     |   4 +-
 tests/conftest.py                                  |   3 +-
 tests/test_scheduled.py                            | 221 +++++++++++++++
 uv.lock                                            |  46 ++++
 18 files changed, 842 insertions(+), 26 deletions(-)
