# Remote sessions and identifiers

Read this reference whenever a request crosses hosts, servers, or sessions.

Workspace, tab, pane, and live-agent names are scoped to one Herdr server. Two
saved machines may both expose `w1:p1` or `reviewer`; rediscover identifiers in
the intended remote session rather than carrying local IDs across hosts.

Selecting a machine in the TUI does not retarget commands launched from the
current pane. Those commands continue using their inherited session and socket
context. Run control commands on the intended host with its explicit session,
then inspect live state there before mutation.

`herdr machine list` is only a saved-profile list, not remote live state. For
profile mutation and setup safeguards, read [`machines.md`](machines.md).
