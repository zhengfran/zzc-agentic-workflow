---
name: status
description: Diagnose Nowledge Mem connectivity and guide setup only when memory commands fail or the user asks about status, setup, or integration.
---

# Nowledge Mem status

Start with one observable check:

```bash
nmem --json status
```

Report connection, server and CLI versions, mode, and configuration without exposing credentials.

## If it fails

1. Check whether `nmem` exists.
2. On the Nowledge Desktop machine, ask the user to open the app and use its bundled CLI installer.
3. On another machine, use the standalone `nmem-cli` only after confirming Python 3.11+ and the intended remote server.
4. For remote mode, inspect `nmem config client show`; never print or overwrite an API key without confirmation.
5. Follow the current installation or integration documentation rather than an embedded agent matrix: <https://mem.nowledge.co/docs/integrations>.

Prefer, in order: a native connector, a supported agent plugin, direct MCP, then reusable CLI skills. Explain the behavior obtained—Working Memory, recall, distillation, and thread capture—without claiming that every host automates all four.

## Verify setup

```bash
nmem --json m search "test" -n 1
```

A result list or an empty list without an error proves the query path works. State which memory behaviors are automatic, guided, or manual for the active host.
