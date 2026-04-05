# Phase 4: Dream Completion — Plan

## Overview

Complete the dream cycle's capabilities across six deliverables. All generated files live in the vault.

**Dropped from roadmap:** Git Autocommit (vault is runtime data, not code).

---

## Task 1: Save spec documentation ✓

This file.

---

## Task 2: Dream Report Append

**File:** `hippo/dream/runner.py` — modify `_write_dream_report()`

If the report file exists: append `---` separator + `## Run at HH:MM UTC` + new body.
If new: create with YAML frontmatter, wrap body in same heading.

**Test:** `tests/test_dream.py` — `TestReportAppend`: call twice, assert both sections + separator present.

---

## Task 3: Scheduler → Buffer Pipeline

**File:** `hippo/scheduler.py` — `_execute_task()`

Add `buffer_store: ObsidianBufferStore` param. After successful agent query, append
`BufferEntry(session="scheduler-{task.id}", tags=("scheduler",))`. Pass through from `run_scheduler()`.

---

## Task 4: Raw Document Ingest

**File:** `hippo/dream/runner.py` — new helpers + `run_dream()` changes

- `_scan_raw_documents(vault_path)` — scans `raw/` for `.md`/`.txt`, skips `processed/`
- `_format_raw_documents(docs)` — formats for query, truncates at 10k chars
- `_move_raw_to_processed(vault_path, filenames)` — moves after processing
- `_build_query()` gets optional `raw_documents` param

**File:** `hippo/dream/prompts.py` — add "Raw document processing" section.

**File:** `tests/conftest.py` — add `raw/` + `raw/processed/` to `tmp_vault`.

---

## Task 5: Dream Skills

### 5a: Install skill-creator into vault

Download `anthropics/skills` skill-creator skill to `<vault>/.claude/skills/skill-creator/`.

### 5b: Update dream prompt

Replace category 3 with instructions referencing the installed skill-creator:
- Threshold: ≥3 occurrences across separate buffer entries/sessions
- Read `.claude/skills/skill-creator/SKILL.md` for the creation workflow
- Write to `.claude/skills/<slug>/SKILL.md` + `evals/evals.json`
- Track in knowledge graph as "skill" entity
- Check for duplicates first

Update DREAM SUMMARY block to add `Skills updated:` line.

---

## Task 6: Semantic Index + Personality Polish

**File:** `hippo/dream/prompts.py` — prompt-only refinements

- Semantic index: explicit path (`semantic/index.md`), skip index file when scanning, use built-in file tools
- Personality: create `personality/` dir if missing, reinforce `<!-- manual -->` preservation

**File:** `tests/conftest.py` — add `personality/` to `tmp_vault` fixture.

---

## Verification

1. `uv run pytest tests/ -v` — all tests pass
2. `uv run ruff check hippo/ tests/` + `uv run ruff format --check hippo/ tests/`
3. Manual: drop `.md` in `raw/`, trigger `/dream`, verify file moved to `raw/processed/`
4. Manual: send messages, trigger `/dream`, verify `semantic/index.md` + `personality/prompt_ext.md` in vault
