# Hippo

> Experimental Claude agent with multi-layered memory. Obsidian vault as
> brain, Telegram as mouth, and a nightly dream cycle that consolidates
> short-term impressions into long-term knowledge and self-written skills.

**Status:** Early development. Phase 1 in progress. Expect breaking changes.

## What it is

Hippo is a personal Claude agent built on the [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python).
Unlike typical chat agents, Hippo treats memory as a first-class concern with
distinct layers that mirror how biological memory works:

- **Short-term memory** — an append-only buffer for impressions during conversation
- **Semantic memory** — a knowledge graph stored as Markdown in an Obsidian vault
- **Episodic memory** — daily journal entries of things that happened
- **Procedural memory** — handled as Claude Agent Skills (`SKILL.md`)

A nightly **dream cycle** runs as a sub-agent, consolidating the short-term
buffer into the appropriate long-term layers, and can even write new skills
autonomously when it detects recurring patterns.

The name comes from the **hippocampus**, the brain region that performs
memory consolidation during sleep in mammals.

## What it isn't (yet)

- Production-ready. This is an experimentation platform.
- A general-purpose framework. It's built for a specific setup
  (one user per bot, local deployment, Claude Pro OAuth).
- Finished. See [PLAN.md](./PLAN.md) for the phased roadmap.

## Architecture

See [PLAN.md](./PLAN.md) for the original design document and the
three-phase development vision. Day-to-day development uses
[Agent OS](https://buildermethods.com/agent-os) for spec-driven workflow
and standards management; specs and standards live under `agent-os/`.

## Inspired by

- [`obsidian-memory-mcp`](https://github.com/YuNaga224/obsidian-memory-mcp)
  by YuNaga224 — the original idea of storing AI memories as Obsidian-linkable
  Markdown. Hippo ports this concept to Python and extends it with the
  short-term buffer and dream-cycle model.
- Anthropic's [memory server](https://github.com/modelcontextprotocol/servers/tree/main/src/memory)
  for the underlying knowledge-graph primitives.

## License

MIT. See [LICENSE](./LICENSE).
