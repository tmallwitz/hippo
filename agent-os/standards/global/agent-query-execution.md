---
name: agent-query-execution
description: Background tasks (scheduler, dream triggers) execute by prompting the agent with the task description, giving them full memory tool access.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-05-phase2b-scheduler
---

# Agent-Query Execution

When a scheduled task fires, the scheduler queries the agent with the task description as a prompt. The agent responds freely, using all available memory tools.

```python
async def _execute_task(task, config, client, client_lock, bot, store, tz):
    async with client_lock:
        response = await query_agent(client, task.description)
    # send response to user via Telegram
```

**Why:** This gives scheduled tasks the same capabilities as live conversation — the agent can search memory, log episodes, create entities, etc. A hardcoded response template would be far less useful.

**Rules:**
- Task descriptions are instructions to the agent, not messages to the user. Example: "Ask the user how their presentation went and log the response as an episode."
- Always acquire `client_lock` before querying the agent.
- The agent's response is sent to all whitelisted Telegram users.
