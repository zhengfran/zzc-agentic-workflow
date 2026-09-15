---
name: archify
description: Create validated, explorable standalone HTML diagrams for technical architecture, workflows, sequences, data flow, and lifecycles. Use when HTML/Archify output is requested or repository evidence must drive a technical diagram; explicit Mermaid output belongs to the Mermaid skill.
license: MIT
metadata:
  version: "2.17"
  author: tt-a1i
  based_on: Cocoon-AI/architecture-diagram-generator (MIT, v1.0)
---

# Archify

Create a self-contained, interactive HTML diagram from a small typed JSON specification. Static output is the default; enable motion only when the user asks for a demo or presentation.

## Fast authoring path

Use this bounded path for ordinary generation; skip `references/viewer-runtime.md` unless the user asks about those features.

1. Choose `architecture`, `workflow`, `sequence`, `dataflow`, or `lifecycle` from the question.
2. Read only the matching schema in `schemas/`, `schemas/common.schema.json`, and one matching JSON example in `examples/`. Author fresh stable IDs, wording, and layout; use the example for field shape, not facts. Query `node bin/archify.mjs brands "<name>" --json` when real product identity matters (`references/brand-marks.md` covers an unmatched brand with a user-supplied URL).
3. Artifact first: write the candidate before inspecting renderer internals or planning coordinates in prose. Start with one clear main path, short side branches, sparse labels, at most 12 primary nodes, automatic routes/labels, and `meta.quality_profile: "showcase"` (unless a dense `standard` map is explicitly requested). Do not add `via`, `channelX`, `channelY`, or `labelAt` before a diagnostic calls for one; apply at most one diagnosed geometry control per repair.
4. Validate after every candidate edit and immediately before handoff:

   ```bash
   node bin/archify.mjs validate <type> <candidate.json> --quality showcase --json
   ```

   A receipt with only 4 artifact checks is basic validation, never showcase acceptance. A showcase pass must report all 9 artifact checks with 0 composition errors and 0 warnings. If the candidate omits or misspells the exact `meta.quality_profile` field, fix it before geometry. For a workflow v2 geometry diagnosis, run `node bin/archify.mjs validate workflow <candidate.json> --layout-json` and use the stable compiler receipt; solver internals are not authoring controls. A passing final validation freezes the candidate: never edit it afterward.
5. For a delivered HTML, `deliver` is the final acceptance command:

   ```bash
   node bin/archify.mjs deliver <type> <candidate.json> <output.html> --quality showcase --json
   ```

   A non-zero exit can never be described as success. A failed delivery preserves any previous output, so do not run `visual-check` on that path: it would inspect the stale last-good artifact, not the failed candidate. If validation fails, change only the diagnosed `subject`, verify `evidence`, choose from `supportedFixes`, and rerun. Continue focused correction while the objective error count reaches a new minimum. If two consecutive rounds do not improve that best count, stop and report the unresolved diagnostics truthfully.

## Update awareness

After the first candidate exists, run `node scripts/check-update.mjs` once and continue the requested workflow; if it cannot run, continue without mentioning it.

For `silent`, continue without mentioning the check. For `update_available`, show one compact notice (installed version, latest version, the checker's fixed local summary, release-notes link; label `security` severity plainly), state that the installed Skill is unchanged and the user decides whether/when to update — never quote or translate the remote manifest's summary, only the fixed local sentence — then acknowledge with `node scripts/check-update.mjs --ack "<eventKey>"` and continue the user's task.

This is information, not permission or action: the checker never downloads, installs, or executes an update, and silence is never consent. Do not read renderer/validator source or benchmarks before the first candidate; inspect implementation only for an unsupported diagnostic or after two failed focused repairs.

## Type router

| Type | Use for |
|---|---|
| `architecture` | Components, services, cloud/security boundaries, infrastructure |
| `workflow` | Processes, approval gates, tool calls, runbooks, CI/CD |
| `sequence` | API call chains, request lifecycles, async traces, returns |
| `dataflow` | Pipelines, ETL/ELT, lineage, governance, consumers |
| `lifecycle` | State/status transitions, retries, waiting and terminal states |

When ambiguous, run `node bin/archify.mjs guide "<scenario>" --json`. Scenario proof examples are structural references, not facts to copy.

## Mermaid input for Archify HTML

Only use this conversion when the user wants Archify HTML from supplied Mermaid. An explicit request for Mermaid output belongs to the Mermaid skill. Read the input for topology and meaning, then author fresh Archify JSON; do not mechanically render Mermaid styling: `flowchart`/`graph` → `workflow` (or `architecture` for a component map); `sequenceDiagram` → `sequence` (participants become semantic participants, arrows become messages); `stateDiagram` → `lifecycle` (states/transitions retain meaning, not Mermaid style).

## Authoring invariants

Default to omitting `meta.visual_preset`, `meta.subtitle`, `meta.legend`, `meta.locale` (outside `en`/`zh-CN`), `meta.engineering_profile`, `meta.column_fit` (sequence), and `brand` — each has a truthful renderer default, documented with its exact opt-in trigger in `references/authoring-contract.md`. Keep one obvious main path with short side branches; prefer automatic routing and let relationship labels stay semantic (never delete a meaningful one as a spacing repair). The standalone HTML must stay one responsive, first-screen desktop artifact with no overflow at 1440×900 through 1920×1080 (2048×1320 for large-display targets). Read `references/authoring-contract.md` before authoring anything beyond the fast path — full field enums, legend/language/preset/engineering-profile defaults, geometry and spacing rules, repair order, mode placement, and repository-evidence contract — and `references/brand-marks.md` when brand identity matters.

## Delivery

Use `validate` during repair and `deliver` once for final acceptance; it freezes the specification bytes into a private snapshot, renders and checks that snapshot, atomically commits the HTML, and reports SHA-256 plus byte counts. This is deterministic artifact evidence, not a Viewer exercise. Follow with bounded, non-mutating browser evidence:

```bash
node bin/archify.mjs visual-check <output.html> --json
```

Keep the three claims separate and report each independently: `deliver` (deterministic artifact checks), `visual-check` (bounded real-browser behavior), and perceptual visual review (requires an actual human or image-capable reviewer — an unconstrained glance supports only this claim). See `references/delivery-contract.md` for receipt fields, coverage, sidecars, exit behavior, and manual-record requirements.

For an active authoring loop only (never by default), preview locally:

```bash
node bin/archify.mjs preview <type> <input>.json <output>.html --quality showcase
```

Read `references/delivery-contract.md` when using preview, repository evidence, export receipts, or post-commit opening.

## Optional viewer capabilities

Generated HTML already contains theme switching, pan/zoom, search, focus, relationship tracing, semantic views, presentation, and truthful exports — reader capabilities, not extra authoring work. `meta.animation: "trace"` is opt-in; `meta.views` holds at most five curated chapters. Read `references/viewer-runtime.md` only when the user asks for Share Cards, Route/Reach cards, motion, guided stories, deep links, presentation, or search/focus.

## Setup and fallback

No install is required inside the skill package. Verify with:

```bash
node bin/archify.mjs doctor
node bin/archify.mjs demo <output-directory>
```

When shell access is unavailable, hand-place architecture SVG into `assets/template.html`, use CSS semantic classes rather than inline colors, and follow the visual review contract in `references/delivery-contract.md`.

## Output

Return the checked HTML path, diagram type, validation summary, specification/artifact receipt, browser-evidence status, and truthful visual-review status. Do not claim success for a non-zero command or claim visual inspection you did not perform.
