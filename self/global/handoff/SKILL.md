---
name: handoff
description: Create a resumable handoff through a portable file, a background agent, or Nowledge Mem. Use only when the user explicitly asks to hand off, checkpoint, or continue work elsewhere.
disable-model-invocation: true
argument-hint: "file | agent | memory; optional next-session focus"
---

# Handoff

Create one compact continuation record, then send it through the transport implied by the request:

- **file** — portable handoff for another harness, directory, person, or later session;
- **agent** — start a fresh background agent with the handoff as its prompt;
- **memory** — save a checkpoint through the runtime's native Nowledge connector or `nmem`.

Ask which transport only when the request does not make it clear. Never claim transcript fidelity: this is a structured continuation record.

## Build the record

Include only:

- goal and current state;
- decisions already made;
- artifact paths, URLs, commits, or issues;
- validation performed;
- unresolved risks or questions;
- one next action;
- suggested skills, or `none`.

Reference existing artifacts instead of copying them. Redact credentials, secrets, and personally identifiable information.

If the user supplied a next-session focus, shape the record around it.

## Send it

- **file:** write Markdown to the OS temporary directory and return its absolute path.
- **agent:** use the harness's native background-agent mechanism in the current working directory. Give the agent a descriptive name and submit the record inline. If no such mechanism exists, fall back to **file** and state that fallback.
- **memory:** prefer a native Nowledge thread/checkpoint tool. Otherwise run `nmem --json t create` with the record. Return the created identifier. If Nowledge is unavailable, fall back to **file**.

Completion means the selected transport accepted the record and the response names where it went.
