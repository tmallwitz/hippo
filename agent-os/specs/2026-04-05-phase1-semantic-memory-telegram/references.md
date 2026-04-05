# References for Phase 1

## TypeScript Reference: obsidian-memory-mcp

- **Repository:** YuNaga224/obsidian-memory-mcp on GitHub
- **Relevance:** The original implementation being ported to Python
- **Key patterns to adopt:**
  - Data model: `Entity { name, entityType, observations[] }`,
    `Relation { from, to, relationType }`, `KnowledgeGraph { entities[], relations[] }`
  - Markdown format: YAML frontmatter + `## Observations` bullet list +
    `## Relations` with `[[Type::Target]]` links
  - Tool signatures: all 9 tools with their parameter shapes
  - Relation storage: unidirectional, stored only in the `from` entity's file
  - Search: case-insensitive substring on name, entityType, observations
- **Key patterns to improve:**
  - Fix `created` date bug (TS overwrites on every save)
  - Add `name` field to YAML frontmatter (TS loses names through filename sanitization)
  - Use category subfolders instead of flat storage
  - Actually use the `updateMetadata` path (dead code in TS)

### TS tool parameter shapes (for reference)

```
create_entities:    { entities: [{ name, entityType, observations[] }] }
create_relations:   { relations: [{ from, to, relationType }] }
add_observations:   { observations: [{ entityName, contents[] }] }
delete_entities:    { entityNames: [] }
delete_observations: { deletions: [{ entityName, observations[] }] }
delete_relations:   { relations: [{ from, to, relationType }] }
read_graph:         {} (no params)
search_nodes:       { query }
open_nodes:         { names: [] }
```

## Claude Agent SDK (Python)

- **Package:** `claude-agent-sdk` on PyPI (import as `claude_agent_sdk`)
- **Relevance:** The agent runtime Hippo is built on
- **Key patterns:**
  - `@tool(name, description, input_schema)` decorator for tool definitions
  - `create_sdk_mcp_server(name, version, tools)` for in-process MCP
  - `ClaudeSDKClient(options=ClaudeAgentOptions(...))` for the agent
  - `async with client:` context manager for lifecycle
  - `await client.query(text)` + `async for msg in client.receive_response():`
  - Message types: `AssistantMessage`, `ResultMessage`, `TextBlock`
  - Auth: uses bundled Claude Code CLI, pre-authenticated via `claude login`
  - `permission_mode="bypassPermissions"` for headless operation
