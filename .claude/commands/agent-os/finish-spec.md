---
description: Close out an implemented spec by capturing deviations, bugfixes, and lessons learned. Reads git history, updates spec documentation, and creates a recap. Does NOT implement or orchestrate code changes.
---

# /finish-spec

Run this command **after** a spec has been implemented and any follow-up bugfixes are done. It reconciles the original plan with what was actually built, updates the spec documentation so it stays truthful, and creates a recap for future reference.

This command does not write application code. It only reads the git history and writes markdown files inside the spec folder and (optionally) under `agent-os/standards/` and `agent-os/product/milestones/`.

## Preconditions

- The current working directory is inside a git repository.
- There is at least one spec folder in `agent-os/specs/`.
- `git` is available on PATH.

If any precondition fails, stop and tell the user exactly what is missing. Do not attempt a fallback.

## Step 1: Select the spec to finish

1. List all folders in `agent-os/specs/` sorted by timestamp descending.
2. For each folder, read the first heading of `shape.md` (if present) to show a human-readable title next to the folder name.
3. Use `AskUserQuestion` to let the user pick which spec to finish. Default to the most recent one. Include an "other" option that lets the user paste a folder name directly.
4. Store the chosen path as `SPEC_DIR`.

## Step 2: Determine the implementation base commit

There are two paths depending on whether the spec was shaped with a Git-aware `/shape-spec`:

### Path A — spec has a recorded base commit (preferred)

1. Read `SPEC_DIR/shape.md` and look for a section `## Implementation Base` containing a line `base_commit: <sha>`.
2. If found, use that SHA as `BASE_SHA`. Verify it still exists in the repo via `git cat-file -e <BASE_SHA>`.
3. If the commit no longer exists (e.g. repo was rewritten), warn the user and fall through to Path B.

### Path B — legacy fallback (spec predates the Git-aware shape-spec)

1. Get the creation time of `SPEC_DIR` via `stat` (fallback: folder mtime).
2. Run `git log --before="<that timestamp>" -n 1 --format=%H` to get the last commit before the spec was created. Store as `BASE_SHA`.
3. Append a new section to `SPEC_DIR/shape.md`:
   ```
   ## Implementation Base

   base_commit: <BASE_SHA>
   captured_at: <ISO timestamp>
   captured_by: finish-spec (legacy fallback)
   ```
   This ensures re-runs of `/finish-spec` on the same spec are stable.

## Step 3: Collect the implementation diff

Run the following read-only git commands and keep their output in memory:

1. `git log --format="%h %s" <BASE_SHA>..HEAD` — list of commits since the base.
2. `git diff --stat <BASE_SHA>..HEAD` — file-level change summary.
3. `git diff <BASE_SHA>..HEAD` — full diff.

If the full diff exceeds roughly 2000 lines, do not load it entirely. Instead:

- Work from `git log` and `git diff --stat` as the overview.
- Read the full diff per file only for the top 10 most-changed files: `git diff <BASE_SHA>..HEAD -- <file>`.
- Mention to the user that the diff was large and that minor files were sampled.

Do not run any git command that writes. No checkout, no reset, no commit, no stash, no merge.

## Step 4: Reconcile plan vs. reality

1. Read `SPEC_DIR/plan.md` carefully. Identify the task list and the intended architecture.
2. Cross-reference the diff from Step 3 against the plan. Produce an internal list of:
   - **Matches** — tasks from the plan that were clearly implemented as described.
   - **Deviations** — things in the diff that differ from the plan (different approach, different file layout, different library, etc.).
   - **Additions** — things in the diff that were not in the plan at all (often bugfixes or follow-up refactors).
   - **Omissions** — tasks from the plan that have no corresponding change in the diff.
3. If any category is ambiguous and you cannot tell from the diff alone, use `AskUserQuestion` to ask targeted questions. Ask at most three questions in this step. Do not ask for information you can read from the diff yourself.

## Step 5: Update `shape.md` and `plan.md`

Append (do not overwrite) a new section to both files. Use the same section heading in both so they can be found easily.

### In `shape.md`, append:

```
## Deviations & Bugfixes

<ISO date of this run>

### What was built as planned
- <bullet list of matches, one line each>

### What was built differently
- <deviation>: <one-line reason>

### What was added beyond the plan
- <addition>: <one-line reason, e.g. "bugfix for X", "follow-up refactor">

### What was not built
- <omission>: <one-line reason, e.g. "deferred to next milestone", "turned out unnecessary">
```

### In `plan.md`, append the same section. Where possible, link each listed item back to the original task by its heading or number.

Keep both sections scan-friendly. One line per item. No prose paragraphs.

## Step 6: Create `recap.md`

Create a new file `SPEC_DIR/recap.md` with this structure:

```
# Recap: <spec title>

**Completed:** <ISO date of this run>
**Base commit:** <BASE_SHA>
**Final commit:** <current HEAD SHA>
**Milestone:** <milestone slug if linked in Step 8, else "unassigned">

## What this spec delivered
<2-4 sentences in plain language. What does the codebase do now that it didn't before?>

## Key decisions
- <the most important architectural or scoping decision, one line>
- <second one if any>
- <third one if any>

## Surprises and lessons
- <anything unexpected during implementation, one line each>

## Carry-over candidates
- <items that should be considered for the NEXT milestone, one line each>
- <leave empty if none>

## Files touched
<output of `git diff --stat <BASE_SHA>..HEAD`, trimmed to the top 20 files if longer>
```

If `recap.md` already exists, use `AskUserQuestion` to ask the user whether to overwrite it, append a new dated section, or abort.

The Milestone line will be updated in Step 8 once linking is confirmed.

## Step 7: Offer standards promotion

1. Review the "Key decisions" and "Surprises and lessons" from the recap you just wrote.
2. For each item that looks like a reusable rule (not a one-off), use `AskUserQuestion` to ask: "Should this become a standard in `agent-os/standards/`?"
   - Offer: yes / no / skip all remaining.
   - If yes, ask which domain folder (list existing subfolders of `agent-os/standards/` plus an "other" option that lets the user type a new folder name).
   - Create a new `.md` file in that folder with a concise standard. Follow the concise-standards style: lead with the rule, one code example if helpful, no prose padding.
   - Add frontmatter `auto_promoted_from: <SPEC_DIR>` so the origin is traceable.
3. If the user says "skip all remaining" at any point, move on immediately.
4. If any new standards were created, remember this for the final summary.

## Step 8: Link recap to milestone

1. Check whether `agent-os/product/milestones/` exists and contains at least one subfolder.
   - If not, skip this step and set `LINKED_MILESTONE = null`. Mention to the user once, as a gentle hint, that they can create milestones with `/plan-product` if they want to organize specs into phases.
2. Read `SPEC_DIR/shape.md` and look for a `## Milestone` section. If the spec was shaped with a known milestone, remember that slug as the default.
3. Use `AskUserQuestion` to let the user confirm or pick a different milestone. List all folders under `milestones/` and include a "none / skip" option. Default to the slug from `shape.md` if present.
4. If a milestone is chosen:
   - Append a line to `milestones/<chosen>/specs.md` (create the file if missing):
     ```
     - [<spec folder name>](../../../specs/<spec folder name>/recap.md) — <one-line summary from recap>
     ```
   - Update `recap.md` to replace the Milestone line with the actual slug.
   - Store the slug as `LINKED_MILESTONE`.
5. If the user chose "none / skip", set `LINKED_MILESTONE = null` and leave `recap.md` marked as unassigned.

## Step 9: Final summary

Print a short summary to the user:

- Spec folder that was finished
- Base commit and final commit SHAs
- Number of deviations, additions, omissions captured
- Whether a recap was created or updated
- Number of standards promoted (if any)
- Which milestone the spec was linked to (or "none")
- Reminder to run `/index-standards` if standards were promoted
- Reminder to run `/close-milestone` later when the milestone is done

Do not print the full content of the files that were written. The user can open them.

## Non-goals

This command explicitly does not:

- Run tests or linters.
- Create or push git commits.
- Modify source code outside `agent-os/`.
- Decide on its own whether a bug is "really fixed".
- Orchestrate subagents or spawn parallel tasks.

It is a pure documentation and reflection step.
