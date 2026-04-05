# References for Phase 4: Dream Completion

## Similar Implementations

### Phase 3 dream cycle runner

- **Location:** `hippo/dream/runner.py`
- **Relevance:** Core orchestration pattern for the dream cycle — all Phase 4 changes extend this file
- **Key patterns:** `run_dream()` async orchestration, `_dream_running` guard, `asyncio.to_thread` for sync file I/O, `finally` block for cleanup

### Phase 3 dream prompt

- **Location:** `hippo/dream/prompts.py`
- **Relevance:** All prompt changes build on the existing `DREAM_SYSTEM_PROMPT`
- **Key patterns:** Numbered classification categories, structured DREAM SUMMARY output block

### Phase 3 buffer store

- **Location:** `hippo/memory/buffer.py`
- **Relevance:** `ObsidianBufferStore.append()` is reused in the scheduler pipeline
- **Key patterns:** `BufferEntry(ts, session, content, tags)`, append-only Markdown at `short_term/buffer.md`

### Scheduler

- **Location:** `hippo/scheduler.py`
- **Relevance:** `_execute_task()` is modified to feed results into the buffer
- **Key patterns:** `buffer_store` already passed to `run_scheduler()`, just needs threading through to `_execute_task()`

### Official skill-creator skill

- **Location:** `github.com/anthropics/skills` → `skills/skill-creator/SKILL.md`
- **Relevance:** Canonical format for skill files; installed into the vault for the dream agent to use
- **Key patterns:** YAML frontmatter (`name`, `description`), imperative markdown body, `evals/evals.json` with test prompts
