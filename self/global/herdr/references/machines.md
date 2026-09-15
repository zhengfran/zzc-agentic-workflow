# Saved machine profiles

Read this reference only when listing, adding, removing, enabling, disabling, or
setting up saved machine profiles. Inspect `herdr machine` and the relevant nested
help before mutation.

`herdr machine list` lists connection profiles, not a cross-machine pane inventory;
use `--json` for scripts. Profile operations affect client connection metadata:
removing a profile disconnects the client but does not stop the remote session.

Add, remove, enable, or disable profiles only when the user explicitly requests
that profile change. Adding a machine uses the remote default session unless
`--remote-session` is supplied. Experimental handoff is not part of `machine add`.

Setup asks before stopping an incompatible server and defaults to No. Preserve
that default unless the user explicitly consents to replacing the server. For
controlling panes or agents on another host, read
[`remotes.md`](remotes.md).
