# Excalidraw JSON Schema Reference

## Color Palette

### Primary Colors
| Purpose | Color | Hex |
|---------|-------|-----|
| Main Title | Deep Blue | `#1e40af` |
| Subtitle | Medium Blue | `#3b82f6` |
| Body Text | Dark Gray | `#374151` |
| Emphasis | Orange | `#f59e0b` |
| Success | Green | `#10b981` |
| Warning | Red | `#ef4444` |

### Background Colors
| Purpose | Color | Hex |
|---------|-------|-----|
| Light Blue | Background | `#dbeafe` |
| Light Gray | Neutral | `#f3f4f6` |
| Light Orange | Highlight | `#fef3c7` |
| Light Green | Success | `#d1fae5` |
| Light Purple | Accent | `#ede9fe` |

## Element Types

### Rectangle
```json
{
  "type": "rectangle",
  "id": "unique-id",
  "x": 100,
  "y": 100,
  "width": 200,
  "height": 80,
  "strokeColor": "#1e40af",
  "backgroundColor": "#dbeafe",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "roughness": 1,
  "opacity": 100,
  "roundness": { "type": 3 }
}
```

### Text
```json
{
  "type": "text",
  "id": "unique-id",
  "x": 150,
  "y": 130,
  "text": "Content here",
  "fontSize": 20,
  "fontFamily": 5,
  "textAlign": "center",
  "verticalAlign": "middle",
  "strokeColor": "#1e40af",
  "backgroundColor": "transparent"
}
```

### Arrow
```json
{
  "type": "arrow",
  "id": "unique-id",
  "x": 300,
  "y": 140,
  "width": 100,
  "height": 0,
  "points": [[0, 0], [100, 0]],
  "strokeColor": "#374151",
  "strokeWidth": 2,
  "startArrowhead": null,
  "endArrowhead": "arrow"
}
```

### Ellipse
```json
{
  "type": "ellipse",
  "id": "unique-id",
  "x": 100,
  "y": 100,
  "width": 120,
  "height": 120,
  "strokeColor": "#10b981",
  "backgroundColor": "#d1fae5",
  "fillStyle": "solid"
}
```

### Diamond
```json
{
  "type": "diamond",
  "id": "unique-id",
  "x": 100,
  "y": 100,
  "width": 150,
  "height": 100,
  "strokeColor": "#f59e0b",
  "backgroundColor": "#fef3c7",
  "fillStyle": "solid"
}
```

### Line
```json
{
  "type": "line",
  "id": "unique-id",
  "x": 100,
  "y": 100,
  "points": [[0, 0], [200, 100]],
  "strokeColor": "#374151",
  "strokeWidth": 2
}
```

## Full JSON Structure

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [
    // Array of elements
  ],
  "appState": {
    "gridSize": null,
    "viewBackgroundColor": "#ffffff"
  },
  "files": {}
}
```

## Font Family Values

| Value | Font Name |
|-------|-----------|
| 1 | Virgil (hand-drawn) |
| 2 | Helvetica |
| 3 | Cascadia |
| 4 | Assistant |
| 5 | Excalifont (recommended) |

## Fill Styles

- `solid` - Solid fill
- `hachure` - Hatched lines
- `cross-hatch` - Cross-hatched
- `dots` - Dotted pattern

## Roundness Types

- `{ "type": 1 }` - Sharp corners
- `{ "type": 2 }` - Slight rounding
- `{ "type": 3 }` - Full rounding (recommended)

## Element Binding

To connect text to a container:

```json
{
  "type": "rectangle",
  "id": "container-id",
  "boundElements": [{ "id": "text-id", "type": "text" }]
}
```

```json
{
  "type": "text",
  "id": "text-id",
  "containerId": "container-id"
}
```

## Arrow Binding

To connect arrows to shapes:

```json
{
  "type": "arrow",
  "startBinding": {
    "elementId": "source-shape-id",
    "focus": 0,
    "gap": 5
  },
  "endBinding": {
    "elementId": "target-shape-id",
    "focus": 0,
    "gap": 5
  }
}
```

## Required runtime contract

Every element must include the common fields below. Do not add `frameId`, `index`, `versionNonce`, or `rawText`; those fields can break excalidraw.com compatibility. Use `boundElements: null`, not an empty array, and use `updated: 1`, not a timestamp.

```json
{
  "id": "unique-id",
  "type": "rectangle",
  "x": 100,
  "y": 100,
  "width": 200,
  "height": 50,
  "angle": 0,
  "strokeColor": "#1e1e1e",
  "backgroundColor": "transparent",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "strokeStyle": "solid",
  "roughness": 1,
  "opacity": 100,
  "groupIds": [],
  "roundness": {"type": 3},
  "seed": 123456789,
  "version": 1,
  "isDeleted": false,
  "boundElements": null,
  "updated": 1,
  "link": null,
  "locked": false
}
```

`strokeStyle` is `solid`, `dashed`, or `dotted`. Text elements also require:

```json
{
  "text": "Visible text",
  "fontSize": 20,
  "fontFamily": 5,
  "textAlign": "center",
  "verticalAlign": "middle",
  "containerId": null,
  "originalText": "Visible text",
  "autoResize": true,
  "lineHeight": 1.25
}
```

Obsidian output uses source `https://github.com/zsviczian/obsidian-excalidraw-plugin`; standard and animated output use `https://excalidraw.com`. Both include `appState` with `gridSize: null` and `viewBackgroundColor: "#ffffff"`, plus an empty `files` object. In Obsidian Markdown, leave the `## Text Elements` section empty because the plugin derives it from JSON.
