# Discover Standards

Extract tribal knowledge from your codebase into concise, documented standards.

## Important Guidelines

- **Always use AskUserQuestion tool** when asking the user anything (interactive mode only)
- **Write concise standards** — Use minimal words. Standards must be scannable by AI agents without bloating context windows.
- **Offer suggestions** — Present options the user can confirm, choose between, or correct. Don't make them think harder than necessary.

## Modes

This command runs in two modes:

- **Interactive (default)** — `/discover-standards [area]`
  Analyze the codebase, then ask the user to confirm, name, and scope each discovered pattern via `AskUserQuestion`. Use this when you have context on the code and want high-quality, well-named standards.

- **Auto** — `/discover-standards --auto [area]`
  Analyze the codebase and generate standards non-interactively. Each generated standard is marked with `auto_generated: true` and `needs_review: true` in its frontmatter. Use this after vibe-coding sessions, for initial greenfield extractions, or when you want a first pass without interruption. Review the results later with a normal `/discover-standards` run, or let `/finish-spec` promote individual decisions into reviewed standards.

## Process

### Step 0: Mode Detection

1. Check whether the command was invoked with `--auto`.
2. If `--auto` is present, set `AUTO_MODE = true` and skip all `AskUserQuestion` calls throughout this command. Substitute the defaults described in each step.
3. If not, set `AUTO_MODE = false` and run the command interactively as described.

### Step 1: Determine Focus Area

Check if the user specified an area when running this command. If they did, skip to Step 2.

If no area was specified:

1. Analyze the codebase structure (folders, file types, patterns)
2. Identify 3-5 major areas. Examples:
   - **Frontend areas:** UI components, styling/CSS, state management, forms, routing
   - **Backend areas:** API routes, database/models, authentication, background jobs
   - **Cross-cutting:** Error handling, validation, testing, naming conventions, file structure

**Interactive mode:** use AskUserQuestion to present the areas:

```
I've identified these areas in your codebase:

1. **API Routes** (src/api/) — Request handling, response formats
2. **Database** (src/models/, src/db/) — Models, queries, migrations
3. **React Components** (src/components/) — UI patterns, props, state
4. **Authentication** (src/auth/) — Login, sessions, permissions

Which area should we focus on for discovering standards? (Pick one, or suggest a different area)
```

Wait for user response before proceeding.

**Auto mode:** do not ask. Process **all** identified areas sequentially, one after the other. Exclude `node_modules`, `.git`, `dist`, `build`, `.next`, `venv`, `.venv`, `__pycache__`, `target`, `vendor`, `agent-os`, and any folder listed in `.gitignore`.

### Step 2: Analyze the Area

Once an area is determined:

1. Read key files in that area (5-10 representative files)
2. Look for patterns that are:
   - **Unusual or unconventional** — Not standard framework/library patterns
   - **Opinionated** — Specific choices that could have gone differently
   - **Tribal** — Things a new developer wouldn't know without being told
   - **Consistent** — Patterns repeated across multiple files

**Interactive mode:** use AskUserQuestion to present findings:

```
I analyzed [area] and found these potential standards worth documenting:

1. **API Response Envelope** — All responses use { success, data, error } structure
2. **Error Codes** — Custom error codes like AUTH_001, DB_002 with specific meanings
3. **Pagination Pattern** — Cursor-based pagination with consistent param names

Would you like to document any of these? You can also suggest other standards for this area.

Options:
- "Yes, all of them"
- "Just 1 and 3"
- "Add: [your suggestion]"
- "Skip this area"
```

**Auto mode:** apply a worth-documenting threshold. Only document a pattern if:

- It appears in **at least 3 distinct files**, OR
- It is a clearly-intentional architectural choice (a dependency injection container, a custom base class used throughout, a consistent error envelope, a shared middleware stack, etc.)

Skip one-off occurrences. Skip patterns that are pure framework defaults (e.g. "uses FastAPI decorators" is not a standard worth documenting; "uses FastAPI dependencies for tenant scoping on every route" is).

### Step 3: Deep Dive on Each Standard

**Interactive mode:** For each standard the user wants to document, ask 1-2 targeted questions to understand the reasoning. Use AskUserQuestion for each.

Example questions (adapt based on the specific standard):

- "What problem does this pattern solve? Why not use the default/common approach?"
- "Are there exceptions where this pattern shouldn't be used?"
- "What's the most common mistake a developer or agent makes with this?"

Keep this brief. The goal is capturing the "why" behind the pattern, not exhaustive documentation.

**Auto mode:** skip this step entirely. The "why" will be inferred from code context and left for review. Do not invent reasons you cannot support from the code.

### Step 4: Write the Standards

For each standard:

1. Determine the appropriate folder (create if needed).

   **Interactive mode:** ask the user which subfolder of `agent-os/standards/` to place it in.

   **Auto mode:** infer from the file paths where the pattern was observed. Use these inference rules in order:
   - If the pattern lives in files under `api/`, `routes/`, `controllers/`, or `handlers/` → `api/`
   - If under `db/`, `database/`, `models/`, `migrations/`, or matches SQL files → `database/`
   - If under `components/`, `pages/`, `src/app/`, or matches `.tsx`/`.jsx` → `frontend/`
   - If under `tests/`, `spec/`, or matches `*_test.*`, `*.test.*`, `*.spec.*` → `testing/`
   - If the pattern is cross-cutting (naming, formatting, error handling across layers) → `global/`
   - Otherwise → root level of `agent-os/standards/`

2. Determine the file name.

   **Interactive mode:** ask the user to confirm or rename.

   **Auto mode:** generate a name from the pattern's most distinctive trait. Use kebab-case. Examples: `fastapi-dependency-injection`, `sql-server-temporal-tables`, `react-query-error-handling`. If a name collides with an existing standard, append `-v2`, `-v3`, etc.

3. Check if a related standard file already exists — append to it if so (interactive mode only; in auto mode, never append to existing files, always create a new one with a suffix to avoid silently polluting reviewed standards).

4. Draft the content.

   **Interactive mode:** use AskUserQuestion to confirm:

   ```
   Here's the draft for api/response-format.md:

   ---
   # API Response Format

   All API responses use this envelope:

   \`\`\`json
   { "success": true, "data": { ... } }
   { "success": false, "error": { "code": "...", "message": "..." } }
   \`\`\`

   - Never return raw data without the envelope
   - Error responses must include both code and message
   - Success responses omit the error field entirely
   ---

   Create this file? (yes / edit: [your changes] / skip)
   ```

   **Auto mode:** write the file directly. Generate a one-line description that starts with a verb (e.g. "Use X when Y", "Prefer A over B", "All API responses follow ..."), under 120 characters.

5. Create the file in `agent-os/standards/[folder]/`.

   **Interactive mode frontmatter:**
   ```
   ---
   description: <one-line description>
   ---
   ```

   **Auto mode frontmatter:**
   ```
   ---
   description: <one-line description>
   auto_generated: true
   needs_review: true
   generated_at: <ISO timestamp>
   generated_from_files:
     - <path1>
     - <path2>
     - <path3>
   ---
   ```

   The `generated_from_files` list should contain up to five representative files where the pattern was observed, so a later reviewer can quickly verify the extraction.

### Step 5: Update the Index

After all standards are created:

1. Scan `agent-os/standards/` for all `.md` files
2. For each new file without an index entry:

   **Interactive mode:** use AskUserQuestion:

   ```
   New standard needs an index entry:
     File: api/response-format.md

   Suggested description: "API response envelope structure and error format"

   Accept this description? (yes / or type a better one)
   ```

   **Auto mode:** use the description from the file's frontmatter as-is.

3. Update `agent-os/standards/index.yml`:

```yaml
api:
  response-format:
    description: API response envelope structure and error format
```

Alphabetize by folder, then by filename.

### Step 6: Report Results

**Interactive mode:** use AskUserQuestion:

```
Standards created for [area]:
- api/response-format.md
- api/error-codes.md

Would you like to discover standards in another area, or are we done?
```

**Auto mode:** print a summary (no question):

```
✓ Auto-discovery complete.

Created <N> standards across <M> areas:
  - api/<file>.md (needs review)
  - database/<file>.md (needs review)
  - frontend/<file>.md (needs review)
  ...

All <N> standards are marked needs_review: true.

Review them by running /discover-standards (without --auto) when you have time,
or let /finish-spec promote individual decisions into reviewed standards as
you close out each spec.

Run /index-standards if the index needs any cleanup (auto mode already added
basic entries).
```

## Output Location

All standards: `agent-os/standards/[folder]/[standard].md`
Index file: `agent-os/standards/index.yml`

## Writing Concise Standards

Standards will be injected into AI context windows. Every word costs tokens. Follow these rules:

- **Lead with the rule** — State what to do first, explain why second (if needed)
- **Use code examples** — Show, don't tell
- **Skip the obvious** — Don't document what the code already makes clear
- **One standard per concept** — Don't combine unrelated patterns
- **Bullet points over paragraphs** — Scannable beats readable

**Good:**
```markdown
# Error Responses

Use error codes: `AUTH_001`, `DB_001`, `VAL_001`

\`\`\`json
{ "success": false, "error": { "code": "AUTH_001", "message": "..." } }
\`\`\`

- Always include both code and message
- Log full error server-side, return safe message to client
```

**Bad:**
```markdown
# Error Handling Guidelines

When an error occurs in our application, we have established a consistent pattern for how errors should be formatted and returned to the client. This helps maintain consistency across our API and makes it easier for frontend developers to handle errors appropriately...
[continues for 3 more paragraphs]
```
