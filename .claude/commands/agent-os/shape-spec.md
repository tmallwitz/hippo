# Shape Spec

Gather context and structure planning for significant work. **Run this command while in plan mode.**

## Important Guidelines

- **Always use AskUserQuestion tool** when asking the user anything
- **Offer suggestions** — Present options the user can confirm, adjust, or correct
- **Keep it lightweight** — This is shaping, not exhaustive documentation

## Prerequisites

This command **must be run in plan mode**.

**Before proceeding, check if you are currently in plan mode.**

If NOT in plan mode, **stop immediately** and tell the user:

```
Shape-spec must be run in plan mode. Please enter plan mode first, then run /shape-spec again.
```
Do not proceed with any steps below until confirmed to be in plan mode.

## Precondition: Git clean state

This command assumes the repository is committed and clean before shaping begins. This is required so that `/finish-spec` can later compute a reliable diff between the spec's starting point and the final implementation.

1. Check that the current working directory is inside a git repository. If not, tell the user that Agent OS expects a git-tracked project and stop.

2. Run `git status --porcelain`. If the output is empty, the working tree is clean — continue.

3. If the working tree is dirty, use `AskUserQuestion` to ask the user how to proceed. Offer exactly these options:

    - **Commit now** — Show the user the output of `git status --short`, propose a commit message derived from the current changes (e.g. `"chore: pre-shape checkpoint before <proposed spec slug>"`), and let them edit it via `AskUserQuestion`. Then run `git add -A && git commit -m "<message>"`. Confirm the resulting commit SHA.
    - **Stash now** — Run `git stash push -u -m "pre-shape stash for <proposed spec slug>"`. Warn the user that the stash must be restored manually later and that `/finish-spec` will not see those changes as part of this spec.
    - **Continue anyway** — Proceed without cleaning. Warn the user explicitly that `/finish-spec` will not be able to compute a clean diff for this spec and that the base commit recorded below will be the last commit before any uncommitted changes.

4. After this step completes (or was skipped), record the base commit. Run `git rev-parse HEAD` and store the result as `BASE_SHA`. This SHA will be written into `shape.md` in the step that creates the spec folder.

## Process

### Step 1: Clarify What We're Building

Use AskUserQuestion to understand the scope:

```
What are we building? Please describe the feature or change.

(Be as specific as you like — I'll ask follow-up questions if needed)
```

Based on their response, ask 1-2 clarifying questions if the scope is unclear. Examples:
- "Is this a new feature or a change to existing functionality?"
- "What's the expected outcome when this is done?"
- "Are there any constraints or requirements I should know about?"

### Step 2: Gather Visuals

Use AskUserQuestion:

```
Do you have any visuals to reference?

- Mockups or wireframes
- Screenshots of similar features
- Examples from other apps

(Paste images, share file paths, or say "none")
```

If visuals are provided, note them for inclusion in the spec folder.

### Step 3: Identify Reference Implementations

Use AskUserQuestion:

```
Is there similar code in this codebase I should reference?

Examples:
- "The comments feature is similar to what we're building"
- "Look at how src/features/notifications/ handles real-time updates"
- "No existing references"

(Point me to files, folders, or features to study)
```

If references are provided, read and analyze them to inform the plan.

### Step 4: Check Product Context and Active Milestone

Check if `agent-os/product/` exists and contains files.

If it exists, read the key files:
- `mission.md`
- `tech-stack.md`
- `milestones/index.yml` (if present)

If `milestones/index.yml` exists, find the milestone with `status: active`. If there is exactly one active milestone, read its `goals.md` and `scope.md` and remember the milestone slug as `ACTIVE_MILESTONE`. If there are multiple active milestones, use AskUserQuestion to ask which one this spec belongs to. If there are none, set `ACTIVE_MILESTONE = null`.

Use AskUserQuestion:

```
I found product context in agent-os/product/. Should this feature align with any specific product goals or constraints?

Key points from your product docs:
- Mission: [summarize relevant points]
[If ACTIVE_MILESTONE is set:]
- Active milestone: {ACTIVE_MILESTONE}
  Goal: [summarize from goals.md]
  In scope: [summarize from scope.md]
  Out of scope: [summarize from scope.md]

(Confirm alignment, or note any adjustments. If this feature is out of scope
for the active milestone, say so now — we can still build it, but the spec
will be flagged.)
```

If the user confirms this spec is out of scope for the active milestone, remember this as `OUT_OF_SCOPE = true` and include a warning in `shape.md` later.

If no product folder exists, skip this step and set `ACTIVE_MILESTONE = null`, `OUT_OF_SCOPE = false`.

### Step 5: Surface Relevant Standards

Read `agent-os/standards/index.yml` to identify relevant standards based on the feature being built.

Use AskUserQuestion to confirm:

```
Based on what we're building, these standards may apply:

1. **api/response-format** — API response envelope structure
2. **api/error-handling** — Error codes and exception handling
3. **database/migrations** — Migration patterns

Should I include these in the spec? (yes / adjust: remove 3, add frontend/forms)
```

Read the confirmed standards files to include their content in the plan context.

### Step 6: Generate Spec Folder Name

Create a folder name using this format:
```
YYYY-MM-DD-HHMM-{feature-slug}/
```

Where:
- Date/time is current timestamp
- Feature slug is derived from the feature description (lowercase, hyphens, max 40 chars)

Example: `2026-01-15-1430-user-comment-system/`

**Note:** If `agent-os/specs/` doesn't exist, create it when saving the spec folder.

### Step 7: Structure the Plan

Now build the plan with **Task 1 always being "Save spec documentation"**.

Present this structure to the user:

```
Here's the plan structure. Task 1 saves all our shaping work before implementation begins.

---

## Task 1: Save Spec Documentation

Base commit recorded: <BASE_SHA>
[If ACTIVE_MILESTONE: "Milestone: {ACTIVE_MILESTONE}"]
[If OUT_OF_SCOPE: "⚠ Out of scope for active milestone"]

Create `agent-os/specs/{folder-name}/` with:

- **plan.md** — This full plan
- **shape.md** — Shaping notes (scope, decisions, context from our conversation)
- **standards.md** — Relevant standards that apply to this work
- **references.md** — Pointers to reference implementations studied
- **visuals/** — Any mockups or screenshots provided

## Task 2: [First implementation task]

[Description based on the feature]

## Task 3: [Next task]

...

---

Does this plan structure look right? I'll fill in the implementation tasks next.
```

### Step 8: Complete the Plan

After Task 1 is confirmed, continue building out the remaining implementation tasks based on:
- The feature scope from Step 1
- Patterns from reference implementations (Step 3)
- Constraints from standards (Step 5)

Each task should be specific and actionable.

### Step 9: Offer Standards Promotion from Shaping Decisions

Before finalizing the plan, review the architectural decisions that emerged during this shaping session. Often `/shape-spec` surfaces choices that would make good standards (e.g. "we decided all new endpoints use cursor pagination", "we decided to put background jobs in `src/jobs/` not `src/tasks/`").

1. List the shaping decisions you made during this session (from Steps 1-5). Keep it short — the top 1 to 3 decisions that feel like reusable rules, not one-offs.

2. For each candidate, use AskUserQuestion:

```
During shaping, we decided: "<decision>"

This looks like it could be a reusable rule for future work. Do you want to
promote it to a standard?

1. Yes, create a new standard now
2. No, this is spec-specific
3. Skip all remaining candidates

(Choose 1, 2, or 3)
```

3. If the user says "skip all remaining", stop offering for this session.

4. If the user says "yes", ask which domain folder (list existing subfolders of `agent-os/standards/` plus an "other" option) and draft a concise standard. Follow the concise-standards rules. Add frontmatter:

```
---
description: <one-line description>
auto_promoted_from: <spec folder name>
---
```

5. If any new standards were created, remind the user to run `/index-standards` before the next `/inject-standards` call, and include a note in `shape.md` listing which standards were promoted from this spec.

This step is deliberately placed **before** the plan is finalized, so that if a new standard is created, it can be included in `standards.md` for this very spec and immediately guide the implementation.

### Step 10: Ready for Execution

When the full plan is ready:

```
Plan complete. When you approve and execute:

1. Task 1 will save all spec documentation first
2. Then implementation tasks will proceed

Ready to start? (approve / adjust)
```

## Output Structure

The spec folder will contain:

```
agent-os/specs/{YYYY-MM-DD-HHMM-feature-slug}/
├── plan.md           # The full plan
├── shape.md          # Shaping decisions and context
├── standards.md      # Which standards apply and key points
├── references.md     # Pointers to similar code
└── visuals/          # Mockups, screenshots (if any)
```

## shape.md Content

The shape.md file should capture:

```markdown
# {Feature Name} — Shaping Notes

## Scope

[What we're building, from Step 1]

## Milestone

[If ACTIVE_MILESTONE is set: the milestone slug and its goal.
 If OUT_OF_SCOPE: add "⚠ This spec is out of scope for the active milestone."
 If no milestone: "No active milestone."]

## Decisions

- [Key decisions made during shaping]
- [Constraints or requirements noted]

## Context

- **Visuals:** [List of visuals provided, or "None"]
- **References:** [Code references studied]
- **Product alignment:** [Notes from product context, or "N/A"]

## Standards Applied

- api/response-format — [why it applies]
- api/error-handling — [why it applies]

## Standards Promoted from this Spec

[List any standards created during Step 9, or "None" if the user skipped promotion.]

## Implementation Base

base_commit: <BASE_SHA>
captured_at: <ISO timestamp of when /shape-spec ran>
captured_by: shape-spec
```

## standards.md Content

Include the full content of each relevant standard:

```markdown
# Standards for {Feature Name}

The following standards apply to this work.

---

## api/response-format

[Full content of the standard file]

---

## api/error-handling

[Full content of the standard file]
```

## references.md Content

```markdown
# References for {Feature Name}

## Similar Implementations

### {Reference 1 name}

- **Location:** `src/features/comments/`
- **Relevance:** [Why this is relevant]
- **Key patterns:** [What to borrow from this]

### {Reference 2 name}

...
```

## Tips

- **Keep shaping fast** — Don't over-document. Capture enough to start, refine as you build.
- **Visuals are optional** — Not every feature needs mockups.
- **Standards guide, not dictate** — They inform the plan but aren't always mandatory.
- **Specs are discoverable** — Months later, someone can find this spec and understand what was built and why.
- **Milestone awareness is opt-in** — If you haven't set up milestones via `/plan-product`, shape-spec still works exactly as before.
