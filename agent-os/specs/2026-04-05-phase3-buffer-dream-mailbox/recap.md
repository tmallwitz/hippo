# Recap: Phase 3 — Short-Term Buffer + Dream Cycle + Inter-Bot Mailbox

**Completed:** 2026-04-08
**Base commit:** 4f4e03298c84882c154a387c37015b9fd6ae9f82
**Final commit:** 44e9e560b08f92e83790df3fecb1858390eb8190
**Milestone:** m1-foundation

## What this spec delivered

Hippo gained its hippocampus-inspired two-stage memory model. During conversation, the agent appends raw impressions to a short-term buffer via the `remember` tool. The dream cycle — a separate sub-agent with its own system prompt and restricted MCP toolset — consolidates these impressions into structured long-term memory (semantic entities, episodic entries, or skills), then archives the buffer. An inter-bot mailbox allows multiple bots to exchange messages that get processed during the receiver's next dream cycle. The dream can be triggered manually via `/dream` in Telegram or automatically when the buffer exceeds a configurable threshold.

## Key decisions

- **Ephemeral dream client** — the dream sub-agent creates a fresh `ClaudeSDKClient` per run and disposes it after, avoiding long-lived state from polluting the main agent.
- **Runner owns cleanup** — buffer archival and inbox clearing happen in the runner's `finally` block, not in the LLM sub-agent, ensuring cleanup always occurs even if the agent fails.
- **Bot registry as convention** — `bots.yaml` in the project root with `load_bot_registry()` returning an empty dict if the file is missing; no `.env` config needed.
- **Markdown buffer instead of JSONL** — buffer.py uses H2 sections rather than the originally-scoped JSONL, keeping consistency with the vault-readable Markdown philosophy.

## Surprises and lessons

- The buffer format changed from JSONL to Markdown during implementation — the Obsidian-readable principle won over the append-efficiency argument.
- Scheduler integration (auto-dream trigger) emerged during implementation and wasn't in the original task list, showing that spec decomposition sometimes misses cross-cutting concerns.

## Carry-over candidates

- Autonomous skill creation by the dream cycle (Phase 4 later delivered a filesystem write tool for this)
- Git autocommit after dream runs (Phase 4 delivered this)
- Concurrent dream prevention needs real-world testing under load

## Files touched

 .env.example                                       |   7 +
 agent-os/product/roadmap.md                        |   8 +-
 agent-os/specs/2026-04-05-phase3.../plan.md        |  78 ++++++
 agent-os/specs/2026-04-05-phase3.../references.md  |  39 +++
 agent-os/specs/2026-04-05-phase3.../shape.md       |  43 +++
 agent-os/specs/2026-04-05-phase3.../standards.md   |  67 +++++
 bots.yaml                                          |  16 ++
 hippo/__main__.py                                  |   8 +-
 hippo/agent.py                                     |  40 ++-
 hippo/config.py                                    |   2 +
 hippo/dream/__init__.py                            |   1 +
 hippo/dream/prompts.py                             |  56 ++++
 hippo/dream/runner.py                              | 184 +++++++++++++
 hippo/memory/__init__.py                           |  22 +-
 hippo/memory/buffer.py                             | 165 ++++++++++++
 hippo/memory/mailbox.py                            | 148 +++++++++++
 hippo/memory/server.py                             | 150 +++++++++-
 hippo/memory/types.py                              |  33 +++
 hippo/scheduler.py                                 |  55 +++-
 hippo/telegram_bridge.py                           |  34 ++-
 27 files changed, 1663 insertions(+), 24 deletions(-)
