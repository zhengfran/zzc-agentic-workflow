---
name: obsidian-task-system
description: Operate and maintain the personal Obsidian Task System. Use when capturing or promoting todos, creating or updating Task notes, working with Task Hub or project Bases, changing task status/WIP/dependencies/completion dates, adding or refreshing Excalidraw task cards and relations, running daily or weekly reviews, or diagnosing and migrating this system.
---

# Obsidian Task System

Treat Task-note metadata as the single source of truth. Treat Bases and
Excalidraw drawings as views over that metadata.

## Ground the Run

1. Resolve the live vault. Prefer the active workspace when it contains
   `03-Cards/Task System Usage Guide.md`; the current personal-vault fallback is
   `/Users/zhichengzheng/obsidian`.
2. Read `03-Cards/Task System Usage Guide.md` before any mutation.
3. Load only the additional live source needed for the requested branch:
   - Governance, review, or migration: `03-Cards/Task System.md`
   - Hub behavior or filtering: `07-Databases/Task Hub.base` and the relevant
     project `.base`
   - Command behavior or repair: `04-Extras/Scripts/JS/task-system.js`,
     `04-Extras/Templates/Task Template.md`, and QuickAdd configuration when
     commands are involved
   - Raw Excalidraw Markdown creation or repair:
     `references/excalidraw-markdown.md`
4. Inspect the target note, checkbox, Base, or drawing before acting.

Proceed when the vault and target are unambiguous and the requested action maps
to one of the branches below. Ask one focused question only when project,
parent, deadline, or the exact source checkbox cannot be inferred safely.

## Choose the Branch

### Capture or Promote Work

- Apply the live capture boundary from the usage guide.
- Leave qualifying tiny, immediately actionable work as a checkbox in its
  current context.
- Create a Task note for trackable work. Use the Task command rather than the
  Base `New` button.
- Promote an overnight checkbox through the promotion command so the original
  context remains traceable.
- Let blank project metadata enter Inbox; do not invent a project.

### Update or Complete a Task

- Preserve the note body and unrelated frontmatter.
- Check the relevant project's active-work limit before moving a task into an
  active state. Inbox is governed separately.
- Treat status, completion timestamp, and dependency metadata as distinct
  facts. Use the live reconciliation rules instead of inferring one from
  another.
- Update links through Obsidian's file APIs when moving or renaming notes so
  Bases and Excalidraw links can follow.

### Work with Bases

- Use Task Hub or the relevant project Base to inspect and move work.
- Verify the resulting Task-note metadata after a drag; the card position is
  not a second source of truth.
- Keep sync-conflict files excluded from views and counts.
- Use the Task creation command for new cards even when a Base offers a
  built-in creation affordance.

### Work with Excalidraw

- Create or attach task cards through the Task commands.
- Refresh cards after task metadata changes.
- Treat arrows as visual proposals until the relation-commit command writes the
  selected relation to metadata.
- Deleting a card or arrow changes the drawing only. Update Task metadata
  explicitly when the user intends a semantic deletion.
- Prefer Excalidraw Automate or the installed plugin API. Read
  `references/excalidraw-markdown.md` before editing `.excalidraw.md` text
  directly.

### Review, Diagnose, or Migrate

- Run reconciliation before interpreting inconsistent dates or states.
- Review Inbox, active work, blocked work, attention items, recent completion,
  and real deadlines using the live guide.
- For migrations, close affected drawings, test one tracer task end to end,
  then expand. Compare task counts and link targets, not only visible card
  totals.
- Exclude `.sync-conflict-` files from migration inputs unless conflict
  resolution is the explicit task.

## Execute

Prefer the installed `Task: ...` commands when they implement the requested
operation. In a live Obsidian session, invoke the exact command from the command
palette or its configured automation. Direct file edits are appropriate for
audits and repairs only when they preserve YAML types, WikiLinks, note bodies,
and unrelated metadata.

After each semantic change:

1. Confirm the Task note contains the intended metadata.
2. Run `Task: Reconcile` when status, dates, dependencies, or migration logic
   were involved.
3. Confirm the task appears in the expected Base view and group.
4. Refresh any affected task cards.
5. If a raw drawing file changed, run the bundled validator from this Skill
   directory:

   ```bash
   node scripts/validate_task_drawing.js "/absolute/path/to/drawing.excalidraw.md"
   ```

6. Close and reopen a changed drawing and visually inspect its text, links, and
   arrows. Re-run the validator after plugin autosave.

## Completion Criteria

Finish only when:

- Task metadata matches the user's intent and the live schema.
- Reconciliation produced no unexplained attention item.
- The expected Base view shows the task in the correct group.
- Affected Excalidraw cards and committed relations agree with metadata.
- No sync-conflict file was accidentally adopted as a canonical Task.

Report the changed note, Base, and drawing paths plus any remaining attention
item. If a required plugin or live Obsidian context is unavailable, complete
safe read-only checks and state the exact blocked action instead of guessing.
