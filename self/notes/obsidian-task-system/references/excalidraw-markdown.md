# Excalidraw Markdown Compatibility

Read this reference only when creating, migrating, or repairing an
`.excalidraw.md` file directly. Ordinary card and relation work should use the
installed Excalidraw Automate or plugin API.

## Parsed Markdown Invariants

- Each mirrored text entry in `## Text Elements` has the form
  `raw text ^<element-id>`.
- `<element-id>` is exactly eight characters. The installed plugin's parser
  consumes exactly eight characters after `^`; longer IDs can split or
  duplicate visible text.
- Each key in `## Element Links` is an eight-character scene element ID.
- Every mirrored text or link ID exists in the serialized scene and is unique.
- Choose canonical mirrored text in this order:
  1. non-empty `rawText`
  2. non-empty `originalText`
  3. `text`
- Treat an empty string as absent. Do not use `rawText ?? originalText`, because
  an empty `rawText` wins that expression and produces a blank textbox.
- Preserve the plugin's section headings, fenced drawing block, and Markdown
  delimiters.

## Safe Rewrite Procedure

1. Close the drawing in Obsidian so an in-memory scene cannot overwrite the
   repair.
2. Parse or decompress the scene before changing it.
3. When changing an element ID, update every scene reference to that ID,
   including bindings, `boundElements`, `containerId`, `frameId`, and the
   Markdown Text Elements or Element Links entry.
4. Keep relation arrows and task links intact unless the requested repair
   explicitly changes their semantics.
5. Write through Obsidian's vault/file APIs when the app is live and link
   rewriting matters.
6. Run:

   ```bash
   node scripts/validate_task_drawing.js "/absolute/path/to/drawing.excalidraw.md"
   ```

7. Reopen the drawing, inspect every label and linked card, allow plugin
   autosave to finish, close it, and run the validator again.

The validator is a serialization check, not a visual-layout test. A successful
run must still be followed by an Obsidian reopen and visual inspection.
