# Migrate Product

One-time migration from the upstream Agent OS layout (flat `roadmap.md`) to the local milestone-based layout (`milestones/` folder with iterative milestones).

**Run this command exactly once per project.** After migration succeeds, this command has nothing more to do and will tell you so.

This command does not touch your specs, standards, code, or git history. It only reads `roadmap.md` and writes new files under `agent-os/product/milestones/`.

## Preconditions

- `agent-os/product/` exists.
- `agent-os/product/mission.md` exists (at least — indicates that Agent OS was previously set up).

If these fail, tell the user:

```
No existing Agent OS product documentation found. You don't need migration.
Run /plan-product to set up the local layout from scratch.
```

and stop.

## Step 1: Detect the current layout

Check which layout the project currently has:

1. Does `agent-os/product/roadmap.md` exist? → legacy layout present
2. Does `agent-os/product/milestones/` exist? → local layout already present

Four possible states:

- **A) Only legacy (roadmap.md, no milestones/)** → proceed with migration.
- **B) Only local (milestones/, no roadmap.md)** → already migrated. Tell the user:
  ```
  This project is already on the local milestone layout. No migration
  needed. You can run /help-flow to see where you are in the workflow.
  ```
  and stop.
- **C) Both present (roadmap.md AND milestones/)** → partial or aborted migration. Use `AskUserQuestion`:
  ```
  This project has both roadmap.md (legacy) and milestones/ (local).
  This usually means a previous migration was interrupted or you
  manually created both.

  How do you want to proceed?

  1. Keep milestones/ as-is and archive roadmap.md to roadmap-legacy.md
  2. Delete milestones/ and re-run migration from roadmap.md
  3. Cancel and resolve manually

  (Choose 1, 2, or 3)
  ```
  Handle each choice and stop or continue accordingly.
- **D) Neither present** → nothing to migrate. Tell the user to run `/plan-product` and stop.

From here on, assume state A.

## Step 2: Read and parse roadmap.md

Read `agent-os/product/roadmap.md` and try to identify its sections. The upstream template typically has:

- `## Phase 1: MVP` — must-have features for launch
- `## Phase 2: Post-Launch` — planned future features

But users edit these freely, so also handle variations like:

- `## MVP`, `## Launch`, `## Now`
- `## Post-Launch`, `## Later`, `## Future`, `## Backlog`
- Arbitrary other phase names

Extract the bullet list items from each section you can identify. If the parsing is ambiguous, fall back to showing the user the raw file content and asking them to categorize it manually in Step 3.

Store the parsed result as:

- `PHASE_1_ITEMS` — list of bullet strings from the first phase / MVP section
- `PHASE_2_ITEMS` — list of bullet strings from any later phase / post-launch section (may be empty)

## Step 3: Confirm the interpretation with the user

Use `AskUserQuestion` to show the user what was parsed:

```
I read your roadmap.md and found:

Phase 1 (will become M1):
  - <PHASE_1_ITEMS item 1>
  - <PHASE_1_ITEMS item 2>
  ...

Phase 2 (will become M2):
  - <PHASE_2_ITEMS item 1>
  - <PHASE_2_ITEMS item 2>
  ...

Is this correct?

1. Yes, proceed with this split
2. No, let me adjust manually (I'll paste corrected lists)
3. Treat everything as M1 only (I'll decide M2 later)
4. Cancel

(Choose 1, 2, 3, or 4)
```

If option 2, ask for the corrected lists via `AskUserQuestion`.
If option 3, set `PHASE_2_ITEMS = []` and proceed.
If option 4, stop without writing anything.

## Step 4: Gather minimal metadata for M1

Use `AskUserQuestion`:

```
What is the slug for M1? (short, lowercase, hyphens, max 30 chars)

Default: "mvp"
```

Store as `M1_SLUG`.

Use `AskUserQuestion`:

```
What is the goal of M1-<M1_SLUG> in one or two sentences?

(If you're not sure, we can default to: "Deliver the features listed in
the original roadmap Phase 1.")
```

Store as `M1_GOAL`.

Use `AskUserQuestion` (skip if PHASE_2_ITEMS is empty):

```
What is the slug for M2? (short, lowercase, hyphens, max 30 chars)

Default: "post-launch"
```

Store as `M2_SLUG`.

Use `AskUserQuestion` (skip if PHASE_2_ITEMS is empty):

```
Should M2 be created now as a planned-but-inactive milestone, or only
created later when you actually get to it?

1. Create M2 now as status: inactive (visible but not active)
2. Skip M2, create it later with /plan-product --milestone

(Choose 1 or 2)
```

Store as `CREATE_M2_NOW` (boolean).

## Step 5: Detect existing specs and their likely milestone

Scan `agent-os/specs/` for existing spec folders. For each:

1. Does it have a `recap.md`? → already finished, skip for linking
2. Does it have a `shape.md` without a `## Milestone` section? → legacy spec, will be assigned to M1 by default since they predate milestones

Count these as `LEGACY_SPECS`. Do not modify them yet — we'll report what the user should do in Step 8.

## Step 6: Write the milestone structure

Create the following files and folders:

1. `agent-os/product/milestones/` (directory)

2. `agent-os/product/milestones/index.yml`:

```yaml
milestones:
  m1-<M1_SLUG>:
    status: active
    created_at: <ISO timestamp of this run>
    closed_at: null
    goal: <M1_GOAL>
  [if CREATE_M2_NOW:]
  m2-<M2_SLUG>:
    status: inactive
    created_at: <ISO timestamp of this run>
    closed_at: null
    goal: Deliver the features listed in the original roadmap Phase 2.
```

3. `agent-os/product/milestones/m1-<M1_SLUG>/goals.md`:

```markdown
# Milestone m1-<M1_SLUG>: Goals

## Goal

<M1_GOAL>

## Migrated from

This milestone was created by `/migrate-product` on <ISO date> from the
Phase 1 / MVP section of the original `roadmap.md`. The original file has
been preserved as `roadmap-legacy.md` for reference.
```

4. `agent-os/product/milestones/m1-<M1_SLUG>/scope.md`:

```markdown
# Milestone m1-<M1_SLUG>: Scope

## In scope

- <PHASE_1_ITEMS item 1>
- <PHASE_1_ITEMS item 2>
- ...

## Out of scope

Nothing explicitly excluded. See m2-<M2_SLUG> for planned post-launch work.
```

5. `agent-os/product/milestones/m1-<M1_SLUG>/specs.md`:

```markdown
# Milestone m1-<M1_SLUG>: Specs

Specs that belong to this milestone will be linked here automatically by `/finish-spec`.

(No specs linked yet. If you have legacy specs that belong here, you can
add them manually or let them get linked the next time you run
/finish-spec on them.)
```

6. If `CREATE_M2_NOW` is true, also create `m2-<M2_SLUG>/goals.md`, `scope.md`, and `specs.md` following the same structure, with `PHASE_2_ITEMS` in scope.

## Step 7: Archive the old roadmap

Rename `agent-os/product/roadmap.md` to `agent-os/product/roadmap-legacy.md`.

Do not delete it. The user may want to refer back to it, and the filename
change makes it obvious that it is no longer authoritative.

Add a header comment at the top of `roadmap-legacy.md`:

```markdown
<!--
This file was the original roadmap.md before /migrate-product ran on
<ISO date>. It is preserved for reference but is no longer read by any
Agent OS command.

The current roadmap lives in agent-os/product/milestones/.

See /help-flow for the current workflow.
-->

<original content>
```

## Step 8: Report and next steps

Print a summary:

```
✓ Migration complete.

Created:
  agent-os/product/milestones/index.yml
  agent-os/product/milestones/m1-<M1_SLUG>/goals.md
  agent-os/product/milestones/m1-<M1_SLUG>/scope.md
  agent-os/product/milestones/m1-<M1_SLUG>/specs.md
  [if CREATE_M2_NOW:]
  agent-os/product/milestones/m2-<M2_SLUG>/goals.md
  agent-os/product/milestones/m2-<M2_SLUG>/scope.md
  agent-os/product/milestones/m2-<M2_SLUG>/specs.md

Archived:
  agent-os/product/roadmap.md → agent-os/product/roadmap-legacy.md

Active milestone: m1-<M1_SLUG>

[if LEGACY_SPECS > 0:]
Note: <LEGACY_SPECS> existing spec(s) were found under agent-os/specs/.
They don't have a milestone assignment yet. Next time you run
/finish-spec on them (or if they were already finished, manually), you
can link them to m1-<M1_SLUG>.

Next step:

  /help-flow

This will show you the full workflow and confirm where you are now.

This migration command has now done its job. Re-running it on this
project will detect the local layout and exit without changes.
```

## Non-goals

This command explicitly does not:

- Modify specs, standards, or code.
- Delete the original roadmap.md (it is renamed, not deleted).
- Auto-link existing specs to milestones.
- Run any other Agent OS command.
- Commit anything to git.

It is a one-time, additive, reversible (via rename) restructuring of
`agent-os/product/` only.
