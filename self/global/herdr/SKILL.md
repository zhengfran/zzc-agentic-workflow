---
name: herdr
description: "Control Herdr, a terminal multiplexer for coding agents. Use only when the user explicitly mentions Herdr or asks to use Herdr to inspect or control panes, tabs, workspaces, commands, or another agent. Do not use for generic delegation or background work. Requires HERDR_ENV=1."
---

# Herdr

Use Herdr only after an explicit Herdr request.

## Invocation workflow

1. **Guard the session.** Before any Herdr inspection or control command, run:

   ```bash
   test "${HERDR_ENV:-}" = 1
   ```

   If it fails, state that this is not a Herdr-managed pane and stop. Never control
   the focused Herdr session from outside Herdr.

2. **Learn the installed CLI.** The binary in `PATH` is authoritative. Begin with
   `herdr --help`, then print the relevant command group by running that group
   without a subcommand, such as `herdr agent` or `herdr pane`.

   Bare `herdr` launches or attaches the TUI. Avoid it for discovery. Never probe
   a mutating nested command by omitting arguments; some execute with defaults.

3. **Load only the branch reference needed for the request.**

   - **Agent lifecycle, launch, prompting, waiting, or agent UI:** read
     [`references/agents.md`](references/agents.md).
   - **Pane layout, shell availability, command execution, tabs, or workspaces:**
     read [`references/panes.md`](references/panes.md).
   - **Saved machine profile setup or mutation:** read
     [`references/machines.md`](references/machines.md).
   - **Remote host/session targeting or cross-machine identifiers:** read
     [`references/remotes.md`](references/remotes.md).
   - **Pane output sources, logs, transcripts, or missing scrollback:** read
     [`references/scrollback.md`](references/scrollback.md).

   Read every reference whose branch the request crosses.

4. **Inspect before mutating.** Discover live state and command options first.
   Use caller context (`$HERDR_WORKSPACE_ID`, `$HERDR_TAB_ID`,
   `$HERDR_PANE_ID`), `--current`, explicit IDs, or a unique live agent name.
   Omitted targets may resolve to another client's UI-focused pane.

5. **Execute from observed state.** Most control commands return JSON. Parse IDs,
   resolved targets, and lifecycle state from responses rather than predicting
   them. Preserve the user's focus with `--no-focus` for background work.

6. **Verify completion.** Inspect the resulting object or agent state and read
   relevant output. A timeout, stalled prompt, `blocked`, or `unknown` state is
   evidence to inspect, not permission to repeat input. Report created IDs,
   observed state, and unresolved blockers.

## Core safety

- Ask the user before answering an approval or question UI recognized as
  `blocked`.
- Close only workspaces, tabs, panes, or sessions created for this request,
  unless the user explicitly identifies another target to close.
- Treat `workspace close --group` as closing the primary workspace and all
  linked worktree workspaces; use it only with explicit user intent.
- Use `--trust-repository` only after the user verifies the repository.
- Check `herdr status` before depending on newly installed server features.
  A missing method is not permission to replace or upgrade the server.
- Run `herdr server stop` only when the user explicitly intends to stop the
  server and its pane processes. Never kill the main Herdr process; use named
  test sessions for isolation.
- Herdr server errors are JSON on stderr with exit status 1; CLI syntax errors
  use exit status 2.
