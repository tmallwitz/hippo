# Product Roadmap

Hippo is built in three phases. Each phase produces a usable system;
later phases layer capabilities on top without breaking earlier ones.
Phase boundaries are strict: features from a later phase are not
pulled forward into an earlier one.

---

## Phase 1: Semantic Memory + Telegram Bridge

**Status:** Planned

Port the core knowledge-graph memory system to Python and connect it to
Telegram. Delivers a working bot that remembers facts across sessions.

### Scope

- Nine semantic memory tools ported from the TypeScript reference project:
  `create_entities`, `create_relations`, `add_observations`,
  `delete_entities`, `delete_observations`, `delete_relations`,
  `read_graph`, `search_nodes`, `open_nodes`
- Markdown storage with YAML frontmatter, relations as `[[Typed::Target]]`
- `MemoryStore` protocol as the storage abstraction from day one
- Telegram bridge via aiogram v3 with user whitelist (`ALLOWED_TELEGRAM_IDS`)
- One bot, one vault, one human user
- System prompt that instructs the agent to use memory tools proactively
- Skills loaded from `.claude/skills/` inside the vault
- Roundtrip tests for all memory operations

### Acceptance Criteria

- `uv run hippo` starts the bot and it responds in Telegram
- Non-whitelisted users are silently ignored
- The bot can be told a fact, writes the corresponding Markdown file,
  and can recall that fact in a later message
- The vault opens cleanly in Obsidian and entities appear in the graph view
- Manual edits in Obsidian are picked up by the bot on the next read
- A hand-authored skill under `.claude/skills/` loads and affects behavior
- All memory operations have passing tests

---

## Phase 2: Episodic Memory

**Status:** Planned

Add a time-ordered memory layer alongside the semantic knowledge graph.
Delivers the bot's ability to remember "what happened when" in addition
to "what is true".

### Scope

- New tools: `log_episode` and `recall_episodes`
- Daily notes in `episodic/YYYY-MM-DD.md` with timestamped entries and tags
- Time-range filtering and text search for recall
- System prompt update: proactively log decisions, milestones, learnings
- Procedural knowledge remains as skills (no separate procedural layer)

### Acceptance Criteria

- After several days of use, daily notes exist and contain meaningful entries
- Asking "what did we discuss on date X" surfaces the right episodes
- Manual edits to episodes are respected on the next read
- A skill that encodes a recurring preference is applied consistently
  across sessions

---

## Phase 2b: Scheduler

**Status:** Planned

Give the bot the ability to perform actions at scheduled times. This
turns Hippo from a reactive assistant into a proactive one that can
remind, check in, and act autonomously on a schedule.

### Scope

- New tool: `schedule_task(description, cron_or_time, channel?)` — the
  user tells the bot "remind me every Monday at 9 to check the deploy"
  or "in 3 hours, ask me how the meeting went"
- Scheduled tasks stored as YAML/Markdown in `scheduled/` in the vault
  (human-readable, editable in Obsidian)
- A scheduler loop that checks for due tasks and executes them by
  querying the agent with the task description as a prompt
- Results sent back to the user via Telegram
- New tool: `list_scheduled_tasks()` — show what's upcoming
- New tool: `cancel_scheduled_task(id)` — remove a scheduled task
- Recurring tasks (cron-style) and one-shot tasks (specific datetime)
- Timezone-aware (configured per bot in `.env`)

### Use Cases

- **Reminders:** "Remind me tomorrow at 10 to call the dentist"
- **Recurring check-ins:** "Every Friday at 17:00, ask me what I
  accomplished this week" (response gets logged as an episode)
- **Proactive memory:** "Every morning at 8, tell me what's on my
  mind" (agent searches recent episodic + semantic memory and sends
  a summary)
- **Delayed follow-ups:** "In 2 hours, ask me how the presentation went"

### Integration with Other Layers

- Scheduler can trigger episodic logging (Phase 2a) — a recurring
  "journal prompt" becomes a natural way to fill the episodic memory
- In Phase 3, scheduled tasks feed into the short-term buffer and
  get consolidated by the dream cycle
- The dream cycle itself (Phase 3) is just a special scheduled task

### Acceptance Criteria

- User says "remind me in 1 hour to drink water" → bot sends the
  reminder at the right time
- User sets a recurring task → it fires reliably on schedule
- `list_scheduled_tasks` shows all upcoming tasks
- Scheduled tasks survive bot restarts (persisted in vault)
- Tasks are visible and editable as files in Obsidian

---

## Phase 3: Short-Term Buffer + Dream Cycle + Inter-Bot Mailbox

**Status:** Planned

Introduce the two-stage memory model and autonomous consolidation.
Delivers the bot's ability to learn overnight and for multiple bots
to exchange information.

### Scope

**Short-Term Buffer**

- `remember(content, tags?)` tool — cheap append to `short_term/buffer.jsonl`
- Agent uses this liberally during conversation, no upfront structure required

**Dream Cycle**

- Implemented as a sub-agent with its own system prompt and tool set
- Reads the buffer and relevant parts of long-term memory for context
- Classifies each buffer entry: semantic fact, episodic event,
  skill-worthy rule, or noise
- Deduplicates aggressively via `search_nodes` before creating entities
- May write new skills autonomously when it detects recurring patterns
- Writes a dream report to `dream_reports/YYYY-MM-DD.md`
- Archives the buffer to `short_term/processed/YYYY-MM-DD.jsonl`
- Triggered by systemd timer (nightly) or `/dream` Telegram command

**Inter-Bot Mailbox**

- `send_message(bot_name, subject, content)` tool
- Messages stored as Markdown files in the target bot's `inbox/` folder
- Incoming messages consolidated during the next dream cycle
- Bot registry via `bots.yaml` in the project root

### Acceptance Criteria

- During a normal conversation, the buffer fills up without the agent
  stopping to structure information
- Running `/dream` produces a report showing plausible consolidation:
  new entities, observations added, episodes logged, skills created or
  updated, and entries discarded as noise
- After a dream cycle, the buffer is archived and empty
- A skill written autonomously by the dream cycle is loaded and applied
  in the next session
- The systemd timer fires nightly and produces a dream report by morning
- A message sent from one bot is correctly consolidated into the
  receiving bot's memory after its next dream cycle
- Git history of the vault shows a clean evolution of memory over time