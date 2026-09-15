# Panes, tabs, and workspaces

Read this reference for layout, available shells, ordinary commands, tabs, or
workspaces. Inspect the relevant installed command-group help before mutation.

## Discover and target

Herdr topology is workspace → tab → pane. Pane commands control raw terminals;
a pane need not contain a recognized agent. Caller context is available as:

```bash
printf '%s\n' "$HERDR_WORKSPACE_ID" "$HERDR_TAB_ID" "$HERDR_PANE_ID"
herdr workspace list
herdr tab list --workspace "$HERDR_WORKSPACE_ID"
herdr pane current --current
herdr pane list --workspace "$HERDR_WORKSPACE_ID"
```

Public IDs are opaque stable handles such as `w1`, `w1:t1`, and `w1:p1`. Closed
tab and pane IDs are not reused. Creation responses provide the next targets:
`workspace create` returns `.result.workspace`, `.result.tab`, and
`.result.root_pane`; `tab create` returns `.result.tab` and `.result.root_pane`;
`pane split` returns `.result.pane`.

After `pane move`, continue with `.result.move_result.pane.pane_id` or the live
agent name. The previous pane ID is not a general target; only the moved process's
inherited caller context keeps resolving it.

## Create layout

For ordinary background work, default to a sibling pane in the current tab and
`$PWD`. Create another workspace, tab, worktree, or cwd only when the user requests
that topology or the task-specific skill requires it.

Honor a requested split direction. Otherwise inspect the anchor:

```bash
herdr pane layout --pane <anchor-pane-id>
```

Split a wide pane right and a narrow or tall pane down. Keep focus unchanged,
preserve cwd explicitly, parse the new pane ID, and alternate geometry as needed
to avoid unusably narrow columns or short rows:

```bash
herdr pane split --pane <anchor-pane-id> --direction <right-or-down> \
  --cwd "<working-directory>" --no-focus
```

An available shell pane is at its interactive prompt with the shell itself in the
foreground and no foreground command, editor, or agent. Treat an occupied or
uncertain pane as a split anchor, not a destination.

## Run an ordinary command

```bash
herdr pane run <pane-id> "just test"
herdr pane wait-output <pane-id> --match "test result" --timeout 120000
herdr pane read <pane-id> --source recent-unwrapped --lines 120
```

`pane run` atomically submits command text and Enter. `wait-output` immediately
searches the selected snapshot, so prior output may match. `--match` is a literal
substring; `--regex` is a Rust regular expression. Without `--timeout`, waiting
is indefinite. For output-source selection and missing history, read
[`scrollback.md`](scrollback.md).
