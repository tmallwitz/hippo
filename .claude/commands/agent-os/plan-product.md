# Plan Product

Establish foundational product documentation through an interactive conversation. Creates mission, tech stack, and milestone files in `agent-os/product/`.

## Important Guidelines

- **Always use AskUserQuestion tool** when asking the user anything
- **Keep it lightweight** — gather enough to create useful docs without over-documenting
- **One question at a time** — don't overwhelm with multiple questions

## Modes

This command runs in two modes:

- **New product (default)** — `/plan-product`
  Creates `mission.md`, `tech-stack.md`, and the first milestone (`m1-mvp/`) interactively. Use this when starting a new product or when no product documentation exists yet.

- **New milestone** — `/plan-product --milestone`
  Assumes `mission.md` and `tech-stack.md` already exist. Creates a new milestone folder (`m2-...`, `m3-...`, etc.) that builds on the previous ones. Use this after a milestone is closed with `/close-milestone` and you want to plan the next phase.

## Process

### Step 0: Mode detection

1. Check whether the command was invoked with `--milestone`.
2. If `--milestone` is present, set `MODE = new-milestone` and jump to the "New milestone" section below.
3. If not, set `MODE = new-product` and continue with Step 1.

---

## New product mode

### Step 1: Check for Existing Product Docs

Check if `agent-os/product/` exists and contains any of these files or folders:
- `mission.md`
- `tech-stack.md`
- `milestones/` (folder)

**If any exist**, use AskUserQuestion:

```
I found existing product documentation:
- mission.md: [exists/missing]
- tech-stack.md: [exists/missing]
- milestones/: [exists/missing]

Would you like to:
1. Start fresh (replace all, including milestones)
2. Update specific files (mission and/or tech-stack only)
3. Add a new milestone instead (switch to --milestone mode)
4. Cancel

(Choose 1, 2, 3, or 4)
```

If option 2, ask which files to update and only gather info for those.
If option 3, switch `MODE = new-milestone` and jump to the "New milestone" section.
If option 4, stop here.

**If no files exist**, proceed to Step 2.

### Step 2: Gather Product Vision (for mission.md)

Use AskUserQuestion:

```
Let's define your product's mission.

**What problem does this product solve?**

(Describe the core problem or pain point you're addressing)
```

After they respond, use AskUserQuestion:

```
**Who is this product for?**

(Describe your target users or audience)
```

After they respond, use AskUserQuestion:

```
**What makes your solution unique?**

(What's the key differentiator or approach?)
```

### Step 3: Establish Tech Stack (for tech-stack.md)

First, check if `agent-os/standards/global/tech-stack.md` exists.

**If the tech-stack standard exists**, read it and use AskUserQuestion:

```
I found a tech stack standard in your standards:

[Summarize the key technologies from global/tech-stack.md]

Does this project use the same tech stack, or does it differ?

1. Same as standard (use as-is)
2. Different (I'll specify)

(Choose 1 or 2)
```

If they choose option 1, use the standard's content for tech-stack.md.
If they choose option 2, proceed to ask them to specify (see below).

**If no tech-stack standard exists** (or they chose option 2 above), use AskUserQuestion:

```
**What technologies does this project use?**

Please describe your tech stack:
- Frontend: (e.g., React, Vue, vanilla JS, or N/A)
- Backend: (e.g., Rails, Node, Django, or N/A)
- Database: (e.g., PostgreSQL, MongoDB, or N/A)
- Other: (hosting, APIs, tools, etc.)
```

### Step 4: Define the First Milestone (M1)

Every product starts with at least one milestone. For a new product this is typically the MVP, but you can name it anything.

Use AskUserQuestion:

```
Now let's plan your first milestone.

**What is the name of this milestone?**

Default: "mvp" (will become m1-mvp/)

(Give a short slug, lowercase, hyphens, max 30 chars)
```

After they respond, use AskUserQuestion:

```
**What is the goal of milestone m1-{slug}?**

(One or two sentences: what does "done" look like for this milestone?)
```

After they respond, use AskUserQuestion:

```
**What is in scope for m1-{slug}?**

(List the must-have features or capabilities for this milestone to be considered complete)
```

After they respond, use AskUserQuestion:

```
**What is explicitly out of scope for m1-{slug}?**

(List things you are deliberately NOT doing in this milestone. Say "none" if everything is open.)
```

### Step 5: Generate Files

Create the `agent-os/product/` directory and `agent-os/product/milestones/` subdirectory if they don't exist.

Generate the following files:

#### mission.md

```markdown
# Product Mission

## Problem

[Insert what problem this product solves - from Step 2]

## Target Users

[Insert who this product is for - from Step 2]

## Solution

[Insert what makes the solution unique - from Step 2]
```

#### tech-stack.md

```markdown
# Tech Stack

## Frontend

[Frontend technologies, or "N/A" if not applicable]

## Backend

[Backend technologies, or "N/A" if not applicable]

## Database

[Database choice, or "N/A" if not applicable]

## Other

[Other tools, hosting, services - or omit this section if nothing mentioned]
```

#### milestones/index.yml

```yaml
milestones:
  m1-{slug}:
    status: active
    created_at: <ISO timestamp>
    closed_at: null
    goal: <one-line summary from Step 4>
```

#### milestones/m1-{slug}/goals.md

```markdown
# Milestone m1-{slug}: Goals

## Goal

[Full goal statement from Step 4]

## Why this milestone

[If the user provided context about why this comes first, include it here. Otherwise omit this section.]
```

#### milestones/m1-{slug}/scope.md

```markdown
# Milestone m1-{slug}: Scope

## In scope

[Bullet list from Step 4]

## Out of scope

[Bullet list from Step 4, or "Nothing explicitly excluded."]
```

#### milestones/m1-{slug}/specs.md

```markdown
# Milestone m1-{slug}: Specs

Specs that belong to this milestone will be linked here automatically by `/finish-spec`.

(No specs linked yet.)
```

### Step 6: Confirm Completion

After creating all files, output to user:

```
✓ Product documentation created:

  agent-os/product/mission.md
  agent-os/product/tech-stack.md
  agent-os/product/milestones/index.yml
  agent-os/product/milestones/m1-{slug}/goals.md
  agent-os/product/milestones/m1-{slug}/scope.md
  agent-os/product/milestones/m1-{slug}/specs.md

Milestone m1-{slug} is now active. Start shaping features for it with /shape-spec.
When the milestone is done, close it with /close-milestone and plan the next one
with /plan-product --milestone.
```

---

## New milestone mode

### Step M1: Preconditions

1. Check that `agent-os/product/mission.md` exists. If not, tell the user:
   ```
   No mission.md found. Run /plan-product first to create the base product documentation.
   ```
   and stop.

2. Check that `agent-os/product/milestones/index.yml` exists. If not, create an empty one:
   ```yaml
   milestones: {}
   ```
   and warn the user that no prior milestones were found — this new one will be `m1`.

3. Read `milestones/index.yml` and determine the highest existing milestone number. The new milestone will be `m<N+1>`.

### Step M2: Check for Open Milestones

If there are any milestones with `status: active` in `index.yml`, use AskUserQuestion:

```
Milestone m{N}-{slug} is still marked as active. You should usually close it
with /close-milestone before starting a new one.

How do you want to proceed?

1. Stop here and run /close-milestone first (recommended)
2. Create the new milestone anyway (both will be active in parallel)
3. Cancel

(Choose 1, 2, or 3)
```

Respect the user's choice.

### Step M3: Read Prior Context

1. Read `mission.md` to remind yourself of the product goal.
2. If the previous milestone has a `recap.md` (written by `/close-milestone`), read it. It contains lessons learned and carry-over items.
3. For any carry-over items flagged in the previous recap, keep them in mind for the scoping questions below.

### Step M4: Gather New Milestone Details

Use AskUserQuestion:

```
Let's plan milestone m{N+1}.

**What is the name of this milestone?**

(Short slug, lowercase, hyphens, max 30 chars. Examples: "uk-launch",
"performance", "auth-v2")
```

After they respond, use AskUserQuestion. If the previous recap had carry-over items, include them in the prompt:

```
**What is the goal of m{N+1}-{slug}?**

[If carry-over items exist:]
Note: the previous milestone (m{N}-{prev-slug}) flagged these items for
follow-up:
- <carry-over item 1>
- <carry-over item 2>

(One or two sentences: what does "done" look like for this milestone?
Feel free to include or reject the carry-over items.)
```

After they respond, use AskUserQuestion:

```
**What is in scope for m{N+1}-{slug}?**

(List the must-have features or capabilities.)
```

After they respond, use AskUserQuestion:

```
**What is explicitly out of scope for m{N+1}-{slug}?**

(List things you are deliberately NOT doing. Say "none" if everything is open.)
```

### Step M5: Generate the New Milestone Files

1. Create `agent-os/product/milestones/m{N+1}-{slug}/`.

2. Write `goals.md`:

```markdown
# Milestone m{N+1}-{slug}: Goals

## Goal

[Full goal statement from Step M4]

## Carry-over from previous milestone

[If any carry-over items were accepted, list them here. Otherwise omit this section.]

## Builds on

- m{N}-{prev-slug} (closed <date>)
- [Any earlier milestones if relevant]
```

3. Write `scope.md`:

```markdown
# Milestone m{N+1}-{slug}: Scope

## In scope

[Bullet list from Step M4]

## Out of scope

[Bullet list from Step M4, or "Nothing explicitly excluded."]
```

4. Write `specs.md`:

```markdown
# Milestone m{N+1}-{slug}: Specs

Specs that belong to this milestone will be linked here automatically by `/finish-spec`.

(No specs linked yet.)
```

5. Update `milestones/index.yml` to add the new milestone:

```yaml
milestones:
  m1-{first-slug}:
    status: closed
    ...
  m{N+1}-{slug}:
    status: active
    created_at: <ISO timestamp>
    closed_at: null
    goal: <one-line summary from Step M4>
```

### Step M6: Confirm Completion

```
✓ Milestone m{N+1}-{slug} created:

  agent-os/product/milestones/m{N+1}-{slug}/goals.md
  agent-os/product/milestones/m{N+1}-{slug}/scope.md
  agent-os/product/milestones/m{N+1}-{slug}/specs.md

  agent-os/product/milestones/index.yml updated

This milestone is now active. Start shaping features for it with /shape-spec.
```

---

## Tips

- If the user provides very brief answers, that's fine — the docs can be expanded later
- The `/shape-spec` command will read `mission.md` and (when milestones exist) the currently active milestone's `goals.md` and `scope.md` for context
- Milestones let you plan iteratively. Don't try to plan everything up front — plan M1, build it, close it, learn, then plan M2.
- A milestone slug is just a label. Use whatever makes sense: "mvp", "beta", "uk-launch", "perf-pass", "auth-rewrite", etc.
