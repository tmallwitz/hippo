# Product Mission

## Problem

LLM chat agents are stateless. They forget everything between sessions,
so conversations never build on each other, preferences aren't learned,
and there is no continuity between interactions. Workarounds like
stuffing context into system prompts or using opaque vector databases
trade one problem for another: either the context window overflows, or
the "memory" becomes a black box the user can't inspect or correct.

## Target Users

Developers and tinkerers who want a personal chat bot they can actually
understand and steer. People who are comfortable reading Markdown, using
Git, running a process on a Linux box, and who prefer transparent tools
over magic ones.

Specifically: single-user-per-bot operation, with support for running
multiple independent bot personalities (separate vaults, separate Telegram
bots) on the same host.

This is not a product for end users looking for a polished assistant.
It's an experimentation platform for people who want to shape how memory
and agency work in an AI agent.

## Solution

Hippo is a Claude agent built on the Claude Agent SDK with Telegram as
the primary interface and an Obsidian vault as its brain. Its core
differentiator is a bio-inspired, multi-layered memory architecture
modeled after the hippocampus:

1. **Layered memory model.** Short-term buffer for raw impressions,
   semantic knowledge graph for structured facts, episodic daily journal
   for time-ordered events, and procedural knowledge as Claude Agent
   Skills. Each layer has a clear purpose and is accessed through
   different tools.

2. **Obsidian vault as the memory backend.** All memory is stored as
   human-readable Markdown files with YAML frontmatter. The user can
   browse, edit, visualize, and version-control the bot's knowledge in
   Obsidian's graph view. Nothing is hidden in a database.

3. **Dream cycle for consolidation.** A scheduled sub-agent processes
   the short-term buffer and moves information into the appropriate
   long-term layer, deduplicating as it goes. It can also write new
   skills autonomously when it detects recurring patterns. The cycle
   runs nightly on a timer or on demand via `/dream`.

4. **Multi-bot on one host.** Each bot instance has its own vault,
   identity, and Telegram token. Multiple bots coexist on one machine
   and can exchange messages via filesystem mailboxes, which are
   consolidated into the receiver's memory on the next dream cycle.

## Non-Goals

Hippo deliberately does not try to be:

- A production-ready assistant with SLAs or multi-tenant hosting
- A general-purpose framework for arbitrary agent architectures
- A replacement for vector databases in retrieval-heavy applications
- A polished chat UI (Telegram is the only interface)
- A multi-user shared workspace (one human per bot, by design)

These constraints are what make the project tractable and focused.