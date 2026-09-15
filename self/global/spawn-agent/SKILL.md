---
name: spawn-agent
description: "Spawn Herdr-supported agents with workspace = project, tab = task, and pane = agent. Use only when the user explicitly asks to spawn, delegate to, or continue agents in Herdr; never for generic delegation. Requires HERDR_ENV=1."
argument-hint: "Task; agent count/roles; harness; model; effort"
---

# Spawn agents

Read [`../herdr/SKILL.md`](../herdr/SKILL.md) as the authority for Herdr CLI
discovery, identifiers, agent and pane behavior, lifecycle states, and safety.

## 1. Guard and topology

Before asking launch questions, run `test "${HERDR_ENV:-}" = 1`. If it fails,
state that spawning requires a Herdr-managed pane and stop.

Maintain one topology invariant:

- **Workspace = project**
- **Tab = task**
- **Pane = agent**

One task has one tab; collaborating agents have separate panes in that tab.

## 2. Resolve the launch group

Record the project root/workspace, task/tab label, agent count, and for every
agent: assignment, harness, model, effort, enforcement status for model and
effort, working directory, and write scope. Confirm any redundant independent
attempts explicitly. Group-wide choices apply to every agent.

Use the current directory and `$HERDR_WORKSPACE_ID` unless the user names another
project. Discover installed agent kinds through the Herdr workflow, then inspect
the chosen harness's local `--help` before translating model or effort into native
arguments. Ask for unresolved choices one at a time. An explicit `harness default`
is valid; never infer model or effort from this agent, configuration, task
complexity, or unstated defaults. If a choice cannot be enforced, ask whether to
accept that, use the harness default, or change harness.

When write scopes overlap, record one collision plan before launch: one writer
plus read-only peers, non-overlapping ownership, user-provided isolated working
directories/worktrees, or explicit acceptance of the race risk.

The group is resolved only when every field and any required collision plan is
explicit.

## 3. Build inline handoffs

Create one compact shared handoff plus an agent-specific assignment. Each handoff
must label: task focus; project root; task-tab ID (`unknown until created` is
valid); sibling names or `none`; harness/model/effort and both enforcement
statuses; exclusive assignment; collaboration boundary; write scope; relevant
artifacts/URLs or `none`; suggested skills or `none`; unresolved questions or
`none`; and this return contract:

> End when finished or blocked with `## Return handoff`: outcome, changed artifact
> paths, validation, unresolved questions, and next action. Reference artifacts
> instead of copying them; redact secrets.

Keep the handoff in memory, scan it for secrets and personal data, and transfer it
inline. Through a shell, protect multiline text with a single-quoted heredoc and a
unique delimiter. Use a temporary file only after an explicit transport-size error.

## 4. Resolve the task tab and panes

Reuse the captured project workspace and task-tab ID when unambiguous. Otherwise
create/select the project workspace and exactly one task tab without changing
focus. A new workspace's initial tab becomes the task tab. If several existing
tabs could match and no ID was captured, ask the user rather than using position.

Use a newly created tab's root pane for the first agent. Reuse another pane only
when Herdr verifies an available shell; otherwise split balanced panes in the task
tab with each agent's cwd and `--no-focus`. Create no additional task tabs.

Choose unique valid agent names, start each requested harness only in its assigned
pane, and pass only help-verified model/effort arguments. Resolve launch failures
through the Herdr workflow without silently changing any selection. Launch is
complete when Herdr recognizes every expected agent as ready.

## 5. Transfer and report

Prompt every agent with its specific inline handoff, without waiting between
submissions so the group can run concurrently. A successful submission to every
agent is the completion criterion; inspect ambiguous failures before retrying.

Report workspace ID, task-tab ID, and each agent's name, pane ID, assignment,
harness, model, effort, enforcement statuses, cwd, write scope, and inline
transport. Leave the original tab focused.
