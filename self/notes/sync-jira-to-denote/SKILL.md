---
name: sync-jira-to-denote
description: Sync Jira tickets into a denote org file with full hierarchy, incremental updates, and org-mode formatting. Use when user says "sync jira", "sync tickets", or references syncing Jira tickets to an org file.
---

# Sync Jira Tickets to Denote Org File

## Trigger
User says: "sync jira" or "sync tickets" while in a denote org project file, or references syncing Jira tickets to an org file.

## Input
A denote org file path (e.g., `~/org/notes/projects/20260610T143359--paccar-analog-camera-bring-up__project.org`)

## Procedure

### 1. Read the org file and extract keywords
- Read the `#+KEYWORDS:` property from the file header (comma-separated list).
- These keywords are used as JQL search terms.

### 1a. Inventory what's already in the file (for incremental sync)
- Scan the whole org file for existing headings with a `:JIRA_KEY:` property.
- Build a map of `JIRA_KEY → :JIRA_UPDATED:` timestamp (and heading location) for everything already present.
- This map drives incremental sync: tickets already in the file are only re-fetched/rewritten when Jira has a newer `updated` time.

### 2. Search Jira for matching tickets
- For each keyword, run: `text ~ "<keyword>" AND assignee = currentUser() ORDER BY updated DESC`
- Deduplicate results across all keyword searches.
- All tickets must be assigned to the current user.

### 2b. Validate keyword presence (filter false positives)
- Jira's `text ~` full-text search can return false positives (matches on linked issues, indexed metadata, or related content that doesn't actually appear in the ticket's own fields).
- After fetching full details for each ticket (step 3), **verify** that at least one keyword actually appears (case-insensitive) in the ticket's own summary OR description text.
- If a ticket is a subtask/child whose **parent** passes validation, the child is kept regardless (inherited relevance).
- Discard any ticket that fails this check and is not a child of a validated ticket.

### 2a. Walk up the parent chain
- For each assigned ticket found in step 2, follow its parent links all the way to the top-level ticket.
- A ticket's parent comes from the `parent` field (for subtasks) or from an issue link of type "Parent-Child" / a parent Epic link.
- Recursively fetch each parent's parent until a ticket with no parent is reached (the top-level ticket, typically an Epic or Initiative).
- Add every ancestor ticket to the sync set, **even if it is not assigned to the current user**. These ancestors are included for hierarchy context only.
- Deduplicate ancestors against the assigned tickets and against each other (a shared parent is synced once).

### 3. Fetch full details for each ticket
- The search/parent-chain results return each ticket's `updated` timestamp cheaply. Before fetching full details, compare against the inventory from step 1a:
  - If the key already exists in the file and its `updated` time is **not newer** than the stored `:JIRA_UPDATED:`, skip it — leave the existing heading untouched.
  - Only call `get_ticket_by_key` for tickets that are **new** or whose Jira `updated` time is **newer** than what's in the file.
- For tickets that need fetching, extract: key, type, status, resolution, priority, assignee, reporter, created, updated, sprint, fix version, story points, team (customfield_21000), domain (customfield_20108), platform (customfield_13713), time spent, estimated time, acceptance criteria (customfield_10115), description, comments, parent, subtasks, issue links.

### 4. Determine org-mode TODO state
- Read the user's `org-todo-keywords` from their Emacs config at `~/dotconfig/basic/editor/emacs/modular/` (grep for `org-todo-keywords`).
- Map Jira status to org keyword:
  - "Working" / "In Progress" → the in-progress keyword (e.g., `ONGOING`)
  - "Closed" / "Done" → `DONE`
  - "Discarded" / "Cancelled" → `CANCEL`
  - Everything else (Open, New, Backlog) → `TODO`

### 5. Determine heading hierarchy from ticket relationships
- Reconstruct the full parent → child chain from the assigned ticket up to its top-level ancestor (from step 2a).
- Nest each ticket as a deeper heading level under its parent: e.g. top-level Epic at `**`, its child Story at `***`, a subtask at `****`.
- A ticket assigned to the current user keeps its full org heading (TODO state, properties, body). Ancestor tickets not assigned to the user are still written as headings (for context) but mark them with a `:JIRA_CONTEXT: t` property so they're distinguishable.
- If a ticket is a **child** of another ticket via issue links (type "Parent-Child"), note in `:RELATIONSHIP:` property.
- If a ticket **clones** another, note in `:RELATIONSHIP:` property.

### 6. Write/update org headings
For each ticket, write a heading in this format. Append the Jira issue type as an org tag at the end of the heading line (e.g. `:Epic:`, `:Story:`, `:Bug:`, `:Task:`, `:Subtask:`). Use the issue type name with spaces removed (e.g. "Sub-task" → `:Subtask:`).

```org
** STATE [[https://ix.jira.automotive.cloud/browse/KEY][KEY]] Summary    :Story:
DEADLINE: <YYYY-MM-DD Day>
:PROPERTIES:
:JIRA_KEY:   KEY
:JIRA_TYPE:  Issue Type
:JIRA_STATUS: Status Name
:JIRA_RESOLUTION: Resolution (if closed)
:JIRA_PRIORITY: Priority
:JIRA_ASSIGNEE: Display Name
:JIRA_REPORTER: Display Name
:JIRA_CREATED: [YYYY-MM-DD Day HH:MM]
:JIRA_UPDATED: [YYYY-MM-DD Day HH:MM]
:JIRA_SPRINT: Sprint Name
:JIRA_FIX_VERSION: Version Name
:JIRA_STORY_POINTS: N
:JIRA_TEAM:  ART / Agile Team
:JIRA_DOMAIN: Domain / SubDomain
:JIRA_PLATFORM: Variant
:JIRA_TIME_SPENT: Xh
:JIRA_ESTIMATED: Xh
:JIRA_TASK_TYPE: Task Type (for subtasks)
:JIRA_ACCEPTANCE: Acceptance criteria text
:JIRA_PARENT: Parent key (for subtasks)
:RELATIONSHIP: relationship info
:END:

Description text from Jira.

- Goal: ...
- Done: ...
- Remaining: ...

**** Comments
- [DATE] Author :: Comment body (skip Jenkins/automation noise)
```

### 6a. DEADLINE from fix version
- If a ticket has a `fixVersions` entry with a `releaseDate`, set an org-mode `DEADLINE:` line using that date.
- The DEADLINE line goes between the heading line and the `:PROPERTIES:` drawer, using the format `DEADLINE: <YYYY-MM-DD Day>` (org active timestamp without time).
- If the ticket has multiple fix versions, use the **earliest** `releaseDate`.
- If `fixVersions` is empty or has no `releaseDate`, omit the DEADLINE line.
- On incremental update, refresh the DEADLINE if the fix version changed; remove it if fix version was cleared.

### 7. Comment filtering
- Skip comments that are purely automated (VERIFYME, Jenkins build logs, DOORS verification logs).
- Include meaningful human comments (status updates, decisions, clarifications).

### 8. Ordering
- Top-level ancestor tickets order their child branches by activity: active/in-progress first, then closed (newest first).
- Within a branch, nest children and subtasks under their parent headings following the chain from step 5.

### 9. Update vs Create (incremental)
- Only act on tickets that were actually fetched in step 3 (new or changed). Skipped tickets are left exactly as-is.
- If a heading with matching `:JIRA_KEY:` already exists, update it in place — refresh the Jira-managed properties, status/TODO state, tag, description, and comments.
  - Preserve any manual content the user added under the heading that isn't Jira-managed (notes, extra subheadings, checkboxes). Don't clobber the whole subtree; only rewrite the Jira-sourced fields.
- If no matching `:JIRA_KEY:` exists, create the heading (nested per step 5, or appended to `* Tasks` if it's a new top-level branch).
- Never remove headings that exist in the file but not in Jira (user may have added manual notes, or it may be a manually-added ticket).

## Notes
- The Jira base URL is: `https://ix.jira.automotive.cloud`
- Org timestamps use format: `[YYYY-MM-DD Day HH:MM]`
- Omit properties that have no value (don't write `:JIRA_TIME_SPENT:` if null).
- IIP-267479 style tickets (created by the user during session) should also be synced.
