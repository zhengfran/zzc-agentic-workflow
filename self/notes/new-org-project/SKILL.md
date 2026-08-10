---
name: new-org-project
description: When the user shares a project idea OR points at an existing/completed project they want documented — a napkin sketch ("I want to build X"), a passing thought ("thinking about starting Y"), a detailed brief, OR an existing codebase path ("this project lives at /path/...") — relentlessly interview them round-by-round to resolve every branch of the decision tree (scope, constraints, risks, success criteria) OR read the existing code to ground the breakdown, then create a single Denote project note in their Emacs org-mode vault whose Epic→Story→Task tree is a native org heading tree wired to org-agenda, TODO keywords, and the project-table dynamic block. Use whenever the user presents ANY project-sized intent, even if they don't explicitly ask for breakdown. Triggers on "/new-org-project", "new project idea", "break this down", "let's plan this project", "新项目", "document this project", "I want to build/make/start", and similar phrasings.
---

# Project Breakdown (Emacs / Denote / Org-mode)

When the user shares a project idea, your job has two phases:

1. **Interview them** relentlessly, one question at a time, walking the decision tree until the project's shape is fully resolved.
2. **Break the outcome down** into a single Denote project note whose Epic→Story→Task structure is a native org heading tree.

Do not skip the interview. The value is in the friction — the questions force the user to confront decisions they were glossing over. A half-grilled idea produces a half-useful note tree.

This is the org-mode sibling of `new-obsidian-project`. The interview is identical; the breakdown maps to org's native primitives (heading tree, TODO keywords, agenda, column view) instead of Obsidian Bases. There is **no per-node file explosion and no database plumbing** — org gives hierarchy and roll-up for free.

## Phase 1 — The Interview

Mirror the `grill-me` methodology:

- **One question at a time.** Never batch. Wait for the answer before asking the next.
- **Walk the tree, don't survey.** Each answer opens new branches and closes others. Let the user's answer steer where you probe next.
- **Resolve dependencies.** If an earlier answer makes a later question moot, skip it. If a later answer contradicts an earlier one, loop back.
- **Always propose your recommended answer.** Frame every question as "Here's what I'd recommend — X — because Y. Does that fit, or would you rather Z?" This turns the interview into a collaborative design session, not a survey.
- **Research before asking.** If something can be answered by reading the vault (e.g., "have I done a similar project before?"), read it before asking. Glob `~/org/notes/projects/*.org` for related projects and reference them.
- **Push back on vagueness.** If the user says "some users", ask "which users, specifically — name one". If they say "soon", ask "by what date". If they say "I don't know", ask "what would you need to find out to know?"

### Dimensions to probe

The interview covers six dimensions. Walk them in rough order, but jump based on where clarity is weakest. Not every round is required for every project — see "Adaptive depth" below.

**Round 1 — Core (Why does this exist?)**
- What exactly are you building? Give me one sentence.
- Why now? What breaks if you don't do this?
- Who benefits? Just you, or others? Name one.
- What triggered this idea?

**Round 2 — Scope (Where are the edges?)**
- What's the minimum viable version — the smallest thing that proves the idea?
- What's the maximum ambition — the shiniest version?
- What's explicitly OUT of scope? Be specific.
- Must-have vs. nice-to-have split?

**Round 3 — Constraints (What's fixed?)**
- Deadline: hard / soft / none?
- Budget of money, time, energy?
- Tech / platform choices already locked in?
- Dependencies on other people or external systems?

**Round 4 — Approach (How?)**
- What are the phases — rough chronological shape?
- Riskiest assumption you're making?
- First concrete step you'd take tomorrow morning?
- Where do you start — core, edges, or infrastructure?

**Round 5 — Risks (What breaks this?)**
- What's most likely to kill this project?
- What would make you lose interest or procrastinate?
- Your failure mode on past projects — what's the pattern?
- Early-exit criterion: when would you abandon this?

**Round 6 — Success (When is it done?)**
- How will you KNOW it's done?
- Minimum "success" outcome?
- What would make you proud in a year?
- What will you specifically point at and say "this worked"?

### Adaptive depth

Calibrate rounds to project size:

- **Tiny** (weekend hack, <1 week): 2-3 rounds (Core + Scope + skim the rest). Move fast to breakdown.
- **Medium** (several weeks): 4-5 rounds.
- **Large** (months): all 6, possibly looped. Real projects deserve real grilling.

After each round, check in: *"Anything missing from this area, or shall we move to [next dimension]?"*

### Stopping criterion

Stop the interview when you can write a ~150-word project summary that covers:
- What it is (Core)
- What's in and out (Scope)
- What's fixed (Constraints)
- How you'll approach it (Approach)
- What could go wrong (Risks)
- How you'll know it's done (Success)

Confirm with the user: *"Here's what I've captured — does this feel like the whole picture? [summary]"*

If yes → proceed to Phase 2. If no → keep grilling on the weak spots.

## Phase 2 — The Breakdown

### Step 1 — Propose the tree

Before creating any file, draft the full tree in chat and get approval. This maps directly onto an org heading tree — Epics are level-1 headings, optional Stories are level-2, Tasks are leaf TODO headings:

```
📦 <Project Name>            (Denote file, #+status: Active)
 ├─ * Epic: <axis of work>            :epic:
 │   ├─ ** TODO <concrete action>     [#B]
 │   ├─ ** TODO <concrete action>
 │   └─ ** TODO <concrete action>
 ├─ * Epic: <axis of work>            :epic:
 │   ├─ ** Story: <grouping>          :story:   (only if Epic is large)
 │   │   ├─ *** TODO <action>
 │   │   └─ *** TODO <action>
 │   └─ ** TODO <action>
 └─ * Epic: ...                       :epic:
```

Sizing guidance:
- **3-7 Epics** per Project. Epics are major axes of work (e.g., "Build data pipeline", "Design UI", "Deploy + monitor"). Each is a level-1 (`*`) heading with an `:epic:` tag.
- **3-8 Tasks** per Epic (or per Story). Tasks are leaf headings carrying a TODO keyword.
- **Stories are optional** — use them only when an Epic has enough work to need intermediate grouping (e.g., 10+ tasks that cluster into 2-3 themes). A Story is a `:story:`-tagged heading one level above its Tasks.
- Every leaf Task should be concrete enough that a future-you can start it without re-planning.

Accept edits. The user will likely trim, merge, or rename things.

### Step 2 — Determine the keywords (the "Space")

This vault uses Denote keywords, not folders, to separate domains. Every project note gets the `project` keyword plus one domain keyword. Infer from context; confirm on ambiguous cases:
- `work` — work projects
- `life` — personal life projects
- `study` — learning projects

The file always lands in `~/org/notes/projects/`. The domain is encoded as a keyword (filetag), e.g. `__project_work`.

### Step 3 — Create the project note

This vault writes **one file per project**. The Epic/Story/Task hierarchy lives *inside* it as a heading tree — do NOT create a separate file per Epic or Task.

#### Step 3a — Compute the Denote filename

Run this to get the identifier, date stamp, and target directory:

```bash
echo "id:   $(date +%Y%m%dT%H%M%S)"
echo "date: $(date '+[%Y-%m-%d %a %H:%M]')"
echo "dir:  ~/org/notes/projects/"
```

Build the filename as `<id>--<slug>__<keywords>.org`:
- `<slug>`: title lowercased, spaces → hyphens, punctuation stripped. "Personal Budget Tracker" → `personal-budget-tracker`.
- `<keywords>`: the keywords joined by `_`, **alphabetically sorted** (Denote sorts them). `project` + `work` → `project_work`.
- Example: `20260630T141500--personal-budget-tracker__project_work.org`

#### Step 3b — Write the file

Write to `~/org/notes/projects/<filename>` using this template. Fill the front matter and replace the tree with the approved breakdown:

```org
#+title:      <Project Name>
#+date:       <date stamp from 3a>
#+filetags:   :project:<domain>:
#+identifier: <id from 3a>
#+status:     Active
#+category:   <ShortCategory>
#+columns:    %40ITEM(Task) %TODO %PRIORITY(Pri) %DEADLINE(Due)
#+startup:    content

* Overview
:PROPERTIES:
:Description: <1-sentence answer to "what is this?">
:Priority:    <High|Medium|Low>
:Due:         <YYYY-MM-DD, or leave empty>
:END:

** 🎯 Goal
<2-3 sentences — the "why" from Round 1>

** 📐 Scope
- *In*: <bullets from Round 2>
- *Out*: <what's explicitly excluded>
- *Success*: <from Round 6>

** ⚠️ Risks & Constraints
<from Rounds 3 + 5>

* Epic: <axis of work> [/]                                            :epic:
** TODO <concrete action>                                            [#B]
   DEADLINE: <YYYY-MM-DD Day>
** TODO <concrete action>
** TODO <concrete action>

* Epic: <axis of work> [/]                                           :epic:
** Story: <intermediate grouping> [/]                               :story:
*** TODO <action>
*** TODO <action>
** TODO <action>

* Epic: <axis of work> [/]                                           :epic:
** TODO <action>
** TODO <action>
```

Notes on the template:
- `#+status:` is the project lifecycle. Use `Active` for a project you intend to work on now (only `Active` projects enter `org-agenda-files`), `On-Hold` to park it, `Archived` when done. These are the exact values the `project-table` / `project-kanban` dynamic blocks recognize — do not invent new ones.
- `[/]` after an Epic/Story is a statistics cookie that auto-counts child TODOs. It counts *direct* children by default; for an Epic that contains Stories, add `:COOKIE_DATA: recursive` to that heading's property drawer if you want it to tally all the way down.
- Priority cookies are standard org: `[#A]` high, `[#B]` medium, `[#C]` low. Omit for unprioritised tasks.
- `DEADLINE:` only where the user gave a date. Don't fabricate deadlines.
- `#+columns:` enables a built-in dashboard: open the file and press `C-c C-x C-c` for a column-view table of every Task with its state, priority, and due date.

### Step 4 — Wire it in and report

The project is `Active`, so it joins the agenda automatically the next time the user opens it (`org-agenda` refreshes `org-agenda-files` from active project files via the `:before` advice). Tell the user they can run `M-x my/denote-refresh-agenda-list` if they want it picked up without reopening the agenda.

Then give a concise summary:
- Path where the file lives (`~/org/notes/projects/<filename>`)
- Count of Epics / Tasks created (e.g., "3 Epics, 11 Tasks")
- How to see it: it's now in `SPC m` agenda views; the project-table dynamic block (`my/project-insert-table-block`) lists it under **Active**.

## Vault schema reference (how the Obsidian concepts map to org)

| Obsidian concept | Org-mode equivalent in this vault |
|---|---|
| Note type Project | The Denote file itself, filetag `:project:` |
| Note type Epic / Story | Heading with `:epic:` / `:story:` tag |
| Note type Task | Leaf heading with a TODO keyword |
| `Phase` (project lifecycle) | `#+status:` keyword — `Active` / `On-Hold` / `Archived` |
| `Status` (Ready/Ongoing/Blocked/Done) | TODO keywords — `TODO` / `ONGOING` / `CANCEL` / `DONE` (Blocked → add a `:blocked:` tag to a TODO) |
| `Parent` (direct parent) | Implicit — heading nesting. No field. |
| `Project` (roll-up anchor) | Implicit — it's the file. No field. |
| `Priority` Low/Medium/High | Org priority cookies `[#C]` / `[#B]` / `[#A]` |
| `Due` | `DEADLINE:` (or `SCHEDULED:` for start dates) |
| `Description` | `:Description:` property in the Overview drawer |
| `![[Tasks.base]]` live tables | `#+columns:` column view + the `project-table` / `project-kanban` dynamic blocks |

Critical distinctions:
- **`#+status:` is ONLY for the project (file level).** Individual headings use TODO keywords, never `#+status:`.
- **Hierarchy is structural, not relational.** Don't add `Parent`/`Project` properties to headings — the heading depth *is* the hierarchy, and org-agenda rolls everything up by file. This is the whole reason the org version is simpler than the Obsidian one.
- **Stay inside the existing TODO keyword set** (`TODO ONGOING | CANCEL DONE`). Don't introduce `WAIT`/`BLOCKED` keywords — they aren't defined and would break agenda coloring. Use a `:blocked:` tag instead.

## Naming conventions

- **Project title** (`#+title:`): Title Case. e.g., "Personal Budget Tracker". The Denote slug is derived automatically.
- **Epic headings**: "Epic: Verb + noun phrase". e.g., "Epic: Build data ingestion pipeline".
- **Story headings**: "Story: <grouping>".
- **Task headings**: Concrete, specific action. e.g., "Define CSV schema for transactions".

## Do NOT

- Don't batch questions. One at a time — this is the core of the method.
- Don't accept "I don't know" without probing what's blocking the answer.
- Don't create the file before showing the full breakdown tree and getting approval.
- Don't skip proposing your recommended answer — it's half the value.
- Don't create a separate file per Epic or Task. One project = one file, hierarchy as headings.
- Don't add `Parent`/`Project` properties to headings — nesting handles it.
- Don't invent `#+status:` values beyond `Active` / `On-Hold` / `Archived`, or TODO keywords beyond the defined set.

## DO

- Do explore the vault first. Glob `~/org/notes/projects/*.org` for similar past projects and mention them: *"Your [[denote:...][Aurora]] project had a similar constraint — want to reuse that approach?"*
- Do propose concrete values (dates, priorities, scope cuts) when the user is vague. You're a collaborator, not a secretary.
- Do loop back if a later answer invalidates an earlier one. Explicitly: *"Your last answer means we should reconsider [earlier question] — let's revisit."*
- Do adapt depth to project size. A weekend hack shouldn't get the same grilling as a 6-month endeavor.
- Do write the `:Description:` property as the 1-sentence answer to "what is this?"
- Do add a `DEADLINE:` when the user gave a date, even informally ("by summer" → the last day of August that year).

## Example opening line

When the user drops an idea, open with something like:

> Got it — a budget tracker. Before I help you break this down, I want to grill you a bit to make sure we carve it up the right way. I'll go one question at a time.
>
> **Round 1, Question 1:** In one sentence, what *exactly* are you building? My guess: "An org-tracked tool that imports bank CSVs and categorizes spending for monthly reviews." Does that match, or are you thinking of something different?

Then listen, resolve, move to the next branch.
