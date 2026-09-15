# Agent control

Read this reference for agent lifecycle, launch, prompting, waiting, or agent UI.
The installed `herdr agent` help remains authoritative for kinds and options.

## Model and targets

A pane exists independently of an agent. `agent start` requires an existing
available shell pane; it never creates, splits, or moves layout. Use pane commands
for ordinary processes and agent commands when Herdr must validate agent identity
or lifecycle.

Agent commands accept a unique live agent name or the pane ID hosting that agent,
not a terminal ID or bare kind. Names match `[a-z][a-z0-9_-]{0,31}` and are unique
among live agents. A name follows its occupant and clears when the agent exits, is
released, or is replaced.

Lifecycle states:

- `idle` and `done`: ready for input. Server "seen" state distinguishes them;
  reads do not mark seen, focus does, and each TUI tracks viewed completions.
- `working`: active.
- `blocked`: recognized approval or question UI; inspect it and ask the user
  before responding.
- `unknown`: present but not confidently classified; never assume completion.

## Start

Verify the destination is at an interactive shell prompt with the shell in the
foreground and no foreground command, editor, or agent. Inspect `herdr agent` for
supported kinds and native options, check `herdr agent list` for name collisions,
then start:

```bash
herdr agent start reviewer --kind <kind> --pane <pane-id>
herdr agent start reviewer --kind <kind> --pane <pane-id> -- <native-args...>
```

Native arguments belong after `--`. Success means Herdr detected the expected
agent in the same pane and found it ready. Startup defaults to 30 seconds.
`agent_not_ready` during a blocked startup leaves the name usable for inspection;
wait for `idle` before prompting.

## Prompt and wait

```bash
herdr agent prompt reviewer "<task>" --wait --timeout 120000
herdr agent wait reviewer --until blocked --timeout 120000
```

Prompt submission writes text and encoded Enter as one ordered operation. A
successful write does not itself prove a turn began. With `--wait`, Herdr requires
observed `working` or `blocked` activity within five seconds, then waits for the
first settled `idle`, `done`, or `blocked` state. The timeout includes submission;
without one, the settled-state wait is indefinite after activity. If the agent was
already working, settlement of that active turn may satisfy the wait.

Use `--until` only for a state-specific workflow. Standalone `agent wait` without
it uses the same settled states. `agent_prompt_stalled` and `timeout` do not prove
the prompt was undelivered: inspect before retrying.

## Inspect and interact

```bash
herdr agent get reviewer
herdr agent read reviewer --source recent-unwrapped --lines 120
herdr agent send-keys reviewer esc
herdr agent send-keys reviewer ctrl+c
```

Prefer the agent surface for recognized agents; use pane input only when raw
terminal control is intentional. Herdr validates all logical keys before writing.
