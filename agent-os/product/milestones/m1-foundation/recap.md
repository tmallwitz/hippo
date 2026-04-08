# Recap: m1-foundation

**Closed:** 2026-04-08
**Status:** closed
**Specs delivered:** 8

## Goal achievement

Achieved.

All seven phases delivered as planned: semantic memory, episodic memory, scheduler, dream cycle with autonomous consolidation, Telegram bridge with voice/image support, embedding-based search, and multi-bot runtime with Windows deployment.

## Biggest lesson

Building all seven phases in rapid succession proved that spec-driven development with retrospective documentation works well for solo projects — the recaps and standards captured patterns that would otherwise be lost.

## Specs delivered

### 2026-04-05-phase1-semantic-memory-telegram

Hippo gained its core architecture: a Python project bootstrapped with uv, a 9-tool semantic memory system (create/read/search/delete entities, relations, and observations) backed by Markdown files in an Obsidian vault, an MCP server exposing those tools to the Claude Agent SDK, a Telegram bridge with user whitelisting and markdown conversion, and a system prompt that instructs the agent to use memory proactively. This is the foundation everything else builds on.

**Key decisions:**
- Flat layout (`hippo/` at project root) over src-layout
- Category subfolders (`semantic/<EntityType>/`) for Obsidian navigability
- Entity name in YAML frontmatter to fix lossy filename round-trip
- SemanticStore protocol as the storage abstraction from day one

### 2026-04-05-phase2-episodic-memory

Hippo gained a time-ordered journal layer alongside its semantic knowledge graph. The bot can now log detailed episode summaries to daily Markdown notes (`episodic/YYYY-MM-DD.md`) and recall them by date range and text query. The system prompt instructs the agent to log verbosely after every meaningful exchange, with the expectation that the dream cycle (Phase 3) will later prune what's not worth keeping.

**Key decisions:**
- Verbose logging by default — pruning deferred to the dream cycle
- No CRUD beyond log+recall — editing happens in Obsidian
- Dash-tolerant H2 parsing for editor resilience

### 2026-04-05-phase2b-scheduler

Hippo became proactive. Three new MCP tools let the agent create one-shot or recurring tasks from natural language. A background scheduler loop checks for due tasks every 30 seconds, executes them by querying the agent with the task description, and sends results to all whitelisted Telegram users. Tasks persist as individual Markdown files in the vault's `scheduled/` folder.

**Key decisions:**
- Agent-query execution — scheduled tasks are as capable as live conversation
- One file per task with frontmatter-only Markdown
- Shared asyncio.Lock for concurrent access safety
- croniter for cron evaluation

### 2026-04-05-phase3-buffer-dream-mailbox

Hippo gained its hippocampus-inspired two-stage memory model. During conversation, the agent appends raw impressions to a short-term buffer via the `remember` tool. The dream cycle — a separate sub-agent with its own system prompt and restricted MCP toolset — consolidates these impressions into structured long-term memory, then archives the buffer. An inter-bot mailbox allows multiple bots to exchange messages.

**Key decisions:**
- Ephemeral dream client — fresh ClaudeSDKClient per run
- Runner owns cleanup in finally blocks
- Bot registry as convention (bots.yaml)
- Markdown buffer instead of JSONL

### 2026-04-05-phase4-dream-completion

The dream cycle became a fully autonomous memory-management engine. It can now append multiple reports per day, ingest raw documents dropped into the vault's `raw/` folder, create skills autonomously when it detects patterns occurring 3+ times, maintain a semantic index file for fast entity lookup, and polish a self-evolving personality extension. Git autocommit was dropped since the vault is runtime data.

**Key decisions:**
- Everything in the vault — all generated files under HIPPO_VAULT_PATH
- Skill-creator bundled as package asset
- Python scans, agent classifies (raw ingest)
- Git autocommit dropped — vault is runtime data

### 2026-04-05-phase5-telegram-upgrade

The Telegram bridge now handles voice messages (transcribed locally via Whisper), images (described via Claude vision), and politely rejects unsupported media types. Four new commands (`/help`, `/status`, `/tasks`, `/memory N`) give the user instant access to bot state without querying the agent.

**Key decisions:**
- Local Whisper transcription — no API key required
- Commands bypass the agent for instant response
- Image description only, no binary storage in vault
- Lazy-loaded Whisper singleton

### 2026-04-06-phase6-memory-intelligence

Hippo's semantic search now uses embedding-based cosine similarity via local sentence-transformers instead of naive substring matching. The dream cycle can detect near-duplicate entities using fuzzy matching, and automatically summarizes old episodic daily notes. A new housekeeping module prunes old buffer archives, dream reports, completed tasks, and raw processed files.

**Key decisions:**
- Local sentence-transformers (all-MiniLM-L6-v2, ~80MB)
- Embeddings stored in vault (semantic/embeddings.json)
- Two thresholds: 0.4 for search, 0.7 for dedup
- Embedding failures never block core operations

### 2026-04-06-phase7-multi-bot-deployment

Hippo can now host multiple named bots simultaneously as independent OS processes. Each bot resolves its own config via pydantic-settings with a two-layer prefixed env var strategy. Three PowerShell scripts make the setup reproducible on a fresh Windows 11 Pro machine.

**Key decisions:**
- Separate processes, not threads — natural isolation
- pydantic-settings two-layer resolution (prefixed + unprefixed fallback)
- TimedRotatingFileHandler in Python for per-bot logging
- project_root fix for send_message path resolution

## Carry-over to next milestone

- Concurrent dream prevention needs real-world testing under load
- Skill quality validation — CI test that created skills follow the format
- Personality convergence testing — does prompt_ext.md stabilize or drift?
- Replace growing store tuples with a Stores dataclass
- Video message support
- Whisper model auto-download on first run
- Incremental embedding optimization for >10k entities
- Housekeeping dry-run mode for debugging retention policies
- Embedding model upgrade path — re-embed when switching models
- Linux/systemd deployment path
- Health-check endpoint per bot

(These items will be surfaced automatically when you run
`/plan-product --milestone` next.)

## Timeline

- Created: 2026-04-08T00:00:00Z
- Closed: 2026-04-08
- Duration: 0 days (milestone was created retroactively via /migrate-product; actual development spanned 2026-04-04 to 2026-04-06)
