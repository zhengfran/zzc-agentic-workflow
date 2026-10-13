# Wayfinder minimap


The **minimap** is the whole effort in one picture: a Mermaid `flowchart` between the map body's `minimap` markers, regenerated from the map and its ticket notes. It is a view, not a store; note frontmatter remains authoritative and the frontier query decides which ticket a session takes.

Use one node per ticket and fog patch. Title ticket nodes with their human-readable note title, never a bare filename or number, and prefix each node to encode state. State is carried **twice**, by prefix and by colour: the prefix so the picture still reads where colour is dropped (plain-text diffs, monochrome print, colour-blind readers), the colour so the shape of the effort reads at a glance without parsing labels.

| Prefix | State | Class | Colour |
| --- | --- | --- | --- |
| `✓` | decided: resolved ticket | `decided` | green |
| `▶` | frontier: open, unblocked, unclaimed | `frontier` | amber |
| `●` | claimed, followed by `@dev` | `claimed` | blue |
| `○` | blocked | `blocked` | red |
| — | the destination | `dest` | violet |
| — | fog patch | `fog` | grey, dashed |
| — | out of scope | `oos` | faint grey, dashed |

The destination is a hexagon (`{{ }}`); fog patches and out-of-scope lines sit in their own labelled subgraphs. Edges run blocker → blocked. Every node is a gist: the detail stays in the tickets, and the answers stay in Decisions-so-far.

The `classDef` block is part of the generated minimap: emit it verbatim every regeneration, then assign every node a class with `class <ids> <name>`. Fills are light with explicit dark text, so the diagram stays legible under both light and dark Obsidian themes rather than inheriting whichever one rendered it.

```mermaid
flowchart LR
  t1(["✓ Where maps live"]) --> t2["▶ Ticket sizing"]
  t1 --> t3["● Label vocabulary @sam"]
  t2 --> t4["○ Blocking convention"]
  t4 --> D{{"Destination: a spec to hand off"}}
  subgraph fogzone ["Not yet specified"]
    f1["how resolutions get reviewed"]
  end
  subgraph ooszone ["Out of scope"]
    o1["migrating old issues"]
  end

  classDef decided  fill:#d3f9d8,stroke:#2f9e44,stroke-width:1.5px,color:#1b4332
  classDef frontier fill:#fff3bf,stroke:#f08c00,stroke-width:2px,color:#5c3d00
  classDef claimed  fill:#d0ebff,stroke:#1971c2,stroke-width:1.5px,color:#0b3d62
  classDef blocked  fill:#ffe3e3,stroke:#e03131,stroke-width:1.5px,color:#6a1414
  classDef dest     fill:#e5dbff,stroke:#7048e8,stroke-width:2px,color:#2f1c5c
  classDef fog      fill:#f1f3f5,stroke:#adb5bd,stroke-width:1px,color:#495057,stroke-dasharray:4 3
  classDef oos      fill:#f8f9fa,stroke:#ced4da,stroke-width:1px,color:#868e96,stroke-dasharray:2 3

  class t1 decided
  class t2 frontier
  class t3 claimed
  class t4 blocked
  class D dest
  class f1 fog
  class o1 oos
```
