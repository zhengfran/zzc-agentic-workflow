---
name: aqrp
description: Check out, build, flash, access, and fast-redeploy AQRP across QNX7/QNX8 software variants and HDK2/HDK3 test benches. Use for any AQRP build, flash, side-load, or target-access task.
---

# aqrp

> **STUB.** Structure and content are being decided in the wayfinder ticket
> "A SKILL.md draft to react to". Do not treat this as the finished skill document.

`aqrp` puts every AQRP stage behind one command. Run `aqrp --help`.

## Workspaces

A **workspace** is a named checkout. Its name *is* its identity — two trees can share
every property and still be different workspaces. Never operate on a tree by path when a
name exists.

```
aqrp workspace list
aqrp workspace show <name>     # every derived value; the "why did it do that" command
```

Registered on this machine: `qnx8`, `prefot`, `qnx7`.

## Not yet implemented

`checkout`, `build`, `flash`, `shell`, `logs`, `push`, `reboot`, `deploy`, `all`.
