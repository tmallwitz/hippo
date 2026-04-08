---
name: ephemeral-sub-agent
description: Sub-agents (dream cycle, batch jobs) create a fresh ClaudeSDKClient per run and dispose it after; never reuse the main agent's client.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-05-phase3-buffer-dream-mailbox
---

# Ephemeral Sub-Agent Client

When running a sub-agent (dream cycle, batch consolidation, etc.), create a fresh `ClaudeSDKClient` for each invocation and dispose it when done.

```python
async def run_dream(config, ...):
    client = ClaudeSDKClient(ClaudeAgentOptions(
        model=config.hippo_dream_model,
        system_prompt=DREAM_SYSTEM_PROMPT,
        mcp_servers=[create_dream_server(vault_path)],
    ))
    async with client:
        # ... run the sub-agent
    # client is disposed here
```

**Rules:**
- Never share a `ClaudeSDKClient` between the main conversational agent and a sub-agent.
- Sub-agent clients get their own system prompt and a restricted MCP server (only the tools they need).
- Use `async with` to guarantee cleanup.
