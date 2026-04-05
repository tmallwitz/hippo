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
