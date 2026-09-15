---
name: grilling
description: Stress-test a plan, decision, or idea through a relentless design-tree interview. Use when the user asks to be grilled or wants assumptions and unresolved decisions exposed.
argument-hint: "Topic; optionally docs mode"
---

# Grilling

Interview until the user and agent share a complete decision model. Represent the work as a **design tree**: each settled decision unlocks dependent decisions.

## Run one round

1. Build the **frontier**: every unresolved decision whose prerequisites are settled.
2. Resolve environmental facts yourself with tools or background research.
3. Ask the whole frontier in one numbered round.
4. Give a recommended answer and short trade-off for each question.
5. Wait for the user's answers, update the tree, and repeat.

A question dependent on another open answer belongs to a later round. Decisions belong to the user; discoverable facts do not.

Use the runtime's user-question tool when it can express the frontier without losing necessary context.

## Docs mode

When the user asks for a paper trail, also apply the `domain-modeling` skill when available:

- update the repository glossary as domain terms settle;
- record only hard-to-reverse decisions as ADRs;
- keep implementation plans out of the glossary.

Do not create documents in ordinary chat mode.

## Completion

The interview is complete when the frontier is empty and every branch is either settled or explicitly out of scope. Present the resulting decisions and unresolved exclusions, then wait for the user's confirmation before implementation.
