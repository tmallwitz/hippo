# Product Roadmap

Hippo is built in phases. Each phase produces a usable system;
later phases layer capabilities on top without breaking earlier ones.
Phase boundaries are strict: features from a later phase are not
pulled forward into an earlier one.

---

## Phase 1: Semantic Memory + Telegram Bridge

**Status:** Done

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

**Status:** Done

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

**Status:** Done

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

**Status:** Done

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

---

## Phase 4: Dream Completion + Git Integration

**Status:** Planned

Complete the dream cycle's original promise (autonomous skill creation)
and add a durable audit trail via Git.

### Scope

**Dream Skills**

- Add a filesystem write tool to the dream sub-agent's MCP server so it
  can actually create `.claude/skills/<slug>/SKILL.md` files
- Dream report tracks newly created skill names
- Raise the bar for skill creation: only write a skill if the pattern
  appears at least three times across different buffer entries
- **Skill quality:** every skill the dream writes must follow the
  [skill-creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)
  process — YAML frontmatter with `name` + `description`, imperative
  instructions, and an `evals/evals.json` with 2–3 test prompts

**Raw Document Ingest**

- Add a `raw/` subfolder to the vault for dropping in arbitrary source
  documents: web clips, articles, PDFs converted to Markdown, notes
- Dream cycle scans `raw/` on each run, compiles summaries + entities
  into semantic memory, then moves processed files to `raw/processed/`
- No new user-facing tool required — dream's existing filesystem tools
  handle it; user just drops files into `raw/`

**Semantic Index File**

- Dream cycle auto-maintains `semantic/index.md` after every run:
  one line per entity — `**Name** (type): one-sentence summary`
- Main agent system prompt updated: read `semantic/index.md` first
  when the user asks a broad question or "what do you know about X";
  use it instead of `read_graph` for orientation, then follow up with
  `open_nodes` or `search_nodes` for detail
- `read_graph` guidance in the system prompt demoted to "last resort"
  once the index exists
- Dream also regenerates the index from scratch on a full rebuild
  (e.g., after bulk imports from `raw/`)
- Inspired by Karpathy's observation that at small-to-medium scale
  (~100 docs) a well-maintained index beats vector search

**Dream Report Append**

- Multiple dream runs on the same day append to (not overwrite)
  `dream_reports/YYYY-MM-DD.md`, with a separator and timestamp per run

**Git Autocommit**

- After every successful dream cycle, run `git add -A && git commit`
  inside the vault directory
- Commit message: `dream: YYYY-MM-DD HH:MM — N entities, M episodes, K skills`
- Configurable: opt-in via `HIPPO_GIT_AUTOCOMMIT=true` in `.env`
- No push — local commit only; user controls when to push

**Scheduler → Buffer Pipeline**

- When a scheduled task completes, its result is also appended to the
  short-term buffer so the dream cycle can consolidate it into memory

**Self-Evolving Personality**

The bot starts with a fixed base system prompt (hardcoded in `agent.py`).
Over time the dream cycle extends it based on observed patterns, building
a personalised layer stored in the vault.

- **Personality store:** `personality/prompt_ext.md` in the vault.
  Plain Markdown sections — each section is a learnt extension to the
  base prompt (preferred language, communication style, recurring context,
  standing instructions the user has implied or stated).
- **Agent startup:** on every launch, `agent.py` reads
  `personality/prompt_ext.md` if it exists and appends it to the base
  system prompt under a `## Learnt personality` heading. Base prompt is
  never modified; extensions are always additive.
- **Dream polishing step:** after consolidating buffer entries, the dream
  cycle runs a second pass ("polish") where it:
  1. Reviews all buffer entries and recent episodes for recurring
     preferences, communication patterns, and implied standing rules
  2. Reads the current `personality/prompt_ext.md`
  3. Writes an updated version — adding, refining, or removing sections
  4. Logs what changed in the dream report under `Personality changes:`
- **What gets captured:** language the user writes in, response length
  preference, topics of ongoing interest, recurring requests the user
  shouldn't have to repeat, implicit expectations about tone or depth.
- **What never changes:** the hard rules from `CLAUDE.md`; the tool
  descriptions; anything structural. Extensions are behavioural only.
- **User override:** the user can edit `personality/prompt_ext.md`
  directly in Obsidian; the dream cycle will preserve manual sections
  (marked with `<!-- manual -->`) and never overwrite them.

### Acceptance Criteria

- A recurring preference observed 3+ times in the buffer becomes a
  `.claude/skills/` file after the next dream cycle
- Every autonomously created skill has valid YAML frontmatter and an
  `evals/evals.json` with at least 2 test prompts
- A Markdown file dropped into `raw/` is summarised into semantic memory
  after the next dream run and moved to `raw/processed/`
- After a dream run, `semantic/index.md` exists and contains a one-line
  entry for every entity in the vault
- Running `/dream` twice on the same day produces a single report file
  with two timestamped sections
- After a dream cycle, `git log` inside the vault shows a new commit
- A scheduled task's output appears in `short_term/buffer.md`
- After several days of use, `personality/prompt_ext.md` exists and
  reflects the user's observed language, style, and preferences
- Manually marked sections (`<!-- manual -->`) in `prompt_ext.md` survive
  dream cycles unchanged
- A fresh bot start loads the personality extensions and visibly applies
  them (e.g., responds in the correct language without being told)

---

## Phase 5: Telegram Upgrade

**Status:** Done

Extend the Telegram bridge to handle non-text input and expose
quick-access commands for common operations.

### Scope

**Media Input**

- **Voice messages**: transcribe via Whisper (local or API), pass
  transcript to agent as text; also append to buffer
- **Images**: describe via Claude's vision capability, pass description
  to agent; also append to buffer
- Other media types (documents, stickers) acknowledged but not processed

**New Commands**

- `/status` — buffer entry count, last dream timestamp, next scheduled task
- `/tasks` — list all pending/active scheduled tasks (shortcut for
  `list_scheduled_tasks`)
- `/memory N` — show last N entities created and N episodes logged
  (default N=5)

### Acceptance Criteria

- Sending a voice message produces a transcript in the chat and an
  entry in the buffer
- Sending an image produces a description in the chat
- `/status` responds instantly without querying the agent
- `/tasks` shows the same list as `list_scheduled_tasks`
- `/memory` shows recent knowledge graph and journal activity

---

## Phase 6: Memory Intelligence

**Status:** Planned

Replace substring matching with embedding-based retrieval and add
automatic compression of the episodic memory layer.

### Scope

**Embedding-Based Semantic Search**

- Embed entity names and observations at write time; store vectors
  alongside Markdown files (e.g. in YAML frontmatter or a sidecar file)
- Replace substring search in `search_nodes` with cosine similarity
  over stored embeddings
- Configurable threshold; fall back to substring if no embeddings exist

**Episodic Summarization**

- Dream cycle detects daily notes older than N days (default 30) that
  exceed a size threshold
- Summarizes them into a compact form, preserving key facts
- Original verbose note archived to `episodic/archive/`

**Fuzzy Entity Matching**

- Before creating a new entity, the dream sub-agent checks for
  near-duplicates using edit distance or embeddings
- Merges probable duplicates rather than creating redundant entities

### Acceptance Criteria

- Searching "Le Guin" finds an entity stored as "Ursula K. Le Guin"
- Daily notes older than 30 days are automatically summarized
- The dream cycle does not create duplicate entities for the same
  real-world concept phrased differently

---

## Phase 7: Multi-Bot Deployment

**Status:** Planned

Make one Hippo installation host multiple named bots simultaneously, and
provide a guided deployment wizard for Windows 11 Pro so the whole setup
can be reproduced on a new machine without manual steps.

### Scope

**Multi-Bot Runtime**

Each bot is identified by its name, passed as the first CLI argument:

```
uv run hippo Alice    # starts bot named "Alice"
uv run hippo BotB     # starts bot named "BotB" in a separate process
```

- `__main__.py` reads `sys.argv[1]` as the bot name; errors loudly if
  missing
- Each bot name maps to its own config block in `.env`:
  ```
  ALICE_TELEGRAM_TOKEN=...
  ALICE_VAULT_PATH=C:/Users/.../vaults/alice
  ALICE_ALLOWED_TELEGRAM_IDS=123,456
  BOTB_TELEGRAM_TOKEN=...
  BOTB_VAULT_PATH=C:/Users/.../vaults/botb
  BOTB_ALLOWED_TELEGRAM_IDS=789
  ```
- `HippoConfig` is extended to accept a bot name prefix and resolve
  the correct env vars at startup
- Common settings (model, timezone, log level) fall back to unprefixed
  vars: `HIPPO_MODEL`, `HIPPO_TIMEZONE`, etc.
- Each bot process is fully independent — separate vault, separate
  Telegram token, separate scheduler loop, separate dream cycle
- `bots.yaml` in the project root lists all known bots and their vault
  paths; used by the inter-bot mailbox (already present from Phase 3)

**Windows Process Management**

Running multiple bots reliably on Windows 11 Pro without a container:

- One PowerShell launcher script `scripts/start-bots.ps1` that reads
  `bots.yaml` and starts each bot as a background job / separate window
- Optional: generate one Windows Task Scheduler XML per bot for
  auto-start on login, created by `scripts/install-tasks.ps1`
- Log output per bot to `logs/<BotName>.log` with daily rotation

**Deployment Wizard**

An interactive PowerShell wizard `scripts/deploy.ps1` that guides the
user through a full setup on a fresh Windows 11 Pro machine:

1. **Prerequisites check** — confirms `git`, `uv`, and Python 3.12+ are
   available; prints install links for anything missing
2. **Clone / update** — `git clone` or `git pull` the repo
3. **Dependencies** — runs `uv sync`
4. **Claude auth** — prompts `claude setup-token` and waits for
   confirmation
5. **Bot configuration** — interactive loop: "How many bots? Name each
   one." Prompts for Telegram token, vault path, and allowed user IDs
   per bot; writes `.env` (never overwrites existing values without
   confirmation)
6. **Vault scaffold** — creates the required subfolder structure
   (`semantic/`, `episodic/`, `short_term/`, `scheduled/`, `raw/`,
   `personality/`, `inbox/`, `.claude/skills/`) for each vault
7. **Smoke test** — starts each bot for 5 seconds, checks it responds
   to a `/start` command, then stops
8. **Task Scheduler** — optionally installs auto-start tasks via
   `install-tasks.ps1`
9. **Summary** — prints a checklist of what was configured and any items
   that need manual follow-up

The wizard is idempotent: safe to re-run for adding a new bot or
updating tokens without touching existing configuration.

### Acceptance Criteria

- `uv run hippo Alice` and `uv run hippo BotB` run simultaneously in
  separate terminals without interfering with each other
- Each bot uses its own vault and Telegram token; messages to Alice do
  not appear in BotB's vault
- Shared settings (`HIPPO_MODEL`) apply to both bots; per-bot overrides
  (`ALICE_MODEL`) take precedence
- `scripts/deploy.ps1` runs end-to-end on a clean Windows 11 Pro machine
  and produces a working two-bot setup without any manual file editing
- The wizard refuses to overwrite existing `.env` values without
  explicit confirmation
- `scripts/start-bots.ps1` starts all bots listed in `bots.yaml` and
  writes separate log files under `logs/`
- Re-running the wizard to add a third bot does not break the existing
  two bots