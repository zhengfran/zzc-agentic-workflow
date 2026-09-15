# Excalidraw output formats

## Obsidian Markdown

Use `.md` with this exact wrapper:

```markdown
---
excalidraw-plugin: parsed
tags: [excalidraw]
---
==⚠  Switch to EXCALIDRAW VIEW in the MORE OPTIONS menu of this document. ⚠== You can decompress Drawing data with the command palette: 'Decompress current Excalidraw file'. For more info check in plugin settings under 'Saving'

# Excalidraw Data

## Text Elements
%%
## Drawing
```json
{JSON data}
```
%%
```

## Standard Excalidraw

Write plain JSON to `.excalidraw`:

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [],
  "appState": {"gridSize": null, "viewBackgroundColor": "#ffffff"},
  "files": {}
}
```

## Animated Excalidraw

Use the standard `.excalidraw` format and add this field to each element:

```json
"customData": {"animate": {"order": 1, "duration": 500}}
```

Order title, main structure, connectors, then detail. Equal order values animate together. The result can be opened at <https://dai-shi.github.io/excalidraw-animate/>.
