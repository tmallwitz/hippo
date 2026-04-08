# Close Milestone

Close out a milestone by aggregating its spec recaps into a milestone recap, updating its status, and preparing carry-over items for the next milestone.

This command does not run tests, build anything, or execute tasks. It only reads spec recaps and writes markdown files inside `agent-os/product/milestones/`.

## Preconditions

- `agent-os/product/milestones/` exists and contains at least one milestone folder.
- `agent-os/product/milestones/index.yml` exists.

If any precondition fails, tell the user:

```
No milestones found. Run /plan-product to create your first milestone.
```

and stop.

## Step 1: Select the milestone to close

1. Read `agent-os/product/milestones/index.yml`.
2. Filter for milestones with `status: active`.
3. If there is exactly one active milestone, propose it as the default.
4. Use `AskUserQuestion` to let the user pick which milestone to close. Include all active milestones and a "cancel" option.
5. Store the chosen slug as `MILESTONE_SLUG`. The folder is `agent-os/product/milestones/<MILESTONE_SLUG>/`.

## Step 2: Verify the milestone has specs

1. Read `agent-os/product/milestones/<MILESTONE_SLUG>/specs.md`.
2. Count the number of spec links.
3. If there are zero specs, use `AskUserQuestion`:

```
Milestone <MILESTONE_SLUG> has no specs linked to it. Closing it now would
create an empty recap.

How do you want to proceed?

1. Close it anyway (the recap will note that no specs were delivered)
2. Cancel and link specs first with /finish-spec

(Choose 1 or 2)
```

## Step 3: Check that all linked specs have recaps

1. For each spec link in `specs.md`, check whether the linked `recap.md` file exists.
2. Collect a list of specs that are linked but have no recap.
3. If any are missing, use `AskUserQuestion`:

```
The following specs are linked to this milestone but have no recap.md:

- <spec folder 1>
- <spec folder 2>

They were probably not finished with /finish-spec.

How do you want to proceed?

1. Cancel and run /finish-spec on them first (recommended)
2. Close the milestone anyway (these specs will be listed as "no recap available")

(Choose 1 or 2)
```

## Step 4: Aggregate spec recaps

For each spec that has a `recap.md`:

1. Read the recap.
2. Extract:
   - The spec title (from the first heading)
   - The "What this spec delivered" paragraph
   - The "Key decisions" bullets
   - The "Surprises and lessons" bullets
   - The "Carry-over candidates" bullets

Keep them in memory grouped by spec folder name.

## Step 5: Gather closing reflection from the user

Use `AskUserQuestion`:

```
Before writing the milestone recap, a few reflection questions.

**Did this milestone achieve its original goal?**

(Yes / Partially / No — and a one-line explanation)
```

After they respond, use `AskUserQuestion`:

```
**What is the single most important thing you learned during this milestone?**

(One or two sentences. This goes to the top of the milestone recap.)
```

After they respond, use `AskUserQuestion`:

```
**Are there any carry-over items you want to flag for the next milestone?**

The following carry-over candidates were collected from individual spec recaps:

- <candidate 1> (from <spec folder>)
- <candidate 2> (from <spec folder>)
- ...

Which of these should move to the next milestone?

1. All of them
2. Pick specific ones (list numbers)
3. None (handled already)
4. Add new ones not in the list above

(Choose one or combine: e.g. "pick 1, 3, 4, and add: rewrite auth middleware")
```

Remember the final carry-over list as `CARRY_OVER`.

## Step 6: Write the milestone recap

Create `agent-os/product/milestones/<MILESTONE_SLUG>/recap.md`:

```markdown
# Recap: <MILESTONE_SLUG>

**Closed:** <ISO date of this run>
**Status:** closed
**Specs delivered:** <count>

## Goal achievement

<answer from Step 5, one of: "Achieved" / "Partially achieved" / "Not achieved">

<one-line explanation from the user>

## Biggest lesson

<the reflection answer from Step 5>

## Specs delivered

[For each spec with a recap:]

### <spec folder name>

<"What this spec delivered" paragraph from the spec recap>

**Key decisions:**
- <decision 1>
- <decision 2>

[If Step 3 had specs without recaps, include a subsection:]

### Specs without recap

- <spec folder name 1>
- <spec folder name 2>

(These specs were linked to the milestone but were never finished with
/finish-spec. Their contributions are not reflected in this recap.)

## Carry-over to next milestone

[If CARRY_OVER is empty:]
None. This milestone closed cleanly.

[If CARRY_OVER has items:]
- <item 1>
- <item 2>
- <item 3>

(These items will be surfaced automatically when you run
`/plan-product --milestone` next.)

## Timeline

- Created: <created_at from index.yml>
- Closed: <ISO date of this run>
- Duration: <difference in days>
```

## Step 7: Update `milestones/index.yml`

Update the entry for `<MILESTONE_SLUG>`:

```yaml
milestones:
  <MILESTONE_SLUG>:
    status: closed
    created_at: <unchanged>
    closed_at: <ISO timestamp of this run>
    goal: <unchanged>
    specs_delivered: <count>
    carry_over:
      - <item 1>
      - <item 2>
```

The `carry_over` list will be read by `/plan-product --milestone` when the next milestone is created.

## Step 8: Final summary

Print a short summary to the user:

```
✓ Milestone <MILESTONE_SLUG> closed.

  Specs delivered: <count>
  Goal achievement: <Achieved / Partially / Not achieved>
  Carry-over items: <count>

Recap written to:
  agent-os/product/milestones/<MILESTONE_SLUG>/recap.md

Next step: when you are ready to plan the next milestone, run:
  /plan-product --milestone

The carry-over items from this milestone will be offered as defaults.
```

## Non-goals

This command explicitly does not:

- Run tests, linters, or builds.
- Create git commits or tags.
- Rebase, merge, or modify branches.
- Modify source code.
- Auto-plan the next milestone (that's `/plan-product --milestone`).

It is a pure reflection and archival step.
