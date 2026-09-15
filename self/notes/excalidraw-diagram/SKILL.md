---
name: excalidraw-diagram
description: Create Excalidraw files only when the user explicitly requests Excalidraw output.
disable-model-invocation: true
---

# Excalidraw diagram

Turn supplied content into an editable Excalidraw diagram and save it in the current working directory.

## Workflow

1. Choose the requested output: Obsidian Markdown (default), standard `.excalidraw`, or animated `.excalidraw`.
2. Identify the concepts, hierarchy, relationships, and reading order.
3. Choose a fitting layout: flowchart, mind map, hierarchy, relationship map, comparison, timeline, matrix, or freeform.
4. Read [`references/excalidraw-schema.md`](references/excalidraw-schema.md), then generate valid elements with unique IDs.
5. Read [`references/output-formats.md`](references/output-formats.md) and wrap the JSON exactly as required.
6. Save the file and report its absolute path and opening instructions.

## Design constraints

- Use `fontFamily: 5` and `lineHeight: 1.25` for text.
- Use at least 20 px for titles, 16 px for ordinary labels, and never below 14 px.
- Keep labeled shapes at least 120×60 px and leave 20–30 px between elements.
- Use simple shapes and color rather than emoji.
- Keep text dark enough for a white background; use a small, consistent semantic palette.
- Estimate text bounds before placing it and prevent overlap with shapes and connectors.
- Bind arrows and contained text when the relationship is structural.
- Include every required Excalidraw field documented in the schema reference.

## Completion

Parse the final JSON before reporting success. Confirm that every element has a unique ID, all text is readable, connectors reach their intended shapes, and the saved extension matches the selected output mode.
