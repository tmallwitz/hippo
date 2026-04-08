# Help Flow

Show the user the canonical Agent OS workflow and detect where they currently are in it. Recommend the next step based on the project's current state.

This command is a compass, not an autopilot. It reads files, diagnoses state, explains what it sees, and suggests a next step. It never runs another command on its own.

## Preconditions

- None. This command works even in an empty directory. If Agent OS is not yet set up, it says so and suggests how to start.

## Process

### Step 1: Print the canonical flow

Always start by printing the reference workflow, regardless of current state. The user needs the mental model before the diagnosis makes sense.

```
Agent OS — Canonical Flow (tmallwitz local)

┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  1. /plan-product                                                       │
│     Create mission, tech stack, and first milestone (M1).               │
│                                                                         │
│  2. /discover-standards  [optional, interactive]                        │
│     /discover-standards --auto  [optional, for vibe-coded codebases]    │
│     Extract patterns from existing code into agent-os/standards/.       │
│                                                                         │
│  3. /shape-spec  [in Plan Mode, git clean]                              │
│     Shape a feature. Reads active milestone, checks scope,              │
│     surfaces standards, records base commit, offers to promote          │
│     shaping decisions to standards.                                     │
│                                                                         │
│  4. [implement]                                                         │
│     Claude Code (or you) executes the plan. Bugfixes happen.            │
│                                                                         │
│  5. /finish-spec                                                        │
│     Diff base commit against HEAD. Update shape.md and plan.md          │
│     with deviations. Write recap.md. Offer standards promotion.         │
│     Link recap to active milestone.                                     │
│                                                                         │
│  6. Repeat 3-5 for every feature in this milestone.                     │
│                                                                         │
│  7. /close-milestone                                                    │
│     Aggregate all spec recaps. Capture goal-achievement reflection.     │
│     Collect carry-over for next milestone. Set status: closed.          │
│                                                                         │
│  8. /plan-product --milestone                                           │
│     Plan M(n+1), defaulting to the carry-over from the closed M(n).    │
│     Goto step 3.                                                        │
│                                                                         │
│  Anytime:                                                               │
│  - /inject-standards              Read standards into context            │
│  - /index-standards               Rebuild index, see review backlog      │
│  - /help-flow                     This command                           │
│  - /migrate-product               One-time migration from legacy         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Step 2: Detect the current state

Run the following checks in order. Each check either passes (continue) or triggers a specific diagnosis (jump to Step 3 with the matching case).

#### Check 1: Is this a git repository?

Run `git rev-parse --is-inside-work-tree`.

- **No** → Diagnosis case `NO_GIT`. Jump to Step 3.
- **Yes** → continue.

#### Check 2: Does `agent-os/` exist?

Check for the directory `agent-os/`.

- **No** → Diagnosis case `NO_AGENT_OS`. Jump to Step 3.
- **Yes** → continue.

#### Check 3: Does `agent-os/product/mission.md` exist?

- **No** → Diagnosis case `NO_PRODUCT`. Jump to Step 3.
- **Yes** → continue.

#### Check 4: Legacy detection — is there an old `roadmap.md`?

Check for `agent-os/product/roadmap.md` (upstream layout) combined with no `agent-os/product/milestones/` folder.

- **Yes (legacy layout detected)** → Diagnosis case `LEGACY_LAYOUT`. Jump to Step 3.
- **No** → continue.

#### Check 5: Is there a milestone structure?

Check for `agent-os/product/milestones/index.yml`.

- **No** → Diagnosis case `NO_MILESTONES`. Jump to Step 3.
- **Yes** → continue. Read `index.yml` into memory.

#### Check 6: Is there an active milestone?

Scan the parsed `index.yml` for entries with `status: active`.

- **Zero active milestones** → Diagnosis case `ALL_MILESTONES_CLOSED`. Jump to Step 3.
- **More than one active milestone** → Diagnosis case `MULTIPLE_ACTIVE`. Jump to Step 3. (This is unusual but allowed; the user was warned when creating the second one.)
- **Exactly one active milestone** → store its slug as `ACTIVE_SLUG` and continue.

#### Check 7: Are there unfinished specs?

Scan `agent-os/specs/` for folders. For each folder:

- Does it have a `recap.md`? If yes, consider it finished.
- Does it have a `plan.md` but no `recap.md`? It is unfinished. Check its `shape.md` for the `Implementation Base` section to get the `base_commit`. If present, check via `git log --format=%H <base_commit>..HEAD` whether any commits exist since that base. Any commits means implementation has started.

Categorize each unfinished spec:

- **Not started** — no commits since base_commit (or base_commit missing)
- **In progress** — commits exist since base_commit
- **Ready to finish** — user should run `/finish-spec` (we can't distinguish this from "in progress" from the outside, so we group them together under "in progress")

Store counts as `SPECS_UNSTARTED`, `SPECS_IN_PROGRESS`.

#### Check 8: Is the working tree clean?

Run `git status --porcelain`.

- **Empty output** → `CLEAN = true`
- **Non-empty** → `CLEAN = false`, remember the number of modified files

#### Check 9: Are there specs linked to the active milestone without recaps?

Read `agent-os/product/milestones/<ACTIVE_SLUG>/specs.md` and check whether each linked spec has a `recap.md`. This catches the case where the user started finishing specs but stopped midway.

Store count as `UNRECAPPED_LINKED`.

#### Check 10: Are there standards needing review?

Grep all files in `agent-os/standards/` for `needs_review: true` in frontmatter. Count matches as `NEEDS_REVIEW_COUNT`.

#### Check 11: Is the current milestone "done-ish"?

Count the specs linked to the active milestone in its `specs.md`. If the count is greater than zero AND all linked specs have `recap.md` files AND there are no unfinished specs elsewhere in `agent-os/specs/` that were created after the milestone became active, then the milestone could plausibly be closed.

Store as boolean `MILESTONE_READY_TO_CLOSE`.

### Step 3: Print the diagnosis and next step

Based on the diagnosis case or the combined state from checks 7-11, print one of the following blocks.

---

#### Case `NO_GIT`

```
━━━ Where you are ━━━

This directory is not a git repository. Agent OS relies on git for
/shape-spec and /finish-spec to track base commits and diffs.

━━━ Next step ━━━

  git init
  git add .
  git commit -m "initial commit"

Then run /help-flow again.
```

---

#### Case `NO_AGENT_OS`

```
━━━ Where you are ━━━

No agent-os/ folder found in this project. Agent OS is not set up here yet.

━━━ Next step ━━━

  /plan-product

This will create the base product documentation and your first milestone.

If this is an existing codebase with patterns worth documenting, you may
also want to run /discover-standards (or /discover-standards --auto for a
quick non-interactive pass) either before or after /plan-product.
```

---

#### Case `NO_PRODUCT`

```
━━━ Where you are ━━━

agent-os/ exists but agent-os/product/mission.md is missing. The product
is not defined yet.

━━━ Next step ━━━

  /plan-product

This is the starting point of the workflow. Everything downstream
(shaping, finishing, closing milestones) reads from this.
```

---

#### Case `LEGACY_LAYOUT`

```
━━━ Where you are ━━━

This project uses the upstream Agent OS layout (roadmap.md, no milestones/
folder). The local workflow uses iterative milestones instead of a flat
roadmap.

━━━ Next step ━━━

  /migrate-product

This is a one-time migration that converts roadmap.md into a first
milestone (M1) and optionally creates M2 from the post-launch items. It
does not touch your specs, standards, or code.

After migration, the rest of the workflow works normally.
```

---

#### Case `NO_MILESTONES`

```
━━━ Where you are ━━━

mission.md exists but there is no milestones/ folder. This is unusual for
the local layout — it means /plan-product was interrupted or was run with
an older version.

━━━ Next step ━━━

  /plan-product

Choose "Update specific files" if you want to keep your mission and tech
stack as-is, and just create M1.
```

---

#### Case `ALL_MILESTONES_CLOSED`

```
━━━ Where you are ━━━

All milestones are closed. No active milestone. You are between phases.

━━━ Next step ━━━

  /plan-product --milestone

This will create the next milestone. If the most recently closed milestone
has carry-over items, they will be offered as defaults.
```

---

#### Case `MULTIPLE_ACTIVE`

```
━━━ Where you are ━━━

Multiple milestones are marked active at once:

  <list active slugs>

This is legal but unusual. /shape-spec will ask you which one a new spec
belongs to, every single time.

━━━ Next step ━━━

Consider closing one of them with /close-milestone before shaping more
specs, to keep the flow clean.

Otherwise, continue with /shape-spec as normal.
```

---

#### Default case: single active milestone, combine the signals

If none of the above cases matched, we have a healthy project with an
active milestone. Now combine the counts from checks 7-11 to give a
precise recommendation.

Decide which single next step is most important, using this priority
order (first match wins):

1. **UNRECAPPED_LINKED > 0** — There are specs linked to the milestone
   without recaps. These are the highest priority because they leave the
   milestone in an inconsistent state.

   ```
   ━━━ Where you are ━━━

   Active milestone: <ACTIVE_SLUG>
   Specs linked to this milestone without a recap: <UNRECAPPED_LINKED>

   Someone (probably you) started finishing specs but didn't complete the
   linking step. These specs have code but no recap.md yet.

   ━━━ Next step ━━━

     /finish-spec

   Pick each of the unrecapped specs and complete the finish step. You
   can run /finish-spec multiple times, once per spec.
   ```

2. **SPECS_IN_PROGRESS > 0** — There is code written for a spec that is
   not yet finished.

   ```
   ━━━ Where you are ━━━

   Active milestone: <ACTIVE_SLUG>
   Specs with commits since their base commit: <SPECS_IN_PROGRESS>
     <list spec folder names>

   Implementation is in flight. Either you are still building, or the
   implementation is done and the spec needs to be finished.

   ━━━ Next step ━━━

   If implementation is done (including bugfixes):

     /finish-spec

   If implementation is still in flight, keep building. No Agent OS
   command needed.
   ```

3. **SPECS_UNSTARTED > 0** — There is at least one spec folder with a
   plan but no commits yet.

   ```
   ━━━ Where you are ━━━

   Active milestone: <ACTIVE_SLUG>
   Specs with a plan but no commits yet: <SPECS_UNSTARTED>
     <list spec folder names>

   A feature was shaped but implementation hasn't started. You are
   either about to start, or this spec is on hold.

   ━━━ Next step ━━━

   Start implementing the plan. Claude Code can execute plan.md
   directly.

   When implementation and bugfixes are done:

     /finish-spec
   ```

4. **MILESTONE_READY_TO_CLOSE = true** — The active milestone has specs
   and all of them are recapped, and there's nothing unfinished
   elsewhere.

   ```
   ━━━ Where you are ━━━

   Active milestone: <ACTIVE_SLUG>
   Specs delivered and recapped: <count>
   No unfinished specs.

   This milestone looks ready to close.

   ━━━ Next step ━━━

     /close-milestone

   This aggregates all spec recaps, asks you for a goal-achievement
   reflection, and captures carry-over items for the next milestone.

   After closing, run /plan-product --milestone to start the next one.
   ```

5. **CLEAN = true and none of the above** — Everything is quiet. The
   milestone is active but has no open specs. Time to shape a new
   feature.

   ```
   ━━━ Where you are ━━━

   Active milestone: <ACTIVE_SLUG>
   No specs in flight. Working tree clean.

   Ready to shape the next feature.

   ━━━ Next step ━━━

     [enter plan mode]
     /shape-spec
   ```

6. **CLEAN = false and none of the above** — Dirty working tree with no
   active spec.

   ```
   ━━━ Where you are ━━━

   Active milestone: <ACTIVE_SLUG>
   No specs in flight, but the working tree has <N> modified files.

   This is an ambiguous state. Either:
   - You are editing code that isn't part of any shaped spec
   - You forgot to commit after a previous spec finished

   ━━━ Next step ━━━

   Decide what the uncommitted changes are:

   - If this is a planned change: enter plan mode and run /shape-spec.
     It will offer to commit or stash your changes before shaping.

   - If this is leftover from the last feature: commit it directly with
     git, then optionally run /finish-spec again on the most recent spec
     if the changes belong there.
   ```

### Step 4: Always append the standards-review footer

Regardless of which case above triggered, if `NEEDS_REVIEW_COUNT > 0`,
append this block at the very end:

```
━━━ Standards review backlog ━━━

<NEEDS_REVIEW_COUNT> standards are marked needs_review: true.

These were likely generated by /discover-standards --auto or auto-promoted
from spec shaping. They are active and injectable but have never been
reviewed by you.

To see which ones:

  /index-standards

To review them one by one:

  /discover-standards
```

This is informational. The user does not need to act on it immediately.

### Step 5: Done

Do not run any other commands. Do not write files. Do not take action.
The user reads the diagnosis and decides.

## Non-goals

This command explicitly does not:

- Run any other Agent OS command automatically.
- Modify any files.
- Make git commits or any other state changes.
- Guess the user's intent beyond what the filesystem state allows.

It is a pure read-only diagnostic and reference.
